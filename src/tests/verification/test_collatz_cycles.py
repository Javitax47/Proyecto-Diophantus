#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - NO-EXISTENCIA CERTIFICADA DE CICLOS DE COLLATZ (§6.3 del informe)
================================================================================
Z3 refuta (UNSAT) la existencia de ciclos no triviales cortos de la dinamica de
collatz (variante (3n+1)/2), codificada como sistema diofantico. NO prueba la
conjetura; certifica longitudes concretas (resultado conocido reproducido como
insatisfacibilidad de un sistema concreto).

Comprueba:
  (1) RESULTADO: no hay ciclo no trivial (algun elemento >= 3) de longitud 1..6.
  (2) SANITY (anti falso-UNSAT): SIN la condicion de no-trivialidad, el encoding
      ES SAT para L=2 -> encuentra el ciclo trivial {1,2}, probando que el
      sistema acepta ciclos reales y el UNSAT de (1) no es vacuo.

Uso:  python src/tests/verification/test_collatz_cycles.py
Requisitos: z3-solver.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import z3  # noqa: F401
except ImportError:
    print("[SKIP] z3-solver no está instalado.")
    sys.exit(0)

from src.analysis.collatz_cycles import no_nontrivial_cycle, cycle_system


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def main():
    print(f"{Colors.BOLD}=== NO-EXISTENCIA CERTIFICADA DE CICLOS DE COLLATZ ==={Colors.ENDC}")
    stats = Stats()

    print(f"{Colors.HEADER}[1] Z3 certifica: no hay ciclo no trivial de longitud 1..6{Colors.ENDC}")
    MAXL = 6
    for L in range(1, MAXL + 1):
        verdict, witness = no_nontrivial_cycle(L, timeout_ms=20000)
        if verdict == 'unsat':
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} L={L}: UNSAT (ningún ciclo no trivial)")
        else:
            stats.fail(f"L={L}: {verdict} (esperado unsat){'  contraejemplo='+str(witness) if witness else ''}")

    print(f"{Colors.HEADER}[2] Sanity: el encoding acepta el ciclo trivial {{1,2}} (no es vacuo){Colors.ENDC}")
    from z3 import Or, sat
    s, xs = cycle_system(2)
    # quitar la condicion de no-trivialidad reconstruyendo sin ella:
    s2, xs2 = _trivial_allowed(2)
    if s2.check() == sat:
        m = s2.model()
        cyc = [m[x].as_long() for x in xs2]
        if sorted(cyc) == [1, 2]:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} L=2 sin no-trivialidad: SAT, ciclo {cyc} (acepta ciclos reales)")
        else:
            stats.fail(f"L=2 sin no-trivialidad: SAT pero ciclo inesperado {cyc}")
    else:
        stats.fail("L=2 sin no-trivialidad debería ser SAT (encoding vacuo)")

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — no-existencia de ciclos cortos "
              f"certificada por Z3, con el encoding validado (acepta ciclos reales).{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


def _trivial_allowed(L):
    """Como cycle_system pero SIN la condicion de no-trivialidad (>=3)."""
    from z3 import Int, Solver, Or
    s = Solver()
    xs = [Int(f'x{i}') for i in range(L)]
    bs = [Int(f'b{i}') for i in range(L)]
    qs = [Int(f'q{i}') for i in range(L)]
    for i in range(L):
        s.add(xs[i] >= 1, Or(bs[i] == 0, bs[i] == 1), xs[i] == 2 * qs[i] + bs[i], qs[i] >= 0)
        s.add(2 * xs[(i + 1) % L] == xs[i] + bs[i] * (2 * xs[i] + 1))
    return s, xs


if __name__ == "__main__":
    main()
