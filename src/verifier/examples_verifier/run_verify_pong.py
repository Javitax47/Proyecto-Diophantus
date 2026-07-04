import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.verifier.verifier_main import run_verification

# --- LÍMITES FÍSICOS DEL JUEGO (Acotación de Variables) ---
# Usamos esto para reducir el espacio de búsqueda infinito de Z3.
# --- VERIFICACIÓN DE LÓGICA DE PUNTUACIÓN ---
CONFIG = {
    # 1. Archivo del Sistema (Elige el modo rápido/LÓGICO)
    "SYSTEM_FILE": "output/pong_logical_poly_system.txt",

    # 2. Variables del Sistema (Extraídas de pong.c)
    "STATE_VARS": ['b', 'c', 'd', 'e', 'f', 'g', 'p', 'q'],
    "INPUT_VARS": ['getch', 'kbhit'],

    # 3. Configuración del Verificador (sin cambios en este ejemplo)
    "VERIFICATION_TYPE": "SEQUENTIAL",
    "BUG_CONDITION": "(f_t1 > f)",
    "K_STEPS": 3,
    "INITIAL_STATE": {
        'b': 1,     # Pelota en el límite izquierdo (a punto de salir)
        'd': -1,    # Moviéndose hacia la izquierda (hacia el vacío)
        'c': 12, 'e': 0, 'p': 10, 'q': 1, 'f': 0, 'g': 0
    },
    "OUTPUT_FILE": "output/pong_verification_report_SEQUENTIAL.tex",

    # En BOUNDS, mantenemos solo las entradas y el estado ACTUAL.
    # Dejamos f_t1 libre para que la BUG_CONDITION haga el filtrado inteligente.
    "BOUNDS": {
        "b": {"min": 0, "max": 80},
        "c": {"min": 0, "max": 24},
        "p": {"min": 0, "max": 24},
        "q": {"min": 0, "max": 24},
        "d": {"min": -1, "max": 1},
        "e": {"min": -1, "max": 1},
        "f": {"min": 0, "max": 100},
        "g": {"min": 0, "max": 100},
        "kbhit": {"min": 0, "max": 1},
        "getch": {"min": 0, "max": 255}
    },
}

if __name__ == "__main__":
    run_verification(CONFIG)