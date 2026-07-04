import os
import sys
# Ajustar el path para encontrar verifier_main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from verifier_main import run_verification

# --- CONFIGURACIÓN PARA DETECTAR GOL ---
# Buscamos demostrar que es posible que f aumente (Gol izquierda)
CONFIG = {
    "TARGET_FILE": "../../examples/pong.c",
    "VERIFICATION_TYPE": "SEQUENTIAL",

    # Condición de éxito: La puntuación futura es mayor que la actual
    "BUG_CONDITION": "(f_t1 > f)",

    # Pasos suficientes para que la pelota vaya de x=2 a x<1
    "K_STEPS": 5,

    # ESTADO INICIAL "TELETRANSPORTADO"
    # Colocamos la pelota muy cerca del borde (b=2) y moviéndose hacia él (d=-1)
    # para que Z3 la encuentre rápido.
    "INITIAL_STATE": {
        'b': 2,    # X cerca del borde izquierdo
        'c': 12,   # Y válido
        'd': -1,   # Velocidad negativa (hacia la izquierda)
        'e': 0,
        'p': 10,
        'q': 10,
        'f': 0,
        'g': 0
    },

    "OUTPUT_FILE": "../../output/pong_verification_report_SEQUENTIAL.tex",

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