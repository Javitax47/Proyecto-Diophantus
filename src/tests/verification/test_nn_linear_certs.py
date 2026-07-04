#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOS NN-LINEAL  (vertical de la capa universal)
================================================================================
Sexto dominio: robustez de una capa lineal y(x)=w·x+b sobre una caja, con el
MISMO certificado portable y el MISMO `recheck` (que gana el primitivo
Positivstellensatz):

  * robusto (y >= L en toda la caja)  -> Positivstellensatz  -> recheck VÁLIDO
  * no robusto                        -> testigo del vértice  -> recheck VÁLIDO
  * soundness: no se certifica robustez falsa; un cert manipulado -> INVÁLIDO

Uso:  python src/tests/verification/test_nn_linear_certs.py
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

from src.product import nn_linear as nn
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


BOX = [(0, 1), (0, 1)]   # x0, x1 en [0,1]


def test_robust(stats):
    # y = 2 x0 + 3 x1 + 1, mínimo en (0,0) = 1 >= 0  -> robusto (pre-activación >= 0)
    cert, robust = nn.certify([2, 3], 1, BOX, L=0)
    _check(stats, robust, "y=2x0+3x1+1 sobre [0,1]²: robusto (y>=0)")
    _check(stats, cert is not None and cert.get('kind') == 'positivstellensatz',
           "robusto -> certificado Positivstellensatz")
    ok, _ = recheck(cert)
    _check(stats, ok, "recheck acepta el Positivstellensatz (VÁLIDO)")


def test_not_robust(stats):
    # y = 2 x0 - 3 x1 + 1, mínimo en (0,1) = -2 < 0  -> NO robusto
    cert, robust = nn.certify([2, -3], 1, BOX, L=0)
    _check(stats, not robust, "y=2x0-3x1+1 sobre [0,1]²: NO robusto (min=-2)")
    _check(stats, cert is not None and cert.get('kind') == 'witness',
           "no robusto -> testigo del vértice")
    ok, _ = recheck(cert)
    _check(stats, ok, "recheck acepta el testigo de violación (VÁLIDO)")


def test_cannot_overclaim(stats):
    # No se puede certificar robustez donde no la hay: min < L -> None.
    _check(stats, nn.certify_lower_bound([2, -3], 1, BOX, L=0) is None,
           "robustez falsa NO se certifica (soundness: min<L -> None)")
    # Cota válida más floja sí (y >= -2).
    _check(stats, nn.certify_lower_bound([2, -3], 1, BOX, L=-2) is not None,
           "cota válida y>=-2 sí se certifica")


def test_soundness_tampered(stats):
    cert = nn.certify_lower_bound([2, 3], 1, BOX, L=0)
    # Multiplicador negativo -> recheck RECHAZA.
    bad = dict(cert); bad['certificate'] = dict(cert['certificate'])
    terms = [list(t) for t in cert['certificate']['terms']]
    terms[0][0] = f"-({terms[0][0]}) - 1"
    bad['certificate']['terms'] = terms
    ok, _ = recheck(bad)
    _check(stats, not ok, "multiplicador negativo -> recheck RECHAZA (soundness)")

    # Constante alterada (rompe la identidad) -> recheck RECHAZA.
    bad2 = dict(cert); bad2['certificate'] = dict(cert['certificate'])
    bad2['certificate'] = {'constant': str(int(cert['certificate']['constant']) + 5),
                           'terms': cert['certificate']['terms']}
    ok2, _ = recheck(bad2)
    _check(stats, not ok2, "constante alterada -> recheck RECHAZA (soundness)")


def main():
    print("=== CERTIFICADOS NN-LINEAL (vertical de la capa universal) ===")
    stats = _Stats()
    test_robust(stats)
    test_not_robust(stats)
    test_cannot_overclaim(stats)
    test_soundness_tampered(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"✓ {stats.passed}/{total} casos OK — la robustez de la capa lineal se "
              f"certifica (Positivstellensatz) con el mismo recheck y no admite "
              f"robustez falsa.")
        sys.exit(0)
    print(f"✗ {stats.failed}/{total} casos FALLARON.")
    sys.exit(1)


if __name__ == "__main__":
    main()
