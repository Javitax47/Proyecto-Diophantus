// [AVANZADO] Tribonacci: recurrencia lineal de 3 términos (a,b,c)->(b,c,a+b+c).
//   Companion 3x3; el motor de descubrimiento puede buscar su estructura.
#define DIOPHANTUS_MAX_RECURSION 60
int seed_a = 0;
int seed_b = 0;
int seed_c = 0;
int out = 0;
int trib(int a, int b, int c, int step) {
    if (step >= 20) { return a; }
    return trib(b, c, a + b + c, step + 1);
}
int main() {
    while (1) { out = trib(seed_a, seed_b, seed_c, 0); break; }
    return 0;
}
