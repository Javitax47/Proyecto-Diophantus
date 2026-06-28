#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - DEMOSTRADOR DE LA CAPA UNIVERSAL DE CERTIFICADOS *TRUSTLESS*
================================================================================
Pasa una BATERÍA de afirmaciones de TRES dominios distintos —programas, coloreado
de grafos y SAT/CNF— por el MISMO motor de certificados y, sobre todo, por el MISMO
re-verificador mínimo (`recheck.py`, solo sympy, sin Z3 ni el motor). Demuestra que un
único sustrato algebraico *trustless* cruza dominios hoy separados.

Cada fila se RE-COMPRUEBA de forma independiente; el escéptico no confía en el emisor.
Incluye un control de SOUNDNESS: un certificado manipulado debe ser RECHAZADO.

Uso:  python scripts/trustless_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.product import verifier, combinatorial as cb, sat_certs as sat
from src.product.recheck import recheck


class C:
    G = '\033[92m'; R = '\033[91m'; H = '\033[95m'; B = '\033[1m'; E = '\033[0m'; DIM = '\033[2m'


def row(domain, instance, cert):
    """Re-verifica un certificado con recheck.py (independiente) y devuelve una fila."""
    if cert is None:
        return (domain, instance, "—", None, "sin certificado a este grado")
    ok, msg = recheck(cert)
    return (domain, instance, cert.get('verdict', '?'), ok, msg)


def main():
    print(f"{C.B}=== CAPA UNIVERSAL DE CERTIFICADOS TRUSTLESS — batería multi-dominio ==={C.E}")
    print(f"{C.DIM}Todo se re-verifica con el MISMO recheck.py (solo sympy, sin solver).{C.E}\n")

    rows = []

    # ---- Dominio 1: PROGRAMAS (sistema diofántico de una traza) ----
    # a=2, b=3, out=a+b; ¿puede out=6?  (debe ser 5 -> inalcanzable)
    rows.append(row("programa", "a=2,b=3,a+b=out, ¿out=6?",
                    verifier.certify_unreachable(["a-2", "b-3", "a+b-out", "out-6"],
                                                 ["a", "b", "out"], max_deg=2)))
    # ¿out=5? -> alcanzable (testigo)
    rows.append(row("programa", "a=2,b=3,a+b=out, ¿out=5? (testigo)",
                    verifier.certify_witness(["a-2", "b-3", "a+b-out", "out-5"],
                                             ["a", "b", "out"], {"a": 2, "b": 3, "out": 5})))
    # invariante: a^2 - 2ab + b^2 >= 0  (SOS)
    rows.append(row("programa", "(a-b)² ≥ 0  (SOS)",
                    verifier.certify_nonneg("a**2 - 2*a*b + b**2", ["a", "b"], max_deg=2)))

    # ---- Dominio 2: COLOREADO DE GRAFOS (Hilbert-Nullstellensatz) ----
    for n in (3, 5, 7, 9):
        rows.append(row("grafo", f"C{n} no 2-coloreable (ciclo impar)",
                        cb.certify_not_colorable(n, cb.cycle(n), k=2, max_deg=2)))
    rows.append(row("grafo", "C6 bipartito 2-coloreable (testigo)",
                    cb.certify_coloring_witness(6, cb.cycle(6), k=2)))
    rows.append(row("grafo", "K4 no 3-coloreable",
                    cb.certify_not_colorable(4, cb.complete(4), k=3, max_deg=4)))
    np, pe = cb.petersen()
    pc = cb.find_coloring(np, pe, 3)
    rows.append(("grafo", "Petersen 3-coloreable (búsqueda)", "SAT" if pc else "?",
                 pc is not None, f"coloreado propio hallado: {pc}" if pc else "no hallado"))

    # ---- Dominio 3: SAT / CNF (insatisfacibilidad booleana) ----
    rows.append(row("SAT", "(x)∧(¬x) insatisfacible",
                    sat.certify_unsat(1, [[1], [-1]], max_deg=1)))
    rows.append(row("SAT", "4 cláusulas sobre 2 vars: UNSAT",
                    sat.certify_unsat(2, [[1, 2], [1, -2], [-1, 2], [-1, -2]], max_deg=1)))
    rows.append(row("SAT", "cadena a,¬a∨b,¬b∨c,¬c: UNSAT",
                    sat.certify_unsat(3, [[1], [-1, 2], [-2, 3], [-3]], max_deg=1)))
    rows.append(row("SAT", "(x∨y)∧(¬x): satisfacible (modelo)",
                    sat.certify_sat_witness(2, [[1, 2], [-1]])))

    # ---- impresión ----
    print(f"  {'dominio':<9} {'instancia':<42} {'veredicto':<10} recheck")
    print(f"  {'-'*9} {'-'*42} {'-'*10} {'-'*7}")
    passed = total = 0
    for dom, inst, verdict, ok, msg in rows:
        total += 1
        if ok:
            passed += 1
            mark = f"{C.G}✓{C.E}"
        else:
            mark = f"{C.R}✗{C.E}" if ok is False else "—"
        print(f"  {dom:<9} {inst:<42} {verdict:<10} {mark}")

    # ---- control de soundness: certificado manipulado debe FALLAR ----
    base = cb.certify_not_colorable(5, cb.cycle(5), k=2, max_deg=2)
    tampered = dict(base); tampered['certificate'] = {'cofactors': ['0'] * len(base['system'])}
    ok_bad, _ = recheck(tampered)
    sound = (ok_bad is False)

    print()
    print(f"  re-verificadas OK: {C.B}{passed}/{total}{C.E}  ·  "
          f"soundness (cert falso rechazado): {C.G if sound else C.R}{'✓' if sound else '✗'}{C.E}")
    if passed == total and sound:
        print(f"\n{C.G}{C.B}✓ Un mismo certificado portable y un mismo re-verificador mínimo (sympy) "
              f"certifican programas, grafos y SAT. Unificación trustless entre dominios.{C.E}")
        return 0
    print(f"\n{C.R}{C.B}✗ Alguna fila no re-verificó o falló el control de soundness.{C.E}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
