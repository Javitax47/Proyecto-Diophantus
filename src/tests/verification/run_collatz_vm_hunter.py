import sys
import os
import time
import re

# Importar VM
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.runtime.vm import VM, Parser

class Colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def load_vm():
    vm = VM()
    parser = Parser()
    filepath = "output/collatz_cycle_interpreter_input.txt"

    if not os.path.exists(filepath):
        print("Error: No existe el archivo compilado.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Cargar funciones P_...
    count = 0
    for line in content.split('\n'):
        m = re.match(r'P_(\w+)\((.*?)\)\s*=\s*(.*)', line.strip())
        if m:
            name, params, body = m.group(1), m.group(2), m.group(3)
            p_list = [x.strip() for x in params.split(',') if x.strip()]
            vm.load_function(name, p_list, parser.parse(body))
            count += 1

    if count == 0:
        print("Error: No se encontraron funciones en el archivo.")
        sys.exit(1)

    return vm

def sanity_check(vm):
    print("\n--- [1] TEST DE CORDURA (SANITY CHECK) ---")

    # TRUCO: Inyectamos un estado donde YA hemos encontrado el ciclo.
    # Función: detect_cycle_recursive(n, original, steps)
    # Lógica C: if (n == original && steps > 0) return 1;

    print("  a. Inyectando ciclo falso (n=5, original=5, steps=10)...", end=" ")
    res_fake = vm.run("detect_cycle_recursive", [5, 5, 10])

    if res_fake == 1:
        print(f"{Colors.OKGREEN}PASÓ (Devolvió 1){Colors.ENDC}")
        print("     -> Conclusión: La lógica de detección de ciclos FUNCIONA.")
    else:
        print(f"{Colors.FAIL}FALLÓ (Devolvió {res_fake}){Colors.ENDC}")
        print("     -> Peligro: La VM no está ejecutando la condición de éxito.")
        sys.exit(1)

    # TRUCO 2: Probamos un número que sabemos que va a 1 (ej: 2)
    print("  b. Probando convergencia normal (n=2)...", end=" ")
    res_normal = vm.run("detect_cycle_recursive", [2, 2, 0])
    # 2 -> 1 (Atractor). Debe devolver 0.

    if res_normal == 0:
        print(f"{Colors.OKGREEN}PASÓ (Devolvió 0){Colors.ENDC}")
        print("     -> Conclusión: La convergencia a 1 se detecta correctamente.")
    else:
        print(f"{Colors.FAIL}FALLÓ (Devolvió {res_normal}){Colors.ENDC}")
        sys.exit(1)

    print(f"{Colors.OKGREEN}>>> SISTEMA COMPLETAMENTE OPERATIVO. INICIANDO CAZA. <<<{Colors.ENDC}\n")

def main():
    print("=== COLLATZ CYCLE HUNTER (VM ENGINE) ===")
    print("Motor: Ejecución Polinómica Estricta")
    print("Objetivo: Encontrar n tal que detect_cycle(n, n, 0) == 1")
    print("----------------------------------------")

    vm = load_vm()

    # Verificar que el cerebro no está lobotomizado
    sanity_check(vm)

    # Rango de Búsqueda
    start = 5
    end = 500000

    t0 = time.time()
    count = 0

    print("--- [2] INICIANDO BARRIDO SECUENCIAL ---")

    try:
        for n in range(start, end):
            # Ejecución Real
            res = vm.run("detect_cycle_recursive", [n, n, 0])

            # Caso Éxito (Contraejemplo encontrado)
            if res == 1:
                print(f"\n{Colors.FAIL}[!!!] ¡CONTRAEJEMPLO ENCONTRADO! n = {n}{Colors.ENDC}")
                print(f"¡La Conjetura de Collatz es FALSA para n={n}!")
                break

            # Latido cada 2500 números
            count += 1
            if count % 2500 == 0:
                elapsed = time.time() - t0
                rate = count / elapsed
                # Imprimimos explícitamente que el resultado fue 0 para confirmar proceso
                print(f"  [Scan] n={n:<7} | Resultado VM: {Colors.BOLD}{res}{Colors.ENDC} (Converge) | {rate:.0f} ops/s")

    except KeyboardInterrupt:
        print("\nDetenido por usuario.")

    dt = time.time() - t0
    print(f"\nResumen: {count} números verificados en {dt:.2f}s")

if __name__ == "__main__":
    main()