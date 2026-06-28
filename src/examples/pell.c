// Recurrencia de Pell (tail-recursiva): (x,y) -> (3x+4y, 2x+3y).
// Preserva la conica x^2 - 2y^2 = 1 (que el motor debe DESCUBRIR, no se inyecta).
#define DIOPHANTUS_MAX_RECURSION 40
int seed_x = 0;
int seed_y = 0;
int out = 0;
int pell(int x, int y, int step) {
    if (step >= 12) { return x; }
    return pell(3 * x + 4 * y, 2 * x + 3 * y, step + 1);
}
int main() {
    while (1) { out = pell(seed_x, seed_y, 0); break; }
    return 0;
}
