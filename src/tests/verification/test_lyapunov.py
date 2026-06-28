#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - ESTRUCTURA POR DESIGUALDAD: FUNCIONES DE LYAPUNOV
================================================================================
Valida src/analysis/lyapunov.py: encontrar estructura DONDE NO HAY INVARIANTE
conservado. El motor de descubrimiento busca igualdades Q(T)=λQ (conservativo);
este busca la cantidad MONÓTONA V que decrece (disipativo/terminante), con
certificado portable exacto (ecuación de Lyapunov discreta, racional, Sylvester).

Demuestra la COMPLEMENTARIEDAD honesta:
  - DISIPATIVO (|λ|<1): hay Lyapunov certificada, NO hay cantidad conservada.
    -> estructura justo donde el motor de invariantes devolvía None.
  - CONSERVATIVO (gato de Arnold, |λ|=1): NO hay Lyapunov PD, SÍ conservada.
  - EXPANSIVO (|λ|>1): ninguno de los dos -> frontera honesta.
Y que el re-verificador RECHAZA un certificado de Lyapunov manipulado.

Uso:  python src/tests/verification/test_lyapunov.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.lyapunov import find_lyapunov, verify_lyapunov
from src.analysis.discovery_engine import find_conserved_quantities, verify_conserved

R = sympy.Rational


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def _has_conserved(A):
    x, y = sympy.symbols('x y')
    T = [A[0][0] * x + A[0][1] * y, A[1][0] * x + A[1][1] * y]
    res = find_conserved_quantities(T, ['x', 'y'], 2, eigenvalues=(1, -1))
    return any(verify_conserved(Q, T, ['x', 'y'], l) and sympy.Poly(Q, x, y).total_degree() > 0
               for l, Q in res)


def test_dissipative(stats):
    print(f"{Colors.HEADER}[1] DISIPATIVO (|λ|<1): Lyapunov certificada DONDE NO hay invariante{Colors.ENDC}")
    A = [[R(1, 2), R(1, 10)], [0, R(1, 2)]]
    cert = find_lyapunov(A, ['x', 'y'])
    if cert is not None and verify_lyapunov(A, cert, ['x', 'y']):
        if not _has_conserved(A):
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} V={cert['V']}")
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} drift V(Ax)-V(x)={cert['drift']} <=0; SIN cantidad conservada")
        else:
            stats.fail("inesperado: el disipativo tendría conservada")
    else:
        stats.fail(f"no certificó Lyapunov para el disipativo: {cert}")


def test_conservative(stats):
    print(f"{Colors.HEADER}[2] CONSERVATIVO (gato de Arnold): NO Lyapunov PD, SÍ conservada{Colors.ENDC}")
    A = [[2, 1], [1, 1]]
    cert = find_lyapunov(A, ['x', 'y'])
    if cert is None and _has_conserved(A):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} sin Lyapunov (no es de Schur) pero con invariante -> métodos complementarios")
    else:
        stats.fail(f"esperaba None + conservada; cert={cert is not None}, conserv={_has_conserved(A)}")


def test_expansive(stats):
    print(f"{Colors.HEADER}[3] EXPANSIVO (|λ|>1): ninguno de los dos (frontera honesta){Colors.ENDC}")
    A = [[2, 0], [0, 3]]
    cert = find_lyapunov(A, ['x', 'y'])
    if cert is None and not _has_conserved(A):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} sin Lyapunov y sin conservada -> el motor no inventa estructura")
    else:
        stats.fail(f"esperaba None + sin conservada; cert={cert is not None}, conserv={_has_conserved(A)}")


def test_reverify_rejects(stats):
    print(f"{Colors.HEADER}[4] El re-verificador RECHAZA un certificado de Lyapunov manipulado{Colors.ENDC}")
    A = [[R(1, 2), R(1, 10)], [0, R(1, 2)]]
    cert = find_lyapunov(A, ['x', 'y'])
    bad = dict(cert)
    bad['P'] = sympy.Matrix(cert['P']) + sympy.Matrix([[1, 0], [0, 0]])  # rompe la ecuación
    if not verify_lyapunov(A, bad, ['x', 'y']):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} P manipulada rechazada (ya no cumple AᵀPA-P+Q=0)")
    else:
        stats.fail("aceptó un P manipulado")
    # P no definida positiva
    bad2 = dict(cert); bad2['P'] = sympy.Matrix([[-1, 0], [0, -1]]); bad2['drift'] = cert['drift']
    if not verify_lyapunov(A, bad2, ['x', 'y']):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} P no definida positiva rechazada")
    else:
        stats.fail("aceptó P no definida positiva")


def main():
    print(f"{Colors.BOLD}=== ESTRUCTURA POR DESIGUALDAD: FUNCIONES DE LYAPUNOV ==={Colors.ENDC}")
    stats = Stats()
    test_dissipative(stats)
    test_conservative(stats)
    test_expansive(stats)
    test_reverify_rejects(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — halla estructura monótona (Lyapunov) "
              f"donde no hay invariante conservado; complementario y certificado, sin sobreafirmar.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
