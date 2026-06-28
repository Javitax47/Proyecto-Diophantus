#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOS ALGEBRAICOS PORTABLES (el "producto estrella")
================================================================================
Valida src/analysis/certificates.py: los certificados de corrección RE-VERIFICABLES
SIN CONFIAR EN EL SOLVER que MONETIZACION.md identifica como el producto recurrente.
La propiedad que se prueba aquí es la que se vende:

  * SOUNDNESS del re-verificador: si `verify_*` acepta, el veredicto es correcto
    con CERTEZA y comprobable con álgebra elemental (expandir y comparar), sin Z3.
  * SOUNDNESS del finder: ante un sistema SATISFACIBLE, el finder de Nullstellensatz
    NO inventa un certificado (devuelve None). Nunca miente.
  * El re-verificador RECHAZA certificados manipulados.

Los dos tipos de certificado:
  - Testigo (SAT): la asignación; re-verificar = sustituir y comprobar 0.
  - Nullstellensatz (UNSAT): cofactores g_i con  Σ g_i·p_i = 1; re-verificar =
    expandir y comprobar = 1. Si existe, el sistema p_i=0 no tiene solución.

Uso:  python src/tests/verification/test_certificates.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.certificates import (
    nullstellensatz_certificate,
    verify_nullstellensatz,
    verify_witness,
    certify_unreachable,
)
from src.analysis.sympy_system import build_system, as_polynomials

x, y, out = sympy.symbols('x y out')


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_witness_sat(stats):
    print(f"{Colors.HEADER}[1] Certificado de SATISFACIBILIDAD (testigo): sustituir y dar 0{Colors.ENDC}")
    # Sistema {x-2, y-3}: el testigo x=2,y=3 lo anula; x=2,y=4 no.
    if verify_witness([x - 2, y - 3], {'x': 2, 'y': 3}, ['x', 'y']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} testigo correcto aceptado (x=2,y=3 anula {{x-2,y-3}})")
    else:
        stats.fail("testigo correcto rechazado")
    if not verify_witness([x - 2, y - 3], {'x': 2, 'y': 4}, ['x', 'y']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} testigo falso rechazado (x=2,y=4 no anula)")
    else:
        stats.fail("testigo falso aceptado")


def test_nullstellensatz_deg1(stats):
    print(f"{Colors.HEADER}[2] Nullstellensatz grado 1: Σ g_i·p_i = 1 (UNSAT){Colors.ENDC}")
    # {x, x-1}: 1·x + (-1)·(x-1) = 1. Sin solución (x=0 y x=1 a la vez).
    cof = nullstellensatz_certificate([x, x - 1], ['x'], 1)
    if cof is not None and verify_nullstellensatz([x, x - 1], cof, ['x']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {{x, x-1}} -> cofactores {cof}, re-verifica = 1")
    else:
        stats.fail(f"{{x, x-1}}: cof={cof}")
    # {x, y, x+y-1}: x=0,y=0 -> x+y-1=-1, infeasible.
    polys = [x, y, x + y - 1]
    cof = nullstellensatz_certificate(polys, ['x', 'y'], 1)
    if cof is not None and verify_nullstellensatz(polys, cof, ['x', 'y']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {{x, y, x+y-1}} -> cofactores {cof}, re-verifica = 1")
    else:
        stats.fail(f"{{x, y, x+y-1}}: cof={cof}")


def test_nullstellensatz_deg2(stats):
    print(f"{Colors.HEADER}[3] Nullstellensatz grado 2: cofactores no constantes{Colors.ENDC}")
    # {x^2, x*y-1}: x=0 -> -1, infeasible. Necesita cofactores cuadráticos.
    polys = [x**2, x * y - 1]
    cof = nullstellensatz_certificate(polys, ['x', 'y'], 2)
    if cof is not None and verify_nullstellensatz(polys, cof, ['x', 'y']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {{x², xy-1}} -> cofactores {cof}, re-verifica = 1")
    else:
        stats.fail(f"{{x², xy-1}}: cof={cof}")


def test_finder_no_miente(stats):
    print(f"{Colors.HEADER}[4] SOUNDNESS del finder: sistema SAT -> None (no inventa){Colors.ENDC}")
    # {x} tiene solución x=0; {x*y} tiene x=0. No debe existir Σ g_i·p_i=1.
    for polys, names, label in (([x], ['x'], "{x}"),
                                ([x * y], ['x', 'y'], "{x·y}"),
                                ([x - 1, y - 1], ['x', 'y'], "{x-1, y-1}")):
        cof = nullstellensatz_certificate(polys, names, 2)
        if cof is None:
            stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label} satisfacible -> None (no fabrica certificado)")
        else:
            stats.fail(f"{label}: inventó cofactores {cof} para un sistema SAT")


def test_reverify_rechaza_manipulado(stats):
    print(f"{Colors.HEADER}[5] El re-verificador RECHAZA certificados manipulados{Colors.ENDC}")
    polys = [x, x - 1]
    if not verify_nullstellensatz(polys, [1, 1], ['x']):       # 1·x + 1·(x-1) = 2x-1 ≠ 1
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} cofactores falsos [1,1] rechazados (dan 2x-1, no 1)")
    else:
        stats.fail("aceptó cofactores falsos [1,1]")
    if not verify_nullstellensatz(polys, [1], ['x']):          # longitud incorrecta
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} cofactores de longitud incorrecta rechazados")
    else:
        stats.fail("aceptó cofactores de longitud incorrecta")


def test_programa_anclado(stats):
    print(f"{Colors.HEADER}[6] Caso real: 'este programa NO puede dar esta salida'{Colors.ENDC}")
    # Programa: out = a + b con a=2, b=3 (luego out=5). Anclamos a salida ERRÓNEA out=6.
    # El sistema {a-2, b-3, a+b-out, out-6} es insatisfacible -> certificado portable.
    eqs, syms = build_system(['a - 2', 'b - 3', 'a + b - out', 'out - 6'])
    names = [s.name for s in syms]
    polys = [p.as_expr() for p in as_polynomials(eqs, syms)]
    res = certify_unreachable(polys, names, 1)
    if res is not None and res['reverify']():
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} veredicto '{res['verdict']}' con cofactores {res['certificate']}")
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} re-verificable SIN solver: a+b (a=2,b=3) no puede dar 6")
        stats.ok()
    else:
        stats.fail(f"no certificó la salida imposible: res={res}")
    # Y la salida CORRECTA out=5 SÍ es alcanzable -> no debe certificarse como imposible.
    eqs2, syms2 = build_system(['a - 2', 'b - 3', 'a + b - out', 'out - 5'])
    names2 = [s.name for s in syms2]
    polys2 = [p.as_expr() for p in as_polynomials(eqs2, syms2)]
    if certify_unreachable(polys2, names2, 1) is None:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} salida correcta out=5 NO se declara imposible (no miente)")
    else:
        stats.fail("declaró imposible una salida alcanzable (out=5)")


def main():
    print(f"{Colors.BOLD}=== CERTIFICADOS ALGEBRAICOS PORTABLES (re-verificables sin solver) ==={Colors.ENDC}")
    stats = Stats()
    test_witness_sat(stats)
    test_nullstellensatz_deg1(stats)
    test_nullstellensatz_deg2(stats)
    test_finder_no_miente(stats)
    test_reverify_rechaza_manipulado(stats)
    test_programa_anclado(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — certificados sólidos y "
              f"re-verificables con álgebra elemental, sin confiar en el solver.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
