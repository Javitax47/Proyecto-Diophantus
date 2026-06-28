// Test: Ackermann function (extremely deep recursion)
// Tests: double recursion, deep call stacks

int m = 3;
int n = 3;
int result = 0;

int ackermann(int m_val, int n_val) {
    if (m_val == 0) {
        return n_val + 1;
    } else {
        if (n_val == 0) {
            return ackermann(m_val - 1, 1);
        } else {
            return ackermann(m_val - 1, ackermann(m_val, n_val - 1));
        }
    }
}

int main() {
    while (1) {
        result = ackermann(m, n);
        break;
    }
    return 0;
}
