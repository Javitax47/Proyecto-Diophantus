
def G_formula(n):
    # FÓRMULA SINTETIZADA POR UNIVERSAL OPTIMIZER
    # Patrón Detectado: x -> 5*x + 3
    # Pasos simulados: 1000000000000000000
    # Complejidad: O(log steps)
    
    if 1000000000000000000 == 0: return n
    
    # Matriz de Transformación T = [[A, B], [0, 1]]
    # Representa la operación lineal en coordenadas homogéneas.
    
    # 1. Multiplicación de Matrices 2x2
    def mat_mul(M1, M2):
        a = M1[0][0]*M2[0][0] + M1[0][1]*M2[1][0]
        b = M1[0][0]*M2[0][1] + M1[0][1]*M2[1][1]
        c = M1[1][0]*M2[0][0] + M1[1][1]*M2[1][0]
        d = M1[1][0]*M2[0][1] + M1[1][1]*M2[1][1]
        return [[a, b], [c, d]]

    # 2. Exponenciación Binaria (Square-and-Multiply)
    base = [[5, 3], [0, 1]]
    res  = [[1, 0], [0, 1]] # Identidad
    exp  = 1000000000000000000
    
    while exp > 0:
        if exp % 2 == 1:
            res = mat_mul(res, base)
        base = mat_mul(base, base)
        exp //= 2
        
    # 3. Aplicar al estado inicial 'n'
    # Vector final = T^steps * [n, 1]
    return res[0][0] * n + res[0][1]
