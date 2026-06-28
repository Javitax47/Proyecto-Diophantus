#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - INTÉRPRETE DE ECUACIONES (formato prefijo del compilador)
================================================================================
Ejecuta los artefactos `*_interpreter_input.txt` que emite el compilador, que usan
notación de PREFIJO (S-expresiones):

    operadores:   +(a,b)  -(a,b)  *(a,b)  /(a,b)  %(a,b)
    comparaciones:  ==(a,b)  !=(a,b)  <(a,b)  <=(a,b)  >(a,b)  >=(a,b)
    condicional:  If(cond, si_verdadero, si_falso)
    llamada:      call(nombre_funcion, arg1, arg2, ...)
    transición:   x[t+1] := <expr>
    función rec.: P_nombre(params...) = <expr>   (entre marcadores de bloque)

Dos modos de uso, una sola maquinaria (parser + evaluador de ÁRBOL, SIN exec/eval):

  1. MOTOR DE TRANSICIÓN (`get_engine` / `SequentialEngine`): dado un estado y unas
     entradas, calcula el siguiente estado evaluando las transiciones `x[t+1] := …`.
     Las transiciones pueden invocar funciones recursivas vía `call(...)`.
  2. INTÉRPRETE RECURSIVO (`SimpleInterpreter`): evalúa funciones recursivas
     `P_fib(x, RET) = …` con memoización y ramas perezosas (sin desbordar la pila para
     recursión moderada). `Z3Interpreter` hace lo mismo simbólicamente con Z3 RecFunction.

