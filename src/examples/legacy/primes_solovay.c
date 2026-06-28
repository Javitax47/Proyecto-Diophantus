// Entrada: Número a verificar
int target = 0;
// Salida: 0 si es primo (pasa ambas bases), >0 si es compuesto
int result = 0;

// --- 1. EXPONENCIACIÓN MODULAR ---
int power_mod(int base, int exp, int mod) {
    if (exp == 0) return 1;
    if (exp == 1) return base % mod;
    int half = power_mod(base, exp / 2, mod);
    int half_sq = (half * half) % mod;
    if (exp % 2 == 0) return half_sq;
    else return (half_sq * base) % mod;
}

// --- 2. SÍMBOLO DE JACOBI RECURSIVO ---
int jacobi_recursive(int a, int n) {
    if (a == 0) return 0;
    if (a == 1) return 1;
    
    if (a % 2 == 0) {
        int j_half = jacobi_recursive(a / 2, n);
        int n_mod_8 = n % 8;
        if ((n_mod_8 == 1) || (n_mod_8 == 7)) return j_half;
        else return -j_half;
    } else {
        int j_recip = jacobi_recursive(n % a, a);
        if (((a % 4) == 3) && ((n % 4) == 3)) return -j_recip;
        else return j_recip;
    }
}

// --- 3. CHECK DE UNA BASE INDIVIDUAL ---
// Retorna 0 si pasa (posible primo), 1 si falla (compuesto)
int check_base(int n, int base) {
    // Euler: a^((n-1)/2) mod n
    int euler_val = power_mod(base, (n - 1) / 2, n);
    
    // Jacobi: (a/n)
    int jacobi_val = jacobi_recursive(base, n);
    
    // Normalizar Jacobi negativo a aritmética modular positiva
    // -1 se convierte en (n - 1)
    int jacobi_mod = jacobi_val;
    if (jacobi_val < 0) {
        jacobi_mod = n + jacobi_val;
    }
    
    // Si coinciden, retorna 0. Si no, retorna 1.
    if (euler_val == jacobi_mod) {
        // Chequeo adicional: Si jacobi es 0, n comparte factor con base -> Compuesto
        if (jacobi_val == 0) return 1; 
        return 0;
    } else {
        return 1;
    }
}

// --- 4. TEST ROBUSTO (MULTI-BASE) ---
int solovay_robust(int n) {
    if (n < 2) return 1;
    if (n == 2) return 0;
    if (n == 3) return 0;
    if (n % 2 == 0) return 1;

    // Base 2
    int r2 = check_base(n, 2);
    
    // Base 3 (El Cazador de Carmichael)
    int r3 = check_base(n, 3);
    
    // La ecuación solo es 0 si AMBOS son 0.
    // Sumamos los errores (al cuadrado para evitar cancelaciones negativas si las hubiera)
    return r2 + r3;
}

int main() {
    while (1) {
        result = solovay_robust(target);
        break;
    }
    return 0;
}