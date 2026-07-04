#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE DOMINANCIA DE DIGITOS / KUMMER-LUCAS
================================================================================
Valida el primitivo para colapsar el cuantificador
universal acotado en el caso general. Comprueba:

  (1) KUMMER-LUCAS: binom(n,k) es impar  <=>  k ⪯ n (dominancia), contrastando
      la formula de Lucas contra el binomial calculado a fuerza bruta.
  (2) DOMINANCIA: a ⪯ b  <=>  a AND b == a  <=>  suma sin acarreo de a y (b-a).
  (3) COLAPSO DIGITO-A-DIGITO: para trazas empaquetadas en base 2^k, "cada digito
      de N esta dominado por el de M en TODA posicion" equivale a UNA sola
      relacion de dominancia global (sin recorrer las posiciones).

Uso:  python src/tests/verification/test_digit_dominance.py
"""

import os
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.analysis.digit_dominance import (
    dominates, carry_free_sum, binom_parity, binom_parity_bruteforce,
    base_pow_digits, all_digits_dominated,
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


def test_kummer_lucas(stats):
    print(f"{Colors.HEADER}[1] Kummer-Lucas: binom(n,k) impar <=> k ⪯ n{Colors.ENDC}")
    bad = 0; total = 0
    for n in range(0, 64):
        for k in range(0, n + 1):
            total += 1
            lucas = binom_parity(n, k)
            brute = binom_parity_bruteforce(n, k)
            dom = 1 if dominates(k, n) else 0
            if not (lucas == brute == dom):
                bad += 1
                if bad <= 3:
                    stats_fail = f"n={n} k={k}: lucas={lucas} brute={brute} dom={dom}"
                    print(f"  {Colors.FAIL}✗{Colors.ENDC} {stats_fail}")
    if bad == 0:
        stats.ok()
        print(f"     {total} pares (n,k) coinciden: Lucas == binomial == dominancia")
    else:
        stats.fail(f"{bad}/{total} discrepancias")


def test_dominance_equivalences(stats):
    print(f"{Colors.HEADER}[2] a ⪯ b <=> AND == a <=> suma sin acarreo de a y (b-a){Colors.ENDC}")
    rng = random.Random(3)
    ok_all = True
    for _ in range(2000):
        a = rng.randint(0, 1 << 12)
        b = rng.randint(0, 1 << 12)
        dom = dominates(a, b)
        and_eq = ((a & b) == a)
        carryfree = (a <= b) and carry_free_sum(a, b - a)
        if not (dom == and_eq == carryfree):
            ok_all = False
            stats.fail(f"a={a} b={b}: dom={dom} and={and_eq} carryfree={carryfree}")
            break
    if ok_all:
        stats.ok()


def test_digitwise_collapse(stats):
    print(f"{Colors.HEADER}[3] Dominancia digito-a-digito (todas las posiciones) en una relacion{Colors.ENDC}")
    rng = random.Random(11)
    k = 5  # base 2^5 = 32
    for _ in range(200):
        n = rng.randint(1, 8)
        N_digits = [rng.randint(0, (1 << k) - 1) for _ in range(n)]
        M_digits = [rng.randint(0, (1 << k) - 1) for _ in range(n)]
        Np = base_pow_digits(N_digits, k)
        Mp = base_pow_digits(M_digits, k)
        # verdad: dominancia en CADA posicion
        truth = all(dominates(N_digits[i], M_digits[i]) for i in range(n))
        # colapso: una sola relacion de dominancia global
        collapsed = all_digits_dominated(k, Np, Mp, n)
        if truth != collapsed:
            stats.fail(f"digitos N={N_digits} M={M_digits}: truth={truth} collapsed={collapsed}")
            return
    stats.ok()
    print(f"     la dominancia global equivale a la dominancia en todas las posiciones")


def main():
    print(f"{Colors.BOLD}=== TEST DE DOMINANCIA DE DIGITOS (Kummer-Lucas) ==={Colors.ENDC}")
    stats = Stats()
    test_kummer_lucas(stats)
    test_dominance_equivalences(stats)
    test_digitwise_collapse(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — el primitivo de "
              f"dominancia/Kummer-Lucas es correcto (insumo del colapso general).{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