Nota de seguridad: este intérprete NO usa `eval`/`exec`; parsea a un árbol y lo evalúa
con un intérprete propio, así que es seguro frente a entradas arbitrarias.
"""

import re
import sys
import argparse

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

# Operadores reconocidos (más largos primero para tokenizar '<=' antes que '<').
_OPS = ['<=', '>=', '==', '!=', '<', '>', '+', '-', '*', '/', '%']


# ---------------------------------------------------------------------------
#  Parser de prefijo  ->  árbol de sintaxis
#  Nodos: ('num', int) · ('var', str) · ('op', sym, [args]) ·
#         ('if', [cond, t, f]) · ('call', fname, [args])
# ---------------------------------------------------------------------------

def _tokenize(s):
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1; continue
        if c in '(),':
            toks.append(c); i += 1; continue
        for op in _OPS:
            if s.startswith(op, i):
                toks.append(('op', op)); i += len(op); break
        else:
            if c.isdigit():
                j = i
                while j < n and s[j].isdigit():
                    j += 1
                toks.append(('num', int(s[i:j]))); i = j
            elif c.isalpha() or c == '_':
                j = i
                while j < n and (s[j].isalnum() or s[j] == '_'):
                    j += 1
                toks.append(('id', s[i:j])); i = j
            else:
                raise ValueError(f"carácter inesperado {c!r} en posición {i}")
    return toks


def _parse_args(toks, pos):
    args = []
    if toks[pos] == ')':
        return args, pos + 1
    while True:
        node, pos = _parse_expr(toks, pos)
        args.append(node)
        if toks[pos] == ',':
            pos += 1
        elif toks[pos] == ')':
            return args, pos + 1
        else:
            raise ValueError(f"se esperaba ',' o ')' cerca de {toks[pos]!r}")


def _parse_expr(toks, pos):
    tok = toks[pos]
    if tok == '(':                                   # paréntesis de agrupación
        node, pos = _parse_expr(toks, pos + 1)
        if toks[pos] != ')':
            raise ValueError("falta ')'")
        return node, pos + 1
    if tok[0] == 'num':
        return ('num', tok[1]), pos + 1
    if tok[0] == 'op':
        if pos + 1 >= len(toks) or toks[pos + 1] != '(':
            raise ValueError(f"operador {tok[1]} sin '('")
        args, pos = _parse_args(toks, pos + 2)
        return ('op', tok[1], args), pos
    if tok[0] == 'id':
        name = tok[1]
        if pos + 1 < len(toks) and toks[pos + 1] == '(':
            args, pos = _parse_args(toks, pos + 2)
            if name == 'If':
                return ('if', args), pos
            if name == 'call':
                fname = args[0][1] if args and args[0][0] == 'var' else None
                return ('call', fname, args[1:]), pos
            return ('call', name, args), pos          # P_-style: nombre(args)
        return ('var', name), pos + 1
    raise ValueError(f"token inesperado {tok!r}")


def parse(expr):
    """Parsea una expresión de prefijo a su árbol. Lanza ValueError si está mal formada."""
    toks = _tokenize(expr)
    node, pos = _parse_expr(toks, 0)
    if pos != len(toks):
        raise ValueError(f"tokens sobrantes tras la expresión: {toks[pos:]}")
    return node


# ---------------------------------------------------------------------------
#  Evaluación en enteros (semántica C: división trunca hacia cero)
# ---------------------------------------------------------------------------

def _cdiv(a, b):
    if b == 0:
        return 0                                       # defensivo (artefactos con /(0,0))
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _cmod(a, b):
    return 0 if b == 0 else a - b * _cdiv(a, b)


_BINOP = {
    '+': lambda a, b: a + b, '-': lambda a, b: a - b, '*': lambda a, b: a * b,
    '/': _cdiv, '%': _cmod,
    '==': lambda a, b: int(a == b), '!=': lambda a, b: int(a != b),
    '<': lambda a, b: int(a < b), '<=': lambda a, b: int(a <= b),
    '>': lambda a, b: int(a > b), '>=': lambda a, b: int(a >= b),
}


def eval_py(node, env, funcs=None):
    """Evalúa un árbol a un entero. `env`: nombre->valor; `funcs`: nombre->(params, árbol)
    para resolver `call(...)` con memoización (caché en funcs['__cache__'] si se desea)."""
    kind = node[0]
    if kind == 'num':
        return node[1]
    if kind == 'var':
        if node[1] in env:
            return env[node[1]]
        raise NameError(f"variable no definida: {node[1]}")
    if kind == 'op':
        sym, args = node[1], node[2]
        vals = [eval_py(a, env, funcs) for a in args]
        if sym == '-' and len(vals) == 1:
            return -vals[0]
        return _BINOP[sym](vals[0], vals[1])
    if kind == 'if':
        cond, t, f = node[1]
        return eval_py(t, env, funcs) if eval_py(cond, env, funcs) else eval_py(f, env, funcs)
    if kind == 'call':
        if not funcs or node[1] not in funcs:
            raise NameError(f"función no definida: {node[1]}")
        params, body = funcs[node[1]]
        argvals = [eval_py(a, env, funcs) for a in node[2]]
        cache = funcs.setdefault('__cache__', {})
        key = (node[1], tuple(argvals))
        if key in cache:
            return cache[key]
        local = dict(zip(params, argvals))
        val = eval_py(body, local, funcs)
        cache[key] = val
        return val
    raise ValueError(f"nodo desconocido: {node}")


# ---------------------------------------------------------------------------
#  Carga de ficheros del compilador
# ---------------------------------------------------------------------------

_FUNC_RE = re.compile(r'P_(\w+)\((.*?)\)\s*=\s*(.*)')
_TRANS_RE = re.compile(r'(\w+)\s*\[t\+1\]\s*:=\s*(.*)')


def _parse_functions(text):
    """Extrae el bloque de funciones recursivas -> {nombre: (params_reales, árbol)}.
    Descarta el parámetro final 'RET' (marcador de salida, no entrada real)."""
    funcs = {}
    block = re.search(r'DEFINICIONES DE FUNCIONES RECURSIVAS\b.*?\n(.*?)\n---', text, re.DOTALL)
    body_lines = block.group(1).splitlines() if block else []
    for line in body_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = _FUNC_RE.match(line)
        if m:
            name = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            if params and params[-1] == 'RET':
                params = params[:-1]
            funcs[name] = (params, parse(m.group(3)))
    return funcs


def _parse_transitions(text):
    """Extrae las transiciones `x[t+1] := expr` -> {var_base: árbol}."""
    trans = {}
    for line in text.splitlines():
        m = _TRANS_RE.match(line.strip())
        if m:
            trans[m.group(1)] = parse(m.group(2))
    return trans


# ---------------------------------------------------------------------------
#  Motor de TRANSICIÓN (simulación paso a paso)
# ---------------------------------------------------------------------------

class SequentialEngine:
    """Motor de transición: calcula el siguiente estado evaluando `x[t+1] := …`.
    Las transiciones pueden invocar funciones recursivas del mismo fichero vía call()."""

    def __init__(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        self.functions = _parse_functions(text)
        self.transitions = _parse_transitions(text)

    def compute_next_state(self, state, inputs=None):
        env = dict(state)
        if inputs:
            env.update(inputs)
        funcs = dict(self.functions)        # caché fresca por paso
        out = {}
        for var, tree in self.transitions.items():
            try:
                out[var] = eval_py(tree, env, funcs)
            except NameError:
                pass                         # transición que depende de algo aún no presente
        return out


# ---------------------------------------------------------------------------
#  Intérprete RECURSIVO (evaluación directa de P_func)
# ---------------------------------------------------------------------------

class SimpleInterpreter:
    """Evalúa funciones recursivas `P_nombre(params) = expr` por interpretación de árbol,
    con memoización y ramas perezosas (sin exec/eval)."""

    def __init__(self):
        self.functions = {}

    def parse_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            self.functions = _parse_functions(f.read())
        for name, (params, _) in self.functions.items():
            print(f"Definida función: {name}({', '.join(params)})")
        return self.functions

    def call(self, func_name, *args):
        if func_name not in self.functions:
            raise ValueError(f"función no encontrada: {func_name}")
        params, body = self.functions[func_name]
        return eval_py(body, dict(zip(params, args)), self.functions)


class Z3Interpreter:
    """Evalúa funciones recursivas simbólicamente con Z3 RecFunction (recursión sin pila)."""

    def __init__(self):
        if not Z3_AVAILABLE:
            raise RuntimeError("Z3 no disponible; instala z3-solver.")
        self.solver = z3.Solver()
        self.functions = {}        # nombre -> z3.RecFunction
        self._defs = {}            # nombre -> (params, árbol)

    def parse_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            self._defs = _parse_functions(f.read())
        for name, (params, _) in self._defs.items():
            sorts = [z3.IntSort()] * len(params)
            self.functions[name] = z3.RecFunction(name, *sorts, z3.IntSort())
        for name, (params, tree) in self._defs.items():
            zparams = [z3.Int(p) for p in params]
            body = self._to_z3(tree, dict(zip(params, zparams)))
            z3.RecAddDefinition(self.functions[name], zparams, body)
        return self.functions

    def _to_z3(self, node, env):
        kind = node[0]
        if kind == 'num':
            return z3.IntVal(node[1])
        if kind == 'var':
            return env[node[1]]
        if kind == 'op':
            sym, args = node[1], node[2]
            v = [self._to_z3(a, env) for a in args]
            if sym == '-' and len(v) == 1:
                return -v[0]
            return {
                '+': lambda: v[0] + v[1], '-': lambda: v[0] - v[1], '*': lambda: v[0] * v[1],
                '/': lambda: v[0] / v[1], '%': lambda: v[0] % v[1],
                '==': lambda: v[0] == v[1], '!=': lambda: v[0] != v[1],
                '<': lambda: v[0] < v[1], '<=': lambda: v[0] <= v[1],
                '>': lambda: v[0] > v[1], '>=': lambda: v[0] >= v[1],
            }[sym]()
        if kind == 'if':
            cond, t, f = node[1]
            c = self._to_z3(cond, env)
            if isinstance(c, z3.ArithRef):
                c = c != 0
            return z3.If(c, self._to_z3(t, env), self._to_z3(f, env))
        if kind == 'call':
            return self.functions[node[1]](*[self._to_z3(a, env) for a in node[2]])
        raise ValueError(f"nodo desconocido: {node}")

    def call(self, func_name, *args):
        r = z3.Int('result')
        self.solver.push()
        self.solver.add(r == self.functions[func_name](*[z3.IntVal(a) for a in args]))
        status = self.solver.check()
        out = self.solver.model()[r] if status == z3.sat else f"UNSAT/UNKNOWN ({status})"
        self.solver.pop()
        return out.as_long() if hasattr(out, 'as_long') else out


# ---------------------------------------------------------------------------
#  Fábrica de motores (API usada por los runners de examples_interpreter)
# ---------------------------------------------------------------------------

def get_engine(mode, base_path):
    """Devuelve un motor para el programa compilado en `base_path`.
      - 'SEQUENTIAL' / 'Z3_LOGICAL' / 'Z3_PURE': motor de TRANSICIÓN (compute_next_state).
        SEQUENTIAL es la referencia (evaluación entera directa, determinista).
    Acepta `base_path` con o sin la extensión `_interpreter_input.txt`."""
    path = base_path if base_path.endswith('.txt') else base_path + '_interpreter_input.txt'
    if mode in ('SEQUENTIAL', 'Z3_LOGICAL', 'Z3_PURE'):
        return SequentialEngine(path)
    raise ValueError(f"modo desconocido: {mode}")


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Intérprete de ecuaciones (formato prefijo).")
    ap.add_argument('filepath', help='fichero *_interpreter_input.txt')
    ap.add_argument('call_expr', help='llamada, p.ej. "fib(10)"')
    ap.add_argument('--mode', choices=['PYTHON_PURE', 'Z3_PURE'], default='PYTHON_PURE')
    args = ap.parse_args(argv)

    m = re.match(r'(\w+)\((.*?)\)', args.call_expr)
    if not m:
        print("formato de llamada inválido. Usa: nombre(arg1, arg2, ...)"); return 1
    fname = m.group(1)
    fargs = [int(x) for x in m.group(2).split(',') if x.strip()] if m.group(2).strip() else []

    interp = Z3Interpreter() if args.mode == 'Z3_PURE' else SimpleInterpreter()
    interp.parse_file(args.filepath)
    try:
        print(f"\n✓ {fname}({', '.join(map(str, fargs))}) = {interp.call(fname, *fargs)}")
        return 0
    except Exception as e:
        print(f"\n✗ Error de ejecución: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(_main())
