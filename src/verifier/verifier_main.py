"""
================================================================================
   DIOPHANTUS - VERIFICADOR FORMAL (Bounded Model Checking sobre el sistema)
================================================================================
Toma el sistema polinómico de transición que emite el compilador (`x[t+1] - f(x) = 0`),
lo DESENROLLA K pasos en Z3 y busca una traza que alcance una condición de bug. Si la
encuentra (`sat`), imprime la traza (contraejemplo); si no (`unsat`), el bug es
inalcanzable en K pasos. Es el clásico esquema BMC, pero sobre la arithmetización fiel.

API:  run_verification(config)  con config = {SYSTEM_FILE, STATE_VARS, INPUT_VARS,
      BUG_CONDITION, K_STEPS, INITIAL_STATE?, BOUNDS?, OUTPUT_FILE?}.
Ejemplos completos en `examples_verifier/` (Pong, Primes). Ejecutable directo:
      python -m src.verifier.verifier_main config.json
"""

import sys
import os
import re
import time
from z3 import Int, Solver, sat, unsat, Or, And, If, BoolRef, ArithRef

# Tokens que el extractor de variables NO debe tratar como variables de estado:
# operadores/llamadas, literales y declaraciones de funciones del sistema lógico.
_NON_VARS = {"pow", "If", "And", "Or", "int", "if", "else", "True", "False",
             "None", "RET", "call"}


def sanitize_name(name):
    """Convierte nombres a formato válido Z3."""
    return name.replace("{", "").replace("}", "").replace("[t+1]", "_t1").replace(":", "")

# --- 1. CARGA DEL SISTEMA ---

def get_equation_system(system_file_path, state_vars_list, input_vars_list):
    print(f"[Verifier] 1. Cargando sistema de ecuaciones desde {system_file_path}...")
    
    try:
        with open(system_file_path, 'r', encoding='utf-8') as f:
            poly_system_strings = [line.strip() for line in f if line.strip() and not line.startswith("---")]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo: {system_file_path}", file=sys.stderr)
        sys.exit(1)

    all_vars_set = set()
    
    # Regex robusto para capturar variables
    var_regex = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*(?:\[t\+1\]|_t\d+)?)')
    
    for eq_str in poly_system_strings:
        for match in var_regex.finditer(eq_str):
            var_name = match.group(1)
            # Limpieza básica
            clean_var = sanitize_name(var_name)
            # Descarta operadores/llamadas/literales y declaraciones de funciones (P_*)
            if not clean_var.isdigit() and clean_var not in _NON_VARS \
                    and not clean_var.startswith("P_"):
                all_vars_set.add(clean_var)

    # Asegurar que las variables de configuración también estén
    for v in state_vars_list + input_vars_list:
        all_vars_set.add(sanitize_name(v))
        all_vars_set.add(sanitize_name(f"{v}_t1"))

    print(f"[Verifier] ...Carga completada. {len(all_vars_set)} variables únicas detectadas.")
    return poly_system_strings, all_vars_set

# --- 2. PARSER ---

def parse_equation_to_z3(eq_str, z3_var_map):
    """
    Parsea una string de ecuación a una restricción Z3.
    Maneja errores explícitamente.
    """
    try:
        sane_expr = sanitize_name(eq_str)
        
        # Limpiar sufijos "= 0" de forma segura
        # Primero quitamos espacios al final
        sane_expr = sane_expr.rstrip()
        if sane_expr.endswith("= 0"): 
            sane_expr = sane_expr[:-3]
        elif sane_expr.endswith("=0"): 
            sane_expr = sane_expr[:-2]
        
        # Convertir potencias X^2 -> pow(X, 2)
        expr_str_pow = re.sub(r'(\b[a-zA-Z_0-9]+\b)\^2', r'pow(\1, 2)', sane_expr)
        
        # Entorno de ejecución seguro para eval
        z3_globals = {"pow": pow, "If": If, "And": And, "Or": Or, "True": True, "False": False}
        
        # Evaluar
        z3_lhs = eval(expr_str_pow, z3_globals, z3_var_map)
        
        # Verificar tipo de retorno y convertir a restricción booleana si es necesario
        if isinstance(z3_lhs,  ArithRef):
            return (z3_lhs == 0) # Si es aritmética (A - B), asumimos A - B = 0
        elif isinstance(z3_lhs, BoolRef):
            return z3_lhs        # Si ya es booleana (A == B), retornamos tal cual
        elif isinstance(z3_lhs, bool):
            return z3_lhs        # Si se simplificó a True/False python
            
        return None

    except Exception as e:
        # DEBUG: Descomenta esto si sigues teniendo problemas para ver qué ecuación falla
        # print(f"[Parse Error] '{eq_str}' -> {e}")
        return None

# --- 3. BOUNDS ---

def _apply_bounds(solver, z3_var_map, bounds_config, k_steps):
    if not bounds_config: return
    
    # 1. Bounds relajados para variables internas (C_n, e_n)
    # Fundamental para que Z3 no se pierda en el infinito
    INTERNAL_BOUND = 100000 
    for name, var in z3_var_map.items():
        if name.startswith("e_") or name.startswith("C_"):
            solver.add(var >= -INTERNAL_BOUND)
            solver.add(var <= INTERNAL_BOUND)

    # 2. Bounds de usuario (Física del juego)
    for var_name, limits in bounds_config.items():
        min_v, max_v = limits.get("min"), limits.get("max")
        
        # Aplicar a todos los pasos de tiempo (t0, t1...)
        for t in range(k_steps + 1):
            t_name = f"{sanitize_name(var_name)}_t{t}"
            if t_name in z3_var_map:
                if min_v is not None: solver.add(z3_var_map[t_name] >= min_v)
                if max_v is not None: solver.add(z3_var_map[t_name] <= max_v)

