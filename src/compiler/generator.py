import sys
import copy
from collections import defaultdict

# Asegurar límite alto internamente también
sys.setrecursionlimit(200000)

class AstFlattener:
    def __init__(self, state_vars, functions_ast, struct_defs, config, symbolic_mode=False):
        self.state_vars = set(state_vars)
        self.functions = functions_ast
        self.struct_defs = struct_defs
        
        self.current_state = {var: var for var in state_vars}
        self.aux_vars = {}
        self.input_vars = set()
        
        self.scope_stack = []
        self.call_counter = 0
        self.recursion_depth = defaultdict(int)
        self.assign_counter = 0 # Para SSA estricto
        
        self.MAX_LOOP_UNROLL = config.get('MAX_LOOP_UNROLL', 5)
        self.MAX_RECURSION_DEPTH = config.get('MAX_RECURSION_DEPTH', 50)
        self.symbolic_mode = symbolic_mode

        # SOUNDNESS (§4.2): rastreo de truncamiento por presupuesto. Si la
        # expansion alcanza el limite de recursion, el sistema generado deja de
        # ser fiel al programa original; en vez de fallar en silencio lo
        # registramos para anclar una variable `overflow` (ver PolynomialConverter).
        self.overflow_triggered = False
        self.overflow_events = 0

        # Normalizacion de control de flujo y anti-blowup en cada cuerpo:
        #  1) hundir las sentencias tras un 'if' que retorna hacia su 'else'
        #     (patron guard-clause: `if(c) return X; resto` -> `if(c, X, resto)`),
        #  2) fusionar tail-calls (anti-blowup exponencial).
        import os as _os
        for _fname, _fdef in self.functions.items():
            if isinstance(_fdef, dict) and _fdef.get('body'):
                _fdef['body'] = self._normalize_early_returns(_fdef['body'])
                if _os.environ.get('DIOPH_NO_TAIL_MERGE') != '1':
                    _fdef['body'] = self._merge_tail_calls(_fdef['body'])
        
        # Cache para resolución
        self.resolve_cache = {}
        self.resolving_stack = set()

    def generate_function_F(self, logic_tree):
        self._visit(logic_tree)
        
        function_F = {}
        for var in self.state_vars:
            if var in self.current_state:
                # Limpiar caché antes de resolución final
                self.resolve_cache = {}
                self.resolving_stack = set()
                function_F[var] = self._resolve_expression(self.current_state[var])
            else:
                function_F[var] = var
        return function_F

    def generate_function_relation(self, func_name, func_node):
        self.current_state = {}
        self.aux_vars = {}
        params = self.functions[func_name]['params']
        for p in params: self.current_state[p] = p
            
        body_expr = self._visit(func_node)
        
        self.resolve_cache = {}
        self.resolving_stack = set()
        return {
            'name': func_name,
            'params': params + ['RET'],
            'body': self._resolve_expression(body_expr)
        }

    def _get_scoped_name(self, name):
        if name in self.state_vars: return name
        prefix = "_".join(self.scope_stack) if self.scope_stack else ""
        return f"{prefix}_{name}" if prefix else name

    def _new_ssa_var(self, name):
        """Crea una nueva versión única de una variable para evitar ciclos."""
        self.assign_counter += 1
        # Si es variable de estado, no cambiamos nombre, pero la lógica de update
        # maneja el valor. Si es auxiliar, versionamos.
        if name in self.state_vars: return name
        scoped = self._get_scoped_name(name)
        return f"{scoped}_v{self.assign_counter}"

    def _resolve_expression(self, expr):
        """
        Resuelve variables recursivamente con protección contra ciclos y memoización.
        """
        # 1. Tipos base
        if isinstance(expr, int): return expr
        
        # 2. Check Memoización (hashable types only)
        try:
            if expr in self.resolve_cache: return self.resolve_cache[expr]
        except: pass # Listas no son hashable, ignorar

        # 3. Variables (Strings)
        if isinstance(expr, str):
            # DETECCIÓN DE CICLOS
            if expr in self.resolving_stack:
                return expr # Ciclo detectado: devolver el símbolo sin expandir
            
            if expr in self.aux_vars:
                self.resolving_stack.add(expr)
                res = self._resolve_expression(self.aux_vars[expr])
                self.resolving_stack.remove(expr)
                self.resolve_cache[expr] = res
                return res
            return expr # Variable libre o input
        
        # 4. Tuplas (Operaciones)
        if isinstance(expr, tuple):
            op = expr[0]
            args = [self._resolve_expression(arg) for arg in expr[1:]]
            res = (op,) + tuple(args)
            try: self.resolve_cache[expr] = res
            except: pass
            return res
            
        return expr

    # --- VISITANTES ---

    def _visit(self, node):
        if node is None: return None
        method = getattr(self, f'_visit_{node["type"]}', self._visit_default)
        return method(node)

    def _visit_default(self, node): return None

    def _visit_Block(self, node):
        last = None
        for s in node['statements']: last = self._visit(s)
        return last

    def _visit_ForLoop(self, node):
        comps = node['components'] # init, cond, inc, body
        if len(comps) < 4: return
        self._visit(comps[0]) # Init
        for _ in range(self.MAX_LOOP_UNROLL):
            cond = self._visit(comps[1])
            self._execute_conditional(cond, comps[3], None)
            self._visit(comps[2]) # Inc

    def _visit_WhileLoop(self, node):
        for _ in range(self.MAX_LOOP_UNROLL):
            cond = self._visit(node['condition'])
            self._execute_conditional(cond, node['body'], None)

    def _execute_conditional(self, cond, body_node, else_node):
        # Guardar estado antes
        state_before = self.current_state.copy()
        
        # Ejecutar rama TRUE
        self._visit(body_node)
        state_true = self.current_state.copy()
        
        # Restaurar y ejecutar rama FALSE
        self.current_state = state_before.copy()
        if else_node: self._visit(else_node)
        state_false = self.current_state
        
        # Merge (Phi function)
        self._merge_states(state_false, state_true, cond)

    def _visit_If(self, node):
        cond = self._visit(node['condition'])
        val_then = None; val_else = None
        
        # State Merge Logic
        state_before = self.current_state.copy()
        
        if node['then_body']: val_then = self._visit(node['then_body'])
        state_then = self.current_state.copy()
        
        self.current_state = state_before
        if node['else_body']: val_else = self._visit(node['else_body'])
        state_else = self.current_state
        
        self._merge_states(state_else, state_then, cond)
        
        # Return value merge (ternary)
        if val_then is not None and val_else is not None:
            return ('if', cond, val_then, val_else)
        return val_then if val_then is not None else val_else

    def _merge_states(self, state_else, state_then, cond):
        new_state = state_else.copy()
        keys = set(state_then.keys()) | set(state_else.keys())
        for k in keys:
            vt = state_then.get(k, k)
            ve = state_else.get(k, k)
            if vt != ve:
                # Aquí creamos una nueva variable auxiliar para el resultado del merge
                # para evitar expresiones gigantes repetidas
                merged_expr = ('if', cond, vt, ve)
                # Opcional: Asignar a variable auxiliar SSA si la expresión crece
                new_state[k] = merged_expr
        self.current_state = new_state

    def _visit_Ternary(self, node):
        # Expresion condicional (creada por la fusion de tail-calls): se
        # aritmetiza igual que un 'if' de valor -> tupla ('if', c, vt, vf).
        cond = self._visit(node['cond'])
        vt = self._visit(node['then'])
        vf = self._visit(node['else'])
        return ('if', cond, vt, vf)

    # --- NORMALIZACION DE 'EARLY RETURN' (guard clauses) ---
    # En un bloque, un `if (c) { ... return ... }` SIN else seguido de mas
    # sentencias significa que esas sentencias solo se ejecutan si c es falso.
    # El modelo de valores del flattener no tiene control de flujo / return
    # temprano, asi que reescribimos:  [if(c, T_que_retorna, None), resto...]
    #   ->  [if(c, T_que_retorna, Block(resto...))]
    # Sin esto, el return temprano (caso base de muchos algoritmos) se perdia y
    # solo sobrevivia el camino de caida (bug de generalidad: guard clauses).
    def _always_returns(self, body):
        """True si `body` retorna en todos sus caminos."""
        if not isinstance(body, dict):
            return False
        t = body.get('type')
        if t == 'Return':
            return True
        if t == 'Block':
            stmts = body.get('statements') or []
            return bool(stmts) and self._always_returns(stmts[-1])
        if t == 'If':
            return (body.get('else_body') is not None
                    and self._always_returns(body.get('then_body'))
                    and self._always_returns(body.get('else_body')))
        return False

    def _normalize_early_returns(self, node):
        if not isinstance(node, dict):
            return node
        t = node.get('type')
        if t == 'Block':
            stmts = [self._normalize_early_returns(s) for s in node.get('statements', [])]
            out = []
            i = 0
            while i < len(stmts):
                s = stmts[i]
                if (isinstance(s, dict) and s.get('type') == 'If'
                        and not s.get('else_body')
                        and self._always_returns(s.get('then_body'))
                        and i + 1 < len(stmts)):
                    # las sentencias restantes pasan a ser el else del if
                    rest = self._normalize_early_returns(
                        {'type': 'Block', 'statements': stmts[i + 1:]})
                    out.append({'type': 'If', 'condition': s['condition'],
                                'then_body': s['then_body'], 'else_body': rest})
                    return {'type': 'Block', 'statements': out}
                out.append(s)
                i += 1
            return {'type': 'Block', 'statements': out}
        if t == 'If':
            if node.get('then_body'):
                node['then_body'] = self._normalize_early_returns(node['then_body'])
            if node.get('else_body'):
                node['else_body'] = self._normalize_early_returns(node['else_body'])
            return node
        return node

    # --- FUSION DE TAIL-CALLS (anti-blowup exponencial) ---
    # Reescribe `if c then [decls_t] return f(A) else [decls_e] return f(B)`
    # en `return f(phi(c, A, B))`, inlinando las declaraciones locales de cada
    # rama en los argumentos. Identidad: f deterministica => f(c?A:B) = c?f(A):f(B).
    # Colapsa la recursion ramificada (collatz, etc.) de 2^profundidad a lineal.
    def _merge_tail_calls(self, node):
        if not isinstance(node, dict):
            return node
        t = node.get('type')
        if t == 'Block':
            node['statements'] = [self._merge_tail_calls(s) for s in node['statements']]
            return node
        if t == 'If':
            if node.get('then_body'):
                node['then_body'] = self._merge_tail_calls(node['then_body'])
            if node.get('else_body'):
                node['else_body'] = self._merge_tail_calls(node['else_body'])
            merged = self._try_merge_if(node)
            return merged if merged is not None else node
        return node

    def _as_tail_call(self, body):
        """Si `body` se reduce a [Declare*, Return(FuncCall(f, args))] devuelve
        (fname, args, subst); subst mapea las locales declaradas a su expresion
        (para inlinarlas en los argumentos). Si no, None."""
        if not isinstance(body, dict):
            return None
        stmts = body['statements'] if body.get('type') == 'Block' else [body]
        subst = {}
        for i, s in enumerate(stmts):
            st = s.get('type')
            if st == 'Declare':
                subst[s['target']] = s.get('value')
            elif st == 'Return':
                if i != len(stmts) - 1:
                    return None
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'FuncCall':
                    return (v['name'], v.get('args', []), subst)
                return None
            else:
                return None  # otra sentencia (Assign con efectos, etc.) -> no fusionar
        return None

    def _inline(self, expr, subst):
        """Sustituye recursivamente las referencias a variables locales de
        `subst` por su expresion (tambien inlinada)."""
        if not isinstance(expr, dict):
            return expr
        if expr.get('type') == 'Var' and expr.get('name') in subst and subst[expr['name']] is not None:
            return self._inline(subst[expr['name']], subst)
        new = dict(expr)
        for key in ('left', 'right', 'operand', 'cond', 'then', 'else', 'value', 'condition'):
            if isinstance(new.get(key), dict):
                new[key] = self._inline(new[key], subst)
        if 'args' in new:
            new['args'] = [self._inline(a, subst) for a in new['args']]
        return new

    def _try_merge_if(self, ifnode):
        cond = ifnode['condition']
        tb, eb = ifnode.get('then_body'), ifnode.get('else_body')
        t_call = self._as_tail_call(tb) if tb else None
        e_call = self._as_tail_call(eb) if eb else None
        if not t_call or not e_call:
            return None
        fname_t, targs, tsubst = t_call
        fname_e, eargs, esubst = e_call
        if fname_t != fname_e or len(targs) != len(eargs):
            return None
        merged_args = []
        for at, ae in zip(targs, eargs):
            at_in = self._inline(at, tsubst)
            ae_in = self._inline(ae, esubst)
            # Conservar la referencia al callee (Var con el nombre de la funcion).
            if (isinstance(at_in, dict) and at_in.get('type') == 'Var'
                    and at_in.get('name') == fname_t):
                merged_args.append(at_in)
            elif at_in == ae_in:
                merged_args.append(at_in)  # argumento identico -> sin ternario
            else:
                merged_args.append({'type': 'Ternary', 'cond': cond,
                                    'then': at_in, 'else': ae_in})
        return {'type': 'Return',
                'value': {'type': 'FuncCall', 'name': fname_t, 'args': merged_args}}

    def _visit_FuncCall(self, node):
        name = node['name']
        args = [self._visit(a) for a in node.get('args', [])]
        
        if self.symbolic_mode or name not in self.functions:
            self.input_vars.add(name)
            return ('call', name, tuple(args))
            
        if self.recursion_depth[name] >= self.MAX_RECURSION_DEPTH:
            # TRUNCAMIENTO POR PRESUPUESTO (§4.2): se alcanzo MAX_RECURSION_DEPTH.
            # Devolver 0 aqui hace que el sistema codifique un programa distinto
            # del original. En vez de hacerlo en silencio, lo registramos: el
            # converter anclara `overflow = 0` y, al haberse disparado el evento,
            # el sistema sera insatisfacible (sin teoremas falsos).
            self.overflow_events += 1
            if not self.overflow_triggered:
                print(f"  [AVISO §4.2] Truncamiento por presupuesto: '{name}' "
                      f"alcanzo MAX_RECURSION_DEPTH={self.MAX_RECURSION_DEPTH}. El "
                      f"sistema generado solo es fiel al programa para entradas "
                      f"cuya traza cabe en ese presupuesto; para trazas mas largas "
                      f"el truncamiento (return 0) codifica un programa distinto. "
                      f"Aumenta DIOPHANTUS_MAX_RECURSION si necesitas mas profundidad.")
            self.overflow_triggered = True
            return 0
            
        self.recursion_depth[name] += 1
        self.call_counter += 1
        # Push Scope
        self.scope_stack.append(f"c{self.call_counter}_{name}")
        
        # Map Params to Args
        func_def = self.functions[name]
        old_state = self.current_state.copy()
        
        for p, val in zip(func_def['params'], args):
            # Usar SSA para los parámetros en esta instancia
            target = self._new_ssa_var(p) 
            self.aux_vars[target] = val
            # Mapeamos el nombre base del param al nuevo target SSA en el scope actual
            # Pero como _visit_Var usa _get_scoped_name, necesitamos que el nombre base
            # apunte al valor correcto.
            # Solución simple: Escribir en current_state con el nombre scoped
            scoped_p = self._get_scoped_name(p)
            self.current_state[scoped_p] = val

        ret = self._visit(func_def['body'])
        
        # Pop Scope
        self.scope_stack.pop()
        self.current_state = old_state # Restaurar variables locales del caller
        self.recursion_depth[name] -= 1
        return ret if ret is not None else 0

    def _visit_Return(self, node):
        return self._visit(node['value'])

    def _visit_Assign(self, node):
        # Determinar nombre
        name = ""
        if node['target']['type'] == 'Var': name = node['target']['name']
        
        val = self._visit(node['value'])
        op = node['op']
        
        # Resolver valor actual para operadores compuestos +=
        if op != '=':
            curr = self._visit(node['target'])
            base_op = op[0] # + de +=
            val = (base_op, curr, val)
            
        # SSA: Generar nueva versión de la variable
        # Pero si es State Var, actualizamos el puntero en current_state
        scoped_name = self._get_scoped_name(name)
        
        if scoped_name in self.state_vars:
            self.current_state[scoped_name] = val
        else:
            # Crear nueva instancia SSA para romper ciclos
            ssa_name = self._new_ssa_var(name)
            self.aux_vars[ssa_name] = val
            # Actualizar puntero del scope actual a la nueva instancia
            self.current_state[scoped_name] = ssa_name

    def _visit_Var(self, node):
        name = node['name']
        scoped = self._get_scoped_name(name)
        # Devolver el valor actual (puede ser una referencia SSA o un valor)
        return self.current_state.get(scoped, scoped)

    def _visit_Constant(self, node): return node['value']
    
    def _visit_BinaryOp(self, node):
        l = self._visit(node['left'])
        r = self._visit(node['right'])
        return (node['op'], l, r)
        
    def _visit_UnaryOp(self, node):
        op = node['op']
        v = self._visit(node['operand'])
        if op == '-': return ('neg', v)
        if op == '~': return ('~', v)
        return v

    def _visit_Update(self, node):
        # ++ / --
        name = node['target']['name']
        op = '+' if node['op'] == '++' else '-'
        
        # Tratar como assign: x = x + 1
        curr = self._visit(node['target'])
        val = (op, curr, 1)
        
        scoped = self._get_scoped_name(name)
        if scoped in self.state_vars:
            self.current_state[scoped] = val
        else:
            ssa = self._new_ssa_var(name)
            self.aux_vars[ssa] = val
            self.current_state[scoped] = ssa
            
    def _visit_Declare(self, node):
        name = node['target']
        val = self._visit(node['value']) if node['value'] else 0
        
        ssa = self._new_ssa_var(name)
        self.aux_vars[ssa] = val
        self.current_state[self._get_scoped_name(name)] = ssa

def generate_function(ast_map):
    flattener = AstFlattener(
        ast_map['state_vars'], 
        ast_map['functions'], 
        ast_map['struct_defs'], 
        ast_map['config']
    )
    F = flattener.generate_function_F(ast_map['logic_tree'])

    # Relaciones simbólicas
    rels = {}
    # (Opcional: Generar rels si se necesita Fase 6)

    # §4.2: se propaga si la expansion trunco por presupuesto, para que el
    # converter ancle la variable `overflow` en consecuencia.
    return F, flattener.input_vars, rels, flattener.overflow_triggered