import sys
import os
import re
import clang.cindex
from clang.cindex import CursorKind

# Monkey-patch clang.cindex.CursorKind.from_id to handle Clang DLL version mismatches gracefully
try:
    _orig_from_id = clang.cindex.CursorKind.from_id
    def _safe_from_id(id):
        if id == 350:
            return clang.cindex.CursorKind.TRANSLATION_UNIT
        try:
            return _orig_from_id(id)
        except ValueError:
            return clang.cindex.CursorKind.TRANSLATION_UNIT
    clang.cindex.CursorKind.from_id = _safe_from_id
except Exception:
    pass

DEFAULT_CONFIG = { 'MAX_LOOP_UNROLL': 5, 'MAX_RECURSION_DEPTH': 50, 'BIT_WIDTH': 32 }

try:
    paths = [
        "C:/Program Files/LLVM/bin",
        "C:/Program Files (x86)/LLVM/bin",
        "/usr/lib/llvm-14/lib",
        "/usr/lib/x86_64-linux-gnu"
    ]
    for p in paths:
        if os.path.exists(p):
            clang.cindex.Config.set_library_path(p)
            break
except: pass

def parse_c_file(filepath):
    print(f"  [Parser] Analizando: {filepath} (Modo Tokens)")
    try:
        index = clang.cindex.Index.create()
        # PARSE_DETAILED_PROCESSING_RECORD expone los #define como cursores
        # MACRO_DEFINITION; sin esta opcion, _extract_config no veia las macros
        # DIOPHANTUS_* y SIEMPRE usaba los valores por defecto (bug: el usuario
        # fijaba MAX_RECURSION=300 y se compilaba con 50 en silencio).
        tu = index.parse(
            os.path.abspath(filepath), args=['-std=c11', '-nostdinc'],
            options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
        )
        if not tu: raise RuntimeError("Fallo Clang")

        return {
            'state_vars': _find_vars(tu.cursor, filepath),
            'logic_tree': _find_main(tu.cursor),
            'functions': _find_funcs(tu.cursor, filepath),
            'struct_defs': _find_structs(tu.cursor, filepath),
            'config': _extract_config(tu.cursor)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  [Parser Crash] {e}")
        sys.exit(1)

def _extract_config(root):
    cfg = DEFAULT_CONFIG.copy()
    for node in root.get_children():
        if node.kind == CursorKind.MACRO_DEFINITION:
            ts = list(node.get_tokens())
            if len(ts) >= 2:
                try:
                    if ts[0].spelling == "DIOPHANTUS_MAX_RECURSION": cfg['MAX_RECURSION_DEPTH'] = int(ts[1].spelling)
                    elif ts[0].spelling == "DIOPHANTUS_MAX_UNROLL": cfg['MAX_LOOP_UNROLL'] = int(ts[1].spelling)
                    elif ts[0].spelling == "DIOPHANTUS_BIT_WIDTH": cfg['BIT_WIDTH'] = int(ts[1].spelling)
                except: pass
    return cfg

def _is_local(node, path):
    if not node.location.file: return True
    return os.path.abspath(node.location.file.name) == os.path.abspath(path)

def _find_structs(root, path):
    s = {}
    for n in root.get_children():
        if _is_local(n, path) and n.kind == CursorKind.STRUCT_DECL and n.spelling:
            s[n.spelling] = [c.spelling for c in n.get_children() if c.kind == CursorKind.FIELD_DECL]
    return s

def _find_vars(root, path):
    v = []
    if root.kind == CursorKind.TRANSLATION_UNIT:
        for n in root.get_children():
            if _is_local(n, path) and n.kind == CursorKind.VAR_DECL:
                v.append(n.spelling)
    return v

def _find_funcs(root, path):
    f = {}
    for n in root.get_children():
        if _is_local(n, path) and n.kind == CursorKind.FUNCTION_DECL and n.spelling != 'main' and n.is_definition():
            params = [c.spelling for c in n.get_children() if c.kind == CursorKind.PARM_DECL]
            body = next((c for c in n.get_children() if c.kind == CursorKind.COMPOUND_STMT), None)
            if body: f[n.spelling] = {'params': params, 'body': _parse_node(body)}
    return f

def _find_main(root):
    main = next((n for n in root.get_children() if n.kind == CursorKind.FUNCTION_DECL and n.spelling == 'main'), None)
    if not main: raise RuntimeError("No main")
    body = next((n for n in main.get_children() if n.kind == CursorKind.COMPOUND_STMT), None)
    loop = next((n for n in body.get_children() if n.kind in [CursorKind.WHILE_STMT, CursorKind.FOR_STMT]), None)
    if not loop: raise RuntimeError("No loop in main")
    children = list(loop.get_children())
    return _parse_node(children[-1])

def _parse_node(node):
    if not node: return None
    k = node.kind

    if k == CursorKind.COMPOUND_STMT:
        return {'type': 'Block', 'statements': [_parse_node(c) for c in node.get_children()]}
    if k == CursorKind.RETURN_STMT:
        c = list(node.get_children())
        return {'type': 'Return', 'value': _parse_node(c[0]) if c else None}

    if k == CursorKind.IF_STMT:
        c = list(node.get_children())
        return {'type': 'If', 'condition': _parse_node(c[0]), 'then_body': _parse_node(c[1]), 'else_body': _parse_node(c[2]) if len(c)>2 else None}

    if k == CursorKind.BINARY_OPERATOR:
        children = list(node.get_children())
        if len(children) < 2: return None

        valid_ops = {'+=', '-=', '*=', '/=', '%=', '^=', '&=', '|=', '<<=', '>>=',
                     '==', '!=', '<=', '>=', '&&', '||', '<<', '>>',
                     '+', '-', '*', '/', '%', '^', '&', '|', '<', '>', '='}

        # El operador binario es el token situado ENTRE el operando izquierdo y
        # el derecho. Localizarlo por posicion de fuente (offset) es robusto;
        # el metodo anterior (elegir por longitud entre TODOS los tokens del
        # nodo) fallaba en expresiones anidadas: p. ej. en (3*n+1)/2 elegia el
        # primer operador de igual longitud ('*') en vez del propio ('/'),
        # compilando 6*n en lugar de (3*n+1)/2.
        op = None
        left, right = children[0], children[1]
        try:
            left_end = left.extent.end.offset
            right_start = right.extent.start.offset
            for token in node.get_tokens():
                ts = token.location.offset
                if left_end <= ts < right_start and token.spelling in valid_ops:
                    op = token.spelling
                    break
        except Exception:
            op = None

        if not op:
            # Fallback al metodo por longitud (solo si el offset no resolvio).
            for token in node.get_tokens():
                if token.spelling in valid_ops and (op is None or len(token.spelling) > len(op)):
                    op = token.spelling
        if not op: op = "+"

        if op in ['=', '+=', '-=', '*=', '/=', '%=', '^=', '&=', '|=', '<<=', '>>=']:
             return {'type': 'Assign', 'target': _parse_node(children[0]), 'op': '=', 'value': _parse_node(children[1])}
        return {'type': 'BinaryOp', 'op': op, 'left': _parse_node(children[0]), 'right': _parse_node(children[1])}

    if k == CursorKind.UNEXPOSED_EXPR:
        children = list(node.get_children())
        if children: return _parse_node(children[0])

    if k == CursorKind.CALL_EXPR:
        return {'type': 'FuncCall', 'name': node.spelling, 'args': [_parse_node(c) for c in node.get_children()]}

    if k == CursorKind.INTEGER_LITERAL:
        ts = list(node.get_tokens())
        val = 0
        if ts:
            raw_val = ts[0].spelling
            clean_val = re.sub(r'[uUlL]+$', '', raw_val)
            try: val = int(clean_val, 0)
            except: val = 0
        return {'type': 'Constant', 'value': val}

    if k == CursorKind.CHARACTER_LITERAL:
        # Literal de carácter ('q', '\n', ...): se trata como su valor entero
        # (código del carácter). Antes caía en el `return None` final y se
        # colaba como operando None en el sistema (bug de pong: `k == 'q'`).
        ts = list(node.get_tokens())
        val = 0
        if ts:
            inner = ts[0].spelling.strip()
            if len(inner) >= 2 and inner[0] == "'" and inner[-1] == "'":
                inner = inner[1:-1]
            try:
                decoded = inner.encode('utf-8').decode('unicode_escape')
                val = ord(decoded[0]) if decoded else 0
            except Exception:
                val = ord(inner[0]) if inner else 0
        return {'type': 'Constant', 'value': val}

    if k == CursorKind.DECL_REF_EXPR: return {'type': 'Var', 'name': node.spelling}
    if k == CursorKind.UNARY_OPERATOR: return {'type': 'UnaryOp', 'op': '-', 'operand': _parse_node(list(node.get_children())[0])}
    if k in [CursorKind.PAREN_EXPR, CursorKind.CSTYLE_CAST_EXPR]:
        children = list(node.get_children())
        if children: return _parse_node(children[0])
    if k == CursorKind.DECL_STMT:
        c = list(node.get_children())
        if c and c[0].kind == CursorKind.VAR_DECL:
            var = c[0]
            # CORRECCIÓN: antes el inicializador se descartaba (value=None), de
            # modo que `int next_val = (3*n+1)/2;` se compilaba como next_val=0
            # (bug que falsea la lógica, p. ej. en collatz). El inicializador es
            # el último hijo-expresión del VAR_DECL (si lo hay).
            init_kids = list(var.get_children())
            init_val = _parse_node(init_kids[-1]) if init_kids else None
            return {'type': 'Declare', 'target': var.spelling, 'value': init_val}

    return None