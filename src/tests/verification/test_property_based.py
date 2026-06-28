#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - PROPERTY-BASED TESTING DEL MODO PURE (Fase 0, item 2)
================================================================================
Generaliza `test_pure_soundness` de operadores sueltos a EXPRESIONES COMPUESTAS
aleatorias (aritmética anidada con comparaciones y módulo). Para cada expresión
y cada asignación de entrada comprueba con Z3 la propiedad central:

    el sistema PURE tiene solución entera  <=>  la salida coincide con la
    semántica de referencia (Python) de la expresión.

Es decir: aritmetización fiel para programas pequeños, no solo para operadores
aislados. Cubre el "property-based testing con programas aleatorios pequeños"
que pide el informe (§7, Fase 0, item 2).

Uso:  python src/tests/verification/test_property_based.py [n_exprs]
Requisitos: z3-solver.
"""

import os
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from z3 import sat  # noqa: F401  (comprueba disponibilidad)
except ImportError:
    print("[SKIP] z3-solver no está instalado.")
    sys.exit(0)

from src.tests.verification._soundness_helpers import pure_system_for, forces_value


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


INPUTS = ['A', 'B', 'C']
ARITH = ['+', '-', '*']
COMPARE = ['<', '>', '<=', '>=', '==', '!=']


def random_expr(rng, depth):
    """Genera una tupla-expresión en el formato del converter. Mantiene los
    operandos dentro de lo que el encoding garantiza (módulo por constante
    positiva; sin división para no fijar el signo del divisor)."""
    if depth <= 0 or rng.random() < 0.3:
        if rng.random() < 0.6:
            return rng.choice(INPUTS)
        return str(rng.randint(-3, 3))
    kind = rng.random()
    if kind < 0.55:  # aritmética
        op = rng.choice(ARITH)
        return (op, random_expr(rng, depth - 1), random_expr(rng, depth - 1))
    elif kind < 0.85:  # comparación (devuelve 0/1, componible en aritmética)
        op = rng.choice(COMPARE)
        return (op, random_expr(rng, depth - 1), random_expr(rng, depth - 1))
    else:  # módulo por constante positiva pequeña
        k = rng.randint(2, 5)
        return ('%', random_expr(rng, depth - 1), str(k))


def eval_expr(expr, env):
    """Semántica de referencia (Python), idéntica al encoding: comparaciones ->
    0/1; `%` por constante positiva = resto euclídeo (Python lo cumple)."""
    if isinstance(expr, str):
        return env[expr] if expr in env else int(expr)
    op = expr[0]
    a = eval_expr(expr[1], env)
    b = eval_expr(expr[2], env)
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op == '%': return a % b
    if op == '<': return int(a < b)
    if op == '>': return int(a > b)
    if op == '<=': return int(a <= b)
    if op == '>=': return int(a >= b)
    if op == '==': return int(a == b)
    if op == '!=': return int(a != b)
    raise ValueError(op)


def main():
    n_exprs = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    print(f"{Colors.BOLD}=== PROPERTY-BASED: {n_exprs} expresiones compuestas aleatorias ==={Colors.ENDC}")
    rng = random.Random(20260613)
    passed = failed = 0
    for i in range(n_exprs):
        expr = random_expr(rng, depth=rng.randint(2, 3))
        try:
            system = pure_system_for(expr)
        except Exception as e:
            print(f"  {Colors.FAIL}✗ generación falló{Colors.ENDC} {expr}: {type(e).__name__}: {e}")
            failed += 1
            continue
        ok_all = True
        for _ in range(4):
            env = {v: rng.randint(-6, 6) for v in INPUTS}
            expected = eval_expr(expr, env)
            if not forces_value(system, dict(env), 'out', expected):
                print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {expr} con {env} -> esperado {expected}")
                ok_all = False
                break
        if ok_all:
            passed += 1
        else:
            failed += 1

    total = passed + failed
    print()
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {passed}/{total} expresiones OK — la "
              f"aritmetización es fiel también en composición.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {failed}/{total} expresiones FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