# --- 4. MOTOR PRINCIPAL ---

def run_verification(config):
    system_file = config["SYSTEM_FILE"]
    bug_cond = config["BUG_CONDITION"]
    bounds = config.get("BOUNDS", {})
    k_steps = config.get("K_STEPS", 1)
    
    print(f"--- VERIFICANDO: {os.path.basename(system_file)} ---")
    
    equations, all_vars_base = get_equation_system(system_file, config["STATE_VARS"], config["INPUT_VARS"])
    
    solver = Solver()
    z3_full_map = {}

    # --- Generación de Variables Desenrolladas (Unrolling) ---
    # Identificar variables base eliminando sufijos
    base_vars = set()
    for v in all_vars_base:
        v_clean = v.replace("_t1", "")
        base_vars.add(v_clean)

    # Crear variables Z3 para cada paso de tiempo t=0..k
    vars_by_time = {} # { 'x': {0: x_t0, 1: x_t1...} }

    for t in range(k_steps + 1):
        for v in base_vars:
            name_t = f"{v}_t{t}"
            var_z3 = Int(name_t)
            z3_full_map[name_t] = var_z3
            if v not in vars_by_time: vars_by_time[v] = {}
            vars_by_time[v][t] = var_z3

    # --- Aplicar Bounds ---
    _apply_bounds(solver, z3_full_map, bounds, k_steps)

    # --- Añadir Ecuaciones de Transición ---
    equations_added = 0
    for t in range(k_steps):
        # Crear contexto local para este paso
        # Mapea 'x' -> x_t, 'x_t1' -> x_{t+1}
        context = {}
        for v in base_vars:
            if t in vars_by_time[v]:
                context[v] = vars_by_time[v][t]
                context[f"{v}_t1"] = vars_by_time[v][t+1]
        
        for eq in equations:
            c = parse_equation_to_z3(eq, context)
            if c is not None: 
                solver.add(c)
                equations_added += 1
    
    print(f"[Verifier] Se añadieron {equations_added} restricciones de transición.")

    # --- Estado Inicial (t=0) ---
    if "INITIAL_STATE" in config:
        for var, val in config["INITIAL_STATE"].items():
            s_var = sanitize_name(var)
            if s_var in vars_by_time and 0 in vars_by_time[s_var]:
                solver.add(vars_by_time[s_var][0] == val)

    # --- Condición de Bug ---
    bug_checks = []
    # Rango de chequeo
    limit = k_steps if "_t1" in bug_cond else k_steps + 1
    
    for t in range(limit):
        context_bug = {}
        for v in base_vars:
            if t in vars_by_time[v]:
                context_bug[v] = vars_by_time[v][t]
                if t+1 in vars_by_time[v]:
                    context_bug[f"{v}_t1"] = vars_by_time[v][t+1]
        
        try:
            # Evaluar condición de bug
            # Inyectamos nombres seguros para eval
            safe_cond = sanitize_name(bug_cond)
            cond_z3 = eval(safe_cond, {"__builtins__":None, "And":And, "Or":Or}, context_bug)
            bug_checks.append(cond_z3)
        except Exception as e:
            print(f"[DEBUG] Error evaluando Bug Condition en T={t}: {e}")
            print(f"        Condición: '{bug_cond}'")
            print(f"        Contexto disponible: {list(context_bug.keys())[:5]}...")
            # No hacemos pass, queremos ver el error

    if bug_checks:
        solver.add(Or(bug_checks))
    else:
        print("[WARNING] No se pudo generar ninguna condición de bug válida.")

    # --- Resolver ---
    # Dump para debug
    if config.get("OUTPUT_FILE"):
        debug_path = str(config["OUTPUT_FILE"]).replace(".tex", "_debug.smt2")
        with open(debug_path, "w") as f:
            f.write(solver.to_smt2())
            
    start_t = time.time()
    result = solver.check()
    elapsed = time.time() - start_t
    
    print(f"[Verifier] Resolución: {result} ({elapsed:.4f}s)")
    
    # Si encontramos bug (SAT), mostrarlo
    if result == sat:
        model = solver.model()
        # Mostrar SOLO las variables declaradas por el usuario (estado + entradas);
        # las auxiliares internas y los tokens de función no son estado significativo.
        shown = [sanitize_name(v) for v in config["STATE_VARS"] + config["INPUT_VARS"]]
        print("\n--- TRAZA DEL BUG ENCONTRADA ---")
        for t in range(limit):
            line = [f"{v}={model.eval(vars_by_time[v][t])}"
                    for v in shown if v in vars_by_time and t in vars_by_time[v]]
            print(f"T={t}: " + ", ".join(line))
        print("--------------------------------")
    return result

def main(argv=None):
    """CLI: re-ejecuta una verificación desde un fichero de configuración JSON."""
    import json
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("uso: python -m src.verifier.verifier_main <config.json>")
        print("(ver ejemplos en src/verifier/examples_verifier/)")
        return 2
    with open(argv[0], encoding="utf-8") as f:
        config = json.load(f)
    result = run_verification(config)
    return 0 if result == sat else 1


if __name__ == "__main__":
    sys.exit(main())