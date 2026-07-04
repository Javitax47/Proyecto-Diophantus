#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL BETA BACKEND: transicion compilada -> (a,b,T)
================================================================================
Valida el puente compilador -> colapso beta de extremo a extremo:

  (1) La transicion de UN PASO extraida del collatz COMPILADO reproduce la
      trayectoria 3n+1 de referencia (esto valida tambien, de paso, el arreglo
      del parseo de operadores anidados: (3*n+1)/2 debe dar la trayectoria
      correcta, no 6*n).
  (2) La traza compilada se empaqueta en testigos beta (a, b, T) y
      check_beta_trajectory la verifica contra la MISMA transicion de un paso,
      para varias longitudes -- el sistema de tamano constante.

Uso:  python src/tests/verification/test_beta_backend.py
Requisitos: LLVM/libclang.
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)
sys.setrecursionlimit(200000)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


def libclang_ok():
    try:
        import src.compiler.parser  # configura libclang
        import clang.cindex
        clang.cindex.Index.create()
        return True
    except Exception:
        return False


def collatz_ref_trajectory(n):
    seq = [n]
    acc = 0
    while n != 1 and acc <= 200:
        n = n // 2 if n % 2 == 0 else (3 * n + 1) // 2
        acc += 1 if seq[-1] % 2 == 0 else 2
        seq.append(n)
    return seq


def main():
    print(f"{Colors.BOLD}=== TEST DEL BETA BACKEND (transicion compilada -> beta) ==={Colors.ENDC}")
    if not libclang_ok():
        print(f"{Colors.WARN}[SKIP] libclang no disponible.{Colors.ENDC}")
        sys.exit(0)

    from src.analysis.beta_backend import extract_transition, run_and_pack
    from src.analysis.trace_packer import check_beta_trajectory

    passed = failed = 0
    # collatz_trajectory(n, acc): estado = (n, acc); 'n' es la variable de traza.
    step = extract_transition("src/examples/collatz.c", "collatz_trajectory", ["n", "acc"])

    print(f"{Colors.HEADER}[1] La transicion compilada reproduce la trayectoria de referencia{Colors.ENDC}")
    for n in [6, 7, 27, 97, 703]:
        trace, a, b, T, halt = run_and_pack(step, {"n": n, "acc": 0}, "n")
        ref = collatz_ref_trajectory(n)
        if trace == ref:
            passed += 1
            print(f"     n={n:4d}: T={T} pasos, coincide con la referencia")
        else:
            failed += 1
            print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} n={n}: compilado {trace[:6]}... != ref {ref[:6]}...")

    print(f"{Colors.HEADER}[2] Los testigos beta verifican la traza compilada (cualquier T){Colors.ENDC}")
    # step ejecutable equivalente para check_beta_trajectory (un paso sobre n).
    one_step = lambda x: x // 2 if x % 2 == 0 else (3 * x + 1) // 2
    for n in [7, 27, 703]:
        trace, a, b, T, halt = run_and_pack(step, {"n": n, "acc": 0}, "n")
        if check_beta_trajectory(a, b, T, one_step, n, accept=lambda x: x == 1):
            passed += 1
        else:
            failed += 1
            print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} n={n}: testigos beta no verifican")

    total = passed + failed
    print()
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {passed}/{total} OK — la transicion compilada se "
              f"colapsa en testigos beta verificables.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
