#!/usr/bin/env python3
"""
Caza de conjeturas: barre PCFs, identifica formas cerradas en constantes y aplica
el filtro de novedad/interés. Imprime un ranking de candidatas (no clásicas),
priorizando constantes poco charteadas y convergencia rápida.

Uso:
  python scripts/hunt_conjectures.py [--a-deg 2] [--b-deg 1] [--range 3]
                                     [--depth 200] [--dps 42] [--top 20]
                                     [--out hits.json]
Honesto: "candidata" ≠ "demostrada nueva"; la novedad autoritativa exige el
contraste externo con la literatura (paso humano).
"""

import os
import sys
import json
import time
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import mpmath  # noqa: F401
except ImportError:
    print("ERROR: mpmath no está instalado en este intérprete de Python.")
    print(f"  Intérprete en uso: {sys.executable}")
    print("  Solución:")
    print(f"    {sys.executable} -m pip install mpmath")
    sys.exit(1)

from src.analysis.conjecturer import (
    search, search_parallel, search_screened, search_structured, search_open,
    _structured_a_forms, annotate_delta, named_constants,
)
from src.analysis.conjecture_filter import rank_candidates, format_ranked


def _poly_str(coeffs_high_first):
    """'x^2 - 3*x + 1' a partir de coeficientes de mayor a menor grado."""
    deg = len(coeffs_high_first) - 1
    terms = []
    for i, c in enumerate(coeffs_high_first):
        p = deg - i
        if c == 0:
            continue
        mono = "x" if p == 1 else (f"x^{p}" if p > 1 else "1")
        terms.append(f"{c:+d}*{mono}" if mono != "1" else f"{c:+d}")
    return " ".join(terms) or "0"


def _dfmt(r):
    """Etiqueta δ (medida de irracionalidad) para un record: '★δ=...' si δ>0."""
    d = r.get('delta')
    if d is None:
        return ""
    return f"  ★δ={d:.3f} (IRRACIONAL, μ≲{1 + 1/d:.1f})" if d > 0 else f"  δ={d:.3f}"


