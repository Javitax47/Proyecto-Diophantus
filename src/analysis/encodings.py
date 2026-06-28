"""
================================================================================
   DIOPHANTUS - ESTRATEGIAS DE CODIFICACIÓN: ¿hay una "ecuación global" mejor?
================================================================================
Todo el proyecto se reduce a CÓMO codificamos un algoritmo en matemáticas. Hay
varias estrategias y NO existe una definitivamente mejor: cada una es óptima para
un OBJETIVO distinto. Este módulo las pone una al lado de otra, con medidas, y
expone el selector que elige la mejor según la estructura del problema.

Estrategias sobre la transición de un paso  x_{k+1} = step(x_k):

  (1) DESENROLLADO directo (unroll). Ejecuta los T pasos. Coste O(T) en tiempo,
      O(1)/O(n) en espacio si no se guarda la traza. Es lo mejor para CALCULAR un
      valor concreto cuando no hay estructura explotable.

  (2) FORMA CERRADA por exponenciación de matrices (sólo si la transición es AFÍN
      x->Ax+d). x_T = bloque de (M^T) con M=[[A,d],[0,1]]. Con exponenciación
      binaria son O(log T) multiplicaciones de matriz (n+1)x(n+1). ES LA ÚNICA que
      da resultados de n GRANDE más rápido — y sólo existe donde hay estructura
      lineal. Honestidad: el VALOR exacto tiene Θ(T) dígitos (no cabe para T
      astronómico); por eso el salto real es "valor mód m en O(log T)", o el valor
      cuando cabe. No hay atajo para el régimen no lineal.

  (3) β-COLLAPSE (empaquetado de Gödel). Reescribe "T pasos -> salida" como UNA
      ecuación diofántica con testigo (a,b). Es la "ecuación global", pero su
      coste NO desaparece: el testigo a CODIFICA LA TRAZA ENTERA, así que su
      tamaño en bits no baja del contenido de información de la traza (lo medimos).
      Su valor es TEÓRICO (mostrar que el problema es diofántico) y alimentar a un
      motor de certificados algebraicos, NO acelerar el cálculo.

Conclusión que el módulo demuestra con números: la "ecuación global definitiva"
(β-collapse) existe pero no acelera nada; la forma cerrada (2) sí acelera, pero
SÓLO donde hay estructura afín. La palanca es la estructura, no la codificación.
"""

import time

from src.analysis.trace_packer import pack_trace


# ---------------------------------------------------------------------------
#  (1) Desenrollado
# ---------------------------------------------------------------------------

def unroll_affine(A, d, x0, T, mod=None):
    """Aplica x->Ax+d exactamente T veces. O(T·n²)."""
    n = len(x0)
    x = list(x0)
    for _ in range(T):
        x = [sum(A[i][j] * x[j] for j in range(n)) + d[i] for i in range(n)]
        if mod is not None:
            x = [v % mod for v in x]
    return x


# ---------------------------------------------------------------------------
#  (2) Forma cerrada por exponenciación de matrices (estructura afín)
# ---------------------------------------------------------------------------

def _mat_mul(X, Y, mod):
    k = len(Y)
    out = [[sum(X[i][t] * Y[t][j] for t in range(k)) for j in range(len(Y[0]))]
           for i in range(len(X))]
    if mod is not None:
        out = [[v % mod for v in row] for row in out]
    return out


def _mat_pow(M, e, mod):
    n = len(M)
    R = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    B = [row[:] for row in M]
    while e > 0:
        if e & 1:
            R = _mat_mul(R, B, mod)
        B = _mat_mul(B, B, mod)
        e >>= 1
    return R


def closed_form_affine(A, d, x0, T, mod=None):
    """x_T para x->Ax+d en O(log T) multiplicaciones de matriz (exponenciación
    binaria del estado aumentado M=[[A,d],[0,1]]). Con `mod`, reduce en cada
    producto -> entradas acotadas -> realmente O(log T) aun para T astronómico.
    Sin `mod`, es exacto pero el valor tiene Θ(T) dígitos (sólo práctico si cabe)."""
    n = len(x0)
    M = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(n):
            M[i][j] = A[i][j]
        M[i][n] = d[i]
    M[n][n] = 1
    Mt = _mat_pow(M, T, mod)
    out = []
    for i in range(n):
        v = sum(Mt[i][j] * x0[j] for j in range(n)) + Mt[i][n]
        out.append(v % mod if mod is not None else v)
    return out


def verify_closed_form_affine(A, d, x0, T, mod=None):
    """Re-verificación: la forma cerrada O(log T) coincide con el desenrollado."""
    return closed_form_affine(A, d, x0, T, mod) == unroll_affine(A, d, x0, T, mod)


# ---------------------------------------------------------------------------
#  (3) β-collapse: medir el coste del testigo (no encoge)
# ---------------------------------------------------------------------------

def beta_collapse_cost(step, start, max_steps=2000):
    """Empaqueta la traza de `step` desde `start` en (a,b) y mide el TAMAÑO del
    testigo. Devuelve {'T','a_bits','b_bits','trace_info_bits'} para mostrar que
    el testigo no baja del contenido de información de la traza."""
    xs = [start]
    x = start
    for _ in range(max_steps):
        x = step(x)
        xs.append(x)
        if x == 1:                 # convenio: parada al llegar a 1 (p.ej. Collatz)
            break
    a, b = pack_trace(xs)
    trace_info = sum(max(1, int(v).bit_length()) for v in xs)
    return {'T': len(xs) - 1, 'a_bits': int(a).bit_length(),
            'b_bits': int(b).bit_length(), 'trace_info_bits': trace_info}


# ---------------------------------------------------------------------------
#  Selector + comparador
# ---------------------------------------------------------------------------

def best_strategy(is_affine):
    """Elige la codificación óptima según la estructura detectada. Honesto sobre
    la complejidad que cada una alcanza."""
    if is_affine:
        return {
            'strategy': 'forma cerrada (exponenciación de matrices)',
            'time': 'O(log T) multiplicaciones',
            'reaches_large_n': True,
            'why': 'la estructura afín permite saltar a x_T sin recorrer los pasos',
        }
    return {
        'strategy': 'desenrollado (con memoización donde aplique)',
        'time': 'O(T)',
        'reaches_large_n': False,
        'why': 'sin estructura explotable hay que ejecutar los pasos; β-collapse no acelera',
    }


def compare_affine(A, d, x0, T, mod=None):
    """Mide desenrollado vs forma cerrada para el mismo T afín. Devuelve dict con
    tiempos y si coinciden."""
    t0 = time.perf_counter()
    r_unroll = unroll_affine(A, d, x0, T, mod)
    t_unroll = time.perf_counter() - t0
    t0 = time.perf_counter()
    r_closed = closed_form_affine(A, d, x0, T, mod)
    t_closed = time.perf_counter() - t0
    return {
        'T': T,
        'match': r_unroll == r_closed,
        't_unroll': t_unroll,
        't_closed': t_closed,
        'speedup': (t_unroll / t_closed) if t_closed > 0 else float('inf'),
    }
