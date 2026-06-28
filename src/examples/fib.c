// Fibonacci como recurrencia acoplada (tail-recursiva): (a,b) -> (b, a+b).
#define DIOPHANTUS_MAX_RECURSION 60
int seed_a = 0;
int seed_b = 0;
int out = 0;
int fib(int a, int b, int step) {
    if (step >= 25) { return a; }
    return fib(b, a + b, step + 1);
}
int main() {
    while (1) { out = fib(seed_a, seed_b, 0); break; }
    return 0;
}
