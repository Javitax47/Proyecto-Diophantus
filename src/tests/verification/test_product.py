#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - PRODUCTO MONETIZABLE (verifier + recheck + metering + atlas)
================================================================================
Valida la capa de producto (la capa de producto): el activo estrella
convertido en algo demostrable, re-verificable por terceros y facturable.

Comprueba:
  - verify emite certificados portables (Nullstellensatz UNSAT, testigo SAT, SOS);
  - recheck INDEPENDIENTE los valida SIN importar Z3 ni el motor (aislamiento) —
    el diferenciador frente a un prover de caja negra;
  - recheck RECHAZA certificados manipulados (soundness del re-verificador);
  - metering: cuotas/tiers enforzables y cotización de precio;
  - atlas: índice algoritmo<->identidad con identidades certificadas.

Uso:  python src/tests/verification/test_product.py
"""

import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy  # noqa: F401
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.product import verifier, recheck, metering, atlas


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_unreachable_roundtrip(stats):
    print(f"{Colors.HEADER}[1] verify(UNSAT) -> recheck independiente VÁLIDO{Colors.ENDC}")
    cert = verifier.certify_unreachable(["a-2", "b-3", "a+b-out", "out-6"], ["a", "b", "out"],
                                        "a+b con a=2,b=3 no puede dar 6", 1)
    if cert is None:
        stats.fail("no certificó la inalcanzabilidad"); return
    ok, msg = recheck.recheck(cert)
    if ok and cert['kind'] == 'nullstellensatz' and cert['verdict'] == 'UNSAT':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {msg}")
    else:
        stats.fail(f"recheck falló: {msg}")


def test_witness_roundtrip(stats):
    print(f"{Colors.HEADER}[2] verify(testigo SAT) -> recheck VÁLIDO{Colors.ENDC}")
    cert = verifier.certify_witness(["x-2", "y-3"], ["x", "y"], {"x": 2, "y": 3}, "alcanzable")
    ok, msg = recheck.recheck(cert)
    if ok and cert['kind'] == 'witness':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {msg}")
    else:
        stats.fail(f"recheck testigo falló: {msg}")


def test_sos_roundtrip(stats):
    print(f"{Colors.HEADER}[3] verify(SOS NONNEG) -> recheck VÁLIDO{Colors.ENDC}")
    cert = verifier.certify_nonneg("x**2 - x*y + y**2", ["x", "y"], "no negativo", 2)
    if cert is None:
        stats.fail("no certificó no-negatividad"); return
    ok, msg = recheck.recheck(cert)
    if ok and cert['kind'] == 'sos':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {msg}")
    else:
        stats.fail(f"recheck SOS falló: {msg}")


def test_recheck_isolation(stats):
    print(f"{Colors.HEADER}[4] El re-verificador NO importa Z3 ni el motor (aislamiento){Colors.ENDC}")
    # recheck en un subproceso limpio; comprobar que z3 y discovery no se cargan.
    cert = verifier.certify_unreachable(["a-1", "a-2"], ["a"], "", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(cert, f); path = f.name
    code = ("import sys, json; import src.product.recheck as r;"
            "ok,_=r.recheck_file(%r);"
            "print(int(ok), int('z3' in sys.modules), int('src.analysis.discovery_engine' in sys.modules))"
            % path)
    import subprocess
    out = subprocess.run([sys.executable, "-c", code],
                         capture_output=True, text=True,
                         cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    os.unlink(path)
    res = out.stdout.strip().split()
    if res == ["1", "0", "0"]:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} recheck válido y SIN cargar z3/motor (sólo álgebra)")
    else:
        stats.fail(f"aislamiento roto: {out.stdout.strip()} {out.stderr.strip()[-200:]}")


def test_recheck_rejects_tamper(stats):
    print(f"{Colors.HEADER}[5] recheck RECHAZA certificados manipulados{Colors.ENDC}")
    cert = verifier.certify_unreachable(["a-2", "b-3", "a+b-out", "out-6"], ["a", "b", "out"], "", 1)
    bad = json.loads(json.dumps(cert))
    bad['certificate']['cofactors'][0] = "5"
    ok, _ = recheck.recheck(bad)
    # testigo falso
    badw = verifier.certify_witness(["x-2"], ["x"], {"x": 3}, "")
    okw, _ = recheck.recheck(badw)
    if not ok and not okw:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} cofactor y testigo manipulados rechazados")
    else:
        stats.fail(f"aceptó manipulación: null={ok} witness={okw}")


def test_metering(stats):
    print(f"{Colors.HEADER}[6] Metering: cuotas/tiers enforzables + cotización{Colors.ENDC}")
    with tempfile.TemporaryDirectory() as d:
        m = metering.UsageMeter(os.path.join(d, "usage.json"))
        # hobby con cuota 50: la 51ª no se permite (sin overage)
        auth = m.authorize("acct1", "hobby", period="2026-06")
        for _ in range(50):
            m.record("acct1", period="2026-06")
        blocked = m.authorize("acct1", "hobby", period="2026-06")
        # pro sí permite overage
        pro = m.authorize("acct1", "pro", period="2026-06")
        q = metering.price_quote("pro", 6000)
        cond = (auth['allowed'] and not blocked['allowed'] and pro['allowed']
                and q['total_usd'] == round(99 + 0.50 * 1000, 2))
        if cond:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} hobby bloquea tras cuota; pro cotiza {q['total_usd']} USD a 6000 verif.")
        else:
            stats.fail(f"metering inesperado: auth={auth} blocked={blocked} pro={pro} quote={q}")


def test_atlas(stats):
    print(f"{Colors.HEADER}[7] Atlas: índice con identidades certificadas + búsqueda{Colors.ENDC}")
    idx = atlas.build_index()
    certified = [e for e in idx['entries'] if e['certified']]
    pell = atlas.search(idx, "pell")
    if len(certified) >= 3 and pell and "2" in str(pell[0]['identity']):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {len(certified)} identidades certificadas; búsqueda 'pell' -> {pell[0]['identity']}")
    else:
        stats.fail(f"atlas inesperado: certified={len(certified)} pell={pell}")


def main():
    print(f"{Colors.BOLD}=== PRODUCTO MONETIZABLE (verifier + recheck + metering + atlas) ==={Colors.ENDC}")
    stats = Stats()
    test_unreachable_roundtrip(stats)
    test_witness_roundtrip(stats)
    test_sos_roundtrip(stats)
    test_recheck_isolation(stats)
    test_recheck_rejects_tamper(stats)
    test_metering(stats)
    test_atlas(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el activo estrella es PRODUCTO: "
              f"certificados portables, re-verificación independiente, facturación y atlas.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
