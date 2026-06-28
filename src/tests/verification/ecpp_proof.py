import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../output/artifacts')))

try:
    # Ahora sí encontrará el módulo
    from ecpp_formula_generated import G_formula
except ImportError:
    print("[ERROR] No se encontró 'ecpp_formula_generated.py' en output/artifacts/.")
    print("Ejecuta primero el deep_optimizer.py")
    sys.exit(1)

"""
=============================================================================
   ECPP DIOFÁNTICO: PRUEBA DE CONCEPTO
=============================================================================
Verificación de Certificados de Primalidad mediante Polinomios.
"""

# -----------------------------------------------------

def test_certificate(name, n, a, b, Gx, Gy, m, vector_x_guess):
    print(f"\n--- Verificando Certificado: {name} ---")
    print(f"  Candidato n: {n}")
    print(f"  Curva: y^2 = x^3 + {a}x + {b}")
    print(f"  Punto G: ({Gx}, {Gy})")
    print(f"  Orden m: {m}")
    
    # Nota: Para ECPP, el vector x es complejo de adivinar a mano.
    # En una demo real, usaríamos el 'minero' (código C) para generarlo.
    # Aquí probaremos si la fórmula evalúa correctamente un vector vacío 
    # (si la reducción fue total) o simularemos el fallo.
    
    # Si la reducción fue perfecta (0 variables), x es irrelevante.
    val = G_formula(n, a, b, Gx, Gy, m, vector_x_guess)
    
    if val > 0:
        print(f"  >> RESULTADO: {val} (PRIMO CERTIFICADO)")
    else:
        print(f"  >> RESULTADO: {val} (FALLO / COMPUESTO)")

def main():
    # CASO 1: Certificado Válido para n=7
    # Curva: y^2 = x^3 + 2x + 3 (mod 7)
    # P = (2, 1). 
    # 2^2 = 4. 2^3 + 2*2 + 3 = 8 + 4 + 3 = 15 = 1. 4 != 1... espera.
    # Vamos a usar un ejemplo real pequeño verificado:
    # n=7, a=0, b=1 (y^2 = x^3 + 1). P=(2, 3). 
    # 3^2=9=2. 2^3+1=9=2. OK. Punto en curva.
    # Orden m=3 (si 3*P = Infinito).
    
    # Vector dummy (si hay variables auxiliares, esto fallará hasta que usemos el minero)
    x_dummy = [0] * 1870
    
    test_certificate("Pequeño Primo (7)", 
                     n=7, a=0, b=1, Gx=2, Gy=3, m=3, 
                     vector_x_guess=x_dummy)

    # CASO 2: Certificado Falso (Punto fuera de curva)
    test_certificate("Falso (Punto Inválido)", 
                     n=7, a=0, b=1, Gx=2, Gy=4, m=3, 
                     vector_x_guess=x_dummy)

if __name__ == "__main__":
    main()