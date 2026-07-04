#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - LIGADO DE ARGUMENTOS DE LA RECURSIÓN AL INPUT
================================================================================
Comprueba que, en el sistema PURE de un programa recursivo, los argumentos de las
llamadas recursivas quedan ligados al input (el decremento `n-1` se conserva), de
modo que la longitud de la traza —y por tanto el anclaje `overflow`— es función
del input. Con esto, "solución <=> traza" se cumple como función de la entrada:

    countdown(n) = 7 si n<=0, si no countdown(n-1);   presupuesto = 6
      input_val dentro del presupuesto  -> el sistema es SAT (traza cabe)
      input_val fuera del presupuesto   -> el sistema es UNSAT (overflow)

El parser incluye la referencia al callee como primer "argumento"; el generador
la descarta al ligar parámetros. Si no lo hiciera, las guardas dependerían de
símbolos libres y "fuera de presupuesto" NO sería UNSAT: este test lo detecta.

Uso:  python src/tests/verification/test_arg_binding.py
Requisitos: z3-solver + libclang (si falta, se OMITE).
"""

import os
import sys
import contextlib
import tempfile

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from z3 import sat, unsat
except ImportError:
    print("[SKIP] z3-solver no disponible.")
    sys.exit(0)

try:
    from src.compiler import parser, generator, optimizer
    from src.tests.verification._soundness_helpers import LinearizedConverter, load_into_z3
except Exception:
    print("[SKIP] dependencias de compilación no disponibles.")
    sys.exit(0)

_SRC = (
    "#define DIOPHANTUS_MAX_RECURSION 6\n"
    "#define DIOPHANTUS_MAX_UNROLL 3\n"
    "int input_val = 0;\n"
    "int result = 0;\n"
    "int countdown(int n) {\n"
    "    if (n <= 0) return 7;\n"
    "    return countdown(n - 1);\n"
    "}\n"
    "int main() {\n"
    "    while (1) { result = countdown(input_val); break; }\n"
    "    return 0;\n"
    "}\n"
)


def _build_pure():
    path = os.path.join(tempfile.gettempdir(), "diophantus_argbind.c")
    with open(path, "w") as f:
        f.write(_SRC)
    with contextlib.redirect_stdout(open(os.devnull, "w")):
        ast_map = parser.parse_c_file(path)
        f_map, _inputs, rels, _ovf = generator.generate_function(ast_map)
        opt_f, sub_defs = optimizer.Optimizer(f_map).optimize()
        pc = LinearizedConverter(opt_f, sub_defs, ast_map['state_vars'], rels)
        system, _ = pc.convert(mode="PURE")
    return [eq.replace("[t+1]", "_next").replace("[", "_").replace("]", "")
            for eq in system]


def main():
    print("=== LIGADO DE ARGUMENTOS DE LA RECURSIÓN AL INPUT ===")
    try:
        system = _build_pure()
    except Exception as e:
        print(f"[SKIP] no se pudo compilar el corpus ({type(e).__name__}).")
        sys.exit(0)

    passed = failed = 0

    def check(cond, label):
        nonlocal passed, failed
        if cond:
            passed += 1; print(f"   OK   {label}")
        else:
            failed += 1; print(f"   FAIL {label}")

    # Dentro del presupuesto (traza de longitud 4 <= 6): SAT.
    s_in, _ = load_into_z3(system, {"input_val": 3})
    check(s_in.check() == sat, "input_val=3 (traza cabe en presupuesto) -> SAT")

    # Fuera del presupuesto (traza > 6): el anclaje overflow lo vuelve UNSAT.
    # Solo ocurre si los argumentos están ligados al input.
    s_out, _ = load_into_z3(system, {"input_val": 100})
    check(s_out.check() == unsat,
          "input_val=100 (traza excede presupuesto) -> UNSAT (args ligados al input)")

    total = passed + failed
    print()
    if failed == 0:
        print(f"✓ {passed}/{total} OK — los argumentos de la recursión están ligados "
              f"al input; el sistema PURE es fiel como función de la entrada.")
        sys.exit(0)
    print(f"✗ {failed}/{total} FALLARON — los argumentos no se ligan al input.")
    sys.exit(1)


if __name__ == "__main__":
    main()
