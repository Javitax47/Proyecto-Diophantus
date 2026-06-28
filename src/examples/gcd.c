// [BÁSICO] Máximo común divisor (algoritmo de Euclides, tail-recursivo).
//   gcd(a,b) = gcd(b, a mod b)
#define DIOPHANTUS_MAX_RECURSION 60
int in_a = 0;
int in_b = 0;
int out = 0;
int gcd(int a, int b) {
    if (b == 0) { return a; }
    return gcd(b, a % b);
}
int main() {
    while (1) { out = gcd(in_a, in_b); break; }
    return 0;
}
