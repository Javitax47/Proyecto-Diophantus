import itertools

def G(n, x):
    # Mapeo del vector x a las variables de tu formula
    # x es una lista de 16 enteros [x0...x15]
    # Ajustamos índices (Python 0-based vs Math 1-based)

    # Termino A: Suma de cuadrados que deben ser 0
    # Indices visuales: 1, 2, 3, 6, 7, 11, 14, 15 -> Python: 0, 1, 2, 5, 6, 10, 13, 14
    A = (x[0]**2 + x[1]**2 + x[2]**2 + x[5]**2 + x[6]**2 + x[10]**2 + x[13]**2 + x[14]**2)

    # Termino B: Restricción de diferencia = 2
    # Positivos: 5, 9, 10, 13 -> Python: 4, 8, 9, 12
    sum_pos = x[4]**2 + x[8]**2 + x[9]**2 + x[12]**2

    # Negativos: 4, 8, 12, 16 -> Python: 3, 7, 11, 15
    sum_neg = x[3]**2 + x[7]**2 + x[11]**2 + x[15]**2

    # Nota: En tu output original B era (-sum_neg + sum_pos - 2).
    # Al cuadrado da igual el signo global.
    B = (-sum_neg + sum_pos - 2)

    # Polinomio Putnam
    return n * (1 - (A**2 + B**2))

print("--- MINANDO PRIMOS CON LA SÚPER FÓRMULA ---")
print("Buscando vector x tal que G(n, x) > 0...")

target_n = 5 # Primo
print(f"\nObjetivo: n = {target_n}")

# Búsqueda bruta pequeña (heurística)
# Como A fuerza a muchos a ser 0, fijamos esos a 0 y buscamos el resto.
# Variables libres reales: 3, 4, 7, 8, 9, 11, 12, 15 (indices python)
found = False
search_range = 10 # Rango pequeño para prueba rápida

# Generador de combinaciones para las 8 variables libres
for val in itertools.product(range(search_range), repeat=8):
    # Construir vector completo
    x_vec = [0] * 16
    # Asignar valores a las variables libres (B component)
    x_vec[3] = val[0]; x_vec[4] = val[1]
    x_vec[7] = val[2]; x_vec[8] = val[3]
    x_vec[9] = val[4]; x_vec[11] = val[5]
    x_vec[12] = val[6]; x_vec[15] = val[7]

    res = G(target_n, x_vec)

    if res > 0:
        print(f"¡ÉXITO! Vector encontrado: {x_vec}")
        print(f"G({target_n}, x) = {res}")
        found = True
        break

if not found:
    print("No se encontró solución en el rango de búsqueda simple.")
    print("(Esto es normal, las soluciones diofánticas pueden ser números grandes)")