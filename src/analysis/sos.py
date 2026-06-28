"""
================================================================================
   DIOPHANTUS - CERTIFICADOS DE DESIGUALDAD: SUMA DE CUADRADOS (Positivstellensatz)
================================================================================
Tercer tipo de certificado portable del proyecto, tras el testigo (SAT) y el
Nullstellensatz (igualdad / UNSAT). Aquí: DESIGUALDAD. Certifica que un polinomio
es NO NEGATIVO exhibiéndolo como SUMA DE CUADRADOS (SOS):

    p(x) = sum_i  c_i * q_i(x)^2 ,   c_i >= 0   =>   p(x) >= 0 para todo x real.

Es la pieza que generaliza:
  - el Nullstellensatz (certificado de IGUALDAD, sum g_i p_i = 1) a DESIGUALDADES;
  - la función de Lyapunov LINEAL (lyapunov.py, forma cuadrática vía ecuación de
    Lyapunov) al caso NO LINEAL (drift polinómico de grado alto).

Búsqueda (sin SDP, sólo Z3 + álgebra racional):
  p = mᵀ G m con m el vector de monomios hasta grado d/2 y G simétrica. Igualar
  coeficientes (lineal en G) y pedir G semidefinida positiva (menores principales
  >= 0) se resuelve con Z3 sobre los racionales. De la G racional se extrae, por
  LDLᵀ, la SUMA DE CUADRADOS EXPLÍCITA -> certificado PORTABLE.

Re-verificación PORTABLE (sin solver): expandir sum c_i q_i² y comprobar que es p,
y que cada c_i >= 0. Pura álgebra y aritmética racional.

Honestidad (límites, importantes):
  - SOS es SÓLIDO pero NO COMPLETO: hay polinomios no negativos que NO son SOS
    (Motzkin: x⁴y²+x²y⁴+1-3x²y² >= 0 por AM-GM, pero no es SOS). El finder
    devuelve None en esos casos: no afirma nada, no miente.
  - Es de GRADO ACOTADO. Aumentar el grado agranda el SDP (aquí, el sistema Z3).
  - Para Collatz y compañía: que el finder devuelva None es el resultado esperado
    y honesto; un certificado SOS de bajo grado para Collatz resolvería Collatz.
"""

import sympy

try:
    import z3
    _HAVE_Z3 = True
except ImportError:
    _HAVE_Z3 = False


def _monomials(syms, half_deg):
    from itertools import combinations_with_replacement
    out = [sympy.Integer(1)]
    for deg in range(1, half_deg + 1):
        for combo in combinations_with_replacement(range(len(syms)), deg):
            m = sympy.Integer(1)
            for c in combo:
                m *= syms[c]
            out.append(m)
    return out


def _z3_to_rational(v):
    """Convierte un RatNumRef de Z3 a sympy.Rational exacto."""
    if z3.is_rational_value(v):
        return sympy.Rational(int(v.numerator_as_long()), int(v.denominator_as_long()))
    if z3.is_int_value(v):
        return sympy.Integer(int(v.as_long()))
    # valor algebraico: aproximar a racional cercano (no debería ocurrir en LP)
    return sympy.nsimplify(sympy.Rational(str(v.as_decimal(30)).rstrip('?')))


