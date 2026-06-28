#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - INSPECTOR / DEBUG DEL SISTEMA DIOFÁNTICO
================================================================================
Herramienta de depuración: dado un fichero de sistema PURE
(`output/<nombre>_pure_poly_system.txt`), lo lee como objetos SymPy reales (vía
`sympy_system`) y reporta:

  * nº de ecuaciones y de variables,
  * categorías de variable (entradas/estado, auxiliares e_*, holguras de 4
    cuadrados, sub-cómputos CALL_*),
  * grado total del sistema y grado por ecuación (máximo),
  * ANOMALÍAS: ecuaciones que no parsean o que no son polinómicas — el tipo de
    fallo que antes pasaba inadvertido al manipular strings.

Uso:
  python src/analysis/inspect_system.py output/collatz_pure_poly_system.txt
  python src/analysis/inspect_system.py output/collatz_pure_poly_system.txt --eqs 20
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    import sympy
except ImportError:
    print("[ERROR] sympy no está instalado (pip install sympy).")
    sys.exit(1)

from src.analysis import sympy_system


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


def categorize(symbols):
    cats = {'auxiliares (e_*)': [], 'holguras (nn_*)': [], 'sub-cómputos (CALL_*)': [],
            'estado (_next)': [], 'entradas/otros': []}
    for s in symbols:
        n = s.name
        if n.startswith('e_'):
            cats['auxiliares (e_*)'].append(n)
        elif n.startswith('nn_'):
            cats['holguras (nn_*)'].append(n)
        elif n.startswith('CALL_'):
            cats['sub-cómputos (CALL_*)'].append(n)
        elif n.endswith('_next'):
            cats['estado (_next)'].append(n)
        else:
            cats['entradas/otros'].append(n)
    return cats


def main():
    ap = argparse.ArgumentParser(description="Inspector de sistemas diofánticos PURE.")
    ap.add_argument("file", help="Ruta a *_pure_poly_system.txt")
    ap.add_argument("--eqs", type=int, default=0, help="Mostrar las primeras N ecuaciones")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        print(f"{Colors.FAIL}[ERROR] No existe: {args.file}{Colors.ENDC}")
        sys.exit(1)

    with open(args.file, encoding="utf-8") as f:
        raw = [l for l in f.read().splitlines() if l.strip()]

    print(f"{Colors.BOLD}{Colors.HEADER}=== INSPECTOR: {os.path.basename(args.file)} ==={Colors.ENDC}")
    print(f"Líneas no vacías: {len(raw)}")

    # Parsear con SymPy, registrando anomalías por ecuación.
    eqs, anomalies = [], []
    for i, line in enumerate(raw):
        try:
            sub_eqs, _ = sympy_system.build_system([line])
            eqs.extend(sub_eqs)
        except Exception as e:
            anomalies.append((i, line, f"no parsea: {type(e).__name__}: {e}"))

    symbols = sorted({s for e in eqs for s in e.lhs.free_symbols}, key=lambda s: s.name)
    print(f"Ecuaciones parseadas: {len(eqs)} | Variables: {len(symbols)}")

    # Categorías
    print(f"\n{Colors.BOLD}Categorías de variable:{Colors.ENDC}")
    for cat, names in categorize(symbols).items():
        if names:
            sample = ", ".join(sorted(names)[:6])
            extra = f" …(+{len(names) - 6})" if len(names) > 6 else ""
            print(f"  {cat:24s}: {len(names):4d}  [{sample}{extra}]")

    # Polinomicidad y grado. Se comprueba con is_polynomial() (barato) y el
    # grado se calcula por ecuacion con sus PROPIAS variables (construir un Poly
    # sobre todas las variables del sistema seria intratable en sistemas grandes,
    # p. ej. collatz con 3709 variables).
    max_deg = 0
    nonpoly = 0
    for e in eqs:
        if not e.lhs.is_polynomial():
            nonpoly += 1
            anomalies.append((-1, str(e.lhs)[:70], "no polinómica"))
            continue
        try:
            gens = sorted(e.lhs.free_symbols, key=lambda s: s.name)
            if gens:
                max_deg = max(max_deg, sympy.Poly(e.lhs, *gens).total_degree())
        except Exception:
            pass

    print(f"\n{Colors.BOLD}Polinomicidad:{Colors.ENDC}")
    if nonpoly == 0:
        print(f"  {Colors.OKGREEN}✓ Todas las ecuaciones son polinómicas{Colors.ENDC} "
              f"(grado total máximo: {max_deg}).")
    else:
        print(f"  {Colors.FAIL}✗ {nonpoly} ecuaciones NO polinómicas{Colors.ENDC}.")

    # Anomalías
    if anomalies:
        print(f"\n{Colors.WARN}{Colors.BOLD}Anomalías ({len(anomalies)}):{Colors.ENDC}")
        for idx, snippet, why in anomalies[:15]:
            loc = f"línea {idx}" if idx >= 0 else "expr"
            print(f"  {Colors.WARN}!{Colors.ENDC} {loc}: {why}  ::  {snippet[:60]}")
    else:
        print(f"\n{Colors.OKGREEN}Sin anomalías.{Colors.ENDC}")

    if args.eqs:
        print(f"\n{Colors.BOLD}Primeras {args.eqs} ecuaciones:{Colors.ENDC}")
        for e in eqs[:args.eqs]:
            print(f"  {sympy.srepr(e.lhs) if False else e.lhs} = 0")

    sys.exit(1 if (nonpoly or any(i >= 0 for i, _, _ in anomalies)) else 0)


if __name__ == "__main__":
    main()
