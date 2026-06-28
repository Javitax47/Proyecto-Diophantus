#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - EXPLORADOR DE INVARIANTES (juega con el motor de descubrimiento)
================================================================================
Apunta el motor de descubrimiento a un mapa de transicion y muestra las primeras
integrales Q(T(s))=lambda*Q(s) que encuentra (sin plantilla). Util para conjeturar
invariantes de mapas enteros / recurrencias.

CLI:
  # mapa afin: matriz A (filas separadas por ';') y vector d
  python src/analysis/explore_invariants.py --affine "3,4;2,3" --d "0,0" --vars x,y --deg 2
  # mapa por expresiones (no lineal), una por variable de estado
  python src/analysis/explore_invariants.py --exprs "x; y; 3*x*y - z" --vars x,y,z --deg 3

Sin argumentos, ejecuta una bateria de demostracion (Pell, Fibonacci, cat map,
Markov/Vieta, cluster).
"""

import argparse
import sys

import sympy

from src.analysis.discovery_engine import (
    find_conserved_quantities, affine_transition_exprs, verify_conserved,
)


def report(name, exprs, vnames, deg):
    print(f"\n=== {name} ===  T = {exprs}")
    res = find_conserved_quantities(exprs, vnames, deg)
    syms = sympy.symbols(vnames)
    nontrivial = [(l, Q) for l, Q in res
                  if sympy.Poly(Q, *syms).total_degree() > 0]
    if not nontrivial:
        print("   (sin primeras integrales no triviales de grado <=", deg, ")")
    for lam, Q in nontrivial:
        ok = verify_conserved(Q, exprs, vnames, lam)
        tag = "✓" if ok else "✗(no verifica)"
        print(f"   λ={lam:>2}:  Q = {sympy.factor(Q)}   [{tag}]")


def _demo():
    x, y, z = sympy.symbols('x y z')
    report("Pell D=2", affine_transition_exprs([[3, 4], [2, 3]], [0, 0], ['x', 'y']), ['x', 'y'], 2)
    report("Fibonacci", affine_transition_exprs([[0, 1], [1, 1]], [0, 0], ['a', 'b']), ['a', 'b'], 2)
    report("Cat map de Arnold", affine_transition_exprs([[2, 1], [1, 1]], [0, 0], ['x', 'y']), ['x', 'y'], 2)
    report("Cluster k=3", affine_transition_exprs([[0, 1], [-1, 3]], [0, 0], ['x', 'y']), ['x', 'y'], 2)
    report("Markov Vieta (z->3xy-z)", [x, y, 3 * x * y - z], ['x', 'y', 'z'], 3)


def main():
    ap = argparse.ArgumentParser(description="Explorador de invariantes (motor de descubrimiento).")
    ap.add_argument("--affine", help="Matriz A, filas con ';' y entradas con ','")
    ap.add_argument("--d", help="Vector d con ','", default=None)
    ap.add_argument("--exprs", help="Expresiones de transicion separadas por ';'")
    ap.add_argument("--vars", help="Variables de estado separadas por ','")
    ap.add_argument("--deg", type=int, default=2)
    args = ap.parse_args()

    if not args.vars:
        _demo()
        return
    vnames = [v.strip() for v in args.vars.split(',')]
    if args.affine:
        A = [[int(e) for e in row.split(',')] for row in args.affine.split(';')]
        d = [int(e) for e in (args.d or ",".join(["0"] * len(vnames))).split(',')]
        exprs = affine_transition_exprs(A, d, vnames)
        report("mapa afin", exprs, vnames, args.deg)
    elif args.exprs:
        syms = {v: sympy.Symbol(v) for v in vnames}
        exprs = [sympy.sympify(e.strip(), locals=syms) for e in args.exprs.split(';')]
        report("mapa por expresiones", exprs, vnames, args.deg)
    else:
        _demo()


if __name__ == "__main__":
    main()
