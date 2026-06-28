"""
================================================================================
   DIOPHANTUS PRODUCT - CLI  (verify / recheck / atlas)
================================================================================
Interfaz de línea de comandos del producto. Tres subcomandos:

  verify   programa/sistema -> certificado portable (JSON)
  recheck  certificado.json -> re-verificación independiente (sin solver)
  atlas    consulta el índice algoritmo <-> identidad

Ejemplos:
  # Certificar que un sistema diofántico es inalcanzable (estado de error imposible)
  python -m src.product.cli verify --system "a-2" "b-3" "a+b-out" "out-6" \
         --vars a b out --claim "a+b con a=2,b=3 no puede dar 6" -o cert.json

  # Un tercero re-verifica SIN confiar en el solver
  python -m src.product.cli recheck cert.json
"""

import sys
import json
import argparse

from src.product import verifier, recheck as recheck_mod


def _cmd_verify(args):
    if args.system:
        if not args.vars:
            print("error: --vars es obligatorio con --system"); return 2
        cert = None
        if args.nonneg:
            cert = verifier.certify_nonneg(args.system[0], args.vars, args.claim, args.max_deg)
        else:
            cert = verifier.certify_unreachable(args.system, args.vars, args.claim, args.max_deg)
        if cert is None:
            print(json.dumps({'verdict': 'UNKNOWN',
                              'reason': f'sin certificado a grado <= {args.max_deg}'}, indent=2))
            return 3
    elif args.pure_file:
        polys, var_names = verifier.system_from_pure_file(args.pure_file)
        cert = verifier.certify_unreachable(polys, var_names, args.claim, args.max_deg)
        if cert is None:
            print(json.dumps({'verdict': 'UNKNOWN'}, indent=2)); return 3
    else:
        print("error: indica --system ... o --pure-file <path>"); return 2

    out = json.dumps(cert, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[verify] {cert['verdict']} — certificado escrito en {args.output}")
    else:
        print(out)
    return 0


def _cmd_recheck(args):
    ok, msg = recheck_mod.recheck_file(args.cert)
    mark = "VÁLIDO ✓" if ok else "INVÁLIDO ✗"
    print(f"[recheck] {mark}: {msg}")
    return 0 if ok else 1


def _cmd_qubo(args):
    from src.analysis import qubo as qubomod
    if not args.vars or not args.bounds:
        print("error: --vars y --bounds (lo:hi por variable) son obligatorios"); return 2
    if len(args.bounds) != len(args.vars):
        print("error: un --bounds lo:hi por cada variable"); return 2
    bounds = {}
    for v, b in zip(args.vars, args.bounds):
        lo, hi = b.split(":")
        bounds[v] = (int(lo), int(hi))
    res = qubomod.export_qubo(args.system, args.vars, bounds)
    out = {
        'n_vars': res['n_vars'], 'offset': res['offset'], 'pubo_degree': res['pubo_degree'],
        'Q': {f"{i},{j}": c for (i, j), c in res['Q'].items()},
        'bin_names': res['bin_names'],
    }
    text = json.dumps(out, indent=2)
    if args.verify:
        ok, d = qubomod.verify_qubo(args.system, args.vars, bounds)
        print(f"[qubo] verificado={ok} E_min={d['energy_min']} soluciones={d['qubo_solutions']}")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[qubo] QUBO ({res['n_vars']} vars, grado PUBO {res['pubo_degree']}) escrito en {args.output}")
    else:
        print(text)
    return 0


def _cmd_factor(args):
    from src.analysis.factorize import solve_and_certify
    r = solve_and_certify(args.N)
    if not r['found']:
        print(f"[factor] no se encontró factorización dentro del presupuesto ({r['stats']})")
        return 3
    print(f"[factor] {args.N} = {r['p']} · {r['q']}  "
          f"(primos: {r['p_prime']}, {r['q_prime']})")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(r['certificate'], f, indent=2, ensure_ascii=False)
        print(f"[factor] certificado portable escrito en {args.output} "
              f"(re-verifícalo: python -m src.product.recheck {args.output})")
    return 0


def _cmd_color(args):
    """Certificado de (no) k-coloreabilidad de un grafo: mismo formato portable,
    re-verificable con el mismo recheck.py (vertical combinatorio de la capa)."""
    from src.product import combinatorial as cb
    edges = []
    for e in args.edges:
        u, v = e.split(":")
        edges.append((int(u), int(v)))
    cert, found = cb.certify_colorability(args.n, edges, args.k, max_deg=args.max_deg)
    if cert is None:
        print(json.dumps({'verdict': 'UNKNOWN',
                          'reason': f'sin certificado a grado <= {args.max_deg}'}, indent=2))
        return 3
    out = json.dumps(cert, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[color] {cert.get('verdict')} — certificado escrito en {args.output} "
              f"(re-verifícalo: python -m src.product.recheck {args.output})")
    else:
        print(out)
    return 0


def _cmd_sat(args):
    """Certificado de (in)satisfacibilidad de una CNF (formato DIMACS por cláusula):
    mismo formato portable, mismo recheck.py (vertical SAT de la capa)."""
    from src.product import sat_certs as sat
    clauses = [[int(x) for x in cl.split(",")] for cl in args.cnf.split(";") if cl.strip()]
    cert, is_sat = sat.certify_sat(args.nvars, clauses, max_deg=args.max_deg)
    if cert is None:
        print(json.dumps({'verdict': 'UNKNOWN',
                          'reason': f'sin certificado a grado <= {args.max_deg}'}, indent=2))
        return 3
    out = json.dumps(cert, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[sat] {cert.get('verdict')} — certificado escrito en {args.output} "
              f"(re-verifícalo: python -m src.product.recheck {args.output})")
    else:
        print(out)
    return 0


def _cmd_atlas(args):
    from src.product import atlas
    idx = atlas.load_or_build()
    if args.query:
        for hit in atlas.search(idx, args.query):
            print(f"  {hit['program']:20} {hit['kind']:12} {hit['identity']}")
    else:
        print(atlas.summary(idx))
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="diophantus", description="Diophantus — verificador y certificados portables")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="emite un certificado portable")
    v.add_argument("--system", nargs="+", help="polinomios p_i (se interpretan = 0)")
    v.add_argument("--vars", nargs="+", help="nombres de variables")
    v.add_argument("--pure-file", help="fichero PURE generado por el compilador")
    v.add_argument("--nonneg", action="store_true", help="certificar p>=0 (SOS) en vez de inalcanzabilidad")
    v.add_argument("--claim", default="", help="enunciado legible del veredicto")
    v.add_argument("--max-deg", type=int, default=2, help="grado de búsqueda del certificado")
    v.add_argument("-o", "--output", help="fichero de salida del certificado")
    v.set_defaults(func=_cmd_verify)

    r = sub.add_parser("recheck", help="re-verifica un certificado SIN solver")
    r.add_argument("cert", help="certificado JSON")
    r.set_defaults(func=_cmd_recheck)

    q = sub.add_parser("qubo", help="exporta un sistema a QUBO (annealing/QAOA)")
    q.add_argument("--system", nargs="+", required=True, help="polinomios p_i (= 0)")
    q.add_argument("--vars", nargs="+", required=True, help="variables enteras")
    q.add_argument("--bounds", nargs="+", required=True, help="rango lo:hi por variable")
    q.add_argument("--verify", action="store_true", help="auditar por fuerza bruta (n pequeño)")
    q.add_argument("-o", "--output", help="fichero de salida del QUBO (JSON)")
    q.set_defaults(func=_cmd_qubo)

    fa = sub.add_parser("factor", help="factoriza N=p·q vía annealing (quantum-ready) + certificado")
    fa.add_argument("N", type=int, help="entero a factorizar")
    fa.add_argument("-o", "--output", help="fichero del certificado portable")
    fa.set_defaults(func=_cmd_factor)

    co = sub.add_parser("color", help="certificado de (no) k-coloreabilidad de un grafo")
    co.add_argument("--n", type=int, required=True, help="nº de vértices (0..n-1)")
    co.add_argument("--edges", nargs="+", required=True, help="aristas u:v")
    co.add_argument("--k", type=int, default=3, help="nº de colores")
    co.add_argument("--max-deg", type=int, default=2, help="grado de búsqueda del certificado")
    co.add_argument("-o", "--output", help="fichero de salida del certificado")
    co.set_defaults(func=_cmd_color)

    sa = sub.add_parser("sat", help="certificado de (in)satisfacibilidad de una CNF")
    sa.add_argument("--nvars", type=int, required=True, help="nº de variables booleanas")
    sa.add_argument("--cnf", required=True,
                    help="cláusulas separadas por ';', literales por ',' (DIMACS). "
                         "Ej.: '1,2;1,-2;-1,2;-1,-2' (literal i ⇒ var i-1; negativo ⇒ ¬)")
    sa.add_argument("--max-deg", type=int, default=2, help="grado de búsqueda del certificado")
    sa.add_argument("-o", "--output", help="fichero de salida del certificado")
    sa.set_defaults(func=_cmd_sat)

    a = sub.add_parser("atlas", help="índice algoritmo <-> identidad")
    a.add_argument("--query", help="término de búsqueda (programa o identidad)")
    a.set_defaults(func=_cmd_atlas)
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
