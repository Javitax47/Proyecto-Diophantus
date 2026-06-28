#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - PROPUESTAS / RESULTADOS PARCIALES CERTIFICADOS
================================================================================
Valida src/analysis/conjectures.py: el emisor disciplinado de propuestas. Prueba
las TRES clases y, sobre todo, que el emisor NO puede mentir:

  (A) Bandas certificadas de problemas ABIERTOS (Goldbach, Erdős–Straus,
      convergencia de Collatz, ciclos de Collatz): el certificado finito
      re-verifica, y el re-verificador RECHAZA testigos manipulados.
  (B) Estructura certificada (invariante global) donde la hay: Pell, gato de
      Arnold -> el motor la descubre y se verifica idénticamente.
  (C) Régimen caótico / no integrable -> el motor devuelve None (frontera
      honesta): Hénon, mapa no unimodular, rama impar de Collatz.

Mensaje calibrado: una banda certificada es un TEOREMA acotado (parcial), no la
solución del problema abierto; el GAP queda siempre explícito.

Uso:  python src/tests/verification/test_conjectures.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.conjectures import (
    goldbach_band, verify_goldbach_band,
    erdos_straus_band, verify_erdos_straus_band,
    collatz_convergence_band, verify_collatz_convergence_band,
    collatz_cycle_band,
    structural_proposal,
)
from src.analysis.discovery_engine import affine_transition_exprs


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def _band_ok(stats, prop, verifier, label, tamper):
    """Comprueba: la propuesta existe, está etiquetada como acotada con GAP,
    re-verifica, y RECHAZA una manipulación del testigo."""
    if prop is None:
        stats.fail(f"{label}: no se generó banda"); return
    if prop['status'] != 'teorema acotado certificado' or not prop['gap']:
        stats.fail(f"{label}: etiquetado/GAP incorrecto"); return
    if not verifier(prop):
        stats.fail(f"{label}: el certificado legítimo no re-verifica"); return
    # manipular un testigo y comprobar que el re-verificador lo caza
    if verifier(tamper(prop)):
        stats.fail(f"{label}: aceptó un certificado manipulado"); return
    stats.ok()
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label}: {prop['scope']}")
    print(f"      GAP: {prop['gap']}")


def test_goldbach(stats):
    print(f"{Colors.HEADER}[A1] Goldbach fuerte: banda certificada por testigos (p,q){Colors.ENDC}")
    prop = goldbach_band(2000)
    def tamper(p):
        q = dict(p); w = dict(q['witnesses']); m = next(iter(w)); a, b = w[m]
        w[m] = (a + 1, b)  # rompe p+q=m
        q['witnesses'] = w; return q
    _band_ok(stats, prop, verify_goldbach_band, "Goldbach hasta 2000", tamper)


def test_erdos_straus(stats):
    print(f"{Colors.HEADER}[A2] Erdős–Straus: banda certificada por ternas (x,y,z){Colors.ENDC}")
    prop = erdos_straus_band(300)
    def tamper(p):
        q = dict(p); w = dict(q['witnesses']); n = next(iter(w)); x, y, z = w[n]
        w[n] = (x + 1, y, z)  # rompe 1/x+1/y+1/z=4/n
        q['witnesses'] = w; return q
    _band_ok(stats, prop, verify_erdos_straus_band, "Erdős–Straus hasta 300", tamper)


def test_collatz_convergence(stats):
    print(f"{Colors.HEADER}[A3] Convergencia de Collatz: banda certificada por #pasos{Colors.ENDC}")
    prop = collatz_convergence_band(5000)
    def tamper(p):
        q = dict(p); w = dict(q['witnesses']); n = next(k for k in w if k > 1)
        w[n] = w[n] + 1  # número de pasos incorrecto
        q['witnesses'] = w; return q
    _band_ok(stats, prop, verify_collatz_convergence_band, "Collatz alcanza 1 hasta n=5000", tamper)


def test_collatz_cycles(stats):
    print(f"{Colors.HEADER}[A4] No-ciclos de Collatz: banda certificada por UNSAT (Z3){Colors.ENDC}")
    try:
        import z3  # noqa: F401
    except ImportError:
        print("  [SKIP] z3 no está instalado."); return
    prop = collatz_cycle_band(5, timeout_ms=20000)
    if prop is None:
        stats.fail("no se certificó ninguna longitud"); return
    if prop['proven'] >= 1 and prop['gap']:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {prop['scope']}")
        print(f"      GAP: {prop['gap']}")
    else:
        stats.fail(f"banda de ciclos inesperada: proven={prop['proven']}")


def test_structure_found(stats):
    print(f"{Colors.HEADER}[B] Estructura certificada (invariante global) donde existe{Colors.ENDC}")
    cases = [
        ([[1, 2], [1, 1]], "Pell (x,y)->(x+2y,x+y)"),
        ([[2, 1], [1, 1]], "gato de Arnold (x,y)->(2x+y,x+y)"),
    ]
    for A, label in cases:
        T = affine_transition_exprs(A, [0, 0], ['x', 'y'])
        prop = structural_proposal(T, ['x', 'y'], f"{label} conserva una forma cuadrática.",
                                   2, eigenvalues=(1, -1))
        if prop['status'] == 'estructura certificada' and prop.get('invariant') is not None:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label}: {prop['certificate']}")
        else:
            stats.fail(f"{label}: no descubrió invariante (status={prop['status']})")


def test_structure_none(stats):
    print(f"{Colors.HEADER}[C] Régimen caótico / no integrable -> None (frontera honesta){Colors.ENDC}")
    x, y = sympy.symbols('x y')
    cases = [
        ([1 - sympy.Rational(7, 5) * x**2 + y, sympy.Rational(3, 10) * x], ['x', 'y'], "Hénon (caótico)"),
        (affine_transition_exprs([[3, 1], [1, 1]], [0, 0], ['x', 'y']), ['x', 'y'], "lineal no unimodular det=2"),
        ([3 * x + 1], ['x'], "rama impar de Collatz x->3x+1"),
    ]
    for T, names, label in cases:
        prop = structural_proposal(T, names, f"{label} tendría invariante de bajo grado.",
                                   2, eigenvalues=(1, -1))
        if prop['status'] == 'sin estructura (None)' and prop['certificate'] is None:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label}: None (no hay invariante polinómico de bajo grado)")
        else:
            stats.fail(f"{label}: inventó estructura (status={prop['status']}, cert={prop['certificate']})")


def main():
    print(f"{Colors.BOLD}=== PROPUESTAS / RESULTADOS PARCIALES CERTIFICADOS ==={Colors.ENDC}")
    stats = Stats()
    test_goldbach(stats)
    test_erdos_straus(stats)
    test_collatz_convergence(stats)
    test_collatz_cycles(stats)
    test_structure_found(stats)
    test_structure_none(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — bandas certificadas (parciales) "
              f"con GAP explícito; estructura donde la hay; None donde no. Sin sobreafirmar.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
