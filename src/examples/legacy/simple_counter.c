#include <stdio.h> // Para printf (que será ignorado)

/*
 * Un programa de prueba simple para el Compilador Diophantus.
 * Sigue todas las reglas de código compatible.
 */

// 1. VARIABLE DE ESTADO (S_t)
int x = 0;

int main() {
    
    // 2. Bucle principal
    while (1) {
        
        // 3. LÓGICA COMPUTABLE (La Función F)
        // (Regla 1: Sin '++')
        x = x + 1;
        
        // 4. I/O (Será ignorado por el parser)
        printf("El valor de x es: %d\n", x);
    }
    
    return 0;
}