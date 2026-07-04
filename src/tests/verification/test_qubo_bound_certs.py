#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOS COTA-QUBO  (vertical de la capa universal)
================================================================================
Quinto dominio: certificar el óptimo / una cota inferior de un QUBO sobre {0,1}^n
con el MISMO certificado portable y el MISMO `recheck` (solo sympy):

  * óptimo V  -> testigo que lo alcanza + Nullstellensatz de que nada lo mejora
  * cada pieza se re-verifica por separado con recheck
  * soundness: NO se puede certificar una cota falsa (demasiado alta) -> None
  * soundness: un sub-certificado manipulado -> recheck INVÁLIDO

Uso:  python src/tests/verification/test_qubo_bound_certs.py
Requisitos: sympy.
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import sympy  # noqa: F401
except ImportError:
    print("[SKIP] sympy no disponible.")
    sys.exit(0)

from src.product import qubo_bound as qb
from src.product.recheck import recheck


class _Stats:
    def __init__(self):
        self.passed = 0
        self.failed = 0


def _check(stats, cond, label):
    if cond:
        stats.passed += 1
        print(f"   OK   {label}")
    else:
        stats.failed += 1
        print(f"   FAIL {label}")


# QUBO de ejemplo: p = x0 + x1 + x2 - 3 x0 x1 - 3 x1 x2  (mínimo real = -3)
LINEAR = {0: 1, 1: 1, 2: 1}
QUAD = {(0, 1): -3, (1, 2): -3}
N = 3


def test_optimum(stats):
    V, arg = qb.brute_min(LINEAR, QUAD, N)
    cert = qb.certify_optimum(LINEAR, QUAD, N)
    _check(stats, cert is not None, "certify_optimum devuelve certificado")
    _check(stats, cert['optimum'] == V, f"óptimo reportado = {V} (fuerza bruta)")

    ok_w, _ = recheck(cert['witness'])
    _check(stats, ok_w, "recheck acepta el testigo del óptimo (VÁLIDO)")

    subs = cert['lower_bound']['infeasible_certs']
    all_ok = all(recheck(c)[0] for c in subs)
    _check(stats, all_ok,
           f"recheck acepta las {len(subs)} piezas de la cota inferior (VÁLIDO)")


def test_cannot_overclaim(stats):
    # Una cota FALSA (mayor que el mínimo real) no debe certificarse: el propio
    # mínimo sigue siendo alcanzable -> su sistema es factible -> sin Nullstellensatz.
    V, _ = qb.brute_min(LINEAR, QUAD, N)
    bad = qb.certify_bound(LINEAR, QUAD, N, V + 1)
    _check(stats, bad is None,
           f"cota falsa p>={V + 1} NO se certifica (soundness: no over-claim)")
    # Una cota válida más floja SÍ se certifica.
    loose = qb.certify_bound(LINEAR, QUAD, N, V)
    _check(stats, loose is not None, f"cota válida p>={V} sí se certifica")


def test_soundness_tampered(stats):
    cert = qb.certify_optimum(LINEAR, QUAD, N)
    sub = cert['lower_bound']['infeasible_certs'][0]
    bad = dict(sub)
    bad['certificate'] = dict(sub['certificate'])
    cof = list(sub['certificate']['cofactors'])
    cof[0] = f"({cof[0]}) + 1"
    bad['certificate']['cofactors'] = cof
    ok, _ = recheck(bad)
    _check(stats, not ok, "cofactor manipulado -> recheck RECHAZA (soundness)")


def main():
    print("=== CERTIFICADOS COTA-QUBO (vertical de la capa universal) ===")
    stats = _Stats()
    test_optimum(stats)
    test_cannot_overclaim(stats)
    test_soundness_tampered(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"✓ {stats.passed}/{total} casos OK — la cota/óptimo QUBO se certifica "
              f"con el mismo recheck trustless y no admite cotas falsas.")
        sys.exit(0)
    print(f"✗ {stats.failed}/{total} casos FALLARON.")
    sys.exit(1)


if __name__ == "__main__":
    main()
