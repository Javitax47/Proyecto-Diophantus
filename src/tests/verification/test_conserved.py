#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE DESCUBRIMIENTO DE CANTIDADES CONSERVADAS (Fase 4)
================================================================================
El motor descubre PRIMERAS INTEGRALES Q(T(s))=lambda*Q(s) del mapa de transicion
(no de una orbita) -> valen para CUALQUIER semilla. Comprueba que redescubre,
sin plantilla, invariantes clasicos de teoria de numeros, sobre mapas LINEALES y
NO LINEALES, y que verifica simbolicamente cada uno; y que NO inventa invariantes
donde no los hay.

Uso:  python src/tests/verification/test_conserved.py
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
    find_conserved_quantities, affine_transition_exprs, verify_conserved,
)

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


def _equiv(P, Q):
    """P y Q definen la misma identidad (multiplo escalar no nulo)."""
    if Q == 0:
        return P == 0
    r = sympy.cancel(P / Q)
    return (not r.free_symbols) and r != 0


def check(stats, label, transition, vnames, deg, expected_Q, expected_lam):
    res = find_conserved_quantities(transition, vnames, deg)
    # ¿alguna conservada descubierta es equivalente a la esperada y se verifica?
    hit = None
    for lam, Q in res:
        if lam == expected_lam and _equiv(Q, expected_Q) and verify_conserved(Q, transition, vnames, lam):
            hit = (lam, Q); break
    if hit:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label}: descubierto Q={sympy.factor(hit[1])} (λ={hit[0]}), verificado")
    else:
        stats.fail(f"{label}: no descubrio {expected_Q} (λ={expected_lam}); halladas={[(l,str(q)) for l,q in res]}")


def main():
    print(f"{Colors.BOLD}=== TEST DE CANTIDADES CONSERVADAS DESCUBIERTAS ==={Colors.ENDC}")
    stats = Stats()

    print(f"{Colors.HEADER}[1] Mapas lineales (formas cuadraticas clasicas){Colors.ENDC}")
    check(stats, "Pell D=2 (x²-2y²)", affine_transition_exprs([[3, 4], [2, 3]], [0, 0], ['x', 'y']),
          ['x', 'y'], 2, x**2 - 2 * y**2, 1)
    check(stats, "Pell D=3 (x²-3y²)", affine_transition_exprs([[2, 3], [1, 2]], [0, 0], ['x', 'y']),
          ['x', 'y'], 2, x**2 - 3 * y**2, 1)
    check(stats, "Fibonacci (b²-ab-a², λ=-1)", affine_transition_exprs([[0, 1], [1, 1]], [0, 0], ['a', 'b']),
          ['a', 'b'], 2, sympy.symbols('b')**2 - sympy.symbols('a') * sympy.symbols('b') - sympy.symbols('a')**2, -1)
    check(stats, "Cat map de Arnold (x²-xy-y²)", affine_transition_exprs([[2, 1], [1, 1]], [0, 0], ['x', 'y']),
          ['x', 'y'], 2, x**2 - x * y - y**2, 1)
    check(stats, "Cluster k=3 (x²-3xy+y²)", affine_transition_exprs([[0, 1], [-1, 3]], [0, 0], ['x', 'y']),
          ['x', 'y'], 2, x**2 - 3 * x * y + y**2, 1)

    print(f"{Colors.HEADER}[2] Mapas NO LINEALES (teoría de números){Colors.ENDC}")
    # Vieta-jumping de Markov/Hurwitz: (x,y,z)->(x,y,xy-z) conserva z(xy-z) (grado 3, no lineal)
    check(stats, "Hurwitz Vieta z(xy-z)", [x, y, x * y - z], ['x', 'y', 'z'], 3, z * (x * y - z), 1)
    # Markov clasico: (x,y,z)->(x,y,3xy-z) conserva z(3xy-z)
    check(stats, "Markov Vieta z(3xy-z)", [x, y, 3 * x * y - z], ['x', 'y', 'z'], 3, z * (3 * x * y - z), 1)

    print(f"{Colors.HEADER}[3] Negativo: sin invariante de bajo grado{Colors.ENDC}")
    res = find_conserved_quantities([2 * x + 1], ['x'], 3)   # x->2x+1
    nontrivial = [Q for lam, Q in res if sympy.Poly(Q, x).total_degree() > 0]
    if not nontrivial:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} x->2x+1: ninguna conservada no trivial (correcto)")
    else:
        stats.fail(f"x->2x+1: inventó {nontrivial}")

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el motor redescubre primeras integrales "
              f"clásicas (lineales y no lineales), verificadas simbólicamente.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
