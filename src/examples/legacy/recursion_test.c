int x = 5;
int y = 0;

int factorial(int n) {
    if (n <= 1) {
        return 1;
    } else {
        return n * factorial(n - 1);
    }
}

int main() {
    while (1) {
        y = factorial(x);
        break;
    }
    return 0;
}
