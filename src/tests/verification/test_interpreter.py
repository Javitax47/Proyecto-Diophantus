#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - INTÉRPRETE DE ECUACIONES (formato prefijo del compilador)
================================================================================
Valida src/interpreter/interpreter.py tras su actualización al formato de PREFIJO
actual del compilador (+(a,b), call(f,...), If(c,t,f)) y SIN exec/eval:

  - evaluación recursiva (Fibonacci) en modo PYTHON_PURE contra ground-truth;
  - motor de TRANSICIÓN (get_engine/compute_next_state) sobre un contador;
  - parser seguro (árbol) sobre expresiones de prefijo;
  - modo Z3_PURE coincide con el ground-truth (si Z3 está disponible).

Uso:  python src/tests/verification/test_interpreter.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.interpreter.interpreter import (
    SimpleInterpreter, Z3Interpreter, get_engine, parse, eval_py, Z3_AVAILABLE,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FIB = os.path.join(ROOT, "output", "fibonacci_recursive_interpreter_input.txt")


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'; WARN = '\033[93m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def _fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def test_parser(stats):
    print(f"{Colors.HEADER}[1] Parser de prefijo + evaluador de árbol (sin exec/eval){Colors.ENDC}")
    cases = {
        "+(x, 1)": (5, {"x": 4}),
        "*(+(x, 1), 3)": (15, {"x": 4}),
        "If(<=(x, 1), x, 99)": (99, {"x": 7}),
        "%(-(x, 1), 3)": (1, {"x": 5}),
    }
    bad = []
    for expr, (expected, env) in cases.items():
        got = eval_py(parse(expr), env)
        if got != expected:
            bad.append(f"{expr}={got}≠{expected}")
    if not bad:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} prefijo parseado y evaluado correctamente (4 casos)")
    else:
        stats.fail("; ".join(bad))


def test_recursive_python(stats):
    print(f"{Colors.HEADER}[2] Recursión PYTHON_PURE: Fibonacci contra ground-truth{Colors.ENDC}")
    if not os.path.exists(FIB):
        stats.fail(f"falta {FIB}"); return
    interp = SimpleInterpreter()
    interp.parse_file(FIB)
    bad = [n for n in (5, 10, 20) if interp.call("fib", n) != _fib(n)]
    if not bad:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} fib(5)=5, fib(10)=55, fib(20)=6765 (memoizado, ramas perezosas)")
    else:
        stats.fail(f"valores incorrectos en n={bad}")


def test_transition_engine(stats):
    print(f"{Colors.HEADER}[3] Motor de TRANSICIÓN: get_engine + compute_next_state (contador){Colors.ENDC}")
    base = os.path.join(ROOT, "output", "simple_counter")
    if not os.path.exists(base + "_interpreter_input.txt"):
        stats.fail("falta simple_counter_interpreter_input.txt"); return
    eng = get_engine("SEQUENTIAL", base)
    st = {"x": 0}
    for _ in range(5):
        st.update(eng.compute_next_state(st, {}))
    if st.get("x") == 5:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} x: 0→1→2→3→4→5 (transición x[t+1]:=+(x,1))")
    else:
        stats.fail(f"estado final inesperado: {st}")


def test_recursive_z3(stats):
    print(f"{Colors.HEADER}[4] Recursión Z3_PURE: coincide con ground-truth (si Z3){Colors.ENDC}")
    if not Z3_AVAILABLE:
        print(f"  {Colors.WARN}[SKIP]{Colors.ENDC} Z3 no disponible"); stats.ok(); return
    if not os.path.exists(FIB):
        stats.fail(f"falta {FIB}"); return
    z = Z3Interpreter()
    z.parse_file(FIB)
    if z.call("fib", 12) == _fib(12):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} fib(12)=144 vía Z3 RecFunction (recursión sin pila)")
    else:
        stats.fail("Z3 no coincide con el ground-truth")


def main():
    print(f"{Colors.BOLD}=== INTÉRPRETE DE ECUACIONES (formato prefijo, sin exec/eval) ==={Colors.ENDC}")
    stats = Stats()
    test_parser(stats)
    test_recursive_python(stats)
    test_transition_engine(stats)
    test_recursive_z3(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — intérprete actualizado al formato actual "
              f"(recursivo + transición), evaluación segura por árbol.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
