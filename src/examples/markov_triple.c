// [AVANZADO] Mapa de Markov (salto de Vieta cíclico): (x,y,z)->(y,z,3*y*z - x).
//   Conserva x^2+y^2+z^2-3xyz (que el motor DESCUBRE y certifica, no se inyecta).
#define DIOPHANTUS_MAX_RECURSION 40
int seed_x = 0;
int seed_y = 0;
int seed_z = 0;
int out = 0;
int markov(int x, int y, int z, int step) {
    if (step >= 8) { return z; }
    return markov(y, z, 3 * y * z - x, step + 1);
}
int main() {
    while (1) { out = markov(seed_x, seed_y, seed_z, 0); break; }
    return 0;
}
