#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DE PARSEO DE OPERADORES ANIDADOS (regresion)
================================================================================
Guarda el arreglo del parseo de BINARY_OPERATOR (el operador es el token ENTRE
los operandos, no el primero de igual longitud). Antes, expresiones como
(3*n+1)/2 o a*b+c se compilaban con el operador equivocado. Aqui se compila un
conjunto de funciones con aritmetica anidada y se comprueba que la transicion
compilada evalua EXACTAMENTE igual que Python sobre varios valores de entrada.

Uso:  python src/tests/verification/test_parser_operators.py
Requisitos: LLVM/libclang.
"""

import os
import sys
import tempfile

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)
sys.setrecursionlimit(200000)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


def libclang_ok():
    try:
        import src.compiler.parser  # configura libclang
        import clang.cindex
        clang.cindex.Index.create()
        return True
    except Exception:
        return False


# (nombre, cuerpo C de la expresion en n, referencia Python)
CASES = [
    ("e1", "(3 * n + 1) / 2", lambda n: (3 * n + 1) // 2),
    ("e2", "3 * n + 1", lambda n: 3 * n + 1),
    ("e3", "n * n + 2 * n + 1", lambda n: n * n + 2 * n + 1),
    ("e4", "(n + 1) * (n + 2)", lambda n: (n + 1) * (n + 2)),
    ("e5", "n * 2 + n * 3", lambda n: n * 2 + n * 3),
    ("e6", "(n + 5) % 7", lambda n: (n + 5) % 7),
    ("e7", "n - 2 * 3 + 4", lambda n: n - 2 * 3 + 4),
    ("e8", "2 * (n - 1) * (n - 1)", lambda n: 2 * (n - 1) * (n - 1)),
]


def main():
    print(f"{Colors.BOLD}=== TEST DE PARSEO DE OPERADORES ANIDADOS ==={Colors.ENDC}")
    if not libclang_ok():
        print(f"{Colors.WARN}[SKIP] libclang no disponible.{Colors.ENDC}")
        sys.exit(0)

    from src.compiler import parser
    from src.compiler.generator import AstFlattener
    from src.analysis.beta_backend import _eval

    # Generar un .c con una funcion por expresion.
    funcs = "\n".join(f"int {name}(int n) {{ return {expr}; }}" for name, expr, _ in CASES)
    src = f"#define DIOPHANTUS_MAX_RECURSION 4\nint dummy = 0;\n{funcs}\nint main(){{ while(1){{ break; }} return 0; }}"
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False, dir="src/examples")
    tmp.write(src); tmp.close()

    passed = failed = 0
    try:
        ast = parser.parse_c_file(tmp.name)
        for name, expr, ref in CASES:
            fl = AstFlattener(ast['state_vars'], ast['functions'], ast['struct_defs'],
                              dict(ast['config']), symbolic_mode=True)
            body = fl._resolve_expression(
                fl.generate_function_relation(name, ast['functions'][name]['body'])['body'])
            ok = all(_eval(body, {"n": v}) == ref(v) for v in range(0, 12))
            if ok:
                passed += 1
                print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {name}: {expr}")
            else:
                failed += 1
                diffs = [(v, _eval(body, {"n": v}), ref(v)) for v in range(12)
                         if _eval(body, {"n": v}) != ref(v)]
                print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {name}: {expr}  ej: {diffs[:3]}")
    finally:
        os.remove(tmp.name)

    total = passed + failed
    print()
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {passed}/{total} OK — los operadores anidados "
              f"se compilan con la precedencia correcta.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
