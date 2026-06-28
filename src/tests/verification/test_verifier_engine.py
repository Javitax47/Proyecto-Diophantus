#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - VERIFICADOR FORMAL (Bounded Model Checking, Z3)
================================================================================
Valida src/verifier/verifier_main.py: desenrolla el sistema de transición K pasos en
Z3 y decide si una condición de bug es ALCANZABLE (sat = contraejemplo) o no (unsat).

Sobre el contador `x[t+1] = x + 1`:
  - una condición coherente con la transición es ALCANZABLE (sat);
  - una condición contradictoria con la transición es INALCANZABLE (unsat).
Esto ejercita carga del sistema, parseo a Z3, desenrollado y resolución.

Uso:  python src/tests/verification/test_verifier_engine.py
"""

import io
import os
import sys
import contextlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    from z3 import sat, unsat
except ImportError:
    print("[SKIP] z3 no está instalado.")
    sys.exit(0)

from src.verifier.verifier_main import run_verification

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SYS = os.path.join(ROOT, "output", "simple_counter_pure_poly_system.txt")


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def _run(bug):
    config = {
        "SYSTEM_FILE": SYS, "STATE_VARS": ["x"], "INPUT_VARS": [],
        "BUG_CONDITION": bug, "K_STEPS": 3, "INITIAL_STATE": {"x": 0},
        "BOUNDS": {"x": {"min": 0, "max": 50}},
    }
    with contextlib.redirect_stdout(io.StringIO()):     # silenciar el ruido del verificador
        return run_verification(config)


def test_reachable(stats):
    print(f"{Colors.HEADER}[1] Bug ALCANZABLE: condición coherente con la transición -> sat{Colors.ENDC}")
    if not os.path.exists(SYS):
        stats.fail(f"falta {SYS}"); return
    res = _run("x_t1 == x + 1")     # la transición fuerza exactamente esto
    if res == sat:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} traza encontrada (sat): el verificador halla el contraejemplo")
    else:
        stats.fail(f"esperaba sat, obtuvo {res}")


def test_unreachable(stats):
    print(f"{Colors.HEADER}[2] Bug INALCANZABLE: condición contradictoria -> unsat{Colors.ENDC}")
    if not os.path.exists(SYS):
        stats.fail(f"falta {SYS}"); return
    res = _run("x_t1 == x + 5")     # contradice x_t1 = x+1 en todo paso
    if res == unsat:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} inalcanzable (unsat): no existe traza que viole la transición")
    else:
        stats.fail(f"esperaba unsat, obtuvo {res}")


def main():
    print(f"{Colors.BOLD}=== VERIFICADOR FORMAL (BMC sobre el sistema de transición) ==={Colors.ENDC}")
    stats = Stats()
    test_reachable(stats)
    test_unreachable(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el verificador BMC decide alcanzabilidad "
              f"(sat=contraejemplo / unsat=inalcanzable) sobre la arithmetización.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
