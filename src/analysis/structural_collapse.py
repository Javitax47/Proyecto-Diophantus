"""
================================================================================
   DIOPHANTUS - COLAPSO ESTRUCTURAL GENERICO (Fase 3, camino universal)
================================================================================
En vez de tratar cada algoritmo a mano, detecta AUTOMATICAMENTE la estructura de
la transicion COMPILADA de cualquier programa y aplica el colapso adecuado:

  * Se extrae la transicion de un paso (beta_backend, symbolic_mode) y, de la
    llamada recursiva, las expresiones de siguiente-estado por registro.
  * Se analiza si cada expresion es AFIN en las variables de estado (por muestreo
    + verificacion). Si TODA la transicion es afin, se reconstruye (A, d) y los T
    pasos colapsan via el colapso acoplado generico (linear_collapse).
  * Si no es afin (p. ej. collatz, con seleccion por paridad), se reporta como tal
    (su colapso requiere las tecnicas no afines / dominancia).

Asi el colapso es generico: la estructura se descubre desde el tuple de
transicion del compilador, no se hardcodea por programa.
"""

import random

from src.compiler import parser
from src.compiler.generator import AstFlattener
from src.analysis.beta_backend import _eval
from src.analysis.linear_collapse import coupled_collapse_holds, choose_base, pack_digits


def _resolved_transition(src, func):
    ast = parser.parse_c_file(src)
    fl = AstFlattener(ast['state_vars'], ast['functions'], ast['struct_defs'],
                      dict(ast['config']), symbolic_mode=True)
    rel = fl.generate_function_relation(func, ast['functions'][func]['body'])
    return fl._resolve_expression(rel['body'])


def next_state_exprs(body):
    """Devuelve las expresiones de siguiente-estado (args de la unica llamada
    recursiva, sin la referencia al callee), o None si no hay exactamente una."""
    calls = []

    def walk(e):
        if isinstance(e, tuple):
            if e[0] == 'call':
                calls.append(e)
            for x in e[1:]:
                walk(x)
    walk(body)
    if len(calls) != 1:
        return None
    return list(calls[0][2][1:])


def as_affine(expr, state_vars, trials=40, lo=-25, hi=25, seed=1):
    """Si `expr` es afin en `state_vars` devuelve (coeffs: dict, const: int);
    si no, None. Coeficientes por muestreo y VERIFICACION en puntos aleatorios."""
    base = {v: 0 for v in state_vars}
    const = _eval(expr, base)
    coeffs = {}
    for v in state_vars:
        env = dict(base); env[v] = 1
        coeffs[v] = _eval(expr, env) - const
    rng = random.Random(seed)
    for _ in range(trials):
        env = {v: rng.randint(lo, hi) for v in state_vars}
        predicted = const + sum(coeffs[v] * env[v] for v in state_vars)
        if _eval(expr, env) != predicted:
            return None
    return coeffs, const


def detect_affine_transition(src, func, state_params):
    """Devuelve (A, d) si la transicion compilada es afin en el estado, o None."""
    body = _resolved_transition(src, func)
    exprs = next_state_exprs(body)
    if exprs is None or len(exprs) != len(state_params):
        return None
    A, d = [], []
    for expr in exprs:
        aff = as_affine(expr, state_params)
        if aff is None:
            return None
        coeffs, const = aff
        A.append([coeffs[v] for v in state_params])
        d.append(const)
    return A, d


def run_states(step, start, max_steps=100000):
    """Ejecuta la transicion y devuelve (estados, halt): estados es la lista de
    vectores de estado [x_0, ..., x_T] (dicts) hasta HALT."""
    state = dict(start)
    states = [dict(state)]
    for _ in range(max_steps):
        kind, payload = step(state)
        if kind == 'HALT':
            return states, payload
        state = payload
        states.append(dict(state))
    return states, None


def collapse_affine_program(src, func, state_params, start):
    """Camino universal: detecta si la transicion es afin y, en tal caso, verifica
    que la traza real colapsa via la ecuacion acoplada generica. Devuelve un dict
    con {'affine', 'A', 'd', 'collapse_ok', 'T'}."""
    from src.analysis.beta_backend import extract_transition
    Ad = detect_affine_transition(src, func, state_params)
    if Ad is None:
        return {'affine': False, 'A': None, 'd': None, 'collapse_ok': None, 'T': None}
    A, d = Ad
    step = extract_transition(src, func, state_params)
    states, _halt = run_states(step, start)
    xs = [[s[p] for p in state_params] for s in states]  # vectores por paso
    m = len(state_params)
    flat = [xs[i][j] for i in range(len(xs)) for j in range(m)]
    base = choose_base(flat)
    packed = [pack_digits([xs[i][j] for i in range(len(xs))], base) for j in range(m)]
    ok = coupled_collapse_holds(packed, xs[0], xs[-1], A, d, base, len(xs) - 1)
    return {'affine': True, 'A': A, 'd': d, 'collapse_ok': ok, 'T': len(xs) - 1}
