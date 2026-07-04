import sys
import sys
# Añadir rutas para encontrar el artefacto y las utils
sys.path.append('output/artifacts')
sys.path.append('tests/utils')

try:
    # Importamos tu nueva creación (ajusta el nombre si es diferente)
    from primes_ecpp_final_ecpp_closed import G_formula
    from ecpp_certificate_maker import find_ecpp_certificate
except ImportError as e:
    print(f"Error de importación: {e}")
    print("Asegúrate de que el archivo generado se llame 'primes_ecpp_final_ecpp_closed.py'")
    sys.exit(1)

class Colors:
    OK = '\033[92m'
    FAIL = '\033[91m'
    END = '\033[0m'

def test_ecpp(n, label):
    print(f"\n--- Probando {label} (n={n}) ---")

    # 1. Generar Certificado (El Prover)
    # Buscamos una curva y un punto válidos para este n
    print("  [Prover] Generando certificado...")
    cert = find_ecpp_certificate(n)

    if not cert:
        print(f"  {Colors.FAIL}[SKIP]{Colors.END} No se encontró curva fácil (n muy pequeño o compuesto).")
        return

    a, b, Gx, Gy, m = cert
    print(f"  Certificado: Curve(a={a}, b={b}), G=({Gx},{Gy}), Orden={m}")

    # 2. Verificar con la Fórmula Cerrada (El Verifier)
    print("  [Verifier] Evaluando G_formula (Singularidad)...")
    energy = G_formula(n, a, b, Gx, Gy, m)

    # Interpretación: >0 es Éxito (Primo), <=0 es Fallo
    if energy > 0:
        print(f"  >> RESULTADO: {Colors.OK}VALIDADO (Energía {energy}){Colors.END}")
    else:
        print(f"  >> RESULTADO: {Colors.FAIL}RECHAZADO (Energía {energy}){Colors.END}")

    # 3. Prueba de Sabotaje (Falsificación)
    print("  [Sabotaje] Intentando engañar con punto falso...")
    # Alteramos el punto para que no esté en la curva
    energy_fake = G_formula(n, a, b, Gx+1, Gy, m)
    if energy_fake <= 0:
        print(f"  >> DEFENSA: {Colors.OK}Falsificación detectada.{Colors.END}")
    else:
        print(f"  >> DEFENSA: {Colors.FAIL}FALLO DE SEGURIDAD.{Colors.END}")

# --- EJECUCIÓN ---
print("=== AUDITORÍA DE SINGULARIDAD ECPP ===")

# 1. Primo Pequeño
test_ecpp(17, "Primo 17")

# 2. Primo Mediano (3 dígitos)
test_ecpp(101, "Primo 101")

# 3. Primo Mayor (Mersenne 127 es muy grande para el generador simple, probamos 127 normal)
test_ecpp(127, "Primo 127")

print("\n=== FIN DE AUDITORÍA ===")