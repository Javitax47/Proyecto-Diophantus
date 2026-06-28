#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE LA REPRESENTACIÓN SYMPY (Fase 0, item 3 del informe)
================================================================================
Valida `src/analysis/sympy_system.py`, que migra el sistema de ecuaciones de
strings frágiles a objetos SymPy reales. Comprueba:

  (1) POLINOMICIDAD: el sistema PURE generado para los operadores de §4.1 es un
      polinomio entero genuino que SymPy puede construir como `Poly`. Es el
      criterio de éxito de la Fase 1 ("un P(x)=0 real que SymPy manipula").
  (2) EQUIVALENCIA SEMÁNTICA: cada ecuación, leída por SymPy, evalúa idéntico
      al `eval` del string original sobre asignaciones enteras aleatorias — la
      migración no cambia la semántica (rigor de no-regresión).

Uso:  python src/tests/verification/test_sympy_system.py
Requisitos: sympy.
"""

import os
import re
import sys
import random
import contextlib

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado (pip install sympy).")
    sys.exit(0)

from src.compiler.polynomial_converter import PolynomialConverter
from src.analysis import sympy_system


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


def gen_pure(op, a='A', b='B', bit_width=8):
    pc = PolynomialConverter({'out': (op, a, b)}, {}, [], {}, bit_width=bit_width)
    with contextlib.redirect_stdout(open(os.devnull, "w")):
        system, _ = pc.convert(mode="PURE")
    return system


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_polynomiality(stats):
    print(f"{Colors.HEADER}[1] El sistema PURE es un polinomio entero (Poly de SymPy){Colors.ENDC}")
    cases = ['/', '%', '<', '>', '<=', '>=', '==', '!=', '&', '|', '^']
    for op in cases:
        eqs_str = gen_pure(op, bit_width=6)
        try:
            eqs, syms = sympy_system.build_system(eqs_str)
            polys = sympy_system.as_polynomials(eqs, syms)
        except Exception as e:
            stats.fail(f"op '{op}': no se pudo construir Poly: {type(e).__name__}: {e}")
            continue
        if len(polys) == len(eqs) and all(isinstance(p, sympy.Poly) for p in polys):
            stats.ok()
        else:
            stats.fail(f"op '{op}': alguna ecuación no resultó polinómica")


def test_semantic_equivalence(stats):
    print(f"{Colors.HEADER}[2] La lectura SymPy es equivalente al eval del string{Colors.ENDC}")
    cases = ['/', '%', '<', '>', '<=', '>=', '==', '!=', '&', '|', '^', '<<', '>>']
    rng = random.Random(20260613)
    for op in cases:
        b_operand = '2' if op in ('<<', '>>') else 'B'
        eqs_str = gen_pure(op, b=b_operand, bit_width=6)
        for eq in eqs_str:
            expr_str = sympy_system.equation_to_expr_str(eq)
            names = sorted(set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', expr_str)))
            sym_expr = sympy.sympify(expr_str)
            for _ in range(5):
                assignment = {n: rng.randint(-9, 9) for n in names}
                # valor vía SymPy
                sym_val = int(sym_expr.subs({sympy.Symbol(n): v
                                             for n, v in assignment.items()}))
                # valor vía eval directo del mismo string Python
                py_val = int(eval(expr_str, {"__builtins__": {}}, dict(assignment)))
                if sym_val != py_val:
                    stats.fail(f"op '{op}': '{expr_str[:60]}...' SymPy={sym_val} eval={py_val}")
                    break
            else:
                stats.ok()


def test_witness_check(stats):
    print(f"{Colors.HEADER}[3] is_satisfied_by reconoce un testigo válido y rechaza uno falso{Colors.ENDC}")
    # Sistema simple: out = A % 5, con A = 12 -> out = 2, cociente e_0 = 2, resto en [0,4].
    eqs_str = gen_pure('%', a='12', b='5')
    eqs, _ = sympy_system.build_system(eqs_str)
    # Testigo correcto: resto 2 (out), cociente 2 (e_0), holguras de 4 cuadrados:
    # 2 = 1+1+0+0 ; (5-1-2)=2 = 1+1+0+0
    good = {'out': 2, 'e_0': 2,
            'e_1': 1, 'e_2': 1, 'e_3': 0, 'e_4': 0,
            'e_5': 1, 'e_6': 1, 'e_7': 0, 'e_8': 0}
    bad = dict(good); bad['out'] = 3  # resto incorrecto
    if sympy_system.is_satisfied_by(eqs, good):
        stats.ok()
    else:
        stats.fail("no reconoció el testigo válido (out=2 para 12%5)")
    if not sympy_system.is_satisfied_by(eqs, bad):
        stats.ok()
    else:
        stats.fail("aceptó un testigo falso (out=3 para 12%5)")


def test_constant_equations(stats):
    print(f"{Colors.HEADER}[4] Ecuaciones constantes: tautología descartada, contradicción conservada{Colors.ENDC}")
    # Mezcla de: tautología (0=0, p. ej. al booleanizar un 0), ecuación normal,
    # y contradicción constante (5=0). build_system debe descartar la tautología
    # y conservar la contradicción como sistema insatisfacible.
    eqs, _ = sympy_system.build_system([
        "0*(1 - 0) = 0",   # tautología -> se descarta
        "x - (3) = 0",     # normal
    ])
    if len(eqs) == 1 and all(isinstance(e, sympy.Eq) for e in eqs):
        stats.ok()
    else:
        stats.fail(f"tautología no descartada / objeto no-Eq: {eqs}")

    eqs2, _ = sympy_system.build_system(["5 = 0", "x - 1 = 0"])
    # La contradicción hace el sistema insatisfacible para cualquier x.
    if not sympy_system.is_satisfied_by(eqs2, {'x': 1}):
        stats.ok()
    else:
        stats.fail("contradicción constante (5=0) no volvió insatisfacible el sistema")


def main():
    print(f"{Colors.BOLD}=== TEST DE LA REPRESENTACIÓN SYMPY DEL SISTEMA ==={Colors.ENDC}")
    stats = Stats()
    test_polynomiality(stats)
    test_semantic_equivalence(stats)
    test_witness_check(stats)
    test_constant_equations(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — "
              f"el sistema vive como objeto SymPy polinómico y semánticamente "
              f"equivalente.{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
