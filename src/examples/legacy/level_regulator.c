#include <stdio.h> 

// State Variables (S_t)
// Nota: La variable 'rate' cambia, por lo que es de estado.
int level = 5;      // Nivel actual (debe ser >= 0)
int rate = 6;       // Tasa de consumo (varía según el nivel)
int throttle_input = 1; // Asumimos que esta entrada se mantiene en 1 (Aplicado)

int main() {
    
    // Asumimos que throttle_input es un input externo que pasa al verificador.
    // El verificador debe ignorar la I/O, pero debe permitir que throttle_input sea
    // interpretado como una variable de estado/entrada constante.
    
    while (1) {
        // --- 1. LÓGICA VULNERABLE: El Consumo ---
        
        // Si el acelerador está activo Y la tasa es alta (rate > 5), consumimos.
        // VULNERABILIDAD: No hay chequeo para que 'level' no se vuelva negativo.
        if (throttle_input > 0 && rate > 5) {
            level = level - rate; 
        } 
        
        // 2. LÓGICA DE COMPLEJIDAD (Cambio de Tasa):
        // Si el nivel es muy bajo, la tasa se reduce para un llenado lento.
        if (level < 10) {
             rate = rate + 1; // Aumentar complejidad del estado (rate varía)
        } else {
             rate = 6; // Estabilizar la tasa
        }
        
        // I/O (Ignorado por el parser)
        printf("Level: %d, Rate: %d\n", level, rate);
    }
    return 0;
}