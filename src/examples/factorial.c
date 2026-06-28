// [BÁSICO] Factorial con acumulador (tail-recursivo): k! = k*(k-1)*...*1
#define DIOPHANTUS_MAX_RECURSION 40
int in_k = 0;
int out = 0;
int factorial(int k, int acc) {
    if (k <= 1) { return acc; }
    return factorial(k - 1, acc * k);
}
int main() {
    while (1) { out = factorial(in_k, 1); break; }
    return 0;
}
