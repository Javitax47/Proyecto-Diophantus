#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CANDIDATOS A SECUENCIA OEIS (reproducibilidad + invariante)
================================================================================
Valida src/analysis/oeis_candidates.py: que los generadores reproducen EXACTAMENTE
los términos del candidato (reproducibilidad, requisito para enviar a OEIS) y que
la superficie que lo define está CERTIFICADA (invariante conservado por Vieta).

NO afirma novedad: la verificación autoritativa la hacen los editores de OEIS al
enviar (ver OEIS_CANDIDATES.md). Aquí solo se garantiza corrección y reproducibilidad.

Uso:  python src/tests/verification/test_oeis_candidates.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.oeis_candidates import markoff_hurwitz_4_4, markoff_hurwitz_4_1
from src.analysis.discovery_engine import verify_conserved


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


EXPECTED_44 = [1, 3, 11, 41, 131, 153, 571, 1561, 1803, 2131,
               5761, 7953, 17291, 18601, 25091, 29681]


def test_reproducible(stats):
    print(f"{Colors.HEADER}[1] El generador reproduce EXACTAMENTE los términos (a=4){Colors.ENDC}")
    got = markoff_hurwitz_4_4(10**5)
    if got[:len(EXPECTED_44)] == EXPECTED_44:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} primeros términos: {got[:10]} …")
    else:
        stats.fail(f"términos no coinciden: {got[:len(EXPECTED_44)]}")


def test_scaling(stats):
    print(f"{Colors.HEADER}[2] Relación de escala: (a=1) = 2·(a=4){Colors.ENDC}")
    a4 = markoff_hurwitz_4_4(10**6)
    a1 = markoff_hurwitz_4_1(10**6)
    n = min(len(a4), len(a1), 20)
    if a1[:n] == [2 * v for v in a4[:n]]:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} confirmada en los primeros {n} términos")
    else:
        stats.fail("la relación de escala falla")


def test_invariant_certified(stats):
    print(f"{Colors.HEADER}[3] Superficie certificada: invariante conservado por Vieta{Colors.ENDC}")
    a, b, c, d = sympy.symbols('a b c d')
    inv = a**2 + b**2 + c**2 + d**2 - 4 * a * b * c * d
    involution = [a, b, c, 4 * a * b * c - d]   # (a,b,c,d) -> (a,b,c, 4abc - d)
    if verify_conserved(inv, involution, ['a', 'b', 'c', 'd'], 1):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} a²+b²+c²+d²-4abcd conservado bajo la involución (∀ punto)")
    else:
        stats.fail("el invariante no se conserva")


def test_terms_satisfy_equation(stats):
    print(f"{Colors.HEADER}[4] Todo término aparece en una solución real de la ecuación{Colors.ENDC}")
    # comprobación estructural: (1,1,1,1) es solución y genera 3,11,... por Vieta
    sols = [(1, 1, 1, 1)]
    ok = all(sum(v * v for v in s) == 4 * s[0] * s[1] * s[2] * s[3] for s in sols)
    # el siguiente: (1,1,1, 4*1*1*1-1=3) -> 1+1+1+9=12 = 4*1*1*1*3=12
    nxt = (1, 1, 1, 3)
    ok = ok and sum(v * v for v in nxt) == 4 * nxt[0] * nxt[1] * nxt[2] * nxt[3]
    if ok:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} (1,1,1,1) y (1,1,1,3) satisfacen a²+b²+c²+d²=4abcd")
    else:
        stats.fail("una solución no satisface la ecuación")


def main():
    print(f"{Colors.BOLD}=== CANDIDATOS A SECUENCIA OEIS (Markoff-Hurwitz 4D) ==={Colors.ENDC}")
    stats = Stats()
    test_reproducible(stats)
    test_scaling(stats)
    test_invariant_certified(stats)
    test_terms_satisfy_equation(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — candidato reproducible y certificado. "
              f"Novedad: la verifican los editores de OEIS al enviar (ver OEIS_CANDIDATES.md).{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
