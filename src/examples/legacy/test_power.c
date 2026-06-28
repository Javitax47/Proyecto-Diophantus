// Test: Power function (x^n) using recursion
// Tests: multiplication, recursion, even/odd logic

int base = 2;
int exponent = 10;
int result = 0;

int power(int x, int n) {
    if (n == 0) {
        return 1;
    } else {
        if (n % 2 == 0) {
            int half = power(x, n / 2);
            return half * half;
        } else {
            return x * power(x, n - 1);
        }
    }
}

int main() {
    while (1) {
        result = power(base, exponent);
        break;
    }
    return 0;
}
