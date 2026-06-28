import sys

def polynomial_mod_step(v_next, v_prev, q, n, base, is_odd_step):
    """
    Esta es la Ecuación Polinómica de un paso de PowerMod.
    Representa la lógica:
       Si el bit es 0 (Par):   v_next = v_prev^2 - q*n
       Si el bit es 1 (Impar): v_next = v_prev^2 * base - q*n
    
    En formato polinómico unificado (sin IFs):
    """
    # Si is_odd_step es 0 o 1 (variable conocida por la posición del bit)
    # El compilador genera algo equivalente a esto:
    
    # Termino Par: (1 - odd) * (v_next - (v_prev^2 - q*n))
    term_even = (1 - is_odd_step) * (v_next - (v_prev**2 - q * n))
    
    # Termino Impar: (odd) * (v_next - (v_prev^2 * base - q*n))
    term_odd  = (is_odd_step) * (v_next - (v_prev**2 * base - q * n))
    
    # La suma debe ser 0
    return term_even + term_odd

def G_full_logic(n, x_vector):
    """
    Fórmula con la lógica completa de Miller-Rabin/Fermat
    para cualquier n (no solo Fermat primes).
    """
    Energy = 0
    base = 2
    
    # Desempaquetar vector: [v0, q0, v1, q1, ...]
    # v0 es el estado inicial (normalmente 1 o base)
    
    # Reconstruimos los pasos basados en los bits de (n-1)
    # Esto es lo que hace el código C internamente.
    exp = n - 1
    bits = bin(exp)[2:] # Representación binaria, ej: 6 -> '110'
    
    # El vector debe tener el tamaño correcto para los pasos
    expected_steps = len(bits)
    
    # Constraint Inicial
    v_current = x_vector[0]
    # En algoritmo power_mod iterativo standard: empieza en 1 (acumulador) o base.
    # Asumiremos acumulador iniciando en 1 para square-and-multiply izquierda-derecha
    # Pero tu código C era recursivo. Simplificamos para demostración polinómica:
    # v_0 debe ser consistente con el primer paso.
    
    # Iteramos sobre la "Cadena de Verdad"
    idx = 0
    current_val = 1 # Valor inicial teórico de la exponenciación
    
    for bit_char in bits:
        is_odd = int(bit_char == '1')
        
        v_next = x_vector[2*idx]     # El valor calculado en este paso
        q      = x_vector[2*idx + 1] # El cociente usado para el mod
        
        # Evaluamos el polinomio de este paso
        eq_val = polynomial_mod_step(v_next, current_val, q, n, base, is_odd)
        Energy += eq_val**2
        
        current_val = v_next
        idx += 1

    # Restricción Final: Fermat (2^(n-1) == 1)
    Energy += (current_val - 1)**2
    
    return n * (1 - Energy)

# --- EL MINERO CORRECTO (Simula el código C real) ---
def mine_correct_vector(n):
    vector = []
    exp = n - 1
    bits = bin(exp)[2:]
    
    val = 1 # Acumulador inicial
    base = 2
    
    for bit_char in bits:
        # 1. Cuadrado
        val = val * val
        
        # 2. Multiplicar si es bit 1
        if bit_char == '1':
            val = val * base
            
        # 3. Modulo (Calculamos el cociente 'q' oculto)
        q = val // n
        r = val % n
        
        # Guardamos en el vector (v, q)
        vector.append(r)
        vector.append(q)
        
        val = r
        
    return vector

def test(n):
    print(f"--- Probando n={n} ---")
    print(f"  Exponente (n-1): {n-1} (Binario: {bin(n-1)[2:]})")
    
    # 1. Ejecutar Minero (Equivalente a correr el código C)
    x = mine_correct_vector(n)
    print(f"  Vector Testigo generado: {x}")
    
    # 2. Validar con la Fórmula (Matemática Pura)
    G = G_full_logic(n, x)
    
    if G > 0:
        print(f"  RESULTADO: {G} -> ¡PRIMO VALIDADO!")
    else:
        print(f"  RESULTADO: {G} -> COMPUESTO (o vector inválido)")

print("=== VALIDACIÓN DE LÓGICA COMPLETA ===")
test(5) # Primo Fermat (4 = 100)
test(7) # Primo NO Fermat (6 = 110) - ¡Este fallaba antes!
test(4) # Compuesto