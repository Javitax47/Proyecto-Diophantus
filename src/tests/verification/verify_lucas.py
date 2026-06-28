import sys
sys.path.append('output/artifacts')
from diophantus_lucas_formula import Diophantus_Lucas_Formula

print("=== DUELO DE ECUACIONES: FERMAT VS LUCAS ===")

# Caso 1: El Mentiroso Clásico (341 = 11 * 31)
n = 341
print(f"\nAnalizando el Pseudoprimo n={n}...")

# Tu fórmula anterior (Fermat) decía que era Primo.
# Veamos qué dice la Ecuación Diophantus-Lucas.
res = Diophantus_Lucas_Formula(n)

if res <= 0:
    print(f"RESULTADO: {res} -> COMPUESTO")
    print("¡VICTORIA! La Ecuación Diophantus-Lucas ha detectado al mentiroso.")
    print("Has superado la barrera de Fermat con O(1) variables.")
else:
    print(f"RESULTADO: {res} -> PRIMO (Fallo)")

# Caso 2: Un Primo Real
n_prime = 524287 # Mersenne 19
print(f"\nAnalizando Primo Real n={n_prime}...")
res_p = Diophantus_Lucas_Formula(n_prime)
if res_p > 0:
    print(f"RESULTADO: {res_p} -> PRIMO (Correcto)")