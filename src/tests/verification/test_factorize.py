#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - FACTORIZACIÓN QUANTUM-READY (annealing) + CERTIFICADO
================================================================================
Valida src/analysis/factorize.py: N=p·q resuelto vía la formulación QUBO de un
annealer, con recocido simulado clásico, devolviendo factores y un CERTIFICADO
portable re-verificable (p·q=N) e identificando los primos con Baillie-PSW.

Comprueba:
  - factoriza semiprimos reales y p·q==N exacto;
  - los factores son primos (Baillie-PSW) -> factorización en primos correcta;
  - el certificado emitido re-verifica con el re-verificador independiente;
  - factorización COMPLETA de un compuesto en sus primos;
  - el exportador to_qubo produce un QUBO (artefacto quantum-ready) para N pequeño.

Casos elegidos para ser RÁPIDOS y fiables; la capacidad real llega a semiprimos
balanceados ~10^8–10^12 (más lentos), documentada en el módulo.

Uso:  python src/tests/verification/test_factorize.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy  # noqa: F401
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.factorize import simulated_anneal_factor, solve_and_certify, factorize, to_qubo
from src.product import recheck
from src.analysis.primality import baillie_psw


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


SEMIPRIMES = [143, 323, 437, 1147, 10403, 16637]   # 11·13 ... 127·131; rápidos


def test_factor_semiprimes(stats):
    print(f"{Colors.HEADER}[1] Factoriza semiprimos reales vía annealing (p·q==N){Colors.ENDC}")
    all_ok = True
    for N in SEMIPRIMES:
        p, q, e, st = simulated_anneal_factor(N)
        if e == 0 and p * q == N and 1 < p < N and 1 < q < N:
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {N} = {p}·{q} (restarts={st['restarts_used']})")
        else:
            all_ok = False
            stats.fail(f"{N}: no factorizó (p={p},q={q},E={e})")
    if all_ok:
        stats.ok()


def test_factors_are_prime(stats):
    print(f"{Colors.HEADER}[2] Los factores son primos (Baillie-PSW){Colors.ENDC}")
    p, q, e, _ = simulated_anneal_factor(10403)
    if e == 0 and baillie_psw(p) and baillie_psw(q) and p * q == 10403:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 10403 = {p}·{q}, ambos primos")
    else:
        stats.fail(f"10403: p={p},q={q} primos?")


def test_certificate_reverifies(stats):
    print(f"{Colors.HEADER}[3] El certificado de factorización re-verifica (independiente){Colors.ENDC}")
    r = solve_and_certify(1147)
    if not r['found']:
        stats.fail("no factorizó 1147"); return
    ok, msg = recheck.recheck(r['certificate'])
    if ok and r['certificate']['kind'] == 'witness':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {msg}")
    else:
        stats.fail(f"recheck del certificado falló: {msg}")


def test_full_factorization(stats):
    print(f"{Colors.HEADER}[4] Factorización COMPLETA en primos de un compuesto{Colors.ENDC}")
    f = factorize(360)
    prod = 1
    for x in f:
        prod *= x if isinstance(x, int) else 1
    if f == [2, 2, 2, 3, 3, 5] and prod == 360:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 360 = {' · '.join(map(str, f))}")
    else:
        stats.fail(f"360 -> {f}")


def test_qubo_artifact(stats):
    print(f"{Colors.HEADER}[5] to_qubo produce el QUBO quantum-ready (N pequeño){Colors.ENDC}")
    res = to_qubo(15)
    if res['Q'] and res['n_vars'] > 0:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} N=15 -> QUBO con {res['n_vars']} vars, |Q|={len(res['Q'])} "
              f"(input de annealer)")
    else:
        stats.fail(f"to_qubo vacío: {res}")


def main():
    print(f"{Colors.BOLD}=== FACTORIZACIÓN QUANTUM-READY (annealing) + CERTIFICADO ==={Colors.ENDC}")
    stats = Stats()
    test_factor_semiprimes(stats)
    test_factors_are_prime(stats)
    test_certificate_reverifies(stats)
    test_full_factorization(stats)
    test_qubo_artifact(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — N=p·q resuelto end-to-end vía la "
              f"formulación de annealer, con certificado re-verificable. Honesto: clásico, no bate a GNFS.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
