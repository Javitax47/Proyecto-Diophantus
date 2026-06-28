# ============================================================================
# /!\ ARTEFACTO HEREDADO ERRONEO / MAL ETIQUETADO -- NO USAR COMO TEST DE PRIMALIDAD
# Verifica UNA identidad ECPP; compuestos 9,15,21 la pasan. 'Deterministic (Proof)' es FALSO: no es prueba de primalidad (falta el certificado completo).
# Auditado con contraejemplos en src/tests/verification/test_primality_audit.py
# Implementacion CORRECTA y validada: src/analysis/primality.py (Baillie-PSW)
# ============================================================================


def ec_point_mul_proj(n, a, mod, Gx, Gy):
    if n == 0: return 0, 1, 0
    Rx, Ry, Rz = 0, 1, 0
    Bx, By, Bz = Gx, Gy, 1
    for bit in bin(n)[2:]:
        if Rz != 0:
            X, Y, Z = Rx, Ry, Rz
            Y2, Z2 = (Y*Y)%mod, (Z*Z)%mod
            S, M = (4*X*Y2)%mod, (3*X*X + a*Z2*Z2)%mod
            Rx = (M*M - 2*S)%mod
            Ry = (M*(S - Rx) - 8*Y2*Y2)%mod
            Rz = (2*Y*Z)%mod
        if bit == '1':
            if Rz == 0: Rx, Ry, Rz = Bx, By, Bz
            else:
                X1, Y1, Z1 = Rx, Ry, Rz
                X2, Y2 = Bx, By
                Z1Z1 = (Z1*Z1)%mod
                U2, S2 = (X2 * Z1Z1)%mod, (Y2 * Z1Z1 * Z1)%mod
                if Rx == U2:
                    if Ry != S2: Rx, Ry, Rz = 0, 1, 0
                else:
                    H = (U2 - Rx)%mod
                    R = (S2 - Ry)%mod
                    H2 = (H*H)%mod
                    Rx_new = (R*R - H*H2 - 2*Rx*H2)%mod
                    Ry = (R*(Rx*H2 - Rx_new) - Ry*H*H2)%mod
                    Rx = Rx_new
                    Rz = (Z1*H)%mod
    return Rx, Ry, Rz

__LATEX_REPR__ = [
    "THEOREM: Projective Weierstrass Form",
    "∃ k ∈ Z  s.t.  P(n, G) = 0",
    "",
    "   P(n) = ( Gy² - Gx³ - a·Gx - b - k·n )²  +  ( Proj_Z(m·G) )²",
    "",
    "   Status: Deterministic (Proof by Geometric Group Law)"
]

def G_formula(n, a, b, Gx, Gy, m):
    lhs = (Gy**2) % n
    rhs = (Gx**3 + a*Gx + b) % n
    err_curve = lhs - rhs
    Rx, Ry, Rz = ec_point_mul_proj(m, a, n, Gx, Gy)
    return err_curve**2 + Rz**2
