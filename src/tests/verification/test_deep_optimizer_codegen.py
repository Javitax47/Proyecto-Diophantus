#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL GENERADOR DE ENERGÍA DEL DEEP OPTIMIZER
================================================================================
Valida `deep_optimizer.build_energy_terms`, que reemplazó la generación de la
fórmula de energía basada en strings (hack `__AUX__`) por sustitución SymPy
estructural. Comprueba:

  (1) EQUIVALENCIA: la fórmula G(inputs, dioph_x) generada (energía = suma de
      cuadrados) evalúa idéntico a la verdad de SymPy —Σ eq(asignación)²— sobre
      asignaciones enteras aleatorias. Es decir, la migración a SymPy conserva
      EXACTAMENTE la semántica de la energía.
  (2) ROBUSTEZ FRENTE A COLISIONES: con nombres de variable solapados (`x`,
      `x1`, `x10`) —el caso que motivaba el viejo hack— el mapeo a dioph_x[i]
      sigue siendo correcto, porque SymPy sustituye por símbolo, no por subcadena.

Uso:  python src/tests/verification/test_deep_optimizer_codegen.py
Requisitos: sympy.
"""

import os
import sys
import random

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import sympy
    from sympy import Symbol
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.deep_optimizer import build_energy_terms


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


def make_energy_callable(py_terms, input_names):
    """Compila los términos en una función G(inputs..., dioph_x) -> energía."""
    args_def = ", ".join(input_names + ["dioph_x"])
    src = f"def _G({args_def}):\n    return {' + '.join(py_terms) or '0'}\n"
    ns = {}
    exec(src, ns)
    return ns["_G"]


def ground_truth_energy(final_eqs, aux_vars, assignment):
    """Verdad: Σ eq(asignación)² evaluado directamente con SymPy."""
    subs = {Symbol(k): v for k, v in assignment.items()}
    return sum(int(eq.subs(subs)) ** 2 for eq in final_eqs)


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def check_system(stats, label, final_eqs, aux_vars, input_names, seed):
    py_terms, _ = build_energy_terms(final_eqs, aux_vars, [Symbol(n) for n in input_names])
    G = make_energy_callable(py_terms, input_names)
    rng = random.Random(seed)
    for _ in range(40):
        assignment = {v: rng.randint(-7, 7) for v in (aux_vars + input_names)}
        # energía generada: inputs por nombre + vector dioph_x indexado por aux_vars
        kwargs = {n: assignment[n] for n in input_names}
        dioph_x = [assignment[v] for v in aux_vars]
        got = G(dioph_x=dioph_x, **kwargs)
        expected = ground_truth_energy(final_eqs, aux_vars, assignment)
        if got != expected:
            stats.fail(f"{label}: G={got} != verdad={expected} en {assignment}")
            return
    stats.ok()


def test_equivalence(stats):
    print(f"{Colors.HEADER}[1] La energía generada == Σ eq² (verdad SymPy){Colors.ENDC}")
    x, y, z, n = sympy.symbols('x y z n')
    systems = [
        ("lineal+producto", [x * y - n, x + y - 2], ['x', 'y'], ['n']),
        ("cuadrático", [x ** 2 - n, x * y - z, y + z - 1], ['x', 'y', 'z'], ['n']),
        ("sin inputs", [x * y - 6, x - y], ['x', 'y'], []),
    ]
    for i, (label, eqs, aux, inp) in enumerate(systems):
        check_system(stats, label, eqs, aux, inp, seed=100 + i)


def test_name_collisions(stats):
    print(f"{Colors.HEADER}[2] Robustez con nombres solapados (x, x1, x10){Colors.ENDC}")
    x, x1, x10, n = sympy.symbols('x x1 x10 n')
    # Sistema donde 'x' es subcadena de 'x1' y 'x10': el viejo replace de strings
    # era propenso a corromper esto; la sustitución SymPy es inmune.
    eqs = [x * x1 - x10, x + x1 + x10 - n, x10 - 2 * x]
    aux = ['x', 'x1', 'x10']  # orden -> dioph_x[0], [1], [2]
    check_system(stats, "colisión x/x1/x10", eqs, aux, ['n'], seed=777)


def main():
    print(f"{Colors.BOLD}=== TEST DEL GENERADOR DE ENERGÍA (deep_optimizer) ==={Colors.ENDC}")
    stats = Stats()
    test_equivalence(stats)
    test_name_collisions(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} OK — la generación "
              f"por sustitución SymPy es exacta y robusta a colisiones de nombres.{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
