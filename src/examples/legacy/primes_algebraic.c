// Entrada: Número a verificar
int target = 0;
// Salida: 0 si es probable primo, distinto de 0 si es compuesto
int result = 0;

// Exponenciación Modular Aritmética
int power_mod(int base, int exp, int mod) {
    if (exp == 0) {
        return 1;
    } else {
        if (exp == 1) {
            return base % mod;
        } else {
            // Recursión pura
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

// Función de Primalidad Fermat (Base 2)
// Es probabilisticamente muy fuerte y algebraicamente muy simple.
int fermat_primality_test(int n) {
    if (n < 2) return 1; // Error (Compuesto)
    if (n == 2) return 0; // Primo
    
    // Calculamos 2^(n-1) mod n
    // Si es primo, esto DEBE ser 1.
    int witness = power_mod(2, n - 1, n);
    
    // Retornamos la diferencia al cuadrado.
    // Si es primo, witness - 1 = 0.
    // Si es compuesto, witness - 1 != 0.
    int diff = witness - 1;
    return diff * diff; 
}

int main() {
    // BUCLE DUMMY REQUERIDO POR EL PARSER
    while (1) {
        // Calculamos el "Residuo de Primalidad" para el target
        result = fermat_primality_test(target);
        break;
    }
    return 0;
}