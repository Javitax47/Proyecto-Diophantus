int target = 10;
int result = 0;

int is_prime_recursive(int n, int i) {
    if (n <= 1) {
        return 0;
    } else {
        if (i * i > n) {
            return 1;
        } else {
            if (n % i == 0) {
                return 0;
            } else {
                return is_prime_recursive(n, i + 1);
            }
        }
    }
}

int is_prime(int n) {
    return is_prime_recursive(n, 2);
}

int nth_prime_recursive(int target_idx, int current_num, int count) {
    int p = is_prime(current_num);
    if (p) {
        if (count + 1 == target_idx) {
            return current_num;
        } else {
            return nth_prime_recursive(target_idx, current_num + 1, count + 1);
        }
    } else {
        return nth_prime_recursive(target_idx, current_num + 1, count);
    }
}

int main() {
    while (1) {
        result = nth_prime_recursive(target, 2, 0);
        break;
    }
    return 0;
}
