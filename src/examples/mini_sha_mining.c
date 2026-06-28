/*
 * MINI-SHA FLAT (Solver Friendly)
 * Usamos macros para garantizar que toda la lógica se aplane
 * en un único circuito SAT sin llamadas a funciones.
 */

#define DIOPHANTUS_MAX_RECURSION 20
#define DIOPHANTUS_MAX_UNROLL 1

// --- INPUT / OUTPUT ---
int nonce = 0;    // La variable que Z3 debe encontrar
int hash_out = 0; // El objetivo (debe ser < 1000000)

// --- LOGIC (MACROS) ---
// Al usar #define, el código se pega literalmente. 
// Z3 recibirá la ecuación expandida.

// Rotación aritmética a la derecha de 32 bits
#define ROTR(x, n) ( ((x) / (1 << (n))) + ((x) * (1 << (32 - (n)))) )

// Ronda de compresión
// h: estado actual
// x: mensaje (nonce + step)
#define COMPRESS(h, x) ( (((h) + (x)) ^ 0x5A5A5A5A) + ROTR((((h) + (x)) ^ 0x5A5A5A5A), 7) + (x) )

int main() {
    int state = 0x12345678; // IV (Initial Vector)
    
    while(1) {
        // Desenrollamos el bucle manualmente o dejamos que el compilador lo haga.
        // Para 4 rondas fijas, es mejor ser explícito para el solver.
        
        // Ronda 1
        state = COMPRESS(state, nonce);
        
        // Ronda 2 (nonce + 1)
        state = COMPRESS(state, nonce + 1);
        
        // Ronda 3 (nonce + 2)
        state = COMPRESS(state, nonce + 2);
        
        // Ronda 4 (nonce + 3)
        state = COMPRESS(state, nonce + 3);


        state = COMPRESS(state, nonce + 4);
        
        // Ronda 5 (nonce + 4)
        state = COMPRESS(state, nonce + 4);

        // Ronda 6 (nonce + 5)
        state = COMPRESS(state, nonce + 5);

        // Ronda 7 (nonce + 6)
        state = COMPRESS(state, nonce + 6);

        // Ronda 8 (nonce + 7)
        state = COMPRESS(state, nonce + 7);

        // Ronda 9 (nonce + 8)
        state = COMPRESS(state, nonce + 8);

        // Ronda 10 (nonce + 9)
        state = COMPRESS(state, nonce + 9);

        // Ronda 11 (nonce + 10)
        state = COMPRESS(state, nonce + 10);
        
        hash_out = state;
        break;
    }
    return 0;
}