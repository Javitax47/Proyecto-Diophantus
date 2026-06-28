#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CERTIFICADOS COMBINATORIOS (capa universal de certificados)
================================================================================
Valida src/product/combinatorial.py: el MISMO certificado portable y el MISMO
re-verificador mínimo (recheck, solo sympy) que certifican propiedades de PROGRAMAS
sirven, sin código de confianza nuevo, para INFACTIBILIDAD COMBINATORIA (coloreado
de grafos vía Hilbert-Nullstellensatz). Demuestra la UNIFICACIÓN trustless.

Comprueba:
  - ciclo impar (C5) NO es 2-coloreable -> certificado Nullstellensatz, re-verificado
    por recheck.py (mismo checker que el de programas);
  - ciclo par (C6) es bipartito -> testigo ENTERO (±1), re-verificado;
  - K3 NO es 2-coloreable -> certificado;
  - SOUNDNESS: un certificado manipulado es RECHAZADO por recheck.py.

Uso:  python src/tests/verification/test_combinatorial_certs.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy  # noqa: F401
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.product import combinatorial as cb
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


def cyc(n):
    return [(i, (i + 1) % n) for i in range(n)]


def test_odd_cycle_unsat(stats):
    print(f"{Colors.HEADER}[1] Ciclo impar C5: NO 2-coloreable -> Nullstellensatz re-verificado{Colors.ENDC}")
    cert = cb.certify_not_colorable(5, cyc(5), k=2, max_deg=2)
    if not cert:
        stats.fail("no se obtuvo certificado para C5"); return
    ok, msg = recheck(cert)
    if ok and cert['verdict'] == 'UNSAT':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {msg}")
    else:
        stats.fail(f"recheck falló: {msg}")


def test_bipartite_witness(stats):
    print(f"{Colors.HEADER}[2] Ciclo par C6: bipartito -> testigo entero (±1) re-verificado{Colors.ENDC}")
    cert = cb.certify_coloring_witness(6, cyc(6), k=2)
    if not cert:
        stats.fail("no se obtuvo testigo para C6"); return
    ok, msg = recheck(cert)
    if ok and cert['verdict'] == 'SAT':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {msg}")
    else:
        stats.fail(f"recheck falló: {msg}")


def test_triangle_unsat(stats):
    print(f"{Colors.HEADER}[3] Triángulo K3: NO 2-coloreable -> certificado re-verificado{Colors.ENDC}")
    cert = cb.certify_not_colorable(3, [(0, 1), (1, 2), (0, 2)], k=2, max_deg=2)
    if not cert:
        stats.fail("no se obtuvo certificado para K3"); return
    ok, _ = recheck(cert)
    # y un grafo bipartito (camino) SÍ debe colorearse
    coloring = cb.find_coloring(4, [(0, 1), (1, 2), (2, 3)], 2)
    if ok and coloring is not None:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} K3 infactible certificado; camino P4 2-coloreable {coloring}")
    else:
        stats.fail(f"K3 ok={ok}, P4 coloring={coloring}")


def test_soundness_tamper(stats):
    print(f"{Colors.HEADER}[4] SOUNDNESS: certificado manipulado -> recheck.py lo RECHAZA{Colors.ENDC}")
    cert = cb.certify_not_colorable(5, cyc(5), k=2, max_deg=2)
    if not cert:
        stats.fail("no se obtuvo certificado base"); return
    bad = dict(cert)
    bad['certificate'] = {'cofactors': ['0'] * len(cert['system'])}
    ok, msg = recheck(bad)
    if not ok:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} certificado falso rechazado: {msg}")
    else:
        stats.fail("recheck ACEPTÓ un certificado manipulado (fallo de soundness)")


def main():
    print(f"{Colors.BOLD}=== CERTIFICADOS COMBINATORIOS (capa universal trustless) ==={Colors.ENDC}")
    stats = Stats()
    test_odd_cycle_unsat(stats)
    test_bipartite_witness(stats)
    test_triangle_unsat(stats)
    test_soundness_tamper(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el mismo certificado portable y el mismo "
              f"re-verificador mínimo (sympy) certifican infactibilidad combinatoria. Unificación trustless.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
