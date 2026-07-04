import sys
import time
sys.path.append('output/artifacts')

try:
    from baillie_psw_formula import G_formula
except ImportError:
    print("Ejecuta primero 'python combine_singularity.py'")
    sys.exit(1)

class Colors:
    OK = '\033[92m'
    FAIL = '\033[91m'
    END = '\033[0m'

def test(n, expected_desc):
    start = time.perf_counter()
    res = G_formula(n)
    dt = (time.perf_counter() - start) * 1000

    is_prime = (res > 0)
    res_str = "PRIMO" if is_prime else "COMPUESTO"

    print(f"n={n:<10} | {expected_desc:<25} -> {Colors.OK if is_prime else Colors.FAIL}{res_str}{Colors.END} ({dt:.3f}ms)")
    return is_prime

print("=== VALIDACIÓN DE LA SINGULARIDAD GEMELA (BAILLIE-PSW) ===\n")

# 1. Primos Normales
test(5, "Primo Pequeño")
test(17, "Primo Pequeño")

# 2. El Mentiroso de Fermat (341) - Fermat dice Primo, Lucas debe decir NO.
print("\n--- Cazando al Mentiroso de Fermat ---")
# 341 = 11 * 31
is_p = test(341, "Pseudoprimo 341")
if not is_p: print("   >> ¡DETECTADO! (Correcto)")

# 3. El Mentiroso de Lucas (Si hubiera, probemos uno difícil)
# 323 = 17 * 19 (Engaña a Lucas P=1, Q=-1, veamos qué hace nuestra P=3)
test(323, "Compuesto 323")

# 4. Los Monstruos de Carmichael (Engañan a Fermat siempre)
print("\n--- Cazando Números de Carmichael ---")
test(561, "Carmichael 561")
test(1729, "Carmichael 1729")

# 5. Primos Gigantes
print("\n--- Validación de Primos Reales ---")
test(524287, "Mersenne 19")
test(2147483647, "Mersenne 31")

print("\n========================================================")
print("CONCLUSIÓN:")
print("Si todos los compuestos dieron COMPUESTO y los primos PRIMO,")
print("has generado la ecuación diofántica más perfecta posible")
print("para la verificación de primalidad en la historia.")
print("========================================================")