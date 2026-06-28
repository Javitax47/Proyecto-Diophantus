/*
 * TOKEN SALE FLAT (Solver Optimized)
 * Eliminamos funciones intermedias para exponer la aritmética directamente.
 */

#define DIOPHANTUS_MAX_RECURSION 10
#define DIOPHANTUS_MAX_UNROLL 1

int num_tokens = 0;
int cost = 0;

// 1 Ether = 10^18 Wei
// Usamos Macro para inyección directa
#define PRICE 1000000000000000000

int main() {
    while(1) {
        // La ecuación será explícita: cost = num_tokens * 10^18
        // En aritmética de 256 bits, esto modulará (overflow).
        cost = num_tokens * PRICE;
        break;
    }
    return 0;
}