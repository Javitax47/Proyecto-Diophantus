import argparse
import sys
import os
import traceback

sys.setrecursionlimit(2000000)

from src.compiler import parser
from src.compiler import generator
from src.compiler import optimizer
from src.compiler import latex_exporter
from src.compiler import polynomial_converter
from src.compiler import equation_exporter
from src.compiler import cas_exporter

def find_pdflatex():
    import shutil
    path = shutil.which("pdflatex")
    if path: return path
    return None

def main():
    cli_parser = argparse.ArgumentParser(description="Compilador C a Ecuación Diophantus.")
    cli_parser.add_argument("input_file", help="Ruta al archivo .c")
    args = cli_parser.parse_args()

    print(f"--- [Project Diophantus] Compilando: {args.input_file} ---")

    try:
        if not os.path.exists(args.input_file):
            raise FileNotFoundError(f"El archivo de entrada no existe: {args.input_file}")

        os.makedirs("output", exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(args.input_file))[0]

        # Rutas
        final_tex_path = os.path.join("output", f"{base_filename}_full_analysis.tex")
        interpreter_input_path = os.path.join("output", f"{base_filename}_interpreter_input.txt")

        # Legacy artifacts (Z3)
        pure_poly_path = os.path.join("output", f"{base_filename}_pure_poly_system.txt")
        logical_poly_path = os.path.join("output", f"{base_filename}_logical_poly_system.txt")
        generator_path = os.path.join("output", f"{base_filename}_generator_formulas.txt")
        putnam_path = os.path.join("output", f"{base_filename}_putnam_equation.txt")

        # Math artifacts
        math_formula_path = os.path.join("output", f"{base_filename}_mathematical_formula.txt")
        recurrence_path = os.path.join("output", f"{base_filename}_recurrence_system.txt")
        sage_script_path = os.path.join("output", f"{base_filename}_analysis_sage.sage")
        sympy_script_path = os.path.join("output", f"{base_filename}_analysis_sympy.py")

        # --- FASES ---
        print("\n[Fase 1-3] Analizando...")
        ast_map = parser.parse_c_file(args.input_file)
        unoptimized_f, input_vars, function_relations, overflow_triggered = generator.generate_function(ast_map)
        opt = optimizer.Optimizer(unoptimized_f)
        optimized_f, sub_defs = opt.optimize()

        print("\n[Fase 4] Convirtiendo a ecuaciones...")
        poly_conv = polynomial_converter.PolynomialConverter(
            optimized_f, sub_defs, ast_map['state_vars'], function_relations,
            bit_width=ast_map['config'].get('BIT_WIDTH', 32)
        )

        # PURE System
        pure_poly_system, function_definitions = poly_conv.convert(mode="PURE")
        all_pure_equations = []
        for f in function_definitions: all_pure_equations.extend(f['equations'])
        all_pure_equations.extend(pure_poly_system)

        # Validar que el sistema PURE se lee como objeto SymPy real (no string).
        try:
            from src.analysis import sympy_system
            _eqs, _syms = sympy_system.build_system(all_pure_equations)
            print(f"  [SymPy] Sistema PURE leído como objeto SymPy: "
                  f"{len(_eqs)} ecuaciones, {len(_syms)} variables.")
        except Exception as _e:
            print(f"  [SymPy] Aviso: no se pudo construir la representación SymPy "
                  f"({type(_e).__name__}: {_e}).")

        # LOGICAL System (Para Z3)
        logical_poly_system, logical_func_defs = poly_conv.convert(mode="LOGICAL")

        # Guardar LOGICAL (Crítico para legacy suite)
        logical_lines = []
        if logical_func_defs:
            logical_lines.append("--- DEFINICIONES ---")
            for f in logical_func_defs: logical_lines.extend(f['equations'])
            logical_lines.append("--- SISTEMA ---")
        logical_lines.extend(logical_poly_system)

        with open(logical_poly_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logical_lines))
        print(f"  -> Generado: {os.path.basename(logical_poly_path)}")

        # Guardar PURE
        with open(pure_poly_path, "w", encoding="utf-8") as f:
            f.write("\n".join(pure_poly_system)) # Simplificado para archivo

        print("\n[Fase 5] Generando matemáticas...")
        eq_exp = equation_exporter.EquationExporter(
            unoptimized_f, optimized_f, sub_defs, ast_map['state_vars'], function_relations
        )

        # Interpreter Input
        interpreter_content = eq_exp.export_optimized()
        with open(interpreter_input_path, "w", encoding="utf-8") as f: f.write(interpreter_content)

        # Math Formulas
        single_poly = eq_exp.export_single_polynomial(all_pure_equations).replace(" = 0", "")
        math_sym = eq_exp.export_formula_symbolic(single_poly)
        math_op = eq_exp.export_formula_operational(single_poly)
        rec_sys = eq_exp.export_recurrence_system()

        with open(math_formula_path, "w", encoding="utf-8") as f: f.write(math_sym + "\n\n" + math_op)
        with open(recurrence_path, "w", encoding="utf-8") as f: f.write(rec_sys)

        # CAS Scripts
        cas_exp = cas_exporter.CASExporter(all_pure_equations, ast_map['state_vars'])
        with open(sympy_script_path, "w", encoding="utf-8") as f: f.write(cas_exp.export_sympy_script())

        # [Fase 6] LaTeX
        poly_info = {'existential_vars_count': 0, 'num_equations': len(all_pure_equations)}
        latex_exp = latex_exporter.LatexExporter(
            unoptimized_f, optimized_f, sub_defs, ast_map['state_vars'], input_vars,
            pure_poly_system, eq_exp.export_single_polynomial(all_pure_equations),
            poly_info, function_definitions, logical_func_defs,
            math_formula_content_symbolic=math_sym,
            math_formula_content_operational=math_op,
            recurrence_content=rec_sys
        )
        with open(final_tex_path, "w", encoding="utf-8") as f: f.write(latex_exp.export_latex())

        if overflow_triggered:
            print("\n[presupuesto] La compilación truncó por presupuesto de "
                  "recursión. El sistema PURE ancla `overflow = 0`: las entradas "
                  "cuya traza cabe en DIOPHANTUS_MAX_RECURSION tienen solución con "
                  "el valor correcto, y las que lo exceden quedan sin solución en "
                  "vez de con un resultado incorrecto. Aumenta el presupuesto para "
                  "admitir trazas más largas.")

        print(f"\n[ÉXITO] Artefactos generados en output/")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1) # CÓDIGO DE SALIDA DE ERROR IMPORTANTE

if __name__ == "__main__":
    main()