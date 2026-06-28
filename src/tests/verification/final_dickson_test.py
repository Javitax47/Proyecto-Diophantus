import sys
import os
import time
import importlib.util

# Configuración visual
class Colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m' # Rojo para fallo grave
    WARN = '\033[93m' # Amarillo para "Mentira detectada" (Falso Positivo)
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# --- CARGADOR DINÁMICO DE ARTEFACTOS ---
def load_formula(filename, func_name="G_formula"):
    path = os.path.join("output", "artifacts", filename)
    if not os.path.exists(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location("mod_" + filename.replace(".", ""), path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, func_name):
            return getattr(mod, func_name)
        # Fallback para Lucas que tenía nombre distinto
        if hasattr(mod, "Diophantus_Lucas_Formula"):
            return getattr(mod, "Diophantus_Lucas_Formula")
        return None
    except Exception as e:
        print(f"Error cargando {filename}: {e}")
        return None

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}================================================================{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}   DICKSON TEST SUITE: LA BATALLA DE LOS POLINOMIOS{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}================================================================{Colors.ENDC}")
    print(" Comparando las 3 Ecuaciones Generadas:")
    print(" 1. FERMAT (Rápida, insegura)")
    print(" 2. LUCAS  (Robusta, ortogonal)")
    print(" 3. BAILLIE-PSW (La Singularidad Unificada)\n")

    # 1. Cargar las Armas
    f_fermat = load_formula("primes_innovative_dickson_final.py")
    f_lucas  = load_formula("diophantus_lucas_formula.py")
    f_bpsw   = load_formula("baillie_psw_formula.py")

    if not f_bpsw:
        print(f"{Colors.FAIL}[CRÍTICO] No se encontró la fórmula final 'baillie_psw_formula.py'.{Colors.ENDC}")
        print("Ejecuta 'python combine_singularity_fixed.py' primero.")
        sys.exit(1)

    # 2. El Zoo de Números (Casos de Prueba)
    test_cases = [
        # (Número, Es_Primo, Descripción)
        (5, True, "Primo Pequeño"),
        (17, True, "Primo Fermat"),
        (4, False, "Compuesto Par"),
        (9, False, "Compuesto Impar"),
        # Los Mentirosos
        (341, False, "Pseudoprimo 341 (Fermat Liar)"),
        (561, False, "Carmichael 561 (El Rey Mentiroso)"),
        (2047, False, "Compuesto 2047 (23*89)"),
        # Los Gigantes
        (65537, True, "Fermat F4"),
        (524287, True, "Mersenne 19"),
        (2147483647, True, "Mersenne 31 (10 dígitos)")
    ]

    # Cabecera de la Tabla
    print(f"{'NUMERO':<12} | {'REALIDAD':<10} || {'FERMAT':<12} | {'LUCAS':<12} || {'BAILLIE-PSW':<15}")
    print("-" * 85)

    total_checks = 0
    bpsw_errors = 0

    for n, is_prime_truth, desc in test_cases:
        # Evaluar Fermat
        res_f = f_fermat(n) if f_fermat else 0
        is_p_f = res_f > 0
        
        # Evaluar Lucas
        res_l = f_lucas(n) if f_lucas else 0
        is_p_l = res_l > 0
        
        # Evaluar Baillie-PSW (La Final)
        t0 = time.time()
        res_b = f_bpsw(n)
        dt_b = (time.time() - t0) * 1000
        is_p_b = res_b > 0

        # --- Formateo de Resultados ---
        
        # Función auxiliar para colorear la salida
        def fmt(pred, truth):
            txt = "PRIMO" if pred else "COMP."
            if pred == truth:
                return f"{Colors.OKGREEN}{txt}{Colors.ENDC}"
            else:
                return f"{Colors.WARN}{txt} (Miente){Colors.ENDC}" # Amarillo para falso positivo

        out_f = fmt(is_p_f, is_prime_truth) if f_fermat else "N/A"
        out_l = fmt(is_p_l, is_prime_truth) if f_lucas else "N/A"
        
        # Baillie-PSW es especial, si falla es rojo (error grave), no amarillo
        if is_p_b == is_prime_truth:
            out_b = f"{Colors.OKGREEN}{Colors.BOLD}{'PRIMO' if is_p_b else 'COMP.'}{Colors.ENDC}"
        else:
            out_b = f"{Colors.FAIL}{Colors.BOLD}FALLO{Colors.ENDC}"
            bpsw_errors += 1

        truth_str = "PRIMO" if is_prime_truth else "COMP."
        
        print(f"{n:<12} | {truth_str:<10} || {out_f:<21} | {out_l:<21} || {out_b:<25} ({dt_b:.3f}ms)")

    print("-" * 85)
    
    if bpsw_errors == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}>>> RESULTADO FINAL: ÉXITO ABSOLUTO <<<{Colors.ENDC}")
        print("La Ecuación Baillie-PSW ha superado todas las pruebas.")
        print("Se ha verificado que corrige los errores de Fermat (341, 561) automáticamente.")
    else:
        print(f"\n{Colors.FAIL}>>> ALERTA: LA ECUACIÓN FINAL FALLÓ EN {bpsw_errors} CASOS <<<{Colors.ENDC}")

if __name__ == "__main__":
    main()