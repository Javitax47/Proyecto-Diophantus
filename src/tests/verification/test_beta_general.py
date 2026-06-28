#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - GENERALIDAD DEL BETA BACKEND (compilador UNIVERSAL)
================================================================================
Demuestra que el puente compilador -> colapso beta NO esta hardcodeado a un
algoritmo: la MISMA maquinaria (extract_transition + run_and_pack, que extrae la
transicion de UN paso de cualquier programa compilado y empaqueta su traza en
testigos beta) reproduce la referencia de VARIOS programas distintos:

  * collatz_trajectory  (no afin, seleccion por paridad, 2 registros)
  * linrec              (recurrencia lineal x -> 2x+1, 2 registros)
  * sum_down            (acumulador k+(k-1)+...+1, 2 registros)

Si la transicion extraida del compilador coincide con la referencia Python de
CADA uno, el camino es universal (collatz es solo un caso de prueba).

Uso:  python src/tests/verification/test_beta_general.py
Requisitos: LLVM/libclang.
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)
sys.setrecursionlimit(200000)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


def libclang_ok():
    try:
        import src.compiler.parser
        import clang.cindex
        clang.cindex.Index.create()
        return True
    except Exception:
        return False


# Referencias Python (la semantica esperada de cada programa del corpus).
def ref_collatz(n):
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else (3 * n + 1) // 2
        seq.append(n)
    return seq

def ref_linrec(x):
    seq = [x]
    for _ in range(20):
        x = 2 * x + 1
        seq.append(x)
    return seq

def ref_sumdown_acc(k):
    # traza del acumulador 'acc' a lo largo de la recursion
    acc = 0
    seq = [acc]
    while k > 0:
        acc = acc + k
        k -= 1
        seq.append(acc)
    return seq


# (archivo, funcion, params de estado, variable de traza, inicial, referencia)
CASES = [
    ("src/examples/collatz.c", "collatz_trajectory", ["n", "acc"], "n",
     lambda v: {"n": v, "acc": 0}, ref_collatz, [6, 7, 27, 97]),
    ("src/examples/linrec.c", "linrec", ["x", "step"], "x",
     lambda v: {"x": v, "step": 0}, ref_linrec, [0, 1, 3, 5]),
    ("src/examples/countdown.c", "sum_down", ["k", "acc"], "acc",
     lambda v: {"k": v, "acc": 0}, ref_sumdown_acc, [1, 4, 7, 10]),
]


def main():
    print(f"{Colors.BOLD}=== GENERALIDAD DEL BETA BACKEND (mismo motor, varios programas) ==={Colors.ENDC}")
    if not libclang_ok():
        print(f"{Colors.WARN}[SKIP] libclang no disponible.{Colors.ENDC}")
        sys.exit(0)

    from src.analysis.beta_backend import extract_transition, run_and_pack
    from src.analysis.trace_packer import verify_packing

    passed = failed = 0
    for src, func, state_params, trace_key, mk_start, ref, inputs in CASES:
        # La MISMA funcion generica extrae la transicion compilada de cada programa.
        step = extract_transition(src, func, state_params)
        ok_prog = True
        for v in inputs:
            trace, a, b, T, halt = run_and_pack(step, mk_start(v), trace_key)
            expected = ref(v)
            # (a) la transicion compilada reproduce la referencia
            # (b) los testigos beta recuperan la traza compilada
            if trace != expected or not verify_packing(a, b, trace):
                ok_prog = False
                print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {func}({v}): compilado {trace[:5]}... vs ref {expected[:5]}...")
                break
        if ok_prog:
            passed += 1
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {func}: {len(inputs)} entradas coinciden con la referencia y empaquetan en beta")
        else:
            failed += 1

    total = passed + failed
    print()
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {passed}/{total} programas — el motor beta es UNIVERSAL "
              f"(no especifico de collatz).{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {failed}/{total} programas FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
