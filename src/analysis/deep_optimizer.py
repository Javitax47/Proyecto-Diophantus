import sys
import glob
import os
import argparse
import importlib.util
import json
from sympy import symbols, solve, IndexedBase, Symbol

sys.setrecursionlimit(20000)


def build_energy_terms(final_eqs, aux_vars, protected_vars):
    """Genera, por cada ecuación, el término `(expr)**2` mapeando las variables
    auxiliares a `dioph_x[i]`.

    ROBUSTEZ: el mapeo se hace por SUSTITUCIÓN SymPy estructural
    (`expr.subs({Symbol(v): dioph_x[i]})`), no por reemplazo de subcadenas. Esto
    elimina el antiguo hack de placeholders `__AUX_{i}__` —que existía solo para
    evitar que un nombre corto (p. ej. `x`) se reemplazara dentro de otro
    (`xy`)— y con él toda una clase de bugs de colisión de nombres. SymPy nunca
    confunde el símbolo `x` con parte de `xy`.

    Devuelve `(py_terms, inputs_found)`."""
    dioph_x = IndexedBase('dioph_x')
    subs_to_array = {Symbol(name): dioph_x[i] for i, name in enumerate(aux_vars)}
    py_terms = []
    inputs_found = set()
    for eq in final_eqs:
        for p_var in protected_vars:
            if p_var in eq.free_symbols:
                inputs_found.add(str(p_var).replace('_next', ''))
        expr_arr = eq.subs(subs_to_array)
        py_terms.append(f"({expr_arr})**2")
    return py_terms, inputs_found


def load_module(path):
    try:
        spec = importlib.util.spec_from_file_location("target_mod", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f"[FATAL] No se pudo cargar el script de análisis: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Deep Optimizer V18: Atomic Substitution")
    parser.add_argument("file", help="Archivo _analysis_sympy.py")
    parser.add_argument("--inputs", required=True, help="Variables a conservar")
    parser.add_argument("--anchor", default=None, help="Condición de anclaje")
    args = parser.parse_args()

    print("--- DEEP OPTIMIZER V18: ATOMIC ---")

    if not os.path.exists(args.file):
        print(f"Error: No existe {args.file}")
        sys.exit(1)

    # 1. Cargar
    mod = load_module(args.file)
    equations = mod.core_eqs
    vars_map = mod.vars_map
    print(f"Sistema cargado: {len(equations)} ecuaciones.")

    # 2. Configurar Inputs
    input_names = [x.strip() for x in args.inputs.split(',')]
    protected_vars = []

    for name in input_names:
        if name in vars_map:
            protected_vars.append(vars_map[name])
        if f"{name}_next" in vars_map:
            protected_vars.append(vars_map[f"{name}_next"])

    protected_str = set([str(s) for s in protected_vars])

    # 3. Configurar Anchor
    subs_rules = {}
    if args.anchor:
        try:
            key, val = args.anchor.split('=')
            key = key.strip(); val = int(val.strip())

            if key in vars_map: subs_rules[vars_map[key]] = val
            if f"{key}_next" in vars_map: subs_rules[vars_map[f"{key}_next"]] = val
        except: pass

    # Vincular estados
    for name in input_names:
        if name in vars_map and f"{name}_next" in vars_map:
            if vars_map[f"{name}_next"] not in subs_rules:
                subs_rules[vars_map[f"{name}_next"]] = vars_map[name]

    # Pre-proceso
    current_eqs = []
    for eq in equations:
        new_eq = eq.subs(subs_rules)
        if new_eq != 0: current_eqs.append(new_eq)

    # 4. Reducción
    all_symbols = set()
    for eq in current_eqs: all_symbols.update(eq.free_symbols)

    vars_to_kill = [v for v in all_symbols if str(v) not in protected_str]
    vars_to_kill.sort(key=lambda x: str(x))

    print(f"Reduciendo {len(vars_to_kill)} variables intermedias...")

    subs_map = {}
    for _ in range(30):
        progress = False
        remaining = []
        for eq in current_eqs:
            curr = eq.subs(subs_map)
            if curr == 0: continue

            candidates = [v for v in curr.free_symbols if str(v) not in protected_str]
            solved = False

            if candidates:
                for v in candidates:
                    try:
                        if curr.diff(v) in [1, -1]:
                            sol = solve(curr, v)
                            if sol:
                                val = sol[0]
                                if v not in val.free_symbols:
                                    subs_map[v] = val
                                    solved = True
                                    progress = True
                                    break
                    except: pass
            if not solved:
                remaining.append(curr)
        current_eqs = remaining
        if not progress: break

    # 5. Generación
    final_eqs = [eq.subs(subs_map) for eq in current_eqs if eq.subs(subs_map) != 0]

    final_syms = set()
    for eq in final_eqs: final_syms.update(eq.free_symbols)

    aux_vars = sorted([str(s) for s in final_syms if str(s) not in protected_str])

    # Generación robusta de los términos de energía (sustitución SymPy, no
    # manipulación de strings). Ver build_energy_terms().
    py_terms, inputs_found = build_energy_terms(final_eqs, aux_vars, protected_vars)

    base_name = os.path.basename(args.file).replace('_analysis_sympy.py', '')
    out_file = f"output/artifacts/{base_name}_formula.py"

    clean_inputs = [i for i in input_names if i in vars_map or f"{i}_next" in vars_map]
    args_def = ", ".join(clean_inputs) + ", dioph_x"

    content = f"""
def G_formula({args_def}):
    # Vars: {len(aux_vars)} | Inputs: {list(inputs_found)}
    energy = (
        {' + '.join(py_terms)}
    )
    return energy
"""
    os.makedirs("output/artifacts", exist_ok=True)
    with open(out_file, "w") as f: f.write(content)

    print(f"[ÉXITO] Fórmula generada: {out_file} ({len(aux_vars)} vars)")

if __name__ == "__main__":
    main()