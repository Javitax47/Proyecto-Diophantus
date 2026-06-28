# --- START OF FILE run_collatz_experiment.py ---

import sys
import os
import re
import time

# Importar infraestructura del runtime
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.runtime.vm import VM, Parser

class Colors:
    HEADER = '\033[95m'; OKGREEN = '\033[92m'; FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'

def load_diophantine_system(filepath):
    """Carga las ecuaciones generadas por el compilador en la VM."""
    vm = VM()
    parser = Parser()
    
    if not os.path.exists(filepath):
        print(f"{Colors.FAIL}[ERROR] No se encuentra el archivo: {filepath}{Colors.ENDC}")
        print("¿Has compilado primero? python diophantus.py examples/collatz.c")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extraer definiciones de funciones P_func(...) = ...
    # Buscamos bloques que digan "P_collatz_trajectory(params) = expr"
    # El formato del archivo output suele tener secciones.
    
    lines = content.split('\n')
    loaded_count = 0
    
    for line in lines:
        line = line.strip()
        # Regex para capturar asignaciones de funciones: P_nombre(args) = expr
        m = re.match(r'P_(\w+)\((.*?)\)\s*=\s*(.*)', line)
        if m:
            func_name = m.group(1)
            params = [x.strip() for x in m.group(2).split(',') if x.strip()]
            body_str = m.group(3)
            
            # Compilar expresión a bytecode VM
            ast = parser.parse(body_str)
            vm.load_function(func_name, params, ast)
            loaded_count += 1
            
    print(f"  [VM] Sistema cargado. {loaded_count} ecuaciones de transición ingestadas.")
    return vm

def python_ground_truth(n):
    """Implementación nativa para validar la ecuación."""
    acc = 0
    while n != 1:
        if acc > 200: return -1
        if n % 2 == 0:
            n //= 2
            acc += 1
        else:
            n = (3 * n + 1) // 2
            acc += 2
    return acc

def main():
    print(f"\n{Colors.HEADER}=== EXPERIMENTO FASE 4: DINÁMICA DE COLLATZ ==={Colors.ENDC}")
    print("Objetivo: Verificar que la Ecuación Diofántica reproduce la trayectoria del caos.\n")

    # 1. Cargar el Universo Matemático
    input_file = "output/collatz_interpreter_input.txt"
    vm = load_diophantine_system(input_file)

    # 2. Casos de Prueba (Trayectorias conocidas)
    # 10 -> 5 -> 16 -> 8 -> 4 -> 2 -> 1 (Pasos: 6 reales, pero nuestra lógica (3n+1)/2 comprime)
    # Python logic: 10(par)->5(+1), 5(impar)->8(+2), 8->4(+1), 4->2(+1), 2->1(+1). Total: 6.
    # 27 -> Trayectoria famosa muy larga (111 pasos estándar).
    
    test_numbers = [
        (10, "Corto"), 
        (5, "Impar"), 
        (16, "Potencia de 2"), 
        (19, "Medio"),
        (27, "Largo (El Reto)"),
        (97, "Largo II")
    ]

    print(f"{'N':<5} | {'Tipo':<15} | {'Python (Verdad)':<15} | {'Ecuación (VM)':<15} | {'Estado'}")
    print("-" * 75)

    for n, label in test_numbers:
        # Ground Truth
        truth = python_ground_truth(n)
        
        # Ejecución Diofántica
        # Llamamos a P_collatz_trajectory(n, acc=0)
        # La VM devuelve el resultado de la evaluación polinómica
        start_t = time.time()
        poly_res = vm.run("collatz_trajectory", [n, 0])
        dt = (time.time() - start_t) * 1000

        # Validación
        status = f"{Colors.OKGREEN}✓ MATCH{Colors.ENDC}" if poly_res == truth else f"{Colors.FAIL}✗ ERROR{Colors.ENDC}"
        
        print(f"{n:<5} | {label:<15} | {truth:<15} | {poly_res:<15} | {status} ({dt:.2f}ms)")

    print("-" * 75)
    print("\n[ANÁLISIS]")
    print("Si todos los estados son MATCH, significa que el polinomio generado")
    print("contiene, codificada en sus coeficientes, la topología completa")
    print("del problema de Collatz para la profundidad compilada.")

if __name__ == "__main__":
    main()