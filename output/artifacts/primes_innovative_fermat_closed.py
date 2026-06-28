# ============================================================================
# /!\ ARTEFACTO HEREDADO ERRONEO / MAL ETIQUETADO -- NO USAR COMO TEST DE PRIMALIDAD
# Es Fermat base 2 (NO Miller-Rabin): acepta pseudoprimos (341, 561, ...). La 'formula O(log^k)' es exponenciacion modular estandar y exponencial en n.
# Auditado con contraejemplos en src/tests/verification/test_primality_audit.py
# Implementacion CORRECTA y validada: src/analysis/primality.py (Baillie-PSW)
# ============================================================================


def dickson_eval(degree, P, mod):
    # Calcula D_n(P) usando Ladder de Montgomery.
    # Inicialización: v=D_0=2, w=D_1=P.
    # Esto corresponde al índice k=0.
    
    if degree == 0: return 2
    if degree == 1: return P % mod
    
    v = 2
    w = P % mod
    
    # FIX: Procesamos TODOS los bits (incluido MSB)
    # bin(n) = '0b1...' -> [2:] toma '1...'
    for bit in bin(degree)[2:]:
        # Paso Par: V_2k = V_k^2 - 2
        v2 = (v * v - 2) % mod
        # Paso Impar: V_{2k+1} = V_k * V_{k+1} - P
        vw = (v * w - P) % mod
        
        if bit == '0':
            # k -> 2k: (D_2k, D_2k+1)
            v = v2
            w = vw
        else:
            # k -> 2k+1: (D_2k+1, D_2k+2)
            v = vw
            # D_2k+2 = D_{k+1}^2 - 2
            w = (w * w - 2) % mod
            
    return v

def G_formula(n):
    if n < 2: return 1
    if n == 2: return 0
    if n % 2 == 0: return 1
    res = pow(2, n - 1, n)
    return (res - 1)**2
