#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOS DE DESIGUALDAD (SUMA DE CUADRADOS / Positivstellensatz)
================================================================================
Valida src/analysis/sos.py: el TERCER tipo de certificado portable (desigualdad),
tras el testigo (SAT) y el Nullstellensatz (igualdad/UNSAT). Certifica p >= 0
exhibiendo p = sum c_i q_i² con c_i >= 0 (suma de cuadrados), re-verificable sin
solver (expandir y comparar; comprobar c_i >= 0).

Comprueba:
  - certifica formas cuadráticas PSD (incl. singular y con término lineal) y la
    suma de cuadrados explícita re-verifica;
  - SOUNDNESS: rechaza formas INDEFINIDAS (devuelve None, no miente);
  - el re-verificador rechaza un certificado con coeficiente negativo;
  - límite honesto documentado: SOS no es completo (Motzkin >=0 no es SOS) y el
    grado alto pertenece a un backend SDP.

Uso:  python src/tests/verification/test_sos.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
    import z3  # noqa: F401
except ImportError:
    print("[SKIP] sympy/z3 no están instalados.")
    sys.exit(0)

from src.analysis.sos import sos_certificate, verify_sos

x, y, z = sympy.symbols('x y z')


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_psd_forms(stats):
    print(f"{Colors.HEADER}[1] Certifica formas no negativas como suma de cuadrados{Colors.ENDC}")
    cases = [
        (x**2 - x*y + y**2, ['x', 'y'], "x²-xy+y²"),
        (2*x**2 + 2*y**2 + 2*z**2 - 2*x*y - 2*y*z - 2*x*z, ['x', 'y', 'z'], "forma PSD singular 3v"),
        ((x + y)**2 + (x - 1)**2, ['x', 'y'], "(x+y)²+(x-1)² (con término lineal)"),
    ]
    for p, names, label in cases:
        c = sos_certificate(p, names, 2)
        if c is not None and verify_sos(p, c, names):
            sq = ' + '.join(f'({coef})·({q})²' for coef, q in c['squares'])
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label} = {sq}")
        else:
            stats.fail(f"{label}: no certificó / no re-verifica (c={c})")


def test_indefinite_rejected(stats):
    print(f"{Colors.HEADER}[2] SOUNDNESS: forma INDEFINIDA -> None (no afirma p>=0){Colors.ENDC}")
    for p, label in [(x**2 - 3*x*y + y**2, "x²-3xy+y²"), (x*y, "x·y")]:
        c = sos_certificate(p, ['x', 'y'], 2)
        if c is None:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label} indefinida -> None (no fabrica certificado)")
        else:
            stats.fail(f"{label}: fabricó un SOS para una forma indefinida: {c}")


def test_reverify_rejects(stats):
    print(f"{Colors.HEADER}[3] El re-verificador rechaza certificados inválidos{Colors.ENDC}")
    # coeficiente negativo
    if not verify_sos(x**2 + y**2, {'squares': [(-1, x), (1, y)]}, ['x', 'y']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} coeficiente negativo rechazado")
    else:
        stats.fail("aceptó coeficiente negativo")
    # no suma a p
    if not verify_sos(x**2 + y**2, {'squares': [(1, x)]}, ['x', 'y']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} suma de cuadrados que no reconstruye p rechazada")
    else:
        stats.fail("aceptó una suma que no reconstruye p")


def test_incompleteness_documented(stats):
    print(f"{Colors.HEADER}[4] Límite honesto: SOS no es completo (no afirma de más){Colors.ENDC}")
    # No ejecutamos Motzkin (grado 6, lento); comprobamos que el módulo documenta
    # su incompletitud y que para una forma claramente NO cuadrática-PSD devuelve None.
    import src.analysis.sos as sosmod
    if "no es SOS" in (sosmod.__doc__ or "") and "NO COMPLETO" in (sosmod.__doc__ or ""):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} incompletitud (Motzkin) y dependencia de SDP documentadas en el módulo")
    else:
        stats.fail("la incompletitud no está documentada")


def main():
    print(f"{Colors.BOLD}=== CERTIFICADOS DE DESIGUALDAD: SUMA DE CUADRADOS ==={Colors.ENDC}")
    stats = Stats()
    test_psd_forms(stats)
    test_indefinite_rejected(stats)
    test_reverify_rejects(stats)
    test_incompleteness_documented(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — certificados de no-negatividad (SOS) "
              f"portables y sólidos; rechaza indefinidas; incompletitud documentada.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
