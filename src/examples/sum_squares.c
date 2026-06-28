// [BÁSICO] Suma de los primeros k cuadrados (tail-recursivo): 1^2+2^2+...+k^2.
//   Forma cerrada conocida k(k+1)(2k+1)/6 que el motor puede contrastar.
#define DIOPHANTUS_MAX_RECURSION 60
int in_k = 0;
int out = 0;
int sum_sq(int k, int acc) {
    if (k <= 0) { return acc; }
    return sum_sq(k - 1, acc + k * k);
}
int main() {
    while (1) { out = sum_sq(in_k, 0); break; }
    return 0;
}
