#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL COLAPSO LINEAL (Fase 2/3, Nivel 3/5)
================================================================================
Valida que, para recurrencias lineales x_{i+1}=c*x_i+d, los T pasos colapsan en
UNA sola ecuacion sobre la traza empaquetada N (eliminacion del cuantificador
universal acotado). Comprueba:

  (1) POSITIVO: una traza lineal real satisface la ecuacion cerrada.
  (2) NEGATIVO: una traza con UN paso roto (o no lineal) NO la satisface.
  (3) INDEPENDENCIA DE T: la MISMA ecuacion vale para T muy distintos.
  (4) round-trip de pack_digits.

Uso:  python src/tests/verification/test_linear_collapse.py
"""

import os
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.analysis.linear_collapse import (
    pack_digits, choose_base, collapse_holds, linear_trace, pack_and_collapse,
    coupled_trace, coupled_collapse_holds, pack_and_collapse_coupled,
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


def test_positive(stats):
    print(f"{Colors.HEADER}[1] Trazas lineales reales satisfacen la ecuacion cerrada{Colors.ENDC}")
    rng = random.Random(20260615)
    for _ in range(50):
        c = rng.randint(1, 5); d = rng.randint(0, 7); x0 = rng.randint(0, 6)
        T = rng.randint(1, 9)
        xs, base, N = pack_and_collapse(c, d, x0, T)
        if collapse_holds(N, xs[0], xs[-1], c, d, base, T):
            stats.ok()
        else:
            stats.fail(f"c={c} d={d} x0={x0} T={T}: traza lineal NO satisface")


def test_negative(stats):
    print(f"{Colors.HEADER}[2] Una traza con un paso roto NO satisface (sin soluciones espurias){Colors.ENDC}")
    rng = random.Random(99)
    bad_caught = 0; total = 0
    for _ in range(40):
        c = rng.randint(1, 4); d = rng.randint(0, 5); x0 = rng.randint(0, 5)
        T = rng.randint(2, 8)
        xs = linear_trace(c, d, x0, T)
        # romper un paso intermedio
        idx = rng.randint(1, len(xs) - 1)
        xs[idx] += rng.choice([-1, 1, 2])
        if any(x < 0 for x in xs):
            continue
        base = choose_base(xs)
        N = pack_digits(xs, base)
        total += 1
        if not collapse_holds(N, xs[0], xs[-1], c, d, base, T):
            bad_caught += 1
    if total > 0 and bad_caught == total:
        stats.ok()
        print(f"     {bad_caught}/{total} trazas rotas detectadas")
    else:
        stats.fail(f"solo {bad_caught}/{total} trazas rotas detectadas")


def test_length_independence(stats):
    print(f"{Colors.HEADER}[3] La MISMA ecuacion vale para T muy distintos{Colors.ENDC}")
    c, d, x0 = 2, 1, 1  # x_{i+1}=2x_i+1 -> Mersenne 1,3,7,15,...
    for T in [1, 5, 20, 60]:
        xs, base, N = pack_and_collapse(c, d, x0, T)
        if collapse_holds(N, xs[0], xs[-1], c, d, base, T):
            stats.ok()
            print(f"     T={T:3d}: OK (N tiene {len(str(N))} digitos decimales)")
        else:
            stats.fail(f"T={T}: falla")


def test_pack_roundtrip(stats):
    print(f"{Colors.HEADER}[4] pack_digits round-trip{Colors.ENDC}")
    rng = random.Random(7)
    for _ in range(20):
        base = rng.randint(2, 50)
        xs = [rng.randint(0, base - 1) for _ in range(rng.randint(1, 10))]
        N = pack_digits(xs, base)
        # desempaquetar
        rec = []
        m = N
        for _ in range(len(xs)):
            rec.append(m % base); m //= base
        if rec == xs:
            stats.ok()
        else:
            stats.fail(f"round-trip falla: {xs} base {base}")


def test_coupled(stats):
    print(f"{Colors.HEADER}[5] Sistemas afines ACOPLADOS (multi-registro){Colors.ENDC}")
    rng = random.Random(2024)
    for _ in range(30):
        m = rng.randint(2, 3)
        A = [[rng.randint(0, 3) for _ in range(m)] for _ in range(m)]
        d = [rng.randint(0, 4) for _ in range(m)]
        x0 = [rng.randint(0, 4) for _ in range(m)]
        T = rng.randint(1, 7)
        xs, base, packed = pack_and_collapse_coupled(A, d, x0, T)
        if coupled_collapse_holds(packed, xs[0], xs[-1], A, d, base, T):
            stats.ok()
        else:
            stats.fail(f"acoplado A={A} d={d} x0={x0} T={T} no satisface")
    # NEGATIVO: romper un paso de un registro
    A = [[0, 1], [1, 1]]; d = [0, 0]; x0 = [0, 1]; T = 6
    xs = coupled_trace(A, d, x0, T)
    xs[3][1] += 1
    base = choose_base([xs[i][j] for i in range(len(xs)) for j in range(2)])
    packed = [pack_digits([xs[i][j] for i in range(len(xs))], base) for j in range(2)]
    if not coupled_collapse_holds(packed, xs[0], xs[-1], A, d, base, T):
        stats.ok()
    else:
        stats.fail("traza acoplada rota paso la verificacion")


def test_fibonacci(stats):
    print(f"{Colors.HEADER}[6] Fibonacci como recurrencia acoplada [a,b] -> [b, a+b]{Colors.ENDC}")
    # A = [[0,1],[1,1]] reproduce Fibonacci: la MISMA ecuacion para varios T.
    A = [[0, 1], [1, 1]]; d = [0, 0]; x0 = [0, 1]
    for T in [4, 10, 25]:
        xs, base, packed = pack_and_collapse_coupled(A, d, x0, T)
        fib = [xs[i][0] for i in range(len(xs))]  # la 1a componente es Fibonacci
        ok_fib = fib[:6] == [0, 1, 1, 2, 3, 5][:len(fib)]
        if coupled_collapse_holds(packed, xs[0], xs[-1], A, d, base, T) and ok_fib:
            stats.ok()
            print(f"     T={T:2d}: Fibonacci {fib[:8]}... verificado")
        else:
            stats.fail(f"Fibonacci T={T} falla")


def main():
    print(f"{Colors.BOLD}=== TEST DEL COLAPSO LINEAL (cuantificador acotado -> 1 ecuacion) ==={Colors.ENDC}")
    stats = Stats()
    test_positive(stats)
    test_negative(stats)
    test_length_independence(stats)
    test_pack_roundtrip(stats)
    test_coupled(stats)
    test_fibonacci(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — los T pasos lineales "
              f"colapsan en UNA ecuacion, independiente de T.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
