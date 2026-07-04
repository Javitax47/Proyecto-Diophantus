"""
================================================================================
   DIOPHANTUS - REPRESENTACIÓN SYMPY DEL SISTEMA DIOFÁNTICO
================================================================================
Convierte el sistema de ecuaciones (hasta ahora manipulado como *strings*, la
"fuente de fragilidad nº1") en objetos SymPy
reales (`Eq`, `Poly`). Esto permite tratar el sistema PURE como lo que el
teorema MRDP afirma que es —un polinomio entero— y manipularlo con el álgebra
de SymPy en lugar de con sustituciones de subcadenas frágiles.

Diseño:
  * El parseo usa el lector de expresiones de SymPy (`sympify`), no regex sobre
    el resultado: las prioridades de operadores y el anidamiento los resuelve
    SymPy, no nosotros.
  * Las únicas transformaciones de *string* son las imprescindibles para que el
    texto sea una expresión Python válida (nombres de variable): `x[t+1]` ->
    `x_next`, y las llamadas residuales `P_f(args)` -> un símbolo atómico
    `CALL_f__args` (representan un sub-cómputo; SymPy las trata como una
    variable más, preservando la dependencia para Gröbner).
  * `^` se mapea a `**` por compatibilidad con artefactos antiguos; el converter
    actual ya no emite `^` en modo PURE (los bit a bit se aritmetizan).
"""

import re
import sys
import sympy
from sympy import Eq, Poly, sympify

# Los sistemas de programas con recursion profunda (p. ej. collatz tras la
# fusion de tail-calls) producen expresiones muy anidadas; sympify recorre el
# arbol recursivamente, asi que aseguramos un limite holgado.
if sys.getrecursionlimit() < 100000:
    sys.setrecursionlimit(100000)


def _replace_call(match):
    """`P_f(a, b)` -> símbolo atómico `CALL_f__a__b` (sub-cómputo opaco)."""
    func_name = match.group(1)
    args = match.group(2)
    clean = (args.replace(", ", "__").replace(",", "__").replace(" ", "")
             .replace("+", "_plus_").replace("-", "_minus_").replace("*", "_mul_")
             .replace("(", "_").replace(")", "_"))
    return f"CALL_{func_name}__{clean}"


def equation_to_expr_str(eq):
    """Convierte una ecuación `LHS = RHS` (o `LHS = 0`) en el string de una
    expresión Python que vale 0 sobre las soluciones: `(LHS) - (RHS)`."""
    if " = " in eq:
        lhs, rhs = eq.split(" = ", 1)
        body = f"({lhs}) - ({rhs})"
    else:
        body = eq
    body = body.replace("[t+1]", "_next").replace("[", "_").replace("]", "")
    body = body.replace("^", "**")
    body = re.sub(r'P_(\w+)\((.*?)\)', _replace_call, body)
    return body


def build_system(equations):
    """Parsea una lista de ecuaciones-string en objetos SymPy reales.

    Devuelve `(eqs, symbols)` donde `eqs` es una lista de `sympy.Eq(expr, 0)`
    y `symbols` el conjunto ordenado de `Symbol` que aparecen. Lanza
    `SympifyError`/`SyntaxError` si alguna ecuación no es parseable — a
    diferencia del manejo por strings, aquí un sistema mal formado falla pronto
    y ruidosamente en vez de propagar texto corrupto."""
    eqs = []
    symbols = set()
    for raw in equations:
        if not raw.strip():
            continue
        expr = sympify(equation_to_expr_str(raw))
        eq = Eq(expr, 0)
        # `Eq(expr, 0)` puede colapsar a un booleano cuando `expr` es constante:
        #   * tautología (`0 = 0`, p. ej. al booleanizar un operando constante):
        #     es vacua, no añade restricción -> se descarta.
        #   * contradicción (`c = 0` con c != 0): el sistema es insatisfacible;
        #     se conserva como `Eq(1, 0)` para preservar esa imposibilidad.
        if eq is sympy.true:
            continue
        if eq is sympy.false:
            # `Eq(const, 0)` con const != 0 colapsa a BooleanFalse; lo
            # reconstruimos sin evaluar para conservar un objeto Eq (con .lhs)
            # que representa la imposibilidad (lhs constante != 0).
            eqs.append(Eq(expr, 0, evaluate=False))
            continue
        eqs.append(eq)
        symbols |= expr.free_symbols
    return eqs, sorted(symbols, key=lambda s: s.name)


def as_polynomials(eqs, gens=None):
    """Devuelve la lista de `sympy.Poly` de los lados izquierdos. Lanza
    `PolynomialError`/`GeneratorsNeeded` si alguna ecuación NO es polinómica.
    Es la comprobación operativa del objetivo de aritmetización fiel: que el
    sistema sea un polinomio entero manipulable por SymPy."""
    if gens is None:
        gens = sorted({s for e in eqs for s in e.lhs.free_symbols},
                      key=lambda s: s.name)
    if not gens:
        return []
    return [Poly(e.lhs, *gens) for e in eqs]


def is_polynomial_system(eqs):
    """True si toda ecuacion es polinomica en sus variables libres. Usa
    `expr.is_polynomial()` (barato), apto para sistemas grandes donde construir
    los `Poly` multivariados explicitos (as_polynomials) seria intratable
    (p. ej. collatz: 1236 ecuaciones, 3709 variables)."""
    return all(bool(e.lhs.is_polynomial()) for e in eqs)


def is_satisfied_by(eqs, assignment):
    """True si la asignación (dict Symbol/str -> int) anula todas las
    ecuaciones. Útil para validar testigos hallados por la VM/miner o por Z3."""
    subs = {(sympy.Symbol(k) if isinstance(k, str) else k): v
            for k, v in assignment.items()}
    return all(sympy.simplify(e.lhs.subs(subs)) == 0 for e in eqs)
