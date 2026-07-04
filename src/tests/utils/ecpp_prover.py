
import random

class ECPP_Prover:
    @staticmethod
    def mod_inv(a, m): return pow(a, -1, m)

    @staticmethod
    def point_add_proj(X1, Y1, Z1, X2, Y2, Z2, a, n):
        if Z1 == 0: return X2, Y2, Z2
        if Z2 == 0: return X1, Y1, Z1

        U1 = (Y1 * Z2) % n; U2 = (Y2 * Z1) % n
        V1 = (X1 * Z2) % n; V2 = (X2 * Z1) % n

        if V1 == V2:
            if U1 != U2: return 0, 1, 0
            else: return ECPP_Prover.point_double_proj(X1, Y1, Z1, a, n)

        u = (U2 - U1) % n; v = (V2 - V1) % n
        v2 = (v * v) % n; v3 = (v2 * v) % n; w = (Z1 * Z2) % n

        A = (u * u * w - v3 - 2 * V1 * v2) % n
        X3 = (v * A) % n
        Y3 = (u * (V1 * v2 - X3) - U1 * v3) % n
        Z3 = (v3 * w) % n
        return X3, Y3, Z3

    @staticmethod
    def point_double_proj(X, Y, Z, a, n):
        if Z == 0: return 0, 1, 0
        XX = (X * X) % n; ZZ = (Z * Z) % n
        w = (3 * XX + a * ZZ) % n
        s = (4 * X * Y * Y) % n
        B = (8 * Y**4) % n
        X3 = (w * w - 2 * s) % n
        Y3 = (w * (s - X3) - B) % n
        Z3 = (2 * Y * Z) % n
        return X3, Y3, Z3

    @staticmethod
    def point_mul_proj(k, Gx, Gy, a, n):
        Ax, Ay, Az = 0, 1, 0
        Bx, By, Bz = Gx, Gy, 1
        curr_k = k
        while curr_k > 0:
            if curr_k % 2 != 0:
                Ax, Ay, Az = ECPP_Prover.point_add_proj(Ax, Ay, Az, Bx, By, Bz, a, n)
            Bx, By, Bz = ECPP_Prover.point_double_proj(Bx, By, Bz, a, n)
            curr_k //= 2
        return Ax, Ay, Az

    @staticmethod
    def generate_certificate(n):
        # print(f"   [PROVER] Buscando curva para n={n}...")
        for _ in range(2000):
            a = random.randint(0, n-1)
            x = random.randint(0, n-1)
            y = random.randint(0, n-1)
            b = (y*y - x*x*x - a*x) % n
            if (4*a**3 + 27*b**2) % n == 0: continue

            # Buscar orden pequeño para test rápido
            for m in range(2, 30):
                Rx, Ry, Rz = ECPP_Prover.point_mul_proj(m, x, y, a, n)
                if Rz == 0: return a, b, x, y, m
        return None
