int target = 0;
int result = 0;

// --- 1. EXPONENCIACIÓN MODULAR ---
int power_mod(int base, int exp, int mod) {
    if (exp == 0) {
        return 1;
    } else {
        if (exp == 1) {
            return base % mod;
        } else {
            int half = power_mod(base, exp / 2, mod);
            int half_sq = (half * half) % mod;
            
            if (exp % 2 == 0) {
                return half_sq;
            } else {
                return (half_sq * base) % mod;
            }
        }
    }
}

// --- 2. ARITMÉTICA DE SIGNOS (ANIDADA) ---
int mult_signs(int s1, int s2) {
    if (s1 == 0) {
        return 0;
    } else {
        if (s2 == 0) {
            return 0;
        } else {
            if (s1 == 1) {
                if (s2 == 1) { return 1; }
                else { return 2; }
            } else {
                if (s2 == 1) { return 2; }
                else { return 1; }
            }
        }
    }
}

// --- 3. JACOBI RECURSIVO (ANIDADO) ---
int jacobi_logic(int a, int n) {
    if (a == 0) {
        return 0; // Caso Base perdido anteriormente
    } else {
        if (a == 1) {
            return 1; // Caso Base perdido anteriormente
        } else {
            if (a % 2 == 0) {
                int j_half = jacobi_logic(a / 2, n);
                int n8 = n % 8;
                int sign_factor = 0;
                
                if (n8 == 1) { sign_factor = 1; }
                else {
                    if (n8 == 7) { sign_factor = 1; }
                    else { sign_factor = 2; }
                }
                return mult_signs(j_half, sign_factor);
            } else {
                int j_recip = jacobi_logic(n % a, a);
                int sign_flip = 1;
                int a4 = a % 4;
                int n4 = n % 4;
                
                if (a4 == 3) {
                    if (n4 == 3) {
                        sign_flip = 2;
                    }
                }
                return mult_signs(j_recip, sign_flip);
            }
        }
    }
}

// --- 4. CHECK BASE (ANIDADO) ---
int check_base(int n, int base) {
    if (n <= base) {
        return 0;
    } else {
        int euler = power_mod(base, (n - 1) / 2, n);
        int j_code = jacobi_logic(base, n);
        
        if (j_code == 0) {
            return 1;
        } else {
            int j_val = 0;
            if (j_code == 1) {
                j_val = 1;
            } else {
                j_val = n - 1;
            }
            
            if (euler == j_val) {
                return 0;
            } else {
                return 1;
            }
        }
    }
}

// --- 5. SOLOVAY 64-BIT (ANIDADO) ---
int solovay_64_bit(int n) {
    if (n < 2) { return 1; }
    else {
        if (n == 2) { return 0; }
        else {
            if (n == 3) { return 0; }
            else {
                if (n % 2 == 0) { return 1; }
                else {
                    return check_base(n, 2) + 
                           check_base(n, 3) + 
                           check_base(n, 5) + 
                           check_base(n, 7) + 
                           check_base(n, 11) + 
                           check_base(n, 13) + 
                           check_base(n, 17) + 
                           check_base(n, 19) + 
                           check_base(n, 23) + 
                           check_base(n, 29) + 
                           check_base(n, 31) + 
                           check_base(n, 37);
                }
            }
        }
    }
}

int main() {
    while (1) {
        result = solovay_64_bit(target);
        break;
    }
    return 0;
}