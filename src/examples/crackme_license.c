/*
 * CRACKME_LICENSE.C
 * Simulación de un algoritmo de validación de serial.
 * Objetivo: Encontrar 'serial_key' tal que 'is_valid' sea 1.
 */

#define DIOPHANTUS_MAX_RECURSION 10
#define DIOPHANTUS_MAX_UNROLL 1

int serial_key = 0;  // INPUT (Secreto)
int is_valid = 0;    // OUTPUT

int check_serial(int key) {
    // Lógica ofuscada típica
    // 1. Mezcla lineal
    int step1 = (key * 1664525) + 1013904223;
    
    // 2. Mezcla no lineal (XOR)
    int step2 = step1 ^ 0xCAFEBABE;
    
    // 3. Condición de Máscara
    // El resultado debe tener ciertos bits activados
    int check = step2 & 0xFFFF0000;
    
    // La condición secreta que el binario espera:
    if (check == 0xDEAD0000) {
        return 1; // Acceso Concedido
    } else {
        return 0; // Acceso Denegado
    }
}

int main() {
    while(1) {
        is_valid = check_serial(serial_key);
        break;
    }
    return 0;
}