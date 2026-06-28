#!/usr/bin/env python3
"""
ACELERACIÓN estructural de fracciones continuas (estilo Apéry).

En vez de buscar a ciegas PCFs de convergencia rápida en un espacio gigante, parte de
la ESTRUCTURA descubierta por la caza --  b(n) factorizado (2n+1)(α n²+β n+γ) o cuadrático,
a(n)=L·n^k  --  y barre solo los pocos parámetros libres (α,β,γ,k,L), midiendo la medida
de irracionalidad δ de cada PCF que sea Möbius del target.  δ>0 PRUEBA que el límite (un
Möbius del target) es irracional y acota μ≲1+1/δ.

Validado: con --target zeta3 --form factored recupera la fórmula de Apéry (17,17,5), δ>0.
Para --target catalan (irracionalidad ABIERTA) es un intento genuino de probarla.

Uso:
  # Validación (recupera Apéry para ζ(3)):
  python scripts/accelerate.py --target zeta3 --form factored --a-powers 6 --a-leads -1 \
      --quad-range 20 --workers 16

  # Intento sobre Catalan (problema abierto):
  python scripts/accelerate.py --target catalan --form factored --a-powers 4 6 \
      --a-leads -2 -1 1 2 --quad-range 25 --workers 16 --out accel_catalan.json
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
    print(f"  Solución: {sys.executable} -m pip install mpmath")
    sys.exit(1)

from src.analysis.conjecturer import search_accelerated, verify_conjecture, named_constants


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="zeta3",
                    help=f"constante objetivo ({', '.join(named_constants())})")
    ap.add_argument("--form", choices=["factored", "quadratic", "lin_quad_free", "biquadratic"],
                    default="factored",
                    help="forma de b(n): 'factored'=(c·n+d)(αn²+βn+γ) [ζ(3)/Apéry]; "
                         "'quadratic'=αn²+βn+γ [semilla de Catalan]; 'lin_quad_free'=igual "
                         "que factored pero (c,d) también se barren; 'biquadratic'="
                         "(αn²+βn+γ)(α'n²+β'n+γ') grado 4 [usar rango pequeño]")
    ap.add_argument("--lin-factors", default=None,
                    help="(form=factored) factores lineales c·n+d a probar, p.ej. "
                         "'2,1;2,-1;1,1;1,0'. Por defecto: el de --lin")
    ap.add_argument("--a-powers", type=int, nargs="+", default=[6],
                    help="grados k del monomio a(n)=L·n^k (Apéry usa 6)")
    ap.add_argument("--a-leads", type=int, nargs="+", default=[-1],
                    help="coeficientes líder L de a(n) (Apéry usa -1)")
    ap.add_argument("--lin", type=int, nargs=2, default=[2, 1],
                    help="factor lineal (c d) -> c·n+d para form=factored (Apéry: 2 1)")
    ap.add_argument("--quad-range", type=int, default=20,
                    help="rango ± para α,β,γ del factor cuadrático")
    ap.add_argument("--depth", type=int, default=400)
    ap.add_argument("--dps", type=int, default=90)
    ap.add_argument("--delta-depth", type=int, default=160)
    ap.add_argument("--delta-dps", type=int, default=320)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--no-progress", action="store_true")
    ap.add_argument("--checkpoint", default=None,
                    help="ruta del checkpoint (por defecto <out>.ckpt). Vuelca progreso "
                         "periódicamente para no perder cómputo si se corta.")
    ap.add_argument("--checkpoint-every", type=int, default=300,
                    help="segundos entre volcados de checkpoint")
    ap.add_argument("--resume", action="store_true",
                    help="reanuda desde el checkpoint (salta combos hechos, precarga hits)")
    ap.add_argument("--analyze", action="store_true",
                    help="al terminar, busca FORMAS LINEALES multi-constante en los hits "
                         "(analyze_linear_forms) — encadena descubrimiento + análisis")
    ap.add_argument("--analyze-basis", default="pi,pi^2,zeta3,zeta5,catalan,ln2",
                    help="(--analyze) constantes de la base de formas lineales")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.target not in named_constants():
        print(f"target desconocido: {args.target}. Opciones: {list(named_constants())}")
        sys.exit(1)

    # checkpoint/resume
    ckpt_path = args.checkpoint or (args.out + ".ckpt" if args.out else None)
    resume_from, resume_hits = 0, None
    if args.resume and ckpt_path and os.path.exists(ckpt_path):
        ck = json.load(open(ckpt_path))
        resume_from, resume_hits = ck.get('done', 0), ck.get('hits')
        print(f"[accel] REANUDANDO desde {ckpt_path}: {resume_from:,}/{ck.get('total','?')} combos, "
              f"{len(resume_hits or [])} hits precargados")

    lin_factors = None
    if args.lin_factors:
        lin_factors = [tuple(int(x) for x in pair.split(",")) for pair in args.lin_factors.split(";")]

    print(f"[accel] target={args.target} form={args.form} a(n)=L·n^k "
          f"(k∈{args.a_powers}, L∈{args.a_leads}); coef libres ±{args.quad_range}"
          f"{'; lin='+str(lin_factors) if lin_factors else ''}; {args.workers} workers")
    t = time.time()
    hits = search_accelerated(target=args.target, form=args.form,
                              a_powers=tuple(args.a_powers), a_leads=tuple(args.a_leads),
                              lin_factor=tuple(args.lin), lin_factors=lin_factors,
                              quad_range=(-args.quad_range, args.quad_range),
                              depth=args.depth, dps=args.dps, delta_depth=args.delta_depth,
                              delta_dps=args.delta_dps, workers=args.workers,
                              progress=not args.no_progress, checkpoint=ckpt_path,
                              checkpoint_every=args.checkpoint_every,
                              resume_from=resume_from, resume_hits=resume_hits)
    dt = time.time() - t
    pos = [h for h in hits if (h.get('delta') or 0) > 0]
    print(f"[accel] {len(hits)} Möbius de {args.target} en {dt:.0f}s; {len(pos)} con δ>0 "
          f"(prueban irracionalidad)\n")

    if pos:
        print(f"★★★ δ>0 — PRUEBAN que el límite (Möbius de {args.target}) es IRRACIONAL:")
        for h in pos[:args.top]:
            ok = verify_conjecture(h['a_coeffs'], h['b_coeffs'], args.target, h['relation'], dps=150)
            print(f"  δ={h['delta']:+.4f}  μ≲{1 + 1/h['delta']:.2f}  a={h['a_coeffs']} "
                  f"b={h['b_coeffs']}  {h['closed_form']}  [verif:{ok}]")
        print()

    print(f"Mejores por δ (top {args.top}):")
    for h in hits[:args.top]:
        d = h.get('delta')
        tag = "★IRRACIONAL" if (d or 0) > 0 else ""
        ds = f"{d:+.4f}" if d is not None else "  None "
        print(f"  δ={ds} {tag:<12} a={h['a_coeffs']} b={h['b_coeffs']} = {h['closed_form']}")

    if args.out:
        json.dump(hits, open(args.out, "w"))
        print(f"\n[accel] guardado en {args.out}")

    # --- encadenado: análisis de FORMAS LINEALES multi-constante sobre los hits ---
    if args.analyze:
        from src.analysis.conjecturer import analyze_linear_forms, annotate_delta
        basis = [s for s in args.analyze_basis.split(",") if s in named_constants()]
        print(f"\n[analyze] buscando formas lineales multi-constante en {len(hits)} hits "
              f"(base={basis}, dps={max(args.dps, 140)})...")
        forms = analyze_linear_forms(hits, basis_names=basis, dps=max(args.dps, 140),
                                     min_constants=2, progress=not args.no_progress)
        if forms:
            annotate_delta(forms, depth=160, dps=max(args.delta_dps, 300),
                           progress=not args.no_progress)
        print(f"[analyze] {len(forms)} formas lineales multi-constante:")
        for f in sorted(forms, key=lambda x: -(x.get('delta') or -9)):
            d = f.get('delta')
            dtag = (f"  δ={d:+.4f}{' ★IRRACIONAL' if (d or 0) > 0 else ''}") if d is not None else ""
            print(f"  {'+'.join(f['constants']):<24} {f['closed_form']:<40} "
                  f"a={f['a_coeffs']} b={f['b_coeffs']}{dtag}")
        if args.out and forms:
            json.dump(forms, open(args.out.replace('.json', '') + '_linforms.json', "w"))

    print("\nNOTA: δ>0 prueba irracionalidad del límite (Möbius del target), por tanto del "
          "TARGET, salvo casos degenerados (criterio Arnold Math. J. 2024). Para Catalan/"
          "ζ(5), un δ>0 verificado a alta precisión sería un resultado sobre un problema "
          "ABIERTO: confírmalo a dps muy alto y contrasta con la literatura (paso externo).")


if __name__ == "__main__":
    main()
