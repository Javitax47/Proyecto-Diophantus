#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOR DE PR (distribución, MONETIZACION.md C4)
================================================================================
Entrada de la GitHub Action: dado uno o más ficheros de "claim" (sistema
diofántico + enunciado), emite los certificados portables y un resumen Markdown
que la Action adjunta al PR. El valor para el plan: el certificado RE-VERIFICABLE
viaja con el PR; cualquiera (revisor humano, otro CI) lo re-comprueba con
`recheck` sin confiar en este motor.

Formato de un fichero de claim (JSON):
  {"kind": "unreachable"|"nonneg",
   "vars": ["a","b","out"],
   "system": ["a-2","b-3","a+b-out","out-6"],     # para unreachable
   "polynomial": "x**2-x*y+y**2",                  # para nonneg
   "claim": "texto", "max_deg": 2}

Uso:  python scripts/certify_pr.py claims/*.json --out-dir certs --summary summary.md
Código de salida: 0 si todo claim quedó certificado (o es informativo), 1 si alguno
pedido como obligatorio no se pudo certificar.
"""

import os
import sys
import json
import glob
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.product import verifier, recheck


def certify_one(claim):
    kind = claim.get('kind', 'unreachable')
    if kind == 'nonneg':
        return verifier.certify_nonneg(claim['polynomial'], claim['vars'],
                                       claim.get('claim', ''), claim.get('max_deg', 2))
    return verifier.certify_unreachable(claim['system'], claim['vars'],
                                        claim.get('claim', ''), claim.get('max_deg', 2))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("claims", nargs="+", help="ficheros/globs de claims JSON")
    ap.add_argument("--out-dir", default="certs")
    ap.add_argument("--summary", default="diophantus_summary.md")
    args = ap.parse_args(argv)

    paths = []
    for c in args.claims:
        paths.extend(sorted(glob.glob(c)))
    os.makedirs(args.out_dir, exist_ok=True)

    rows = []
    any_fail = False
    for path in paths:
        with open(path, encoding="utf-8") as f:
            claim = json.load(f)
        name = os.path.splitext(os.path.basename(path))[0]
        cert = certify_one(claim)
        if cert is None:
            rows.append((name, "⚠️ UNKNOWN", "sin certificado al grado dado", "—"))
            if claim.get('required'):
                any_fail = True
            continue
        cert_path = os.path.join(args.out_dir, f"{name}.cert.json")
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert, f, indent=2, ensure_ascii=False)
        ok, msg = recheck.recheck(cert)        # auto re-verificación independiente
        verdict = f"OK {cert['verdict']}" if ok else "FALLO recheck"
        if not ok:
            any_fail = True
        rows.append((name, verdict, cert.get('claim', ''), os.path.basename(cert_path)))

    lines = ["## 🔏 Diophantus — Certificados de Corrección", "",
             "Certificados **portables** adjuntos. Re-verifícalos sin confiar en este motor:",
             "`python -m src.product.recheck <cert.json>`", "",
             "| Claim | Veredicto | Descripción | Certificado |",
             "|---|---|---|---|"]
    for name, verdict, desc, cf in rows:
        lines.append(f"| {name} | {verdict} | {desc} | `{cf}` |")
    summary = "\n".join(lines)
    with open(args.summary, "w", encoding="utf-8") as f:
        f.write(summary + "\n")
    print(summary)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
