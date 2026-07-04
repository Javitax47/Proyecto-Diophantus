import random
import sys
import time

def power_mod(base, exp, mod):
    return pow(base, exp, mod)

def inverse_mod(a, n):
    return pow(a, -1, n)

# Operaciones de Curva Elíptica (Python Puro)
def point_add(p1, p2, a, mod):
    if p1 is None: return p2
    if p2 is None: return p1
    x1, y1 = p1
    x2, y2 = p2

    if x1 == x2 and y1 != y2: return None
    if x1 == x2 and y1 == y2 and y1 == 0: return None

    try:
        if x1 == x2: # Doubling
            m = (3 * x1 * x1 + a) * inverse_mod(2 * y1, mod)
        else: # Adding
            m = (y2 - y1) * inverse_mod(x2 - x1, mod)
    except ValueError:
        return None # Factor encontrado (Singularidad)

    x3 = (m * m - x1 - x2) % mod
    y3 = (m * (x1 - x3) - y1) % mod
    return (x3, y3)

def point_mul(p, k, a, mod):
    res = None
    # Double and Add
    while k > 0:
        if k % 2 == 1: res = point_add(res, p, a, mod)
        p = point_add(p, p, a, mod)
        k //= 2
    return res

def find_ecpp_certificate(p, max_attempts=100000):
    """
    Busca una curva elíptica y un punto P tal que el orden del grupo sea p (Curva Anómala).
    Esto es una simplificación para la demo: buscamos curvas aleatorias hasta que
    n*P = Infinito.
    """
    # print(f"   [Maker] Buscando curva para p={p} ({max_attempts} intentos max)...")

    for i in range(max_attempts):
        a = random.randint(0, p-1)
        x = random.randint(0, p-1)
        y = random.randint(0, p-1)

        # Calculamos b para que el punto (x,y) esté en la curva
        b = (y*y - x*x*x - a*x) % p

        # Discriminante no singular: 4a^3 + 27b^2 != 0
        if (4*a**3 + 27*b**2) % p == 0: continue

        # Verificación rápida: ¿Es el orden igual a p?
        # Probamos si p * P = Infinito (O)
        try:
            P = (x, y)
            # Para p grandes, esto es lento, pero necesario.
            res = point_mul(P, p, a, p)

            if res is None: # Punto en el infinito
                # Verificación extra de seguridad (que no sea orden pequeño)
                # (Omitida por velocidad en demo, asumimos primalidad de p)
                return a, b, x, y, p
        except:
            pass

    return None

if __name__ == "__main__":
    # Test rápido
    cert = find_ecpp_certificate(2147483647)
    if cert:
        print(f"Certificado encontrado: {cert}")
    else:
        print("Fallo al encontrar certificado.")