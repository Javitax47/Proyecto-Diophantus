"""
Utilidades compartidas para los tests de soundness basados en Z3.

Centraliza:
  * `LinearizedConverter`: el `PolynomialConverter` con el gadget de Lagrange
    (suma de cuatro cuadrados que codifica `>= 0`) sustituido por una variable
    `nn_*` que el test restringe a `>= 0`. La equivalencia es el teorema de
    Lagrange; linealizar deja intacta la LÓGICA del encoding y vuelve la
    verificación con Z3 decidible y determinista (su solver NO lineal responde
    `unknown` justo en los números que exigen los cuatro cuadrados, p. ej. 7).
  * `pure_system_for`: construye el sistema PURE de una expresión.
  * `load_into_z3` / `forces_value`: cargan el sistema en Z3 y comprueban la
    propiedad "solución entera <=> traza válida".
"""

import os
import re
import sys
import contextlib

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from src.compiler.polynomial_converter import PolynomialConverter

_NN_PREFIX = "nn_"


class LinearizedConverter(PolynomialConverter):
    """Converter de producción salvo que la no-negatividad se codifica con una
    variable fresca `nn_*` (que el cargador Z3 restringe a `>= 0`) en lugar de
    la suma de cuatro cuadrados. Equisatisfacible por el teorema de Lagrange."""

    def _sum_of_four_squares(self):
        v = f"{_NN_PREFIX}{self.existential_vars_count}"
        self.existential_vars_count += 1
        return v


def pure_system_for(expr_tuple, target="out", bit_width=8):
    """Devuelve el sistema PURE (lista de ecuaciones-string) de `target = expr`.
    `expr_tuple` es una tupla en el formato del converter, o `(op, a, b)`."""
    pc = LinearizedConverter({target: expr_tuple}, {}, [], {}, bit_width=bit_width)
    with contextlib.redirect_stdout(open(os.devnull, "w")):
        system, _ = pc.convert(mode="PURE")
    return system


def load_into_z3(equations, fixed):
    """Carga ecuaciones `LHS = 0` en un Solver Z3. Las variables `nn_*` se
    restringen a `>= 0`. `fixed` fija entradas concretas. Devuelve (solver, ctx)."""
    from z3 import Int, Solver
    names = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', " ".join(equations)))
    ctx = {n: Int(n) for n in names}
    s = Solver()
    s.set("timeout", 10000)
    for eq in equations:
        lhs = eq.split("= 0")[0]
        s.add(eval(lhs, {"__builtins__": {}}, ctx) == 0)
    for name, var in ctx.items():
        if name.startswith(_NN_PREFIX):
            s.add(var >= 0)
    for k, v in fixed.items():
        if k in ctx:  # una entrada puede no aparecer en el sistema (queda libre)
            s.add(ctx[k] == v)
    return s, ctx


def forces_value(equations, fixed, out_name, expected):
    """True sii el sistema (a) es satisfacible con out==expected y (b) es
    INSATISFACIBLE con out!=expected. Es la propiedad solución<=>traza."""
    from z3 import sat, unsat
    s, ctx = load_into_z3(equations, fixed)
    out = ctx[out_name]
    s.push(); s.add(out == expected); sat_ok = (s.check() == sat); s.pop()
    s.push(); s.add(out != expected); unsat_bad = (s.check() == unsat); s.pop()
    return sat_ok and unsat_bad
