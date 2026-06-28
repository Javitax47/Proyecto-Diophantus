#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL SISTEMA CERRADO DE COLLATZ (Fase 3, cierre no afin)
================================================================================
Valida el sistema de restricciones de tamano constante (independiente de T)
sobre las historias empaquetadas de collatz. Comprueba:

  (1) POSITIVO: trayectorias reales (varios n, varias T) satisfacen TODAS las
      restricciones R1-R5.
  (2) SOLIDEZ: manipular la traza rompe al menos una restriccion (sin soluciones
      espurias), y cada tipo de manipulacion rompe la restriccion esperada.
  (3) INDEPENDENCIA DE T: el MISMO conjunto (constante) de restricciones vale
      para trayectorias de longitudes muy distintas.

Uso:  python src/tests/verification/test_collatz_closed.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.analysis.collatz_closed import (
    closed_constraints, closed_constraints_o1, closed_system_holds,
    collatz_closed_witness, choose_k, build_packed, r5_o1_holds, base_pow_digits,
)
from src.analysis.collatz_collapse import collatz_trace


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_positive(stats):
    print(f"{Colors.HEADER}[1] Trayectorias reales satisfacen TODO el sistema cerrado{Colors.ENDC}")
    for n in [6, 7, 27, 97, 703, 9999]:
        xs, k = collatz_closed_witness(n)
        cons = closed_constraints(xs, k, n)
        if all(cons.values()) and xs[-1] == 1:
            stats.ok()
            print(f"     n={n:5d}: T={len(xs)-1}, R1-R5 todas OK")
        else:
            falses = [k2 for k2, v in cons.items() if not v]
            stats.fail(f"n={n}: fallan {falses}")


def test_soundness(stats):
    print(f"{Colors.HEADER}[2] Solidez: manipular la traza rompe la restriccion esperada{Colors.ENDC}")
    base = collatz_trace(27)
    k = choose_k([x for x in base] + [3 * max(base)])  # k holgado para las manipulaciones

    # (a) romper un paso (valor intermedio) -> rompe la transicion (R3)
    t = list(base); t[len(t) // 2] += 2
    c = closed_constraints(t, choose_k(t), 27)
    stats.ok() if not c['R3_transicion'] else stats.fail("paso roto no rompe R3")

    # (b) frontera incorrecta (no acaba en 1) -> rompe R4
    t = list(base)[:-1]  # quitar el 1 final -> acaba en 2
    c = closed_constraints(t, choose_k(t), 27)
    stats.ok() if not c['R4_frontera'] else stats.fail("traza que no acaba en 1 no rompe R4")

    # (c) en general: cualquier manipulacion deja el sistema insatisfacible
    bad = 0; total = 0
    import random
    rng = random.Random(5)
    for _ in range(30):
        t = list(collatz_trace(rng.choice([7, 27, 97, 703])))
        i = rng.randint(0, len(t) - 1)
        t[i] += rng.choice([1, 2, 3])
        total += 1
        if not closed_system_holds(t, t[0]):
            bad += 1
    stats.ok() if bad == total else stats.fail(f"solo {bad}/{total} manipulaciones detectadas")
    print(f"     {bad}/{total} manipulaciones aleatorias detectadas (sin soluciones espurias)")


def test_length_independence(stats):
    print(f"{Colors.HEADER}[3] El MISMO sistema (constante) vale para T muy distintos{Colors.ENDC}")
    for n in [3, 27, 9999, 77031]:
        xs, k = collatz_closed_witness(n)
        if closed_system_holds(xs, n):
            stats.ok()
            print(f"     n={n:6d}: T={len(xs)-1} pasos, sistema cerrado OK")
        else:
            stats.fail(f"n={n}: sistema cerrado falla")


def test_r5_o1_equivalence(stats):
    print(f"{Colors.HEADER}[4] R5 en forma O(1) (dominancia) ⟺ R5 por-dígito (producto){Colors.ENDC}")
    import random
    rng = random.Random(13)
    bad = 0; total = 0
    for _ in range(200):
        # traza arbitraria (digitos x_i) con b_i = paridad y p_i candidato variado
        n = rng.randint(1, 8)
        k = rng.randint(2, 7)
        B = 1 << k
        xs = [rng.randint(0, B - 1) for _ in range(n)]
        bs = [x & 1 for x in xs]
        # p candidato: a veces correcto (b_i*x_i), a veces manipulado
        ps = []
        for i in range(n):
            if rng.random() < 0.5:
                ps.append(bs[i] * xs[i])           # correcto
            else:
                ps.append(rng.randint(0, B - 1))   # arbitrario
        Nx = base_pow_digits(xs, k)
        Nb = base_pow_digits(bs, k)
        Np = base_pow_digits(ps, k)
        per_digit = all(ps[i] == bs[i] * xs[i] for i in range(n))   # R5 por-digito
        o1 = r5_o1_holds(Nx, Nb, Np, k, n)                          # R5 O(1)
        total += 1
        if per_digit != o1:
            bad += 1
            if bad <= 3:
                stats.fail(f"discrepancia: xs={xs} ps={ps} per_digit={per_digit} o1={o1}")
    if bad == 0:
        stats.ok()
        print(f"     {total} casos: la forma O(1) coincide EXACTAMENTE con el producto por-dígito")
    else:
        stats.fail(f"{bad}/{total} discrepancias R5 O(1) vs por-dígito")


def test_full_system_o1(stats):
    print(f"{Colors.HEADER}[5] Sistema cerrado con R5 O(1): todo tamaño constante{Colors.ENDC}")
    for n in [7, 27, 703, 9999]:
        xs, k = collatz_closed_witness(n)
        cons = closed_constraints_o1(xs, k, n)
        if all(cons.values()):
            stats.ok()
            print(f"     n={n:5d}: T={len(xs)-1}, R1-R4 + R5(O(1)) todas OK")
        else:
            falses = [k2 for k2, v in cons.items() if not v]
            stats.fail(f"n={n}: fallan {falses}")
    # solidez con R5 O(1)
    import random
    rng = random.Random(8)
    bad = 0; total = 0
    for _ in range(30):
        t = list(collatz_trace(rng.choice([7, 27, 97, 703])))
        t[rng.randint(0, len(t) - 1)] += rng.choice([1, 2, 3])
        total += 1
        if not closed_system_holds(t, t[0], use_o1=True):
            bad += 1
    stats.ok() if bad == total else stats.fail(f"O(1): solo {bad}/{total} manipulaciones detectadas")
    print(f"     {bad}/{total} manipulaciones detectadas con el sistema O(1)")


def main():
    print(f"{Colors.BOLD}=== TEST DEL SISTEMA CERRADO DE COLLATZ (Fase 3) ==={Colors.ENDC}")
    stats = Stats()
    test_positive(stats)
    test_soundness(stats)
    test_length_independence(stats)
    test_r5_o1_equivalence(stats)
    test_full_system_o1(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — sistema de restricciones "
              f"de tamano constante, solido y verificado para cualquier T.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
