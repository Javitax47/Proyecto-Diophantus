#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - EXPORTADOR A QUBO (backend de optimización binaria / annealing)
================================================================================
Valida src/analysis/qubo.py: la conversión sistema diofántico -> QUBO cuyos
mínimos globales (energía 0) son EXACTAMENTE las soluciones del sistema. Es el
tercer backend (junto a LaTeX/CAS) y conecta la arithmetización con annealers/QAOA.
SIN sensacionalismo: es un exportador útil y auditable, no "programación cuántica".

Comprueba (auditoría por fuerza bruta, corrección del exportador):
  - sistema LINEAL -> QUBO directo (grado 2), argmin == soluciones;
  - sistema NO LINEAL -> PUBO grado 4 -> cuadratización de Rosenberg -> QUBO,
    argmin == soluciones (la cuadratización preserva los mínimos);
  - sistema INFEASIBLE -> energía mínima > 0 (sin solución), coherente;
  - sistema con varias ecuaciones -> solución única correcta.

Uso:  python src/tests/verification/test_qubo.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy  # noqa: F401
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.qubo import export_qubo, verify_qubo, energy, brute_force_min


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def _check(stats, polys, vn, bounds, label, expect_feasible, max_deg_expected=None):
    ok, d = verify_qubo(polys, vn, bounds)
    feasible = d['energy_min'] == 0
    if ok and feasible == expect_feasible:
        stats.ok()
        deg = d['pubo_degree']
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label}: argmin==soluciones; E_min={d['energy_min']}, "
              f"grado PUBO={deg}, n_vars={d['n_vars']}")
        if d['qubo_solutions']:
            print(f"      soluciones = {d['qubo_solutions']}")
    else:
        stats.fail(f"{label}: ok={ok} feasible={feasible} (esperado {expect_feasible}) detalle={d}")


def test_linear(stats):
    print(f"{Colors.HEADER}[1] Sistema lineal -> QUBO directo (grado 2){Colors.ENDC}")
    _check(stats, ['a+b-3'], ['a', 'b'], {'a': (0, 3), 'b': (0, 3)}, "a+b=3", True)


def test_nonlinear_quadratize(stats):
    print(f"{Colors.HEADER}[2] Sistema NO LINEAL -> cuadratización de Rosenberg{Colors.ENDC}")
    ok, d = verify_qubo(['a*b-6'], ['a', 'b'], {'a': (0, 3), 'b': (0, 3)})
    # debe haber requerido cuadratización (grado PUBO >= 3) y dar las soluciones
    if ok and d['pubo_degree'] >= 3 and d['qubo_solutions'] == [(2, 3), (3, 2)]:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} a·b=6: PUBO grado {d['pubo_degree']} cuadratizado a "
              f"{d['n_vars']} vars; soluciones {d['qubo_solutions']}")
    else:
        stats.fail(f"a·b=6 inesperado: {d}")


def test_infeasible(stats):
    print(f"{Colors.HEADER}[3] Sistema INFEASIBLE -> energía mínima > 0{Colors.ENDC}")
    _check(stats, ['a-2', 'a-3'], ['a'], {'a': (0, 3)}, "a=2 ∧ a=3", False)


def test_multi(stats):
    print(f"{Colors.HEADER}[4] Varias ecuaciones -> solución única{Colors.ENDC}")
    ok, d = verify_qubo(['a+b-4', 'a-b'], ['a', 'b'], {'a': (0, 3), 'b': (0, 3)})
    if ok and d['qubo_solutions'] == [(2, 2)]:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} a+b=4 ∧ a=b -> {d['qubo_solutions']}")
    else:
        stats.fail(f"multi inesperado: {d}")


def test_matrix_consistency(stats):
    print(f"{Colors.HEADER}[5] La matriz Q reproduce la energía del PUBO{Colors.ENDC}")
    res = export_qubo(['a+b-3'], ['a', 'b'], {'a': (0, 3), 'b': (0, 3)})
    emin, argmins = brute_force_min(res['Q'], res['offset'], res['n_vars'])
    # energía 0 alcanzable y no negativa en todos los estados de mínimo
    if emin == 0 and all(energy(res['Q'], res['offset'], b) == 0 for b in argmins):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Q+offset coherente; E_min=0 en {len(argmins)} estados")
    else:
        stats.fail(f"matriz incoherente: E_min={emin}")


def main():
    print(f"{Colors.BOLD}=== EXPORTADOR A QUBO (sistema diofántico -> optimización binaria) ==={Colors.ENDC}")
    stats = Stats()
    test_linear(stats)
    test_nonlinear_quadratize(stats)
    test_infeasible(stats)
    test_multi(stats)
    test_matrix_consistency(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — exportación a QUBO correcta y auditada: "
              f"argmin(QUBO) ⟺ soluciones del sistema, con cuadratización exacta.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
