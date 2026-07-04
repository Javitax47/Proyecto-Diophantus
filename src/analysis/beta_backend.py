"""
================================================================================
   DIOPHANTUS - BETA BACKEND: de la transicion compilada a (a, b, T)
================================================================================
Conecta el compilador con el colapso beta. Extrae la funcion de transicion de UN
PASO de un programa (compilando en symbolic_mode, que mantiene la llamada
recursiva como ('call',...) en vez de desenrollarla) y la convierte en un step
ejecutable. Con el, un "Witness Miner" ejecuta el programa y empaqueta toda la
traza en los testigos beta (a, b, T) -- el sistema de tamano constante de la
Valido para cualquier profundidad sin recompilar.
"""

import operator

from src.compiler import parser
from src.compiler.generator import AstFlattener
from src.analysis.trace_packer import pack_trace, check_beta_trajectory

_OPS = {
    '+': operator.add, '-': operator.sub, '*': operator.mul,
    '/': lambda x, y: x // y if y else 0, '%': lambda x, y: x % y if y else 0,
    '==': lambda x, y: int(x == y), '!=': lambda x, y: int(x != y),
    '<': lambda x, y: int(x < y), '>': lambda x, y: int(x > y),
    '<=': lambda x, y: int(x <= y), '>=': lambda x, y: int(x >= y),
    '&&': lambda x, y: int(bool(x) and bool(y)), '||': lambda x, y: int(bool(x) or bool(y)),
}


def _eval(e, env):
    """Evalua una expresion-tupla del flattener en terminos del estado `env`."""
    if isinstance(e, int):
        return e
    if isinstance(e, str):
        return env.get(e, 0)
    op = e[0]
    if op == 'if':
        return _eval(e[2], env) if _eval(e[1], env) else _eval(e[3], env)
    if op == 'neg':
        return -_eval(e[1], env)
    a = _eval(e[1], env)
    b = _eval(e[2], env) if len(e) > 2 else 0
    return _OPS.get(op, lambda x, y: 0)(a, b)


def extract_transition(src, func_name, state_params):
    """Devuelve un `step(state_dict)` que aplica UN paso de la transicion
    compilada y devuelve ('STEP', nuevo_estado) o ('HALT', valor_retorno).

    `state_params` son los nombres de los parametros de estado (en el orden de
    la firma de la funcion), que es como se mapean los argumentos de la llamada
    recursiva al estado siguiente."""
    ast = parser.parse_c_file(src)
    fl = AstFlattener(ast['state_vars'], ast['functions'], ast['struct_defs'],
                      dict(ast['config']), symbolic_mode=True)
    rel = fl.generate_function_relation(func_name, ast['functions'][func_name]['body'])
    body = fl._resolve_expression(rel['body'])

    def step(state):
        node = body
        # Recorrer el arbol de 'if' hasta un valor (HALT) o la llamada (STEP).
        while isinstance(node, tuple) and node[0] == 'if':
            node = node[2] if _eval(node[1], state) else node[3]
        if isinstance(node, tuple) and node[0] == 'call':
            call_args = node[2][1:]  # saltar la referencia al callee
            new_state = {p: _eval(a, state) for p, a in zip(state_params, call_args)}
            return ('STEP', new_state)
        return ('HALT', _eval(node, state))

    return step


def run_and_pack(step, start_state, trace_key, max_steps=100000):
    """Ejecuta la transicion desde `start_state` hasta HALT y empaqueta la
    sucesion de valores de `trace_key` en testigos beta. Devuelve
    (trace, a, b, T, halt_value)."""
    state = dict(start_state)
    trace = [state[trace_key]]
    halt_value = None
    for _ in range(max_steps):
        kind, payload = step(state)
        if kind == 'HALT':
            halt_value = payload
            break
        state = payload
        trace.append(state[trace_key])
    a, b = pack_trace(trace)
    return trace, a, b, len(trace) - 1, halt_value
