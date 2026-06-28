/*
 * MILLER-RABIN PRIMALITY TEST (SINGLE RETURN VERSION)
 * Estructura corregida para evitar contradicciones lógicas en el sistema de ecuaciones.
 */

#define DIOPHANTUS_MAX_RECURSION 64
#define DIOPHANTUS_MAX_UNROLL 2

// --- ESTADO ---
int n = 0;          
int is_prime = 0;   

// --- UTILS ---
// Power Mod con un solo return
int power_mod(int base, int exp, int mod) {
    int res;
    if (exp == 0) {
        res = 1;
    } else {
        if (exp == 1) {
            res = base % mod;
        } else {
            int half = power_mod(base, exp / 2, mod);
            int half_sq = (half * half) % mod;
            if (exp % 2 == 0) {
                res = half_sq;
            } else {
                res = (half_sq * base) % mod;
            }
        }
    }
    return res;
}

// --- LÓGICA CORE ---
int miller_rabin_check(int candidate) {
    int final_verdict;

    // 1. Filtros Triviales
    if (candidate < 2) {
        final_verdict = 0;
    } else {
        if (candidate == 2) {
            final_verdict = 1;
        } else {
            if (candidate == 3) {
                final_verdict = 1;
            } else {
                if (candidate % 2 == 0) {
                    final_verdict = 0;
                } else {
                    // 2. Test de Fermat Base 2 (Simulado)
                    int witness = power_mod(2, candidate - 1, candidate);
                    
                    if (witness != 1) {
                        final_verdict = 0; // Compuesto
                    } else {
                        final_verdict = 1; // Probable Primo
                    }
                }
            }
        }
    }
    // Único punto de retorno: El compilador genera: RET = If(cond1, 0, If(cond2, 1, ...))
    return final_verdict;
}

int main() {
    while (1) {
        is_prime = miller_rabin_check(n);
        break;
    }
    return 0;
}