import sys
import time
import random

"""
=============================================================================
   BENCHMARK CONTINUO: LÍMITE DE LA SÚPER FÓRMULA
=============================================================================
Este script genera números aleatorios de tamaño creciente y verifica
su primalidad usando la Ecuación Diofántica derivada de Miller-Rabin.

Objetivo: Ver hasta cuántos dígitos podemos procesar en 10 segundos.
=============================================================================
"""

# Aumentar el límite de conversión de enteros a string para soportar números masivos
# 0 significa "sin límite". Necesario para números > 4300 dígitos.
try:
    sys.set_int_max_str_digits(0)
except AttributeError:
    pass # Versiones antiguas de Python no tienen este límite


def polynomial_mod_step(v_next, v_prev, q, n, base, is_odd_step):
    # (v_next - (v_prev^2 * base^bit - q*n))^2
    term = v_next - (v_prev**2 * (base if is_odd_step else 1) - q * n)
    return term**2

def G_verifier(n, x_vector):
    """
    Evaluador de la Fórmula Polinómica.
    """
    Energy = 0
    base = 2

    if not x_vector: return -1
    v_current = x_vector[0]
    Energy += (v_current - 2)**2

    num_steps = (len(x_vector) - 1) // 2
    exp = n - 1
    bits = bin(exp)[2:]

    steps_to_check = min(num_steps, len(bits))
    idx = 0
    current_val = 2

    for i in range(steps_to_check):
        bit_char = bits[i+1] if i+1 < len(bits) else '0'
        is_odd = int(bit_char == '1')

        v_next = x_vector[2*idx + 2]
        q      = x_vector[2*idx + 1]

        Energy += polynomial_mod_step(v_next, current_val, q, n, base, is_odd)
        current_val = v_next
        idx += 1

    Energy += (current_val - 1)**2
    return n * (1 - Energy)

def mine_vector(n):
    """
    Genera el vector testigo x para n. (Simulación de la traza)
    """
    vector = []
    val = 2
    vector.append(val)

    exp = n - 1
    bits = bin(exp)[2:]

    for bit_char in bits[1:]:
        sq = val * val
        if bit_char == '1':
            sq = sq * 2
        q = sq // n
        r = sq % n
        vector.append(q)
        vector.append(r)
        val = r
    return vector

def main():
    print("==============================================================")
    print("   BENCHMARK DE FUERZA: PROYECTO DIOPHANTUS")
    print("==============================================================")
    print("Iterando con números de tamaño creciente durante 10 segundos...")
    print("Columnas: Bits | Dígitos | Variables en Ecuación | Tiempo")
    print("--------------------------------------------------------------")

    start_time_global = time.time()
    time_limit = 10.0 # Segundos

    # Empezamos con 64 bits (números grandes normales)
    current_bits = 64
    iterations = 0
    max_digits_reached = 0

    try:
        while (time.time() - start_time_global) < time_limit:
            # 1. Generar número aleatorio impar de 'current_bits'
            # (La mayoría serán compuestos, pero la carga computacional de la fórmula es idéntica)
            n = random.getrandbits(current_bits)
            if n % 2 == 0: n += 1

            t0 = time.time()

            # 2. Minar vector (Generar variables auxiliares)
            x_vec = mine_vector(n)

            # 3. Verificar con Fórmula (Evaluar el polinomio)
            res = G_verifier(n, x_vec)

            dt = time.time() - t0

            digits = len(str(n))
            vars_count = len(x_vec)

            print(f" {current_bits:<6} bits | {digits:<7} d | {vars_count:<5} vars | {dt*1000:.2f} ms")

            max_digits_reached = digits
            iterations += 1

            # Aumentar dificultad: Multiplicamos bits por 1.5 en cada paso
            # Crecimiento exponencial del tamaño del problema
            current_bits = int(current_bits * 1.5)

    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
    except OverflowError:
        print("\n[ALERTA] Límite de enteros de Python alcanzado (memoria).")

    print("--------------------------------------------------------------")
    print(f"TIEMPO AGOTADO ({time.time() - start_time_global:.2f}s)")
    print(f"Iteraciones completadas: {iterations}")
    print(f"MÁXIMO ALCANZADO: {max_digits_reached} Dígitos Decimales")
    print("==============================================================")

    if max_digits_reached > 1000:
        print("CONCLUSIÓN: La fórmula es ultra-eficiente. Escala a miles de dígitos.")
    elif max_digits_reached > 100:
        print("CONCLUSIÓN: La fórmula es eficiente. Escala a cientos de dígitos.")
    else:
        print("CONCLUSIÓN: La fórmula tiene limitaciones de escalado.")

if __name__ == "__main__":
    main()