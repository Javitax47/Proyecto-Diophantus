#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE PRIMALIDAD CORRECTA (Baillie-PSW que reemplaza la erronea)
================================================================================
Comprueba que el nuevo baillie_psw es CORRECTO donde el antiguo fallaba:

  (1) ACUERDO TOTAL con la verdad (sympy.isprime, que usa BPSW) para todo n en
      un rango amplio: ni un falso positivo ni un falso negativo.
  (2) RECHAZA los contraejemplos del test antiguo (2465, 6601, 11305, 13981,
      30889, 68101) — compuestos que la "Ecuacion Suprema" declaraba primos.
  (3) RECHAZA pseudoprimos clasicos: Carmichael (561, 1105, 1729, 2465, 2821,
      6601, 8911) y pseudoprimos fuertes base 2 (2047, 3277, 4033, ...).
  (4) Componentes: Jacobi correcto; MR fuerte base 2 caza 561.

Uso:  python src/tests/verification/test_primality.py
Requisitos: sympy (solo para el oraculo de verdad).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from sympy import isprime, jacobi_symbol
except ImportError:
    print("[SKIP] sympy no está instalado (oráculo de verdad).")
    sys.exit(0)

from src.analysis.primality import (
    baillie_psw, jacobi, miller_rabin_strong_base2, strong_lucas_prp,
    is_prime_deterministic_64,
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


def test_agreement(stats):
    print(f"{Colors.HEADER}[1] Acuerdo total con la verdad (sympy.isprime) en [2, 100000){Colors.ENDC}")
    mism = [n for n in range(2, 100000) if baillie_psw(n) != bool(isprime(n))]
    if not mism:
        stats.ok()
        print(f"     0 discrepancias en ~100000 valores (ni falsos +, ni falsos -)")
    else:
        stats.fail(f"{len(mism)} discrepancias, p. ej. {mism[:10]}")


def test_old_counterexamples(stats):
    print(f"{Colors.HEADER}[2] Rechaza los contraejemplos de la 'Ecuacion Suprema' antigua{Colors.ENDC}")
    olds = [2465, 6601, 11305, 13981, 30889, 68101]
    bad = [n for n in olds if baillie_psw(n)]
    if not bad:
        stats.ok()
        print(f"     todos {olds} correctamente rechazados (son compuestos)")
    else:
        stats.fail(f"acepta como primos: {bad}")


def test_pseudoprimes(stats):
    print(f"{Colors.HEADER}[3] Rechaza Carmichael y pseudoprimos fuertes base 2{Colors.ENDC}")
    carmichael = [561, 1105, 1729, 2465, 2821, 6601, 8911, 10585, 15841, 29341]
    spsp2 = [2047, 3277, 4033, 4681, 8321, 15841, 29341, 42799, 49141, 52633]
    bad = [n for n in carmichael + spsp2 if baillie_psw(n)]
    if not bad:
        stats.ok()
        print(f"     {len(set(carmichael+spsp2))} pseudoprimos clásicos rechazados")
    else:
        stats.fail(f"acepta pseudoprimos: {bad}")


def test_components(stats):
    print(f"{Colors.HEADER}[4] Componentes correctos{Colors.ENDC}")
    # Jacobi coincide con sympy
    jbad = [(a, n) for n in range(3, 200, 2) for a in range(0, n)
            if jacobi(a, n) != jacobi_symbol(a, n)]
    stats.ok() if not jbad else stats.fail(f"Jacobi discrepa en {jbad[:5]}")
    # MR fuerte base 2 caza 561 (Carmichael) pero NO 2047 (spsp base 2)
    if not miller_rabin_strong_base2(561) and miller_rabin_strong_base2(2047):
        stats.ok()
        print(f"     MR fuerte base2: rechaza 561, acepta 2047 (spsp base2) — y Lucas lo caza")
    else:
        stats.fail("MR fuerte base 2 inconsistente en 561/2047")
    # el Lucas fuerte caza 2047 (lo que MR base 2 no ve)
    stats.ok() if not strong_lucas_prp(2047) else stats.fail("Lucas fuerte acepta 2047")


def test_deterministic_64(stats):
    print(f"{Colors.HEADER}[5] Determinista demostrado 64-bit (lo que 'La Bestia' pretendía){Colors.ENDC}")
    # acuerdo con la verdad en un rango
    mism = [n for n in range(2, 50000) if is_prime_deterministic_64(n) != bool(isprime(n))]
    # y sobre enteros grandes de 64 bits (primos y compuestos conocidos)
    big_primes = [(1 << 61) - 1, (1 << 31) - 1, 18446744073709551557]  # Mersenne y mayor primo < 2^64
    big_comp = [(1 << 61) - 1 - 2, 18446744073709551557 - 4, 9999999999999999999]
    pbad = [p for p in big_primes if not is_prime_deterministic_64(p)]
    cbad = [c for c in big_comp if is_prime_deterministic_64(c) != bool(isprime(c))]
    if not mism and not pbad and not cbad:
        stats.ok()
        print(f"     0 discrepancias en [2,50000) y correcto en enteros de 64 bits")
    else:
        stats.fail(f"determinista64 falla: mism={mism[:5]} pbad={pbad} cbad={cbad}")


def main():
    print(f"{Colors.BOLD}=== TEST DE PRIMALIDAD CORRECTA (Baillie-PSW) ==={Colors.ENDC}")
    stats = Stats()
    test_agreement(stats)
    test_old_counterexamples(stats)
    test_pseudoprimes(stats)
    test_components(stats)
    test_deterministic_64(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — Baillie-PSW correcto: acuerda con "
              f"la verdad y rechaza los contraejemplos del test antiguo.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
