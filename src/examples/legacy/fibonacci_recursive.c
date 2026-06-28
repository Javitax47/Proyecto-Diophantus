int n = 10;
int result = 0;

int fib(int x) {
    if (x <= 1) {
        return x;
    } else {
        return fib(x - 1) + fib(x - 2);
    }
}

int main() {
    while (1) {
        result = fib(n);
        break;
    }
    return 0;
}
