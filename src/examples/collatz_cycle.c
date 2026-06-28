// --- START OF FILE examples/collatz_cycle.c ---
#define DIOPHANTUS_MAX_RECURSION 300
// Entrada
int start_n = 0;
// Salida
int is_cycle = 0;

// 1. La Lógica Recursiva (Ya funcionaba bien, la mantenemos igual)
int detect_cycle_recursive(int n, int original, int steps) {
    if (n == original) {
        if (steps > 0) {
            return 1;
        } else {
             if (n % 2 == 0) return detect_cycle_recursive(n / 2, original, steps + 1);
             else return detect_cycle_recursive((3 * n + 1) / 2, original, steps + 2);
        }
    } else {
        if (n == 1) {
            return 0;
        } else {
            // Horizonte de sucesos (ajustado a la profundidad del parser)
            if (steps > 150) {
                return 0;
            } else {
                if (n % 2 == 0) {
                    return detect_cycle_recursive(n / 2, original, steps + 1);
                } else {
                    return detect_cycle_recursive((3 * n + 1) / 2, original, steps + 2);
                }
            }
        }
    }
}

// 2. El Envoltorio (Wrapper)
// Movemos la lógica de decisión aquí para que el main sea una asignación limpia.
int logic_wrapper(int n) {
    if (n > 4) {
        // Iniciamos la búsqueda
        return detect_cycle_recursive(n, n, 0);
    } else {
        return 0;
    }
}

int main() {
    while(1) {
        // Asignación directa: Obliga al compilador a vincular la variable
        is_cycle = logic_wrapper(start_n);
        break;
    }
    return 0;
}