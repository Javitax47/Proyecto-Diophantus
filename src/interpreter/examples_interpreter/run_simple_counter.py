import sys
import time
import os
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.interpreter.interpreter import get_engine

def main():
    parser = argparse.ArgumentParser(description="Ejecuta el contador simple usando el motor de ecuaciones.")
    parser.add_argument('base_path', nargs='?',
                        default=os.path.join(os.path.dirname(__file__), '../../../output/simple_counter'),
                        help='Ruta base al archivo compilado (sin extensión).')
    parser.add_argument('--mode', choices=['SEQUENTIAL', 'Z3_LOGICAL', 'Z3_PURE'],
                        default='SEQUENTIAL', help='Motor de ejecución a utilizar.')
    args = parser.parse_args()

    # 1. Obtener el motor desde la fábrica
    # Nota: get_engine añadirá la extensión correcta (.txt, _logical..., etc.)
    try:
        # Aseguramos que la ruta sea absoluta para evitar confusiones
        abs_path = os.path.abspath(args.base_path)
        engine = get_engine(args.mode, abs_path)
    except Exception as e:
        print(f"Error inicializando motor: {e}")
        print(f"Verifica que hayas compilado el ejemplo en: {args.base_path}")
        sys.exit(1)

    current_state = {'x': 0} # Estado inicial del contador

    print("\n--- Iniciando Simulación del Contador ---")
    print(f"Modo: {args.mode}")

    for i in range(20):
        print(f"Estado (t={i}): x = {current_state.get('x', 'N/A')}")

        # No hay entradas externas (teclado) para este programa
        inputs = {}

        try:
            next_state = engine.compute_next_state(current_state, inputs)
            current_state.update(next_state)
        except Exception as e:
            print(f"Error en cálculo: {e}")
            break

        time.sleep(0.2)

if __name__ == "__main__":
    main()