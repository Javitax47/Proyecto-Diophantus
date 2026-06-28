// Un bucle lineal simple, pero gigantesco.
// Configuración para que la VM pueda ejecutar al menos 1 paso
#define DIOPHANTUS_MAX_RECURSION 10 
#define DIOPHANTUS_MAX_UNROLL 1

int val = 2; // Semilla inicial
int dummy_out = 0;

// Función de transición de un solo paso
// x -> 5x + 3
int step_function(int x, int dummy) {
    return x * 5 + 3;
}

int main() {
    // EL PARSER NECESITA ESTE BUCLE PARA DETECTAR EL CICLO DE RELOJ
    while(1) {
        val = step_function(val, 0);
        break; // Un solo paso lógico es suficiente para que el compilador genere la función
    }
    return 0;
}