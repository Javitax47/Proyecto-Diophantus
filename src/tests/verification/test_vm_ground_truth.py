#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE LA VM CONTRA GROUND-TRUTH
================================================================================
Verifica que la Máquina Virtual de pila (`src/runtime/vm.py`) ejecuta la lógica
recursiva con la MISMA semántica que una referencia en Python, sobre un conjunto
de algoritmos clásicos y muchas entradas. Es la pata "(a) ejecutar en VM contra
ground truth" del item 2.

Las funciones se definen directamente en el formato de AST de la VM (sin pasar
por el compilador C, para que el test sea rápido y autocontenido) y se contrasta
`vm.run(...)` con la implementación de referencia para cada entrada.

Uso:  python src/tests/verification/test_vm_ground_truth.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.runtime.vm import VM


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


# --- AST de la VM para cada algoritmo (formato: listas [op, args...]) ---
ASTS = {
    # gcd(a, b) = b==0 ? a : gcd(b, a mod b)
    'gcd': (['a', 'b'],
            ['If', ['eq', 'b', 0], 'a',
             ['Call', 'gcd', 'b', ['mod', 'a', 'b']]]),
    # factorial(n) = n<=1 ? 1 : n * factorial(n-1)
    'factorial': (['n'],
                  ['If', ['lte', 'n', 1], 1,
                   ['mul', 'n', ['Call', 'factorial', ['sub', 'n', 1]]]]),
    # power(b, e) = e==0 ? 1 : b * power(b, e-1)
    'power': (['b', 'e'],
              ['If', ['eq', 'e', 0], 1,
               ['mul', 'b', ['Call', 'power', 'b', ['sub', 'e', 1]]]]),
    # sum_to(n) = n<=0 ? 0 : n + sum_to(n-1)
    'sum_to': (['n'],
               ['If', ['lte', 'n', 0], 0,
                ['add', 'n', ['Call', 'sum_to', ['sub', 'n', 1]]]]),
    # collatz(n, acc) = n==1 ? acc : (n%2==0 ? collatz(n/2,acc+1) : collatz(3n+1,acc+1))
    'collatz': (['n', 'acc'],
                ['If', ['eq', 'n', 1], 'acc',
                 ['If', ['eq', ['mod', 'n', 2], 0],
                  ['Call', 'collatz', ['div', 'n', 2], ['add', 'acc', 1]],
                  ['Call', 'collatz', ['add', ['mul', 3, 'n'], 1], ['add', 'acc', 1]]]]),
}


# --- Referencias Python (semántica esperada) ---
def ref_gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def ref_factorial(n):
    return 1 if n <= 1 else n * ref_factorial(n - 1)

def ref_power(b, e):
    return 1 if e == 0 else b * ref_power(b, e - 1)

def ref_sum_to(n):
    return 0 if n <= 0 else n * (n + 1) // 2

def ref_collatz(n, acc):
    while n != 1:
        n, acc = (n // 2, acc + 1) if n % 2 == 0 else (3 * n + 1, acc + 1)
    return acc


CASES = [
    ('gcd', ref_gcd, [(48, 18), (100, 75), (17, 5), (1071, 462), (9, 9), (13, 1)]),
    ('factorial', ref_factorial, [(n,) for n in range(0, 9)]),
    ('power', ref_power, [(2, e) for e in range(0, 11)] + [(3, 4), (5, 3), (7, 0)]),
    ('sum_to', ref_sum_to, [(n,) for n in range(0, 12)]),
    ('collatz', ref_collatz, [(n, 0) for n in range(1, 28)]),
]


def main():
    print(f"{Colors.BOLD}=== TEST DE LA VM CONTRA GROUND-TRUTH ==={Colors.ENDC}")
    vm = VM()
    for name, (params, ast) in ASTS.items():
        vm.load_function(name, params, ast)

    passed = failed = 0
    for name, ref, inputs in CASES:
        ok_all = True
        for args in inputs:
            got = vm.run(name, list(args))
            expected = ref(*args)
            if got != expected:
                print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {name}{args}: VM={got} != ref={expected}")
                ok_all = False
        if ok_all:
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {name}: {len(inputs)} entradas coinciden con la referencia")
            passed += 1
        else:
            failed += 1

    total = passed + failed
    print()
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {passed}/{total} algoritmos: la VM coincide "
              f"con el ground-truth.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {failed}/{total} algoritmos divergen.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
