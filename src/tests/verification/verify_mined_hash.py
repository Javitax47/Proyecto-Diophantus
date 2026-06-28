def to_int32(v):
    v = v & 0xFFFFFFFF
    if v >= 2**31: return v - 2**32
    return v

def rotr(x, n):
    # Simulación exacta de la rotación en C de 32 bits
    ux = x & 0xFFFFFFFF
    return to_int32((ux >> n) | (ux << (32 - n)))

def compress(h, x):
    # Macro COMPRESS traducida: 
    # (((h) + (x)) ^ 0x5A5A5A5A) + ROTR(...) + (x)
    
    # 1. Suma inicial
    s1 = to_int32(h + x)
    # 2. XOR Mágico
    xor_val = s1 ^ 0x5A5A5A5A
    # 3. Rotación
    rot_val = rotr(xor_val, 7)
    # 4. Suma final
    return to_int32(xor_val + rot_val + x)

def check_hash(nonce):
    print(f"Verificando Nonce: {nonce} (Hex: {hex(nonce & 0xFFFFFFFF)})")
    
    state = 0x12345678
    
    # 4 Rondas idénticas al código C
    for i in range(4):
        state = compress(state, nonce + i)
        
    print(f"Hash Resultante: {state}")
    
    if state < 1000000:
        print("✅ ¡VÁLIDO! El hash es menor que 1,000,000")
    else:
        print("❌ FALLO. El hash es muy alto.")

if __name__ == "__main__":
    # El valor que te dio Z3
    mined_nonce = 729111555 
    check_hash(mined_nonce)