def sos_certificate(p, var_names, max_deg=2, timeout_ms=10000):
    """Busca un certificado SOS para p >= 0: p = sum c_i q_i² con c_i >= 0.
    Devuelve {'squares': [(c_i, q_i), ...]} (certificado portable) o None.
    Requiere Z3 para el finder (la re-verificación NO).

    ROBUSTO para formas cuadráticas (max_deg=2): rápido y exacto. Para grado
    superior la codificación PSD por determinantes crece mucho y Z3 puede agotar
    el `timeout_ms` -> devuelve None (sin afirmar nada). El caso de grado alto
    pertenece propiamente a un backend SDP (Positivstellensatz general)."""
    if not _HAVE_Z3:
        return None
    syms = list(sympy.symbols(var_names)) if len(var_names) > 1 else [sympy.Symbol(var_names[0])]
    p = sympy.expand(p)
    half = max_deg // 2
    monos = _monomials(syms, half)
    k = len(monos)
    # Gram simétrica de incógnitas
    G = [[z3.Real(f'g_{i}_{j}') if i <= j else None for j in range(k)] for i in range(k)]
    for i in range(k):
        for j in range(i):
            G[i][j] = G[j][i]
    s = z3.Solver()
    s.set("timeout", timeout_ms)
    # mᵀ G m  (como dict monomio-sympy -> expresión Z3 de coeficientes)
    coeff = {}
    for i in range(k):
        for j in range(k):
            term = sympy.expand(monos[i] * monos[j])
            for mono, c in term.as_coefficients_dict().items():
                coeff[mono] = coeff.get(mono, 0) + int(c) * G[i][j]
    # igualar a los coeficientes de p
    pdict = p.as_coefficients_dict()
    all_monos = set(coeff) | set(pdict)
    for mono in all_monos:
        lhs = coeff.get(mono, 0)
        rhs = int(pdict.get(mono, 0))
        s.add(lhs == rhs)
    # G PSD: menores principales líderes >= 0 (necesario; suficiente con la
    # extracción LDLᵀ posterior que comprueba D >= 0 exactamente).
    Gz = [[G[i][j] for j in range(k)] for i in range(k)]
    for t in range(1, k + 1):
        s.add(_z3_det([row[:t] for row in Gz[:t]]) >= 0)
    if s.check() != z3.sat:
        return None
    m = s.model()
    Gs = sympy.Matrix(k, k, lambda i, j: _z3_to_rational(m.eval(G[i][j], model_completion=True)))
    # extraer suma de cuadrados explícita por LDLᵀ (tolerante a pivotes cero, que
    # en una matriz PSD implican columna nula -> ese cuadrado tiene coeficiente 0)
    ld = _ldl_psd(Gs)
    if ld is None:
        return None
    L, D = ld
    mvec = sympy.Matrix(monos)
    squares = []
    for j in range(k):
        c = D[j]
        if c == 0:
            continue
        if c < 0:
            return None
        qj = sum(L[i, j] * monos[i] for i in range(k))   # (Lᵀ m)_j
        squares.append((c, sympy.expand(qj)))
    cert = {'squares': squares}
    return cert if verify_sos(p, cert, var_names) else None


def _ldl_psd(G):
    """LDLᵀ racional tolerante a pivotes cero. Para G PSD, un pivote cero fuerza
    columna nula (se omite); si no, G no es PSD-descomponible aquí -> None.
    Devuelve (L unitriangular inferior, D lista diagonal) con G = L·diag(D)·Lᵀ."""
    n = G.rows
    A = G.copy()
    L = sympy.eye(n)
    D = [sympy.Integer(0)] * n
    for j in range(n):
        d = sympy.nsimplify(A[j, j])
        D[j] = d
        if d == 0:
            for i in range(j + 1, n):
                if A[i, j] != 0:
                    return None
            continue
        for i in range(j + 1, n):
            L[i, j] = A[i, j] / d
        for i in range(j + 1, n):
            for kk in range(j + 1, n):
                A[i, kk] = A[i, kk] - L[i, j] * L[kk, j] * d
    return L, D


def _z3_det(M):
    """Determinante simbólico (expansión de Laplace) de una matriz de expr Z3."""
    n = len(M)
    if n == 1:
        return M[0][0]
    if n == 2:
        return M[0][0] * M[1][1] - M[0][1] * M[1][0]
    total = 0
    for j in range(n):
        minor = [row[:j] + row[j + 1:] for row in M[1:]]
        total += ((-1) ** j) * M[0][j] * _z3_det(minor)
    return total


def verify_sos(p, cert, var_names):
    """Re-verificador PORTABLE (sin solver): comprueba que sum c_i q_i² == p y que
    todo c_i >= 0. Si se cumple, p >= 0 para todo real -> certificado válido."""
    if cert is None or 'squares' not in cert:
        return False
    syms = list(sympy.symbols(var_names)) if len(var_names) > 1 else [sympy.Symbol(var_names[0])]
    acc = sympy.Integer(0)
    for c, q in cert['squares']:
        if c < 0:
            return False
        acc += c * q**2
    return sympy.expand(acc - sympy.expand(p)) == 0
