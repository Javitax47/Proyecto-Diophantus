/*
 * FERMAT PRIMALITY TEST (BASE 2)
 * Implementación "Diophantine-Compliant"
 * 
 * Lógica: Si n es primo, entonces 2^(n-1) = 1 (mod n).
 * 
 * NOTA: Esta implementación usa recursión pura para permitir
 * que el compilador transforme la dimensión temporal (bucles)
 * en profundidad algebraica.
 */

// --- CONFIGURACIÓN DEL COMPILADOR ---
// Ajustamos la profundidad para permitir números de hasta ~100 bits
// (o lo que soporte tu hardware al compilar el polinomio).
#define DIOPHANTUS_MAX_RECURSION 128
#define DIOPHANTUS_MAX_UNROLL 2

// --- VARIABLES DE ESTADO (INPUT/OUTPUT) ---
int n = 0;          // Entrada: Número a verificar
int is_prime = 0;   // Salida: 1 (Probable Primo), 0 (Compuesto)

// --- MOTOR: Exponenciación Modular Recursiva ---
// Calcula: (base^exp) % mod
// Complejidad: O(log exp)
int power_mod(int base, int exp, int mod) {
    // Caso Base 1: x^0 = 1
    if (exp == 0) {
        return 1;
    }
    
    // Caso Base 2: x^1 = x
    if (exp == 1) {
        return base % mod;
    }

    // Recursión: Divide y Vencerás (Square and Multiply)
    int half = power_mod(base, exp / 2, mod);
    
    // Al elevar al cuadrado el resultado parcial, evitamos duplicar trabajo.
    // Usamos aritmética modular en cada paso para mantener los números bajos.
    int half_sq = (half * half) % mod;

    if (exp % 2 == 0) {
        // Si el exponente es par: (x^(n/2))^2
        return half_sq;
    } else {
        // Si el exponente es impar: (x^(n/2))^2 * x
        return (half_sq * base) % mod;
    }
}

// --- LÓGICA: Test de Fermat ---
int fermat_test(int candidate) {
    // 1. Filtros Triviales
    if (candidate < 2) return 0;
    if (candidate == 2) return 1;
    if (candidate % 2 == 0) return 0; // Descartar pares rápidamente

    // 2. El Teorema de Fermat
    // Verificamos si 2^(n-1) == 1 mod n
    // Usamos Base 2 fija por eficiencia y simplicidad algebraica.
    int witness = power_mod(2, candidate - 1, candidate);

    if (witness == 1) {
        return 1; // Pasa el test (Probable Primo o Pseudoprimo Base 2)
    } else {
        return 0; // Falla el test (Definitivamente Compuesto)
    }
}

int main() {
    // Bucle dummy para el Parser de Diophantus
    while (1) {
        is_prime = fermat_test(n);
        break;
    }
    return 0;
}