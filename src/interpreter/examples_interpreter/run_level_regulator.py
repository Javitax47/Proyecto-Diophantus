import sys
import os
import time
import argparse

# Entrada de teclado portable: msvcrt en Windows; en otros SO se degrada a "sin teclado"
# (el panel sigue ejecutándose) en lugar de fallar al importar.
try:
    import msvcrt

    def kb_hit():
        return msvcrt.kbhit()

    def kb_get():
        return msvcrt.getch()
    KEYBOARD = True
except ImportError:
    def kb_hit():
        return False

    def kb_get():
        return b''
    KEYBOARD = False

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.interpreter.interpreter import get_engine

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_dashboard(state, step, mode):
    """
    Renderiza el tablero de control y las instrucciones.
    """
    clear_screen()
    level = state.get('level', 0)
    rate = state.get('rate', 0)
    throttle = state.get('throttle_input', 0)

    print(f"--- SIMULACIÓN DE REGULADOR DE NIVEL (Paso {step}) ---")
    print(f"Motor: {mode} | Project Diophantus\n")

    # Visualización del Tanque Gráfica
    max_bar = 20
    # Escalamos para que se vea bien incluso con niveles negativos (underflow)
    display_level = max(0, min(100, level))
    bar_fill = int((display_level / 100) * max_bar)
    bar_str = "█" * bar_fill + "░" * (max_bar - bar_fill)

    print(f"NIVEL:    [{bar_str}] {level}")
    print(f"CONSUMO:  {rate} unidades/frame")

    # Visualización del Throttle (Válvula)
    status = "APAGADO (0)" if throttle == 0 else f"ENCENDIDO (Nivel {throttle})"
    print(f"VÁLVULA:  {status}")

    print("\n" + "="*40)
    print(" CONTROLES EN TIEMPO REAL:")
    print(" [0]     -> Cerrar Válvula")
    print(" [1]-[5] -> Abrir Válvula (Nivel 1-5)")
    print(" [Q]     -> Salir")
    print("="*40)

    print("\n--- Estado del Sistema ---")
    if level < 0:
        print(">>> ALERTA CRÍTICA: ¡UNDERFLOW DEL TANQUE DETECTADO! <<<")
    elif level < 10:
        print("AVISO: Nivel Bajo. El sistema aumentará el consumo automáticamente.")
    elif throttle == 0:
        print("ESTADO: En espera (Válvula cerrada, el nivel se mantiene).")
    else:
        print("ESTADO: Operativo (Consumiendo recursos).")

def main():
    parser = argparse.ArgumentParser(description="Ejecuta el regulador de nivel.")
    parser.add_argument('--mode', choices=['SEQUENTIAL', 'Z3_LOGICAL', 'Z3_PURE'],
                        default='SEQUENTIAL', help='Motor de ejecución a utilizar.')
    args = parser.parse_args()

    # Ruta base por defecto (ajustar si la estructura de carpetas cambia)
    base_path = os.path.join(os.path.dirname(__file__), '../../../output/level_regulator')

    # 1. Inicializar el Motor usando la factoría
    try:
        engine = get_engine(args.mode, base_path)
    except Exception as e:
        print(f"Error inicializando motor: {e}")
        print(f"Asegúrate de haber compilado 'examples/level_regulator.c' en: {base_path}")
        sys.exit(1)

    # 2. Definir Estado Inicial
    current_state = {
        'level': 100,  # Empezamos llenos para probar
        'rate': 6,
        'throttle_input': 0 # Empezamos apagados
    }

    print("Iniciando simulación interactiva...")
    time.sleep(1)

    step = 0
    try:
        while True:
            # 3. Renderizar
            render_dashboard(current_state, step, args.mode)

            # 4. Gestión de Entradas (Teclado)
            if kb_hit():
                key = kb_get()
                try:
                    # Intentar decodificar la tecla
                    char = key.decode('utf-8').lower()

                    if char == 'q':
                        print("\nSaliendo...")
                        break

                    # Control numérico del throttle
                    if char in '012345':
                        new_val = int(char)
                        # Inyectamos el valor directamente en el estado actual
                        current_state['throttle_input'] = new_val

                except:
                    pass # Ignorar teclas especiales

            # 5. Calcular Siguiente Estado
            # Pasamos inputs vacío porque throttle_input es una variable de estado en este modelo C
            try:
                next_state = engine.compute_next_state(current_state, {})
                current_state.update(next_state)
            except RuntimeError as e:
                 print(f"\n[Crash del Motor] {e}")
                 break

            step += 1

            # Velocidad de simulación
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nSimulación detenida por el usuario.")

if __name__ == "__main__":
    main()