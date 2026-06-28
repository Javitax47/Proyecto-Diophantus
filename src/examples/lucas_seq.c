// [AVANZADO] Sucesión de Lucas V_n con P=3, Q=1: V_n = 3*V_{n-1} - V_{n-2}.
//   (a,b) = (V_{k-1}, V_k) -> (V_k, 3*V_k - V_{k-1}). Base del test de Lucas.
//   Semillas: V_0 = 2, V_1 = P = 3.
#define DIOPHANTUS_MAX_RECURSION 60
int seed_a = 0;
int seed_b = 0;
int out = 0;
int lucasV(int a, int b, int step) {
    if (step >= 15) { return a; }
    return lucasV(b, 3 * b - a, step + 1);
}
int main() {
    while (1) { out = lucasV(seed_a, seed_b, 0); break; }
    return 0;
}
