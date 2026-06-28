// Test: GCD (Greatest Common Divisor) using Euclidean algorithm
// Tests: recursion with modulo, base case handling

int a = 48;
int b = 18;
int result = 0;

int gcd(int x, int y) {
    if (y == 0) {
        return x;
    } else {
        return gcd(y, x % y);
    }
}

int main() {
    while (1) {
        result = gcd(a, b);
        break;
    }
    return 0;
}
