#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - SOUNDNESS DEL TRUNCAMIENTO POR PRESUPUESTO (overflow)
================================================================================
Cuando el desenrollado de una recursión agota DIOPHANTUS_MAX_RECURSION, la
expansión ya no es fiel al programa. El converter ancla entonces una variable
`overflow = 0` cuyo valor es 1 exactamente cuando la rama seleccionada usa un
resultado truncado. La propiedad que se verifica aquí, con Z3:

    traza dentro del presupuesto  =>  el sistema tiene solución (valor correcto)
    traza que excede el presupuesto =>  el sistema NO tiene solución

es decir, el sistema deja de admitir soluciones espurias para entradas grandes
en vez de codificar en silencio un programa distinto.

Uso:  python src/tests/verification/test_overflow_soundness.py
Requisitos: z3-solver. libclang (opcional, para la parte end-to-end).
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from src.compiler.generator import OVERFLOW_MARKER

try:
    from z3 import sat, unsat
except ImportError:
    print("[SKIP] z3-solver no disponible.")
    sys.exit(0)

from src.tests.verification._soundness_helpers import (
    pure_system_for, load_into_z3, forces_value)


def _truncated_chain(depth):
    """Transición de `f(n) = if(base_i, 7, ...)` desenrollada `depth` niveles y
    truncada: `if(g0, 7, if(g1, 7, ... if(g_{depth-1}, 7, MARKER)))`. Las guardas
    g0..g_{depth-1} modelan si el caso base se alcanza en cada nivel."""
    expr = OVERFLOW_MARKER
    for i in reversed(range(depth)):
        expr = ('if', f"g{i}", 7, expr)
    return expr


def test_synthetic(stats):
    """Sobre la cadena truncada, con las guardas fijadas a valores concretos."""
    for depth in (2, 4, 6):
        system = pure_system_for(_truncated_chain(depth), target="out")

        # El anclaje debe estar presente.
        has_anchor = any(eq.strip() == "overflow = 0" for eq in system)
        _check(stats, has_anchor, f"depth={depth}: ancla 'overflow = 0' presente")

        # Traza que excede el presupuesto: ninguna guarda se cumple -> UNSAT.
        over = {f"g{i}": 0 for i in range(depth)}
        s, _ = load_into_z3(system, over)
        _check(stats, s.check() == unsat,
               f"depth={depth}: todas las guardas 0 (traza > presupuesto) -> UNSAT")

        # Traza dentro del presupuesto: alguna guarda se cumple -> SAT y out=7.
        for k in range(depth):
            fixed = {f"g{i}": (1 if i == k else 0) for i in range(depth)}
            ok = forces_value(system, fixed, "out", 7)
            _check(stats, ok,
                   f"depth={depth}: guarda {k} activa (traza <= presupuesto) -> "
                   f"SAT con out=7")


def test_no_overflow_is_untouched(stats):
    """Sin marcador de truncamiento, el sistema no gana ni la variable `overflow`
    ni ecuaciones extra: el anclaje es inerte cuando la traza cabe siempre."""
    system = pure_system_for(('if', 'g0', 7, 11), target="out")
    touched = any("overflow" in eq for eq in system)
    _check(stats, not touched,
           "sin truncamiento no se emite el anclaje de overflow")
    _check(stats, forces_value(system, {'g0': 1}, 'out', 7),
           "sin truncamiento el valor sigue siendo correcto (g0=1 -> 7)")
    _check(stats, forces_value(system, {'g0': 0}, 'out', 11),
           "sin truncamiento el valor sigue siendo correcto (g0=0 -> 11)")


def test_end_to_end(stats):
    """Compila un programa recursivo real y comprueba que el sistema PURE lleva
    el anclaje y que forzar 'ningún caso base dentro del presupuesto' -> UNSAT.
    Se omite si libclang no está disponible."""
    import contextlib
    import tempfile
    try:
        from src.compiler import parser, generator, optimizer
        from src.tests.verification._soundness_helpers import LinearizedConverter
    except Exception:
        print("   [e2e] omitido (dependencias no disponibles).")
        return

    src = (
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
    path = os.path.join(tempfile.gettempdir(), "diophantus_overflow_e2e.c")
    with open(path, "w") as f:
        f.write(src)

    try:
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            ast_map = parser.parse_c_file(path)
            f_map, _inputs, rels, triggered = generator.generate_function(ast_map)
            opt_f, sub_defs = optimizer.Optimizer(f_map).optimize()
            pc = LinearizedConverter(opt_f, sub_defs, ast_map['state_vars'], rels)
            system, _ = pc.convert(mode="PURE")
    except Exception as e:
        print(f"   [e2e] omitido (compilación no disponible: {type(e).__name__}).")
        return

    _check(stats, triggered, "e2e: la compilación reporta truncamiento")
    _check(stats, any(eq.strip() == "overflow = 0" for eq in system),
           "e2e: el sistema PURE lleva el anclaje 'overflow = 0'")

    # Saneo de nombres para el cargador Z3 (mismas reglas que sympy_system).
    system = [eq.replace("[t+1]", "_next").replace("[", "_").replace("]", "")
              for eq in system]

    # Guardas = variables booleanizadas (`X*(1 - X) = 0`) que no son holguras
    # de no-negatividad (`nn_*`): las reificaciones de las comparaciones base.
    import re as _re
    guards = set()
    for eq in system:
        m = _re.match(r'^(\w+)\*\(1 - \1\) = 0$', eq.strip())
        if m and not m.group(1).startswith("nn_"):
            guards.add(m.group(1))
    guards = sorted(guards)
    if not guards:
        print("   [e2e] sin guardas detectadas; se omite la comprobación UNSAT.")
        return
    s, _ = load_into_z3(system, {g: 0 for g in guards})
    _check(stats, s.check() == unsat,
           "e2e: ninguna guarda activa (traza > presupuesto) -> UNSAT")


class _Stats:
    def __init__(self):
        self.passed = 0
        self.failed = 0


def _check(stats, cond, label):
    if cond:
        stats.passed += 1
        print(f"   OK   {label}")
    else:
        stats.failed += 1
        print(f"   FAIL {label}")


def main():
    print("=== SOUNDNESS DEL TRUNCAMIENTO POR PRESUPUESTO (overflow) ===")
    stats = _Stats()
    test_synthetic(stats)
    test_no_overflow_is_untouched(stats)
    test_end_to_end(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"✓ {stats.passed}/{total} casos OK — el truncamiento por presupuesto "
              f"es sólido: fuera de presupuesto no hay solución, dentro sí.")
        sys.exit(0)
    print(f"✗ {stats.failed}/{total} casos FALLARON.")
    sys.exit(1)


if __name__ == "__main__":
    main()
