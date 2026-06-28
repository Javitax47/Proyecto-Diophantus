#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE SOUNDNESS DEL MODO PURE (Fase 0, item 2 del informe)
================================================================================
Verifica empíricamente, con Z3, la propiedad central de la aritmetización fiel:

    el sistema diofántico PURE tiene solución entera  <=>  la traza es válida.

Es decir, para cada operador aritmetizado en §4.1 se comprueba sobre una rejilla
de entradas concretas que:
  (a) el sistema ES satisfacible cuando la salida coincide con la semántica real
      del operador (la traza existe), y
  (b) el sistema es INSATISFACIBLE para cualquier otra salida (no hay soluciones
      espurias).

Cubre: división/módulo con cota de resto, comparaciones reificadas
(<, >, <=, >=, ==, !=), booleanos y operadores bit a bit (&, |, ^, <<, >>).

Uso:  python src/tests/verification/test_pure_soundness.py
Requisitos: z3-solver (pip install z3-solver).
"""

import os
import sys
import operator

# --- Path al raíz del repo para importar src.* ---
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from z3 import sat  # noqa: F401  (solo para detectar disponibilidad de Z3)
except ImportError:
    print("[SKIP] z3-solver no está instalado (pip install z3-solver).")
    sys.exit(0)

# La lógica de construcción/verificación (converter linealizado + carga en Z3)
# vive en el helper compartido para no duplicarla entre tests de soundness.
from src.tests.verification._soundness_helpers import pure_system_for, forces_value


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


def build_pure_system(op, a_operand, b_operand, bit_width=8):
    """Sistema PURE para `out = a_operand <op> b_operand`."""
    return pure_system_for((op, a_operand, b_operand), bit_width=bit_width)


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def check(self, label, ok):
        if ok:
            self.passed += 1
        else:
            self.failed += 1
            print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {label}")


def assert_forces(stats, equations, fixed, out_name, expected):
    """Comprueba: satisfacible con out==expected, e insatisfacible con out!=expected."""
    ok = forces_value(equations, fixed, out_name, expected)
    stats.check(f"{fixed} -> {out_name}={expected}", ok)


def test_div_mod(stats):
    print(f"{Colors.HEADER}[1] División / módulo (resto acotado 0<=r<b){Colors.ENDC}")
    for a in range(0, 18):
        for b in range(1, 8):
            sys_div = build_pure_system('/', str(a), str(b))
            assert_forces(stats, sys_div, {}, 'out', a // b)
            sys_mod = build_pure_system('%', str(a), str(b))
            assert_forces(stats, sys_mod, {}, 'out', a % b)


def test_comparisons(stats):
    print(f"{Colors.HEADER}[2] Comparaciones reificadas (<, >, <=, >=, ==, !=){Colors.ENDC}")
    ops = {
        '<': operator.lt, '>': operator.gt, '<=': operator.le,
        '>=': operator.ge, '==': operator.eq, '!=': operator.ne,
    }
    for sym, fn in ops.items():
        for a in range(-4, 5):
            for b in range(-4, 5):
                eqs = build_pure_system(sym, 'A', 'B')
                assert_forces(stats, eqs, {'A': a, 'B': b}, 'out', int(fn(a, b)))


def test_bitwise(stats):
    print(f"{Colors.HEADER}[3] Operadores bit a bit (&, |, ^, <<, >>){Colors.ENDC}")
    W = 4
    bin_ops = {'&': operator.and_, '|': operator.or_, '^': operator.xor}
    for sym, fn in bin_ops.items():
        eqs = build_pure_system(sym, 'A', 'B', bit_width=W)
        for a in range(0, 2 ** W):
            for b in range(0, 2 ** W):
                assert_forces(stats, eqs, {'A': a, 'B': b}, 'out', fn(a, b))
    # desplazamientos por constante
    for a in range(0, 2 ** W):
        eqs_l = build_pure_system('<<', 'A', '2', bit_width=W)
        assert_forces(stats, eqs_l, {'A': a}, 'out', a * 4)
        eqs_r = build_pure_system('>>', 'A', '1', bit_width=W)
        assert_forces(stats, eqs_r, {'A': a}, 'out', a // 2)
    # desplazamientos por cantidad VARIABLE (2^S codificado por bits de S)
    eqs_vl = build_pure_system('<<', 'A', 'S', bit_width=W)   # nbits(S) = 2 -> S in [0,3]
    eqs_vr = build_pure_system('>>', 'A', 'S', bit_width=W)
    for a in range(0, 2 ** W):
        for s in range(0, 4):
            assert_forces(stats, eqs_vl, {'A': a, 'S': s}, 'out', a << s)
            assert_forces(stats, eqs_vr, {'A': a, 'S': s}, 'out', a >> s)


def main():
    print(f"{Colors.BOLD}=== TEST DE SOUNDNESS PURE (solución entera <=> traza válida) ==={Colors.ENDC}")
    stats = Stats()
    test_div_mod(stats)
    test_comparisons(stats)
    test_bitwise(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} casos OK — "
              f"el sistema PURE es sólido para los operadores de §4.1.{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} casos FALLARON.{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
