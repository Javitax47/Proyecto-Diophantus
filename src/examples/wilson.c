// [PRIMALIDAD] Teorema de Wilson: n es primo  <=>  (n-1)! ≡ -1 (mod n).
//   Calcula (n-1)! mod n; result = ese valor (es n-1 sii n primo).
#define DIOPHANTUS_MAX_RECURSION 200
int n = 0;
int result = 0;
int factmod(int k, int acc, int m) {
    if (k <= 1) { return acc; }
    return factmod(k - 1, (acc * k) % m, m);
}
int main() {
    while (1) { result = factmod(n - 1, 1, n); break; }
    return 0;
}
