#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CRUCE MOTOR DE DESCUBRIMIENTO <-> SUCESIONES DE LUCAS (Fase 4)
================================================================================
Une el motor de descubrimiento (Fase 4) con la primalidad CORRECTA (primality.py,
Baillie-PSW). Las sucesiones de Lucas U_n, V_n (parametros P, Q; D=P^2-4Q) son la
base del componente Lucas de Baillie-PSW, y satisfacen identidades cerradas. El
motor las redescubre sin plantilla:

  (1) El mapa companero de Lucas (U_n,U_{n-1}) -> (P*U_n - Q*U_{n-1}, U_n) tiene la
      forma norma  x^2 - P*x*y + Q*y^2  como invariante RELATIVO de autovalor
      lambda = Q (el determinante del mapa). El motor la DESCUBRE y se verifica.
  (2) Consecuencia (identidad de la forma norma): a lo largo de la sucesion,
      U_{n+1}^2 - P*U_{n+1}*U_n + Q*U_n^2 = Q^n.
  (3) Identidad clasica de Lucas:  V_n^2 - D*U_n^2 = 4*Q^n  (la que sustenta el
      test de Lucas). Se verifica EXACTAMENTE sobre las sucesiones reales.

Uso:  python src/tests/verification/test_lucas_discovery.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.discovery_engine import find_conserved_quantities, verify_conserved

x, y = sympy.symbols('x y')


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def lucas_uv_exact(k, P, Q):
    """U_k, V_k EXACTOS (sin mod) por recurrencia."""
    U0, U1 = 0, 1
    V0, V1 = 2, P
    if k == 0:
        return 0, 2
    for _ in range(k - 1):
        U0, U1 = U1, P * U1 - Q * U0
        V0, V1 = V1, P * V1 - Q * V0
    return U1, V1


# (P, Q): incluye Fibonacci (1,-1), Pell-Lucas (2,-1), y parámetros tipo Selfridge.
CASES = [(1, -1), (2, -1), (3, 2), (1, 2), (4, 1), (5, 5)]


def test_discover_norm_form(stats):
    print(f"{Colors.HEADER}[1] El motor descubre la forma norma de Lucas x²-Pxy+Qy² (λ=Q){Colors.ENDC}")
    for P, Q in CASES:
        T = [P * x - Q * y, x]                       # mapa companero
        res = find_conserved_quantities(T, ['x', 'y'], 2, eigenvalues=(Q,))
        target = x**2 - P * x * y + Q * y**2
        found = any(not sympy.cancel(f / target).free_symbols
                    for l, f in res if sympy.Poly(f, x, y).total_degree() > 0 and l == Q)
        verified = verify_conserved(target, T, ['x', 'y'], Q)
        if found and verified:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} P={P},Q={Q} (D={P*P-4*Q}): descubre x²-{P}xy+{Q}y² (λ={Q}), verificado")
        else:
            stats.fail(f"P={P},Q={Q}: found={found} verified={verified}")


def test_norm_form_identity(stats):
    print(f"{Colors.HEADER}[2] Identidad de la forma norma: U_{{n+1}}²-P·U_{{n+1}}U_n+Q·U_n² = Qⁿ{Colors.ENDC}")
    ok_all = True
    for P, Q in CASES:
        for n in range(0, 12):
            Un, _ = lucas_uv_exact(n, P, Q)
            Un1, _ = lucas_uv_exact(n + 1, P, Q)
            if Un1**2 - P * Un1 * Un + Q * Un**2 != Q**n:
                ok_all = False
                stats.fail(f"forma norma falla P={P},Q={Q},n={n}")
                break
    if ok_all:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} se cumple para {len(CASES)} parámetros, n=0..11")


def test_lucas_VU_identity(stats):
    print(f"{Colors.HEADER}[3] Identidad clásica de Lucas: V_n² - D·U_n² = 4·Qⁿ (base del test de Lucas){Colors.ENDC}")
    ok_all = True
    for P, Q in CASES:
        D = P * P - 4 * Q
        for n in range(0, 12):
            Un, Vn = lucas_uv_exact(n, P, Q)
            if Vn**2 - D * Un**2 != 4 * Q**n:
                ok_all = False
                stats.fail(f"V²-DU²≠4Qⁿ en P={P},Q={Q},n={n}: {Vn**2 - D*Un**2} vs {4*Q**n}")
                break
    if ok_all:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} V_n²-D·U_n²=4Qⁿ exacto para {len(CASES)} parámetros, n=0..11")


def main():
    print(f"{Colors.BOLD}=== CRUCE MOTOR DE DESCUBRIMIENTO <-> SUCESIONES DE LUCAS ==={Colors.ENDC}")
    stats = Stats()
    test_discover_norm_form(stats)
    test_norm_form_identity(stats)
    test_lucas_VU_identity(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el motor redescubre la estructura "
              f"de Lucas que sustenta el Baillie-PSW correcto.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
