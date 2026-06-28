"""
================================================================================
   DIOPHANTUS - ESTRUCTURA DONDE NO HAY INVARIANTE: FUNCIONES DE LYAPUNOV
================================================================================
El motor de descubrimiento (discovery_engine) busca CANTIDADES CONSERVADAS:
igualdades  Q(T(s)) = λ·Q(s)  (estructura de sistemas integrables/conservativos).
Cuando no existe tal invariante polinómico de bajo grado, devuelve None.

Este módulo encuentra la estructura de DESIGUALDAD, que es la que tienen los
sistemas NO conservativos (disipativos, contractivos, terminantes): una función
de Lyapunov  V(s) >= 0  que DECRECE,  V(T(s)) - V(s) <= 0  (estricta fuera del
punto fijo). Donde no hay cantidad conservada, puede haber cantidad MONÓTONA — y
una función de Lyapunov certifica convergencia / estabilidad / terminación, que
es justo lo que una identidad conservada no puede dar.

Para un mapa LINEAL x -> A x (A de Schur, autovalores |λ|<1) la forma cuadrática
de Lyapunov  V = xᵀPx  se obtiene EXACTAMENTE resolviendo la ECUACIÓN DE LYAPUNOV
DISCRETA  AᵀPA - P = -Q  (Q definida positiva, p. ej. I): un sistema LINEAL en
las entradas de P, resoluble con álgebra racional (sin SDP, sin coma flotante).

Certificado PORTABLE (re-verificable sin solver, en la línea de certificates.py):
  - P, Q racionales simétricas;
  - identidad exacta  V(Ax) - V(x) = -xᵀQx  (expandir y comparar);
  - P, Q definidas positivas por menores principales líderes (Sylvester, exacto).
Si se aceptan, V certifica que toda trayectoria converge al origen.

Frontera honesta:
  - Sólo da estructura cuando A es de Schur. Conservativo (área-preservante, p.ej.
    el gato de Arnold) -> no hay Lyapunov PD (devuelve None) pero SÍ cantidad
    conservada: ambos métodos son COMPLEMENTARIOS. Expansivo -> ninguno.
  - Para mapas NO lineales, el análogo es el Positivstellensatz/SOS (V SOS, drift
    SOS) vía SDP — requiere un solver SDP (no disponible aquí); es la extensión
    natural pero ya no es álgebra lineal exacta.
"""

import sympy


def _is_pd(M):
    """Definida positiva por el criterio de Sylvester (menores principales
    líderes > 0). Exacto sobre racionales (M simétrica)."""
    n = M.shape[0]
    for k in range(1, n + 1):
        if M[:k, :k].det() <= 0:
            return False
    return True


def find_lyapunov(A, var_names, Q=None):
    """Para el mapa lineal x -> A x, halla V = xᵀPx de Lyapunov resolviendo la
    ecuación de Lyapunov discreta AᵀPA - P = -Q (Q PD, por defecto I). Devuelve
    un dict-certificado {'P','Q','V','drift'} si P resulta definida positiva
    (=> A es de Schur => convergencia certificada), o None si no la hay."""
    A = sympy.Matrix(A)
    n = A.shape[0]
    if Q is None:
        Q = sympy.eye(n)
    else:
        Q = sympy.Matrix(Q)
    # P simétrica de incógnitas
    ps = {}
    P = sympy.zeros(n, n)
    for i in range(n):
        for j in range(i, n):
            s = sympy.Symbol(f'p{i}_{j}')
            ps[(i, j)] = s
            P[i, j] = s
            P[j, i] = s
    M = A.T * P * A - P + Q          # = 0
    eqs = [M[i, j] for i in range(n) for j in range(i, n)]
    sol = sympy.solve(eqs, list(ps.values()), dict=True)
    if not sol:
        return None
    Ps = P.subs(sol[0])
    if Ps.free_symbols or not _is_pd(Ps) or not _is_pd(Q):
        return None
    xs = sympy.Matrix(sympy.symbols(var_names))
    V = sympy.expand((xs.T * Ps * xs)[0])
    Ax = A * xs
    Vnext = sympy.expand((Ax.T * Ps * Ax)[0])
    drift = sympy.expand(Vnext - V)            # debe ser -xᵀQx
    return {'P': Ps, 'Q': Q, 'V': V, 'drift': drift}


def verify_lyapunov(A, cert, var_names):
    """Re-verificador PORTABLE (sin solver): comprueba que el certificado es
    válido por pura álgebra y aritmética racional:
      (1) AᵀPA - P + Q == 0  (identidad exacta);
      (2) drift == -xᵀQx  (la cantidad decrece exactamente en -xᵀQx);
      (3) P y Q definidas positivas (Sylvester).
    Si las tres se cumplen, V >= 0 decrece estrictamente -> convergencia al origen."""
    if cert is None:
        return False
    A = sympy.Matrix(A)
    P, Q = sympy.Matrix(cert['P']), sympy.Matrix(cert['Q'])
    if sympy.expand((A.T * P * A - P + Q)) != sympy.zeros(*P.shape):
        return False
    xs = sympy.Matrix(sympy.symbols(var_names))
    if sympy.expand(cert['drift'] + (xs.T * Q * xs)[0]) != 0:
        return False
    return _is_pd(P) and _is_pd(Q)
