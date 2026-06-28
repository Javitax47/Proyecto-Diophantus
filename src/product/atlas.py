"""
================================================================================
   DIOPHANTUS PRODUCT - ATLAS (índice algoritmo <-> identidad)  (C2)
================================================================================
MVP del "Atlas Algebraico de Algoritmos": un índice consultable que asocia cada
programa/algoritmo del corpus con su IDENTIDAD/INVARIANTE algebraico certificado.
Soporta búsqueda directa (por programa) e inversa (por identidad) — el embrión de
la "búsqueda semántica de código / detección de equivalencia" del plan (efecto
OEIS: cada entrada añadida aumenta el valor).

El índice se cachea en output/atlas_index.json. Las entradas con invariante
provienen del motor (cantidades conservadas verificadas) y de formas cerradas
afines detectadas; cada identidad reportada está, por construcción, CERTIFICADA.
"""

import os
import json

import sympy

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_INDEX_PATH = os.path.join(_REPO, "output", "atlas_index.json")


# Entradas semilla: (programa, familia, mapa de transición, vars, grado, nota).
# Las identidades se DESCUBREN y VERIFICAN al construir el índice (no se inyectan).
def _seed_maps():
    x, y, z, w = sympy.symbols('x y z w')
    return [
        ("pell.c",      "Pell / unidad fundamental", [3 * x + 4 * y, 2 * x + 3 * y], ['x', 'y'], 2,
         "x²-2y² conservado (norma de Z[√2])"),
        ("fib.c",       "Fibonacci / recurrencia lineal", [x + y, x], ['x', 'y'], 2,
         "forma cuadrática de la recurrencia"),
        ("linrec.c",    "Recurrencia lineal 2º orden", [x + y, x], ['x', 'y'], 2,
         "invariante de la companion matrix"),
        ("collatz.c",   "Collatz (3n+1)", None, None, None,
         "sin invariante polinómico de bajo grado (régimen no integrable)"),
        ("collatz_cycle.c", "Collatz - ciclos", None, None, None,
         "no-existencia de ciclos cortos certificada por Z3 (UNSAT)"),
    ]


def build_index():
    """Construye el índice descubriendo+certificando la identidad de cada entrada."""
    from src.analysis.discovery_engine import (
        find_conserved_quantities, verify_conserved, reduce_powers,
    )
    entries = []
    for prog, family, T, vn, deg, note in _seed_maps():
        identity = None
        kind = "sin-invariante"
        if T is not None:
            syms = sympy.symbols(vn)
            res = find_conserved_quantities(T, vn, deg, (1, -1))
            nz = [(l, Q) for l, Q in res if sympy.Poly(Q, *syms).total_degree() > 0]
            ess = reduce_powers([Q for _, Q in nz], vn)
            if ess:
                Q = ess[0]
                lam = next((l for l, q in nz if sympy.expand(q - Q) == 0), 1)
                if verify_conserved(Q, T, vn, lam):
                    identity = str(Q)
                    kind = "invariante-conservado"
        entries.append({
            'program': prog, 'family': family, 'kind': kind,
            'identity': identity or note, 'note': note, 'certified': identity is not None,
        })
    return {'schema': 'diophantus-atlas/v1', 'entries': entries}


def load_or_build(rebuild=False):
    if not rebuild and os.path.exists(_INDEX_PATH):
        with open(_INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    idx = build_index()
    os.makedirs(os.path.dirname(_INDEX_PATH), exist_ok=True)
    with open(_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
    return idx


def search(idx, query):
    """Búsqueda directa (programa/familia) o inversa (identidad). Subcadena, case-insensitive."""
    q = query.lower()
    return [e for e in idx['entries']
            if q in e['program'].lower() or q in e['family'].lower()
            or q in str(e['identity']).lower()]


def summary(idx):
    lines = [f"ATLAS ({len(idx['entries'])} entradas):"]
    for e in idx['entries']:
        tag = "✓cert" if e['certified'] else "  ----"
        lines.append(f"  [{tag}] {e['program']:20} {e['family']:32} {e['identity']}")
    return "\n".join(lines)
