import subprocess
import sys
import os

def run(cmd):
    if cmd.startswith("python "):
        cmd = f'"{sys.executable}"' + cmd[6:]
    print(f"[$] {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("=== GENERANDO EL ESPECTRO COMPLETO (CON SOLOVAY) ===")

    # 1. FERMAT (Base 2)
    print("\n--- [1] Generando FERMAT ---")
    run("python diophantus.py src/examples/fermat.c")
    run('python src/analysis/deep_optimizer.py output/fermat_analysis_sympy.py --inputs "n,is_prime" --anchor "is_prime=1"')
    run("python src/analysis/math_kernels.py output/artifacts/fermat_formula.py --type fermat --var n")

    # 2. MILLER-RABIN
    print("\n--- [2] Generando MILLER-RABIN ---")
    run("python diophantus.py src/examples/primes_innovative.c")
    run('python src/analysis/deep_optimizer.py output/primes_innovative_analysis_sympy.py --inputs "n,is_prime" --anchor "is_prime=1"')

    # 3. LUCAS
    print("\n--- [3] Generando LUCAS ---")
    run("python diophantus.py src/examples/primes_lucas.c")
    # Nota: Lucas usa kernel directo, el deep_opt es un trámite para tener el archivo base
    run('python src/analysis/deep_optimizer.py output/primes_lucas_analysis_sympy.py --inputs "n,result" --anchor "result=0"')
    run("python src/analysis/math_kernels.py output/artifacts/primes_lucas_formula.py --type lucas --var n")

    # 4. SOLOVAY-STRASSEN
    print("\n--- [4] Generando SOLOVAY-STRASSEN ---")
    run("python diophantus.py src/examples/primes_solovay_64.c")
    # Solovay devuelve 0 errores si es primo. Inputs: target. Anchor: result=0.
    run('python src/analysis/deep_optimizer.py output/primes_solovay_64_analysis_sympy.py --inputs "target,result" --anchor "result=0"')

    # 5. ECPP (Geometría)
    print("\n--- [5] Generando ECPP ---")
    run("python diophantus.py src/examples/primes_ecpp_final.c")
    run("python src/analysis/math_kernels.py output/artifacts/primes_ecpp_final_formula.py --type ecpp --var n")

    # 6. BAILLIE-PSW (Linker)
    print("\n--- [6] Enlazando Baillie-PSW ---")
    run("python src/analysis/equation_linker.py --inputs output/artifacts/fermat_fermat_closed.py output/artifacts/primes_lucas_lucas_closed.py --output baillie_psw_formula.py")

    print("\n[OK] Generación Completa.")

if __name__ == "__main__":
    main()