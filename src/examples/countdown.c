// Cuenta atras con acumulador (tail-recursiva): suma k + (k-1) + ... + 1
#define DIOPHANTUS_MAX_RECURSION 60
int start_k = 0;
int total = 0;
int sum_down(int k, int acc) {
    if (k <= 0) { return acc; }
    return sum_down(k - 1, acc + k);
}
int main() {
    while (1) { total = sum_down(start_k, 0); break; }
    return 0;
}
