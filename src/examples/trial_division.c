// [PRIMALIDAD] Test por división de prueba (recursivo, correcto y exacto).
//   Prueba divisores d=2,3,... hasta d*d>n. result=1 primo, 0 compuesto.
#define DIOPHANTUS_MAX_RECURSION 200
int n = 0;
int result = 0;
int trial(int m, int d) {
    if (d * d > m) { return 1; }
    if (m % d == 0) { return 0; }
    return trial(m, d + 1);
}
int main() {
    while (1) {
        if (n < 2) { result = 0; break; }
        result = trial(n, 2);
        break;
    }
    return 0;
}
