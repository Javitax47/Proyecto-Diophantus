def point_add_py(p1, p2, a, mod):
    if p1 is None: return p2
    if p2 is None: return p1
    x1, y1 = p1
    x2, y2 = p2

    if x1 == x2 and y1 != y2: return None
    if x1 == x2 and y1 == y2 and y1 == 0: return None

    if x1 == x2: # Double
        if y1 == 0: return None
        m = (3 * x1 * x1 + a) * inverse_mod(2 * y1, mod)
    else: # Add
        m = (y2 - y1) * inverse_mod(x2 - x1, mod)

    x3 = (m * m - x1 - x2) % mod
    y3 = (m * (x1 - x3) - y1) % mod
    return (x3, y3)

def point_mul_py(p, k, a, mod):
    res = None
    # Double and add
    binary = bin(k)[2:]
    for b in binary:
        res = point_add_py(res, res, a, mod)
        if b == '1':
            res = point_add_py(res, p, a, mod)
    return res

def get_valid_certificate(n):
    """Encuentra a, b, P y m tal que m*P = O en la curva."""
    print(f"[SETUP] Buscando certificado válido para n={n}...")
    while True:
        a = random.randint(0, n-1)
        x = random.randint(0, n-1)
        y = random.randint(0, n-1)
        b = (y*y - x*x*x - a*x) % n

        # Discriminante no singular
        if (4*a**3 + 27*b**2) % n == 0: continue

        P = (x, y)
        # Buscamos el orden (fuerza bruta pequeña para demo)
        # Probamos m pequeños hasta encontrar el infinito
        for m in range(2, 20):
            res = point_mul_py(P, m, a, n)
            if res is None: # Infinito
                print(f"  -> Encontrado: Curva a={a}, b={b}, P=({x},{y}), Orden m={m}")
                return {'n': n, 'a': a, 'b': b, 'Gx': x, 'Gy': y, 'm': m}

    else:
        print(f">> [FALLO] Algo anda mal. Res={res_vm}")

    # 3. TEST INVÁLIDO (SABOTAJE)
    inputs_bad = inputs_valid.copy()
    inputs_bad['b'] = (inputs_bad['b'] + 1) % 7 # Romper la curva
    print(f"\n[SABOTAJE] Probando curva incorrecta b={inputs_bad['b']}...")

    x, res_vm_bad = mine_trace_vector(inputs_bad)

    if res_vm_bad != 0:
        print(f">> [ÉXITO] El Código rechazó correctamente el certificado falso (Res={res_vm_bad}).")
    else:
        print(">> [PELIGRO] Falso Positivo.")

if __name__ == "__main__":
    main()