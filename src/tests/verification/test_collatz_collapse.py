#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL COLAPSO DE COLLATZ
================================================================================
Valida la forma polinomica por paso de la transicion de collatz y el colapso de
su esqueleto lineal sobre la traza empaquetada. Comprueba:

  (1) RELACION POR PASO: 2*x_{i+1} = x_i + b_i*(2x_i+1) (b_i=paridad) se cumple
      en trayectorias reales y FALLA en pasos manipulados (sin soluciones espurias).
  (2) COLAPSO DEL ESQUELETO LINEAL: con p_i=b_i*x_i auxiliar, los T pasos se
      reducen a UNA ecuacion sobre las historias empaquetadas N_x, N_p, N_b;
      vale para varias longitudes y falla en trazas rotas.

Uso:  python src/tests/verification/test_collatz_collapse.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.analysis.collatz_collapse import (
    collatz_step, collatz_trace, step_relation_holds, verify_trace_relations,
    linear_skeleton_collapses, safe_base,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_step_relation(stats):
    print(f"{Colors.HEADER}[1] Relacion polinomica por paso (2x'=x+b(2x+1)){Colors.ENDC}")
    # positivo: pasos reales de collatz
    ok_all = True
    for x in range(1, 500):
        nxt = collatz_step(x)
        if not step_relation_holds(x, nxt, x % 2):
            ok_all = False
            stats.fail(f"x={x}: paso real no cumple la relacion")
            break
    if ok_all:
        stats.ok()
    # negativo: un siguiente-estado equivocado no cumple
    bad = 0; total = 0
    for x in range(1, 200):
        total += 1
        wrong = collatz_step(x) + 1
        if not step_relation_holds(x, wrong, x % 2):
            bad += 1
    if bad == total:
        stats.ok()
        print(f"     {bad}/{total} siguiente-estado erroneos rechazados")
    else:
        stats.fail(f"solo {bad}/{total} erroneos rechazados")


def test_full_traces(stats):
    print(f"{Colors.HEADER}[2] La relacion por paso se cumple en trayectorias completas{Colors.ENDC}")
    for n in [6, 7, 27, 97, 703, 9999]:
        xs = collatz_trace(n)
        if verify_trace_relations(xs) and xs[-1] == 1:
            stats.ok()
            print(f"     n={n:5d}: T={len(xs)-1} pasos, relacion por paso OK")
        else:
            stats.fail(f"n={n}: la relacion por paso falla en la traza")


def test_linear_skeleton_collapse(stats):
    print(f"{Colors.HEADER}[3] El esqueleto lineal colapsa en UNA ecuacion (cualquier T){Colors.ENDC}")
    for n in [6, 27, 97, 703]:
        xs = collatz_trace(n)
        base = safe_base(xs)
        if linear_skeleton_collapses(xs, base):
            stats.ok()
            print(f"     n={n:4d}: T={len(xs)-1}, esqueleto lineal empaquetado verifica")
        else:
            stats.fail(f"n={n}: el esqueleto lineal empaquetado NO verifica")
    # NEGATIVO: romper un paso de la traza
    xs = collatz_trace(27)
    xs[len(xs) // 2] += 2  # mantener paridad para aislar el fallo del esqueleto
    base = safe_base(xs)
    if not linear_skeleton_collapses(xs, base):
        stats.ok()
    else:
        stats.fail("una traza rota paso el colapso del esqueleto lineal")


def main():
    print(f"{Colors.BOLD}=== TEST DEL COLAPSO DE COLLATZ (transicion no afin) ==={Colors.ENDC}")
    stats = Stats()
    test_step_relation(stats)
    test_full_traces(stats)
    test_linear_skeleton_collapse(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — collatz tiene forma "
              f"polinomica por paso y su esqueleto lineal colapsa por empaquetado.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
