// CONFIGURACIÓN: PDA-1k (Carga Pesada)
// Necesitamos pila profunda en el parser
#define DIOPHANTUS_MAX_RECURSION 500005
#define DIOPHANTUS_MAX_UNROLL 1

// Entrada
int seed = 123456789;
// Salida
int hash_result = 0;

int avalanche_cycle(int state, int noise, int step) {
    // 1. CASO BASE (Nidificación Estricta)
    if (step >= 500000) {
        return state;
    } else {
        // 2. LÓGICA DE CAOS
        // (noise * 17 + 1013) % 32768
        int next_noise = (noise * 17 + 1013) % 32768;
        
        int sum = state + next_noise;

        if (sum % 2 == 0) {
            // Rama A: Expansión
            int next_state = (sum * 3) + 1;
            return avalanche_cycle(next_state, next_noise, step + 1);
        } else {
            // Rama B: Contracción
            int next_state = sum / 2;
            return avalanche_cycle(next_state, next_noise, step + 1);
        }
    }
}

int main() {
    while (1) {
        hash_result = avalanche_cycle(seed, 1, 0);
        break;
    }
    return 0;
}