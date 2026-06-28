#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - ESTRATEGIAS DE CODIFICACIÓN (¿ecuación global mejor?)
================================================================================
Valida src/analysis/encodings.py y demuestra, con números, la tesis honesta:

  (2) FORMA CERRADA (exponenciación de matrices) acelera de verdad —O(log T)—
      PERO sólo donde la transición es AFÍN (estructura lineal). Coincide con el
      desenrollado y resuelve T astronómico (mód m).
  (3) β-COLLAPSE produce la "ecuación global" pero su testigo NO encoge: codifica
      la traza entera, su tamaño en bits >= información de la traza. No acelera.
  Selector: afín -> forma cerrada (alcanza n grande); no afín -> desenrollado.

Mensaje: la palanca es la ESTRUCTURA, no la codificación. Ninguna codificación
acelera el régimen sin estructura (Collatz y los problemas duros).

Uso:  python src/tests/verification/test_encodings.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.analysis.encodings import (
    closed_form_affine, unroll_affine, verify_closed_form_affine,
    beta_collapse_cost, compare_affine, best_strategy,
)

P = 10**9 + 7


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


# Sistemas afines: Fibonacci, Pell (x,y)->(x+2y,x+y), recurrencia con término constante.
AFFINE = [
    ([[1, 1], [1, 0]], [0, 0], (1, 0), "Fibonacci"),
    ([[1, 2], [1, 1]], [0, 0], (1, 1), "Pell"),
    ([[2, 0], [0, 1]], [3, 1], (1, 0), "x->2x+3, y->y+1"),
]


def test_closed_form_matches(stats):
    print(f"{Colors.HEADER}[1] Forma cerrada (O(log T)) == desenrollado (exacto){Colors.ENDC}")
    for A, d, x0, name in AFFINE:
        ok = all(verify_closed_form_affine(A, d, x0, T, P) for T in (10, 100, 1000, 4000))
        if ok:
            stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {name}: coincide para T en {{10,100,1000,4000}} (mód p)")
        else:
            stats.fail(f"{name}: forma cerrada != desenrollado")


def test_large_T_fast(stats):
    print(f"{Colors.HEADER}[2] Forma cerrada resuelve T ASTRONÓMICO (mód p) al instante{Colors.ENDC}")
    A, d, x0, _ = AFFINE[0]
    t0 = time.perf_counter()
    r = closed_form_affine(A, d, x0, 10**18, P)
    dt = time.perf_counter() - t0
    if dt < 1.0 and 0 <= r[0] < P:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} F(10^18+1) mód p = {r[0]} en {dt*1000:.2f} ms")
    else:
        stats.fail(f"T=10^18 tardó {dt:.2f}s (esperado <1s)")


def test_speedup(stats):
    print(f"{Colors.HEADER}[3] La forma cerrada es MÁS RÁPIDA que el desenrollado (T grande){Colors.ENDC}")
    A, d, x0, _ = AFFINE[0]
    c = compare_affine(A, d, x0, 30000, P)
    if c['match'] and c['t_closed'] < c['t_unroll']:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} T=30000: cerrada {c['t_closed']*1000:.2f}ms < unroll {c['t_unroll']*1000:.1f}ms "
              f"(×{c['speedup']:.0f})")
    else:
        stats.fail(f"sin aceleración: {c}")


def test_beta_witness_not_smaller(stats):
    print(f"{Colors.HEADER}[4] β-collapse: el testigo NO encoge (codifica la traza entera){Colors.ENDC}")
    def collatz(n): return n // 2 if n % 2 == 0 else 3 * n + 1
    all_ok = True
    for start in (27, 97, 871):
        info = beta_collapse_cost(collatz, start)
        if info['a_bits'] < info['trace_info_bits']:
            all_ok = False
            stats.fail(f"start={start}: testigo {info['a_bits']}b < info traza {info['trace_info_bits']}b")
        else:
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} start={start}: T={info['T']}, testigo a={info['a_bits']}b "
                  f">= info traza {info['trace_info_bits']}b (no acelera)")
    if all_ok:
        stats.ok()


def test_selector(stats):
    print(f"{Colors.HEADER}[5] Selector: afín alcanza n grande; no afín no{Colors.ENDC}")
    if best_strategy(True)['reaches_large_n'] and not best_strategy(False)['reaches_large_n']:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} afín -> {best_strategy(True)['time']}; "
              f"no afín -> {best_strategy(False)['time']}")
    else:
        stats.fail("selector incoherente")


def main():
    print(f"{Colors.BOLD}=== ESTRATEGIAS DE CODIFICACIÓN: ¿ecuación global mejor? ==={Colors.ENDC}")
    stats = Stats()
    test_closed_form_matches(stats)
    test_large_T_fast(stats)
    test_speedup(stats)
    test_beta_witness_not_smaller(stats)
    test_selector(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — la forma cerrada acelera donde hay "
              f"estructura afín; β-collapse no acelera. La palanca es la estructura.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
