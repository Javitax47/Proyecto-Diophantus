#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL COLAPSO ESTRUCTURAL GENERICO (Fase 3, universal)
================================================================================
Demuestra que el colapso se descubre AUTOMATICAMENTE desde la transicion
compilada de cualquier programa, sin hardcodear:

  (1) DETECCION AFIN: el motor extrae (A, d) correctos de programas afines
      (linrec: x->2x+1 ; sum_down: k->k-1, acc->acc+k) y reconoce collatz como
      NO afin (transicion seleccionada por paridad).
  (2) COLAPSO GENERICO: para los programas afines, la traza real colapsa via la
      ecuacion acoplada generica con la (A, d) auto-detectada.

Uso:  python src/tests/verification/test_structural_collapse.py
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
        import src.compiler.parser
        import clang.cindex
        clang.cindex.Index.create()
        return True
    except Exception:
        return False


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def main():
    print(f"{Colors.BOLD}=== TEST DEL COLAPSO ESTRUCTURAL GENERICO ==={Colors.ENDC}")
    if not libclang_ok():
        print(f"{Colors.WARN}[SKIP] libclang no disponible.{Colors.ENDC}")
        sys.exit(0)

    from src.analysis.structural_collapse import detect_affine_transition, collapse_affine_program
    stats = Stats()

    print(f"{Colors.HEADER}[1] Deteccion automatica de estructura afin desde la transicion compilada{Colors.ENDC}")
    # linrec(x, step): x -> 2x+1, step -> step+1  => A=[[2,0],[0,1]], d=[1,1]
    Ad = detect_affine_transition("src/examples/linrec.c", "linrec", ["x", "step"])
    if Ad == ([[2, 0], [0, 1]], [1, 1]):
        stats.ok(); print(f"     linrec: afin detectado A={Ad[0]} d={Ad[1]}")
    else:
        stats.fail(f"linrec: (A,d) inesperado {Ad}")

    # sum_down(k, acc): k -> k-1, acc -> acc+k => A=[[1,0],[1,1]], d=[-1,0]
    Ad = detect_affine_transition("src/examples/countdown.c", "sum_down", ["k", "acc"])
    if Ad == ([[1, 0], [1, 1]], [-1, 0]):
        stats.ok(); print(f"     sum_down: afin detectado A={Ad[0]} d={Ad[1]}")
    else:
        stats.fail(f"sum_down: (A,d) inesperado {Ad}")

    # collatz: NO afin (seleccion por paridad)
    Ad = detect_affine_transition("src/examples/collatz.c", "collatz_trajectory", ["n", "acc"])
    if Ad is None:
        stats.ok(); print(f"     collatz: reconocido como NO afin (correcto)")
    else:
        stats.fail(f"collatz: deberia ser no afin, dio {Ad}")

    print(f"{Colors.HEADER}[2] Colapso acoplado generico con la (A,d) auto-detectada{Colors.ENDC}")
    for src, func, sp, start in [
        ("src/examples/linrec.c", "linrec", ["x", "step"], {"x": 1, "step": 0}),
        ("src/examples/countdown.c", "sum_down", ["k", "acc"], {"k": 9, "acc": 0}),
    ]:
        res = collapse_affine_program(src, func, sp, start)
        if res['affine'] and res['collapse_ok']:
            stats.ok(); print(f"     {func}: afin, colapso verifica (T={res['T']})")
        else:
            stats.fail(f"{func}: {res}")
    # collatz: no afin -> no se intenta el colapso afin (correcto)
    res = collapse_affine_program("src/examples/collatz.c", "collatz_trajectory", ["n", "acc"], {"n": 27, "acc": 0})
    if res['affine'] is False:
        stats.ok(); print(f"     collatz: no afin -> el colapso afin no aplica (correcto)")
    else:
        stats.fail(f"collatz: deberia reportarse no afin, dio {res}")

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — la estructura se descubre "
              f"y colapsa automaticamente desde la transicion compilada.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