def report_open(res, top=20):
    """Imprime el resultado del barrido ABIERTO (sin objetivo)."""
    A, N, U, C = res['algebraic'], res['named'], res['unknown'], res['collisions']
    Lf = res.get('linear', [])
    print(f"[open] {len(A)} algebraicos · {len(N)} nombrados · {len(Lf)} formas lineales · "
          f"{len(U)} desconocidos · {len(C)} colisiones PCF↔PCF\n")
    if Lf:
        print("FORMAS LINEALES (combinación entera de varias constantes — tipo Apéry/Zudilin):")
        for f in sorted(Lf, key=lambda x: -(x.get('delta') or -9))[:top]:
            print(f"  {'+'.join(f['constants']):<22} {f['closed_form']:<34} "
                  f"a={f['a_coeffs']} b={f['b_coeffs']}{_dfmt(f)}")
        print()
    # destaca pruebas de irracionalidad (δ>0) en constantes nombradas
    irr = sorted([n for n in N if (n.get('delta') or 0) > 0],
                 key=lambda n: -n['delta'])
    if irr:
        print("★ IRRACIONALIDAD (δ>0: la PCF PRUEBA que su límite es irracional):")
        for n in irr[:top]:
            print(f"  {n['constant']:<10} δ={n['delta']:.4f}  μ≲{1 + 1/n['delta']:.2f}  "
                  f"{n['closed_form']:<28} a={n['a_coeffs']} b={n['b_coeffs']}")
        print()
    if A:
        print("ALGEBRAICOS (raíz de polinomio entero — descubierto sin objetivo):")
        for a in sorted(A, key=lambda x: -(x.get('delta') or -9))[:top]:
            print(f"  grado {a['degree']}: {_poly_str(a['poly']):<26} ≈ {a['value']:<20} "
                  f"a={a['a_coeffs']} b={a['b_coeffs']}{_dfmt(a)}")
        print()
    if N:
        print("NOMBRADOS (Möbius de constante conocida — etiqueta):")
        for n in sorted(N, key=lambda x: -(x.get('delta') or -9))[:top]:
            print(f"  {n['constant']:<10} {n['closed_form']:<30} "
                  f"a={n['a_coeffs']} b={n['b_coeffs']}{_dfmt(n)}")
        print()
    if C:
        print("COLISIONES (≥2 PCFs distintas -> MISMO valor = identidad descubierta):")
        for c in sorted(C, key=lambda x: -x['count'])[:top]:
            print(f"  x{c['count']} [{c['kind']}] {c['value']}")
            for m in c['members'][:3]:
                print(f"       a={m['a_coeffs']} b={m['b_coeffs']}")
        print()
    if U:
        print("DESCONOCIDOS (convergen; ni racional, ni algebraico≤grado, ni nombrado —")
        print("  SOSPECHOSOS de constante nueva; exigen confirmar a más dps y grado):")
        for u in U[:top]:
            print(f"  {u['value']:<24} a={u['a_coeffs']} b={u['b_coeffs']}")
    print("\nNOTA: 'desconocido' = no clasificado AQUÍ (dps/grado/base limitados), NO "
          "'constante nueva probada'. Confírmalo subiendo --dps y --max-alg-deg, y "
          "contrasta con la literatura (paso externo).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a-deg", type=int, default=2)
    ap.add_argument("--b-deg", type=int, default=1)
    ap.add_argument("--range", type=int, default=3)
    ap.add_argument("--depth", type=int, default=200)
    ap.add_argument("--dps", type=int, default=42)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--constants", default=None,
                    help="lista separada por comas para ENFOCAR (p.ej. zeta3,catalan,euler_gamma). "
                         "Por defecto: todas.")
    ap.add_argument("--workers", type=int, default=1,
                    help="procesos en paralelo (multiproceso; >1 acelera ~lineal con núcleos)")
    ap.add_argument("--screen", action="store_true",
                    help="pre-cribado float64 (etapa 1 barata) -> mpmath solo en supervivientes. Para cazas GRANDES.")
    ap.add_argument("--screen-depth", type=int, default=400,
                    help="profundidad de la criba float64")
    ap.add_argument("--structured", action="store_true",
                    help="barrido ESTRUCTURADO al régimen de Apéry: a(n)=L·n^k de grado ALTO "
                         "(hasta --a-max-deg) x b(n) grado --b-deg con coef ±--b-range. Donde "
                         "viven ζ(3)/Catalan; un hit ahí sería genuinamente nuevo. Implica --screen.")
    ap.add_argument("--a-max-deg", type=int, default=6,
                    help="(estructurado) grado máximo del monomio a(n)=L·n^k (Apéry usa k=6)")
    ap.add_argument("--a-lead", type=int, default=2,
                    help="(estructurado) rango del coeficiente líder L de a(n): ±a-lead")
    ap.add_argument("--b-range", type=int, default=15,
                    help="(estructurado) rango de coeficientes de b(n): ±b-range")
    ap.add_argument("--open", dest="open_mode", action="store_true",
                    help="barrido ABIERTO (SIN objetivo): clasifica cada límite como "
                         "algebraico / nombrado / desconocido y detecta colisiones PCF↔PCF. "
                         "Combinable con --structured (espacio de Apéry).")
    ap.add_argument("--max-alg-deg", type=int, default=4,
                    help="(abierto) grado máximo del polinomio entero a probar (algebraicidad)")
    ap.add_argument("--linear", default=None,
                    help="(abierto) detecta FORMAS LINEALES multi-constante en los límites no "
                         "clasificados; pasa una lista de constantes separadas por comas, p.ej. "
                         "'pi,pi^2,zeta3,zeta5,catalan,ln2'. Clase tipo-Apéry/Zudilin.")
    ap.add_argument("--delta", action="store_true",
                    help="calcula la medida de irracionalidad δ de cada hit (convergentes "
                         "enteros exactos): δ>0 PRUEBA irracionalidad y acota μ≲1+1/δ. "
                         "Convierte la caza en resultados DIOFÁNTICOS cuantitativos.")
    ap.add_argument("--delta-depth", type=int, default=150,
                    help="profundidad de los convergentes enteros para δ")
    ap.add_argument("--delta-dps", type=int, default=240,
                    help="precisión para δ (debe superar los dígitos correctos a delta-depth)")
    ap.add_argument("--no-progress", action="store_true",
                    help="desactiva la barra de progreso (p.ej. en logs/CI)")
    ap.add_argument("--checkpoint", default=None,
                    help="ruta del checkpoint (por defecto <out>.ckpt si hay --out). Vuelca "
                         "el progreso periódicamente para no perder cómputo si se corta.")
    ap.add_argument("--checkpoint-every", type=int, default=300,
                    help="segundos entre volcados de checkpoint (modos dirigido/cribado)")
    ap.add_argument("--resume", action="store_true",
                    help="reanuda desde el checkpoint: salta los combos ya hechos y precarga "
                         "los hits guardados (modos dirigido/estructurado/cribado)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    # checkpoint path (auto desde --out) y carga de reanudación
    ckpt_path = args.checkpoint or (args.out + ".ckpt" if args.out else None)
    resume_from, resume_hits = 0, None
    if args.resume and ckpt_path and os.path.exists(ckpt_path):
        ck = json.load(open(ckpt_path))
        resume_from, resume_hits = ck.get('done', 0), ck.get('hits')
        print(f"[hunt] REANUDANDO desde {ckpt_path}: {resume_from:,}/{ck.get('total','?')} combos, "
              f"{len(resume_hits or [])} hits precargados")

    const_names = None
    if args.constants:
        allc = named_constants()
        const_names = [k for k in args.constants.split(",") if k in allc]
        print(f"[hunt] enfocado en constantes: {const_names}")

    # --- modo ABIERTO (sin objetivo) -------------------------------------------
    if args.open_mode:
        t = time.time()
        a_forms = (_structured_a_forms(args.a_max_deg, (-args.a_lead, args.a_lead))
                   if args.structured else None)
        b_cr = (-args.b_range, args.b_range) if args.structured else (-args.range, args.range)
        space = ("ESTRUCTURADO (Apéry)" if args.structured
                 else f"rejilla a_deg={args.a_deg} b_deg={args.b_deg} ±{args.range}")
        linear_basis = [s for s in args.linear.split(",")] if args.linear else None
        print(f"[hunt] ABIERTO (sin objetivo) sobre {space}; max_alg_deg={args.max_alg_deg}; "
              f"{'formas lineales='+str(linear_basis)+'; ' if linear_basis else ''}"
              f"criba float64 (depth {args.screen_depth}) + {args.workers} workers")
        res = search_open(a_degree=args.a_deg, b_degree=args.b_deg,
                          coeff_range=(-args.range, args.range), depth=args.depth,
                          dps=args.dps, screen_depth=args.screen_depth,
                          max_alg_degree=args.max_alg_deg, const_names=const_names,
                          workers=args.workers, a_forms=a_forms, b_coeff_range=b_cr,
                          progress=not args.no_progress, linear_basis=linear_basis)
        dt = time.time() - t
        print(f"[hunt] barrido abierto en {dt:.0f}s")
        if args.delta:
            print(f"[hunt] calculando δ (irracionalidad) de algebraicos/nombrados/lineales...")
            annotate_delta(res['algebraic'], depth=args.delta_depth, dps=args.delta_dps,
                           progress=not args.no_progress)
            annotate_delta(res.get('linear', []), depth=args.delta_depth, dps=args.delta_dps,
                           progress=not args.no_progress)
            annotate_delta(res['named'], depth=args.delta_depth, dps=args.delta_dps,
                           progress=not args.no_progress)
            # colisiones: anota usando el primer miembro de cada una
            for c in res['collisions']:
                m = c['members'][0]
                from src.analysis.conjecturer import irrationality_delta
                try:
                    c['delta'] = irrationality_delta(m['a_coeffs'], m['b_coeffs'],
                                                     depth=args.delta_depth, dps=args.delta_dps)
                except Exception:
                    c['delta'] = None
        print()
        if args.out:
            json.dump(res, open(args.out, "w"))
        report_open(res, top=args.top)
        return

    t = time.time()
    if args.structured:
        print(f"[hunt] ESTRUCTURADO (régimen Apéry): a(n)=L·n^k, k≤{args.a_max_deg}, L=±{args.a_lead}; "
              f"b(n) grado {args.b_deg}, coef ±{args.b_range}; criba float64 (depth {args.screen_depth}) "
              f"+ {args.workers} workers")
        hits = search_structured(a_max_degree=args.a_max_deg, a_lead_range=(-args.a_lead, args.a_lead),
                                 b_degree=args.b_deg, b_coeff_range=(-args.b_range, args.b_range),
                                 depth=args.depth, dps=args.dps, screen_depth=args.screen_depth,
                                 const_names=const_names, workers=args.workers,
                                 progress=not args.no_progress, checkpoint=ckpt_path,
                                 checkpoint_every=args.checkpoint_every,
                                 resume_from=resume_from, resume_hits=resume_hits)
    elif args.screen:
        print(f"[hunt] pre-cribado float64 (depth {args.screen_depth}) + {args.workers} workers")
        hits = search_screened(a_degree=args.a_deg, b_degree=args.b_deg,
                               coeff_range=(-args.range, args.range), depth=args.depth,
                               dps=args.dps, screen_depth=args.screen_depth,
                               const_names=const_names, workers=args.workers,
                               progress=not args.no_progress, checkpoint=ckpt_path,
                               checkpoint_every=args.checkpoint_every,
                               resume_from=resume_from, resume_hits=resume_hits)
    elif args.workers and args.workers > 1:
        print(f"[hunt] multiproceso: {args.workers} workers")
        hits = search_parallel(a_degree=args.a_deg, b_degree=args.b_deg,
                               coeff_range=(-args.range, args.range), depth=args.depth,
                               dps=args.dps, const_names=const_names, workers=args.workers,
                               progress=not args.no_progress)
    else:
        consts = {k: named_constants()[k] for k in const_names} if const_names else None
        hits = search(a_degree=args.a_deg, b_degree=args.b_deg,
                      coeff_range=(-args.range, args.range), depth=args.depth, dps=args.dps,
                      constants=consts)
    dt = time.time() - t
    print(f"[hunt] {len(hits)} identificaciones en {dt:.0f}s "
          f"(a_deg={args.a_deg}, b_deg={args.b_deg}, coef ±{args.range})")
    if args.delta and hits:
        print(f"[hunt] calculando δ (irracionalidad) de {len(hits)} hits...")
        annotate_delta(hits, depth=args.delta_depth, dps=args.delta_dps,
                       progress=not args.no_progress)
    if args.out:
        json.dump(hits, open(args.out, "w"))
    ranked = rank_candidates(hits)
    cands = [r for r in ranked if r['status'].startswith('CANDIDATA')]
    known = [r for r in ranked if r['status'].startswith('CONOCIDA')]
    print(f"[hunt] {len(cands)} candidatas (no clásicas), {len(known)} clásicas conocidas\n")
    print(format_ranked(ranked, top=args.top))
    if args.delta:
        irr = sorted([h for h in hits if (h.get('delta') or 0) > 0], key=lambda h: -h['delta'])
        print(f"\n★ δ>0 (PRUEBA de irracionalidad): {len(irr)} de {len(hits)} hits")
        for h in irr[:args.top]:
            print(f"  {h['constant']:<10} δ={h['delta']:.4f}  μ≲{1 + 1/h['delta']:.2f}  "
                  f"a={h['a_coeffs']} b={h['b_coeffs']}")
    print("\nNOTA: 'candidata' = no clásica AQUÍ; la novedad real exige contraste "
          "con la literatura / base de la Ramanujan Machine (paso externo). δ>0 = "
          "irracionalidad PROBADA del límite (criterio Arnold Math. J. 2024).")


if __name__ == "__main__":
    main()
