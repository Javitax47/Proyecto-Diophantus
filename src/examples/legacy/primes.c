#include <stdio.h>

// --- VARIABLES DE ESTADO (S_t) ---
int n = 1;            // Candidato actual (Inicia en 1 para que el primero sea 3)
int d = 3;            // Divisor actual
int r = 0;            // Variable auxiliar para el resto
int state = 0;        // Máquina de estados: 0=NEXT_NUM, 1=CHECK_LIMIT, 2=MODULO, 3=RESULT
int found_prime = 2;  // Salida: El último primo hallado (iniciamos con 2)

int main() {
    while (1) {
        
        // --- STATE 0: Generación de Candidatos ---
        // Solo probamos números IMPARES. Esto elimina el 50% del trabajo.
        if (state == 0) {
            n = n + 2;  // 1 -> 3 -> 5 -> 7...
            d = 3;      // Reiniciamos divisor al primer impar (3)
            state = 1;  // Pasamos a verificar
        } 
        
        // --- STATE 1: Optimización Matemática (La clave de la velocidad) ---
        // Si d^2 > n, es matemáticamente imposible que haya más divisores.
        // Esto convierte el algoritmo en O(sqrt(N)). 
        // Ejemplo: Para n=101, solo probamos d=3, 5, 7, 9. (4 pruebas vs 50).
        else if (state == 1) {
            if (d * d > n) {
                found_prime = n; // ¡PRIMO CONFIRMADO!
                state = 0;       // Buscar el siguiente
            } else {
                r = n;       // Preparamos 'r' para simular el módulo
                state = 2;   // Vamos al bucle de resta
            }
        }
        
        // --- STATE 2: Simulación de División (Fuerza Bruta Mecánica) ---
        // Restamos 'd' repetidamente porque no tenemos operador '%'
        else if (state == 2) {
            if (r >= d) {
                r = r - d;
                // state se mantiene en 2 hasta terminar la resta
            } else {
                state = 3; // Resta terminada, verificar residuo
            }
        }
        
        // --- STATE 3: Verificación de Divisibilidad ---
        else if (state == 3) {
            if (r == 0) {
                // División exacta (residuo 0) -> ES COMPUESTO
                state = 0; // Descartar 'n', ir al siguiente impar
            } else {
                // No divisible -> Probar siguiente divisor IMPAR
                d = d + 2; // Saltamos los pares (3 -> 5 -> 7...)
                state = 1; // Volver a comprobar límites
            }
        }

        // I/O (Ignorado por el compilador, útil para debug en C normal)
        // printf("State: %d | N: %d | Div: %d | Found: %d\n", state, n, d, found_prime);
    }
    return 0;
}