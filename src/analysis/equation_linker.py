import sys
import os
import argparse

def generate_linker_script(files, input_var):
    combined_code = "import sys\n\n"

    # Metadata con caracteres Unicode
    combined_code += f"""
__LATEX_REPR__ = [
    "THEOREM: The Twin Singularity (Diophantine Form)",
    "∃ k_1, k_2 ∈ Z  s.t.  P({input_var}) = 0",
    "",
    "   P({input_var}) = ( 2^({input_var}-1) - 1 - k_1·{input_var} )²  +  ( D_{{{input_var}}}(3) - 3 - k_2·{input_var} )²",
    "",
    "   Where D_n(x) is the Dickson Polynomial (Chebyshev Type I).",
    "   Status: P({input_var})=0 => {input_var} is Prime (Definitive)"
]
"""
    combined_code += "# FUSIÓN DE ENERGÍAS\n"
    terms = []

    for i, fpath in enumerate(files):
        # LEER CON UTF-8 IMPLÍCITO
        with open(fpath, 'r', encoding='utf-8') as f:
            code = f.read()

        # Namespace Isolation
        code = code.replace("__LATEX_REPR__", f"__META_{i}__")
        code = code.replace("dickson_eval", f"d_{i}")
        code = code.replace("ec_point_mul_proj", f"ec_{i}")
        code = code.replace("G_formula", f"G_{i}")

        combined_code += f"\n# --- {os.path.basename(fpath)} ---\n{code}\n"
        terms.append(f"G_{i}({input_var})")

    energy_expr = " + ".join(terms)
    combined_code += f"""
def G_formula({input_var}):
    return {energy_expr}
"""
    return combined_code

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs='+', required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--var", default="n")
    args = parser.parse_args()

    content = generate_linker_script(args.inputs, args.var)
    out_path = os.path.join("output/artifacts", args.output)

    # ESCRITURA UTF-8 BLINDADA
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Linker -> {out_path}")

if __name__ == "__main__":
    main()