import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.verifier.verifier_main import run_verificationion

# --- CONFIGURACIÓN DE VERIFICACIÓN ---
CONFIG = {
    # 1. Archivo del Sistema
    # Usamos el sistema LÓGICO porque la aritmética de divisiones/restas es compleja 
    # y queremos una respuesta rápida para ver si la lógica funciona.
    "SYSTEM_FILE": "output/primes_optimized_logical_poly_system.txt",

    # 2. Variables del Sistema (Extraídas de primes_optimized.c)
    "STATE_VARS": ['n', 'd', 'r', 'state', 'found_prime'],
    "INPUT_VARS": [], # No hay inputs externos

    # 3. Configuración del Verificador
    "VERIFICATION_TYPE": "SEQUENTIAL",
    "K_STEPS": 20,  # Pasos suficientes para que el algoritmo pase de 5 a 7
    
    # PREGUNTA: ¿Puede el programa encontrar el primo 7?
    # Buscamos un estado futuro donde found_prime sea 7.
    "BUG_CONDITION": "(found_prime == 7)", 

    # Estado inicial (Justo después de encontrar el 5, por ejemplo, o desde el inicio)
    # Aquí iniciamos desde cero para probar los primeros ciclos.
    "INITIAL_STATE": {
        'n': 1, 'd': 3, 'r': 0, 'state': 0, 'found_prime': 2
    },
    
    "OUTPUT_FILE": "output/primes_optimized_verification_report.tex",
    
    # LÍMITES FÍSICOS (BOUNDS)
    # Acotamos las variables para ayudar a Z3 a no buscar en el infinito.
    "BOUNDS": {
        "n": {"min": 0, "max": 20},
        "d": {"min": 0, "max": 20},
        "r": {"min": 0, "max": 20},
        "state": {"min": 0, "max": 4},
        "found_prime": {"min": 0, "max": 20}
    },
}

if __name__ == "__main__":
    print("Verificando si la lógica matemática puede derivar el primo 7...")
    run_verification(CONFIG)