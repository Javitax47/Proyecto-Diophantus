import sys
import os
import argparse

"""
=============================================================================
   MATH KERNELS V5.3 (UTF-8 Fix)
=============================================================================
"""

def get_dickson_core():
    return """
def dickson_eval(degree, P, mod):
    if degree == 0: return 2
    if degree == 1: return P % mod
    v, w = 2, P % mod # v=D_0, w=D_1
    # Ladder desde bit 2 (incluyendo el MSB explícito si queremos iterar todo, 
    # o saltando si inicializamos con el resultado del MSB).
    # La forma canónica robusta:
    for bit in bin(degree)[2:]:
        v2 = (v * v - 2) % mod
        vw = (v * w - P) % mod
        if bit == '0': 
            v, w = v2, vw
        else:          
            v, w = vw, (w * w - 2) % mod
    return v
"""

def get_ecpp_core():
    return """
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
"""

def generate_fermat_kernel(input_var):
    return get_dickson_core() + f"""
__LATEX_REPR__ = [
    "THEOREM: Fermat's Equation (Base 2)",
    "∃ k ∈ Z  s.t.",
    "",
    "   ( 2^({input_var}-1) - 1 - k·{input_var} )² = 0",
    "",
    "   Status: Probabilistic (Roots exist for Pseudoprimes)"
]

def G_formula({input_var}):
    if {input_var} < 2: return 1
    if {input_var} == 2: return 0
    if {input_var} % 2 == 0: return 1
    res = pow(2, {input_var} - 1, {input_var})
    return (res - 1)**2
"""

def generate_lucas_kernel(input_var):
    return get_dickson_core() + f"""
__LATEX_REPR__ = [
    "THEOREM: Strong Lucas Equation (Parameter P=3)",
    "∃ k ∈ Z  s.t.",
    "",
    "   ( D_{{{input_var}}}(3) - 3 - k·{input_var} )² = 0",
    "",
    "   Status: Robust (No shared roots with Fermat known)"
]

def G_formula({input_var}):
    if {input_var} < 2: return 1
    if {input_var} == 2: return 0
    if {input_var} == 3: return 0
    if {input_var} % 2 == 0: return 1
    val = dickson_eval({input_var}, 3, {input_var})
    return (val - 3)**2
"""

def generate_ecpp_kernel(input_var):
    return get_ecpp_core() + f"""
__LATEX_REPR__ = [
    "THEOREM: Projective Weierstrass Form",
    "∃ k ∈ Z  s.t.  P({input_var}, G) = 0",
    "",
    "   P({input_var}) = ( Gy² - Gx³ - a·Gx - b - k·{input_var} )²  +  ( Proj_Z(m·G) )²",
    "",
    "   Status: Deterministic (Proof by Geometric Group Law)"
]

def G_formula({input_var}, a, b, Gx, Gy, m):
    lhs = (Gy**2) % {input_var}
    rhs = (Gx**3 + a*Gx + b) % {input_var}
    err_curve = lhs - rhs
    Rx, Ry, Rz = ec_point_mul_proj(m, a, {input_var}, Gx, Gy)
    return err_curve**2 + Rz**2
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--type", required=True)
    parser.add_argument("--var", default="n")
    args = parser.parse_args()

    if args.type == 'fermat': code = generate_fermat_kernel(args.var)
    elif args.type == 'lucas': code = generate_lucas_kernel(args.var)
    elif args.type == 'ecpp': code = generate_ecpp_kernel(args.var)
        
    base = os.path.basename(args.file).replace('_formula.py', '')
    out = f"output/artifacts/{base}_{args.type}_closed.py"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    
    # FIX: Forzar UTF-8 para caracteres matemáticos
    with open(out, "w", encoding="utf-8") as f: 
        f.write(code)
    print(f"[OK] Kernel {args.type} -> {out}")

if __name__ == "__main__":
    main()