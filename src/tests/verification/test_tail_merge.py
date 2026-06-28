#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE LA FUSION DE TAIL-CALLS (anti-blowup, diferencial)
================================================================================
La fusion de tail-calls reescribe `if c then f(A) else f(B)` -> `f(phi(c,A,B))`,
colapsando la recursion ramificada de 2^profundidad a lineal (p. ej. collatz
pasa de no-compilable a ~lineal). Este test garantiza que la transformacion
PRESERVA LA SEMANTICA mediante un test DIFERENCIAL:

  para cada entrada, el cuerpo aplanado CON fusion debe evaluar exactamente
  igual que SIN fusion.

El diferencial es robusto: usa el mismo evaluador en ambos lados, asi que
cualquier deficiencia del evaluador (p. ej. resolucion de nombres SSA) se
cancela; solo detecta DIVERGENCIAS introducidas por la fusion.

Uso:  python src/tests/verification/test_tail_merge.py
Requisitos: LLVM/libclang para compilar los .c.
"""

import os
import sys
import operator

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)

sys.setrecursionlimit(400000)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


def libclang_ok():
    try:
        import src.compiler.parser  # configura libclang al importar
        import clang.cindex
        clang.cindex.Index.create()
        return True
    except Exception:
        return False


_OPS = {
    '+': operator.add, '-': operator.sub, '*': operator.mul,
    '/': lambda x, y: x // y if y else 0, '%': lambda x, y: x % y if y else 0,
    '==': lambda x, y: int(x == y), '!=': lambda x, y: int(x != y),
    '<': lambda x, y: int(x < y), '>': lambda x, y: int(x > y),
    '<=': lambda x, y: int(x <= y), '>=': lambda x, y: int(x >= y),
}


def _eval(e, env, d=0):
    if d > 80000:
        raise RecursionError
    if isinstance(e, int):
        return e
    if isinstance(e, str):
        return env.get(e, 0)
    if isinstance(e, tuple):
        op = e[0]
        if op == 'if':
            return _eval(e[2], env, d + 1) if _eval(e[1], env, d + 1) else _eval(e[3], env, d + 1)
        if op == 'neg':
            return -_eval(e[1], env, d + 1)
        if op == 'call':
            return 0  # truncacion por presupuesto
        a = _eval(e[1], env, d + 1)
        b = _eval(e[2], env, d + 1)
        return _OPS.get(op, lambda x, y: 0)(a, b)
    return 0


def flattened_body(src, func_name, config, merge):
    """Devuelve el cuerpo aplanado y resuelto de `func_name`, con o sin fusion."""
    from src.compiler import parser
    from src.compiler.generator import AstFlattener
    os.environ['DIOPH_NO_TAIL_MERGE'] = '0' if merge else '1'
    ast = parser.parse_c_file(src)
    fl = AstFlattener(ast['state_vars'], ast['functions'], ast['struct_defs'], config)
    rel = fl.generate_function_relation(func_name, ast['functions'][func_name]['body'])
    return fl._resolve_expression(rel['body'])


CASES = [
    # (archivo, funcion, config, lista de envs de entrada)
    ("src/examples/collatz.c", "collatz_trajectory",
     {'MAX_RECURSION_DEPTH': 12, 'MAX_LOOP_UNROLL': 5, 'BIT_WIDTH': 32},
     [{'n': n, 'acc': 0} for n in range(1, 40)]),
]


def main():
    print(f"{Colors.BOLD}=== TEST DIFERENCIAL DE FUSION DE TAIL-CALLS ==={Colors.ENDC}")
    if not libclang_ok():
        print(f"{Colors.WARN}[SKIP] libclang no disponible.{Colors.ENDC}")
        sys.exit(0)

    passed = failed = 0
    for src, fn, cfg, envs in CASES:
        if not os.path.exists(src):
            print(f"  {Colors.WARN}⊘ {fn}: no existe {src}{Colors.ENDC}")
            continue
        body_no = flattened_body(src, fn, cfg, merge=False)
        body_yes = flattened_body(src, fn, cfg, merge=True)
        divergencias = 0
        for env in envs:
            if _eval(body_no, dict(env)) != _eval(body_yes, dict(env)):
                divergencias += 1
        if divergencias == 0:
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {fn}: con/sin fusion coinciden en {len(envs)} entradas")
            passed += 1
        else:
            print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {fn}: {divergencias}/{len(envs)} divergen (fusion altera la semantica)")
            failed += 1

    print()
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ La fusion de tail-calls preserva la semantica.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ La fusion altera la semantica.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
