#!/usr/bin/env python3
"""
POST-PROCESO de una caza ya hecha: lee el JSON de --out y busca FORMAS LINEALES
multi-constante (combinaciones enteras tipo a·ζ(3)+b·π³+...) en los límites de las
PCFs halladas, SIN re-ejecutar la caza. También recalcula δ (irracionalidad) opcional.

Sirve para aprovechar el JSON de una caza larga: aunque la caza solo buscara Möbius de
UNA constante, sus PCFs convergen a valores que pueden ser formas lineales de VARIAS
constantes -- una clase de conjetura más rica que se detecta aquí a posteriori.

Uso:
  python scripts/analyze_hits.py caza_8h_dirigida.json \
      --basis pi,pi^2,zeta3,zeta5,catalan,ln2 --dps 140 --min-const 2
"""

import os
import sys
import json
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import mpmath  # noqa: F401
except ImportError:
    print("ERROR: mpmath no está instalado.")
    print(f"  Solución: {sys.executable} -m pip install mpmath")
    sys.exit(1)

from src.analysis.conjecturer import analyze_linear_forms, annotate_delta, named_constants


def _collect_records(data):
    """Normaliza el JSON de la caza a una lista de records con a_coeffs/b_coeffs.
    Soporta el formato dirigido (lista de hits) y el abierto (dict de buckets)."""
    if isinstance(data, list):
        return list(data)
    recs = []
    if isinstance(data, dict):
        for key in ('named', 'unknown', 'algebraic', 'linear'):
            for r in data.get(key, []):
                if 'a_coeffs' in r and 'b_coeffs' in r:
                    recs.append(r)
        # colisiones: usa el primer miembro
        for c in data.get('collisions', []):
            m = (c.get('members') or [{}])[0]
            if 'a_coeffs' in m and 'b_coeffs' in m:
                recs.append(m)
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file", help="JSON producido por una caza (--out)")
    ap.add_argument("--basis", default="pi,pi^2,zeta3,zeta5,catalan,ln2",
                    help=f"constantes para la forma lineal ({', '.join(named_constants())})")
    ap.add_argument("--dps", type=int, default=140)
    ap.add_argument("--min-const", type=int, default=2,
                    help="mínimo de constantes que deben intervenir (≥2 = multi-constante real)")
    ap.add_argument("--delta", action="store_true", help="recalcula δ de las formas halladas")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    data = json.load(open(args.json_file))
    recs = _collect_records(data)
    if not recs:
        print("No se encontraron records con a_coeffs/b_coeffs en el JSON.")
        sys.exit(0)
    basis = [s for s in args.basis.split(",") if s in named_constants()]
    print(f"[analyze] {len(recs)} PCFs del JSON; base lineal={basis}; dps={args.dps}, "
          f"min_const={args.min_const}")

    found = analyze_linear_forms(recs, basis_names=basis, dps=args.dps,
                                 min_constants=args.min_const, progress=True)
    print(f"\n[analyze] {len(found)} formas lineales multi-constante encontradas\n")
    if args.delta and found:
        annotate_delta(found, depth=160, dps=max(args.dps, 280), progress=True)

    for f in sorted(found, key=lambda x: -(x.get('delta') or -9)):
        d = f.get('delta')
        dtag = (f"  δ={d:+.4f}{' ★IRRACIONAL' if (d or 0) > 0 else ''}") if d is not None else ""
        print(f"  {'+'.join(f['constants']):<24} {f['closed_form']:<40} "
              f"a={f['a_coeffs']} b={f['b_coeffs']}{dtag}")

    if args.out:
        json.dump(found, open(args.out, "w"))
        print(f"\n[analyze] guardado en {args.out}")
    print("\nNOTA: una forma lineal hallada AQUÍ es una conjetura candidata (re-verificable "
          "subiendo --dps); la novedad exige contraste con la literatura (paso externo).")


if __name__ == "__main__":
    main()
