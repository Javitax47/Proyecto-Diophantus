import sys
import os
import time
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.interpreter.interpreter import get_engine

def main():
    parser = argparse.ArgumentParser(description="Ejecuta el Buscador de Primos Optimizado.")
    parser.add_argument('--mode', choices=['SEQUENTIAL', 'Z3_LOGICAL', 'Z3_PURE'], 
                        default='SEQUENTIAL', help='Motor de ejecución a utilizar.')
    args = parser.parse_args()

    # Ruta base apuntando a la salida de primes
    base_path = os.path.join(os.path.dirname(__file__), '../../../output/primes')

    # 1. Obtener el motor
    try:
        engine = get_engine(args.mode, base_path)
    except Exception as e:
        print(f"Error inicializando motor: {e}")
        print(f"¿Has compilado 'examples/primes.c'?")
        sys.exit(1)
    
    # Estado inicial (coincide con las variables globales de primes.c)
    current_state = {
        'n': 1, 
        'd': 3, 
        'r': 0, 
        'state': 0, 
        'found_prime': 2
    }
    
    print(f"\n--- BUSCADOR DE PRIMOS DIOPHANTUS ({args.mode}) ---")
    print("Iniciando búsqueda... (Ctrl+C para detener)")
    time.sleep(1)

    last_prime = 2
    steps = 0
    start_time_total = time.time()

    try:
        while True:
            # 2. Inputs (No hay inputs externos en este algoritmo)
            inputs = {}
            
            # 3. Calcular Siguiente Estado
            # El motor resuelve las ecuaciones polinómicas para avanzar un paso
            next_state = engine.compute_next_state(current_state, inputs)
            current_state.update(next_state)
            steps += 1
            
            # 4. Detectar hallazgo (Cambio en la variable de salida)
            current_prime = current_state.get('found_prime', 0)
            
            if current_prime != last_prime:
                elapsed = time.time() - start_time_total
                print(f"[HITO] ¡Nuevo Primo Hallado! >> {current_prime} << (Paso: {steps}, T: {elapsed:.2f}s)")
                last_prime = current_prime

            # No usamos sleep en SEQUENTIAL para ir a máxima velocidad.
            # Z3 modes son lentos por naturaleza.

    except KeyboardInterrupt:
        print(f"\nBúsqueda detenida. Último candidato evaluado: {current_state.get('n')}")
    except RuntimeError as e:
        print(f"\n[Crash Matemático] {e}")

if __name__ == "__main__":
    main()