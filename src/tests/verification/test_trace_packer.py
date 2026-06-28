#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL TRACE PACKER / FUNCION BETA (Fase 2, Nivel 2)
================================================================================
Valida la codificacion de Goedel que sustituye el desenrollado: toda la traza
se mete en dos enteros (a, b) con beta(a, b, i) = x_i. Comprueba:

  (1) ROUND-TRIP: para trazas aleatorias (incl. ceros, repeticiones), pack_trace
      produce (a, b) tales que beta los recupera exactamente.
  (2) COLLATZ REAL: la trayectoria 3n+1 de varios n se codifica y se recupera.
  (3) INDEPENDENCIA DE LA LONGITUD: el MISMO esquema beta codifica trazas de
      longitudes muy distintas (5 y varios cientos) sin "recompilar" -- la
      propiedad que persigue la Fase 2 (el numero de variables es constante; lo
      que crece es el tamano de los testigos a, b).

Uso:  python src/tests/verification/test_trace_packer.py
"""

import os
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.analysis.trace_packer import (
    beta, pack_trace, verify_packing, beta_moduli,
    check_beta_trajectory, pack_and_check,
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


def collatz_trajectory(n):
    """Sucesion de valores de n a lo largo de la trayectoria 3n+1 (hasta 1)."""
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq


def test_roundtrip(stats):
    print(f"{Colors.HEADER}[1] Round-trip de trazas aleatorias{Colors.ENDC}")
    rng = random.Random(20260615)
    for _ in range(60):
        n = rng.randint(1, 25)
        xs = [rng.randint(0, 200) for _ in range(n)]
        # mezclar ceros y repeticiones
        if rng.random() < 0.3:
            xs[rng.randrange(n)] = 0
        a, b = pack_trace(xs)
        if verify_packing(a, b, xs):
            stats.ok()
        else:
            stats.fail(f"no recupera {xs} -> (a={a}, b={b})")


def test_collatz(stats):
    print(f"{Colors.HEADER}[2] Codificacion de trayectorias Collatz reales{Colors.ENDC}")
    for n in [6, 7, 11, 27, 97]:
        xs = collatz_trajectory(n)
        a, b = pack_trace(xs)
        if verify_packing(a, b, xs) and beta(a, b, 0) == n and beta(a, b, len(xs) - 1) == 1:
            stats.ok()
        else:
            stats.fail(f"collatz({n}) longitud {len(xs)} no se recupera")


def test_length_independence(stats):
    print(f"{Colors.HEADER}[3] Mismo esquema beta para longitudes muy distintas{Colors.ENDC}")
    # Trayectorias cortas y largas se codifican con la MISMA maquinaria.
    for n in [5, 27, 703]:  # 703 da una trayectoria de varios cientos de pasos
        xs = collatz_trajectory(n)
        a, b = pack_trace(xs)
        # m_i estrictamente crecientes y coprimos por construccion; comprobamos
        # que la decodificacion es exacta en TODA la traza, sea cual sea su largo.
        if verify_packing(a, b, xs):
            stats.ok()
            print(f"     longitud {len(xs):4d}: OK")
        else:
            stats.fail(f"collatz({n}) longitud {len(xs)} falla")


def test_edge_cases(stats):
    print(f"{Colors.HEADER}[4] Casos limite{Colors.ENDC}")
    for xs in [[], [0], [42], [0, 0, 0], [5, 5, 5, 5]]:
        a, b = pack_trace(xs)
        if verify_packing(a, b, xs):
            stats.ok()
        else:
            stats.fail(f"caso limite {xs} falla")


def test_trajectory_verification(stats):
    print(f"{Colors.HEADER}[5] Verificacion de trayectoria contra UNA transicion (cualquier T){Colors.ENDC}")
    # Transicion Collatz de un solo paso (independiente de la profundidad).
    step = lambda x: x // 2 if x % 2 == 0 else 3 * x + 1
    accept = lambda x: x == 1
    # El MISMO predicado check_beta_trajectory verifica T muy distintos.
    for n in [5, 27, 703]:
        a, b, T = pack_and_check(step, n, accept)
        if check_beta_trajectory(a, b, T, step, n, accept):
            stats.ok()
            print(f"     n={n:4d}: trayectoria de T={T} pasos verificada")
        else:
            stats.fail(f"n={n}: la trayectoria valida no verifica")
    # NEGATIVO: un testigo manipulado (un paso roto) NO debe verificar.
    xs = collatz_trajectory(27)
    xs[len(xs) // 2] += 1  # romper un paso intermedio
    a, b = pack_trace(xs)
    if not check_beta_trajectory(a, b, len(xs) - 1, step, 27, accept):
        stats.ok()
    else:
        stats.fail("un testigo con un paso roto pasó la verificacion (deberia fallar)")


def main():
    print(f"{Colors.BOLD}=== TEST DEL TRACE PACKER (funcion beta de Goedel) ==={Colors.ENDC}")
    stats = Stats()
    test_roundtrip(stats)
    test_collatz(stats)
    test_length_independence(stats)
    test_edge_cases(stats)
    test_trajectory_verification(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — la traza se "
              f"colapsa en (a, b) y beta la recupera, sea cual sea su longitud.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
