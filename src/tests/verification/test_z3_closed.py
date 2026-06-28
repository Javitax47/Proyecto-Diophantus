#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL SISTEMA CERRADO EMITIDO A Z3 (Fase 3, cierre del caveat)
================================================================================
Cierra el caveat de honestidad: el sistema cerrado de collatz (R1-R5) ya no se
comprueba con `==` de Python, sino que se EMITE como bit-vectors de Z3 y es el
SOLVER quien verifica:

  (1) SAT con el testigo verdadero (el sistema acepta la traza valida).
  (2) UNSAT para cualquier Nx distinto con el mismo inicio -> la trayectoria es
      la UNICA solucion del sistema: solucion entera <=> traza valida, probado
      por Z3 (no por Python). Es la propiedad de soundness sin soluciones espurias.

Se usan n con trayectorias cortas para que el razonamiento BV sea rapido; el
sistema es el mismo para cualquier longitud.

Uso:  python src/tests/verification/test_z3_closed.py
Requisitos: z3-solver.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import z3  # noqa: F401
except ImportError:
    print("[SKIP] z3-solver no está instalado.")
    sys.exit(0)

from src.analysis.collatz_collapse import collatz_trace
from src.analysis.z3_closed import verify_with_z3


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


def main():
    print(f"{Colors.BOLD}=== TEST DEL SISTEMA CERRADO EMITIDO A Z3 ==={Colors.ENDC}")
    print(f"{Colors.HEADER}Z3 verifica: SAT con la traza verdadera + UNSAT con cualquier otra{Colors.ENDC}")
    passed = failed = 0
    for n in [5, 6, 7, 9, 12]:
        xs = collatz_trace(n)
        sat_true, unsat_other = verify_with_z3(xs, n)
        if sat_true and unsat_other:
            passed += 1
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} n={n}: T={len(xs)-1} — SAT(traza) y UNSAT(cualquier otra) => trayectoria UNICA")
        else:
            failed += 1
            print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} n={n}: sat_true={sat_true} unsat_other={unsat_other}")

    total = passed + failed
    print()
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {passed}/{total} — Z3 prueba que el sistema cerrado tiene "
              f"como UNICA solucion la traza valida (sin soluciones espurias).{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
