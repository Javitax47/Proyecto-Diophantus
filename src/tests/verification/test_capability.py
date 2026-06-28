#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - UMBRAL DE CAPACIDAD DEL MOTOR DE DESCUBRIMIENTO (Fase 4)
================================================================================
Mapea, como regresion, DONDE encuentra estructura el motor y donde para —el
"umbral de capacidad"— con honestidad:

  (1) INTEGRABLES (con invariante): lo encuentra y lo VERIFICA simbolicamente,
      en mapas lineales y NO lineales, en 2-4 variables (Pell, cat map, Markov 3D
      y Markov-Hurwitz 4D).
  (2) FRONTERA (no integrables/caoticos): NO inventa invariantes
      (det != ±1, escala diagonal, Henon-like) -> ahi para la herramienta.
  (3) AUDIT: el invariante esencial de Markov (3D y 4D) esta realmente conservado.
  (4) reduce_powers limpia potencias puras sin destruir invariantes distintos.

Conclusion (documentada): el motor es un SINTETIZADOR DE INVARIANTES / detector
de integrabilidad acotado por el coste combinatorio C(n+grado, grado). No produce
teoremas nuevos: redescubre estructura algebraica conocida y certifica casos
acotados.

Uso:  python src/tests/verification/test_capability.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.discovery_engine import (
    find_conserved_quantities, verify_conserved, reduce_powers,
)

x, y, z, w = sympy.symbols('x y z w')


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def _nontrivial(res, vnames):
    syms = sympy.symbols(vnames)
    return [(l, Q) for l, Q in res if sympy.Poly(Q, *syms).total_degree() > 0]


def test_integrable(stats):
    print(f"{Colors.HEADER}[1] Integrables: encuentra invariante (lineal y no lineal, 2-4 vars){Colors.ENDC}")
    cases = [
        ("Pell", [3 * x + 4 * y, 2 * x + 3 * y], ['x', 'y'], 2),
        ("cat map", [2 * x + y, x + y], ['x', 'y'], 2),
        ("Markov 3D", [x, y, 3 * x * y - z], ['x', 'y', 'z'], 3),
        ("Markov-Hurwitz 4D", [x, y, z, x * y * z - w], ['x', 'y', 'z', 'w'], 4),
    ]
    for name, T, vn, deg in cases:
        nz = _nontrivial(find_conserved_quantities(T, vn, deg), vn)
        ok = nz and all(verify_conserved(Q, T, vn, l) for l, Q in nz)
        stats.ok() if ok else stats.fail(f"{name}: no encontró/verificó ({nz})")
        if ok:
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {name}: {len(nz)} invariante(s) verificado(s)")


def test_boundary(stats):
    print(f"{Colors.HEADER}[2] Frontera: caóticos/no integrables -> NADA (no inventa){Colors.ENDC}")
    cases = [
        ("det=-2 [[1,3],[1,1]]", [x + 3 * y, x + y], ['x', 'y']),
        ("escala [[2,0],[0,3]]", [2 * x, 3 * y], ['x', 'y']),
        ("Hénon-like", [y, x + 1 - 2 * y * y], ['x', 'y']),
        ("det=2 [[3,1],[1,1]]", [3 * x + y, x + y], ['x', 'y']),
    ]
    for name, T, vn in cases:
        nz = _nontrivial(find_conserved_quantities(T, vn, 4), vn)
        stats.ok() if not nz else stats.fail(f"{name}: inventó {[(l, str(Q)) for l, Q in nz]}")
        if not nz:
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {name}: 0 invariantes (correcto: ahí para)")


def test_audit_markov(stats):
    print(f"{Colors.HEADER}[3] Audit: invariante esencial de Markov realmente conservado{Colors.ENDC}")
    a = verify_conserved(x**2 + y**2 + z**2 - 3 * x * y * z, [x, y, 3 * x * y - z], ['x', 'y', 'z'], 1)
    b = verify_conserved(x**2 + y**2 + z**2 + w**2 - x * y * z * w, [x, y, z, x * y * z - w], ['x', 'y', 'z', 'w'], 1)
    stats.ok() if (a and b) else stats.fail(f"Markov esencial: 3D={a} 4D={b}")
    if a and b:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Markov 3D y 4D: invariante esencial conservado (verificado)")


def test_reduce_powers(stats):
    print(f"{Colors.HEADER}[4] reduce_powers: quita potencias puras, conserva invariantes distintos{Colors.ENDC}")
    # Pell grado 8: muchas potencias de x^2-2y^2 -> debe quedar 1
    res = find_conserved_quantities([3 * x + 4 * y, 2 * x + 3 * y], ['x', 'y'], 8)
    ess = reduce_powers([Q for l, Q in res], ['x', 'y'])
    cond1 = len(ess) == 1 and not sympy.cancel(ess[0] / (x**2 - 2 * y**2)).free_symbols
    # invariantes DISTINTOS no deben fusionarse
    ess2 = reduce_powers([x**2 - 2 * y**2, x * y, x + y], ['x', 'y'])
    cond2 = len(ess2) == 3
    stats.ok() if (cond1 and cond2) else stats.fail(f"reduce_powers: pell->{ess} distintos->{ess2}")
    if cond1 and cond2:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Pell deg8 -> 1 esencial; invariantes distintos preservados")


def main():
    print(f"{Colors.BOLD}=== UMBRAL DE CAPACIDAD DEL MOTOR DE DESCUBRIMIENTO ==={Colors.ENDC}")
    stats = Stats()
    test_integrable(stats)
    test_boundary(stats)
    test_audit_markov(stats)
    test_reduce_powers(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — umbral confirmado: encuentra "
              f"invariantes de mapas integrables, nada de los caóticos.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
