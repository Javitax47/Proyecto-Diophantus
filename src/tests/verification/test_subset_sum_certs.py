#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOS DE SUBSET-SUM  (vertical de la capa universal)
================================================================================
Comprueba que el cuarto dominio (subset-sum) emite el MISMO certificado portable
y lo re-verifica el MISMO `recheck` (solo sympy) que programas, coloreado y SAT:

  * factible   -> testigo entero 0/1        -> recheck VÁLIDO
  * infactible -> certificado Nullstellensatz -> recheck VÁLIDO
  * control de soundness: un certificado manipulado -> recheck INVÁLIDO

Uso:  python src/tests/verification/test_subset_sum_certs.py
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

from src.product import subset_sum
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


def test_feasible(stats):
    weights, target = [3, 5, 7, 11], 15   # 3 + 5 + 7 = 15
    cert, feasible = subset_sum.certify(weights, target)
    _check(stats, feasible, f"{weights} suma {target}: reportado factible")
    _check(stats, cert is not None and cert.get('kind') == 'witness',
           "factible -> certificado de testigo")
    ok, _msg = recheck(cert)
    _check(stats, ok, "recheck acepta el testigo (VÁLIDO)")


def test_infeasible(stats):
    for weights, target in ([2, 4, 6], 5), ([1, 2], 4), ([3, 5, 7], 1):
        cert, feasible = subset_sum.certify(weights, target)
        _check(stats, not feasible, f"{weights} no suma {target}: reportado infactible")
        _check(stats, cert is not None and cert.get('kind') == 'nullstellensatz',
               f"{weights}/{target} infactible -> certificado Nullstellensatz")
        ok, _msg = recheck(cert)
        _check(stats, ok, f"{weights}/{target}: recheck acepta el Nullstellensatz (VÁLIDO)")


def test_soundness_tampered(stats):
    # Nullstellensatz manipulado: alterar un cofactor rompe la identidad = 1.
    cert, _ = subset_sum.certify([2, 4, 6], 5)
    bad = dict(cert)
    bad['certificate'] = dict(cert['certificate'])
    cof = list(cert['certificate']['cofactors'])
    cof[0] = f"({cof[0]}) + 1"
    bad['certificate']['cofactors'] = cof
    ok, _msg = recheck(bad)
    _check(stats, not ok, "cofactor manipulado -> recheck RECHAZA (soundness)")

    # Testigo manipulado: una asignación que no anula el sistema.
    cert_w, _ = subset_sum.certify([3, 5, 7, 11], 15)
    badw = dict(cert_w)
    badw['certificate'] = dict(cert_w['certificate'])
    assign = dict(cert_w['certificate']['assignment'])
    first = next(iter(assign))
    assign[first] = 1 - assign[first]     # voltear un bit rompe la suma
    badw['certificate']['assignment'] = assign
    ok, _msg = recheck(badw)
    _check(stats, not ok, "testigo manipulado -> recheck RECHAZA (soundness)")


def main():
    print("=== CERTIFICADOS DE SUBSET-SUM (vertical de la capa universal) ===")
    stats = _Stats()
    test_feasible(stats)
    test_infeasible(stats)
    test_soundness_tampered(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"✓ {stats.passed}/{total} casos OK — subset-sum emite el mismo "
              f"certificado portable, re-verificado por el mismo recheck trustless.")
        sys.exit(0)
    print(f"✗ {stats.failed}/{total} casos FALLARON.")
    sys.exit(1)


if __name__ == "__main__":
    main()
