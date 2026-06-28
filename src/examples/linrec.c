// Recurrencia lineal generica (tail-recursiva): x -> 2*x + 1
#define DIOPHANTUS_MAX_RECURSION 40
int seed = 0;
int out = 0;
int linrec(int x, int step) {
    if (step >= 20) { return x; }
    return linrec(2 * x + 1, step + 1);
}
int main() {
    while (1) { out = linrec(seed, 0); break; }
    return 0;
}
