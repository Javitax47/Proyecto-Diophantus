#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOS SAT/CNF (capa universal de certificados)
================================================================================
Valida src/product/sat_certs.py: el MISMO certificado portable y el MISMO
re-verificador mínimo (recheck, solo sympy) certifican INSATISFACIBILIDAD booleana
(CNF) vía Hilbert-Nullstellensatz. Tercer dominio de la capa universal trustless.

Comprueba:
  - (x)∧(¬x) y 4-cláusulas-sobre-2-vars y una cadena de implicaciones: UNSAT ->
    certificado Nullstellensatz, re-verificado por recheck.py;
  - una CNF satisfacible -> testigo (modelo 0/1), re-verificado;
  - SOUNDNESS: certificado manipulado RECHAZADO.

Uso:  python src/tests/verification/test_sat_certs.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy  # noqa: F401
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.product import sat_certs as sat
from src.product.recheck import recheck


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_unsat_certificates(stats):
    print(f"{Colors.HEADER}[1] CNF insatisfacibles -> Nullstellensatz re-verificado por recheck.py{Colors.ENDC}")
    cases = [
        ("(x)∧(¬x)", 1, [[1], [-1]]),
        ("4 cláusulas / 2 vars", 2, [[1, 2], [1, -2], [-1, 2], [-1, -2]]),
        ("cadena a,¬a∨b,¬b∨c,¬c", 3, [[1], [-1, 2], [-2, 3], [-3]]),
    ]
    for name, n, clauses in cases:
        cert = sat.certify_unsat(n, clauses, max_deg=2)
        if not cert or cert['verdict'] != 'UNSAT':
            stats.fail(f"{name}: sin certificado UNSAT"); return
        ok, msg = recheck(cert)
        if not ok:
            stats.fail(f"{name}: recheck rechazó un certificado válido: {msg}"); return
    stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 3 CNF UNSAT certificadas y re-verificadas independientemente")


def test_sat_witness(stats):
    print(f"{Colors.HEADER}[2] CNF satisfacible -> testigo (modelo 0/1) re-verificado{Colors.ENDC}")
    cert = sat.certify_sat_witness(2, [[1, 2], [-1]])   # b0=0 -> ¬x; b1=1 -> y ; satisface
    if not cert or cert['verdict'] != 'SAT':
        stats.fail("no se obtuvo testigo SAT"); return
    ok, msg = recheck(cert)
    if ok:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {msg}")
    else:
        stats.fail(f"recheck rechazó el testigo: {msg}")


def test_unified_verdict(stats):
    print(f"{Colors.HEADER}[3] Veredicto unificado: distingue SAT (testigo) de UNSAT (certificado){Colors.ENDC}")
    cert_sat, is_sat = sat.certify_sat(2, [[1, 2]])               # satisfacible
    cert_unsat, is_sat2 = sat.certify_sat(1, [[1], [-1]], max_deg=1)  # insatisfacible
    ok1 = is_sat and recheck(cert_sat)[0]
    ok2 = (not is_sat2) and recheck(cert_unsat)[0]
    if ok1 and ok2:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} SAT->testigo y UNSAT->Nullstellensatz, ambos re-verificados")
    else:
        stats.fail(f"veredicto unificado inesperado: sat_ok={ok1} unsat_ok={ok2}")


def test_soundness(stats):
    print(f"{Colors.HEADER}[4] SOUNDNESS: certificado manipulado -> recheck.py lo RECHAZA{Colors.ENDC}")
    cert = sat.certify_unsat(2, [[1, 2], [1, -2], [-1, 2], [-1, -2]], max_deg=1)
    bad = dict(cert); bad['certificate'] = {'cofactors': ['0'] * len(cert['system'])}
    ok, msg = recheck(bad)
    if not ok:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} certificado falso rechazado: {msg}")
    else:
        stats.fail("recheck ACEPTÓ un certificado manipulado (fallo de soundness)")


def main():
    print(f"{Colors.BOLD}=== CERTIFICADOS SAT/CNF (capa universal trustless) ==={Colors.ENDC}")
    stats = Stats()
    test_unsat_certificates(stats)
    test_sat_witness(stats)
    test_unified_verdict(stats)
    test_soundness(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el mismo certificado portable y el mismo "
              f"re-verificador (sympy) certifican (in)satisfacibilidad CNF. Tercer dominio de la capa.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
