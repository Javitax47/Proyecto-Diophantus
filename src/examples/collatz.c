// --- START OF FILE examples/collatz.c ---
#define DIOPHANTUS_MAX_RECURSION 300
// Entrada: Número inicial
int start_n = 0;
// Salida: Pasos para llegar a 1
int total_steps = 0;

// Función de Trayectoria (Versión Nested / Diophantine-Safe)
int collatz_trajectory(int n, int acc) {
    // 1. Caso Base: Éxito
    if (n == 1) {
        return acc;
    } else {
        // 2. Caso Base: Límite de seguridad
        if (acc > 200) {
            return -1;
        } else {
            // 3. Dinámica del Sistema
            if (n % 2 == 0) {
                // Paso Par
                return collatz_trajectory(n / 2, acc + 1);
            } else {
                // Paso Impar
                int next_val = (3 * n + 1) / 2;
                return collatz_trajectory(next_val, acc + 2);
            }
        }
    }
}

int main() {
    while(1) {
        total_steps = collatz_trajectory(start_n, 0);
        break;
    }
    return 0;
}