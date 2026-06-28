#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - AUDITORIA DE LOS ARTEFACTOS DE PRIMALIDAD ANTIGUOS (erroneos)
================================================================================
Documenta, con contraejemplos, por que los artefactos de primalidad heredados NO
son tests de primalidad validos (y por que sus sellos del README estaban
inflados). Sirve de guardia: nadie debe volver a presentarlos como correctos.
La implementacion CORRECTA esta en src/analysis/primality.py (Baillie-PSW).

Hallazgos:
  * "Ecuacion Logaritmica (Miller-Rabin Base 2)" (primes_innovative_fermat_closed):
    es Fermat base 2 DEBIL, no Miller-Rabin. Acepta pseudoprimos de Fermat
    (341, 561, ...). 341 lo pasa pero MR-fuerte base 2 lo caza -> no es MR.
  * "ECPP Deterministic (Proof)" (primes_ecpp_final_ecpp_closed): solo verifica
    UNA identidad (punto en curva + Z(m*G)=0). Compuestos (9, 15, 21) la pasan
    -> NO es una prueba de primalidad (falta el certificado completo: factor
    primo grande del orden, recursion, cota de Goldwasser-Kilian/Atkin).

Uso:  python src/tests/verification/test_primality_audit.py
"""

import os
import sys
import importlib.util

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _REPO)

try:
    from sympy import isprime
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.primality import miller_rabin_strong_base2


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


def _load(rel):
    path = os.path.join(_REPO, rel)
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(os.path.basename(rel), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0; self.skipped = 0
    def ok(self): self.passed += 1
    def skip(self, m): self.skipped += 1; print(f"  {Colors.WARN}⊘ {m}{Colors.ENDC}")
    def fail(self, m): self.failed += 1; print(f"  {Colors.FAIL}✗ {m}{Colors.ENDC}")


def audit_logarithmic(stats):
    print(f"{Colors.HEADER}[1] 'Logarítmico (Miller-Rabin)' es Fermat débil con pseudoprimos{Colors.ENDC}")
    m = _load("output/artifacts/primes_innovative_fermat_closed.py")
    if m is None or not hasattr(m, "G_formula"):
        stats.skip("artefacto ausente (ya retirado)"); return
    comp = [n for n in range(3, 2000, 2) if m.G_formula(n) == 0 and not isprime(n)]
    is_fermat = (m.G_formula(341) == 0) and (not miller_rabin_strong_base2(341))
    if comp and is_fermat:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓ confirmado defecto{Colors.ENDC}: acepta compuestos {comp[:5]}; "
              f"341 pasa pero MR lo caza -> es Fermat, no Miller-Rabin")
    else:
        stats.fail(f"auditoría logarítmico inesperada: comp={comp[:5]} is_fermat={is_fermat}")


def audit_ecpp(stats):
    print(f"{Colors.HEADER}[2] 'ECPP Deterministic (Proof)' solo verifica una identidad{Colors.ENDC}")
    m = _load("output/artifacts/primes_ecpp_final_ecpp_closed.py")
    if m is None or not hasattr(m, "G_formula"):
        stats.skip("artefacto ausente (ya retirado)"); return
    # compuestos que pasan la identidad (curva y^2=x^3, punto (1,1))
    bad = []
    for n in (9, 15, 21):
        for mm in range(2, 3 * n):
            if m.G_formula(n, 0, 0, 1, 1, mm) == 0:
                bad.append((n, mm)); break
    if len(bad) >= 2:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓ confirmado defecto{Colors.ENDC}: compuestos pasan la identidad "
              f"{[b[0] for b in bad]} -> no es prueba de primalidad")
    else:
        stats.fail(f"auditoría ECPP inesperada: bad={bad}")


def main():
    print(f"{Colors.BOLD}=== AUDITORÍA DE ARTEFACTOS DE PRIMALIDAD ANTIGUOS ==={Colors.ENDC}")
    stats = Stats()
    audit_logarithmic(stats)
    audit_ecpp(stats)
    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} auditorías confirmadas "
              f"({stats.skipped} omitidas) — defectos documentados; usar primality.py.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
