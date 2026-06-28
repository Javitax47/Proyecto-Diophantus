"""
================================================================================
   DIOPHANTUS - PROPUESTAS / RESULTADOS PARCIALES CERTIFICADOS
================================================================================
Emisor DISCIPLINADO de "propuestas" a problemas (incluidos abiertos). Por diseño
no puede confundirse con una solución total: cada propuesta lleva OBLIGATORIAMENTE

    CLAIM       : el enunciado
    SCOPE       : dónde está demostrado (acotado: n ≤ N, longitud ≤ L, grado ≤ d)
    STATUS      : 'teorema acotado certificado' | 'estructura certificada' |
                  'sin estructura (None)'  -- nunca 'resuelto'
    CERTIFICATE : testigos / cofactores / invariante -- re-verificable sin solver
    GAP         : lo que queda SIN probar para el caso general (explícito)

Tres clases de propuesta, según lo que el proyecto SÍ sabe hacer con rigor:

  (A) BANDA CERTIFICADA por testigos/UNSAT  (resultados parciales de problemas
      abiertos): Goldbach, Erdős–Straus, convergencia de Collatz hasta N,
      no-existencia de ciclos de Collatz hasta longitud L. El certificado es
      finito y comprobable por cualquiera con aritmética elemental.

  (B) ESTRUCTURA CERTIFICADA (invariante global) donde la hay: Pell, mapa del
      gato. El motor la descubre y se verifica IDÉNTICAMENTE (∀ semilla).

  (C) SIN ESTRUCTURA: en el régimen caótico/no integrable el motor devuelve
      None. Es la frontera honesta: los problemas abiertos duros son abiertos
      precisamente porque carecen de invariante polinómico de bajo grado, y por
      eso sólo admiten banda certificada (A), no invariante global (B).
"""

from fractions import Fraction

from src.analysis.primality import baillie_psw
from src.analysis.discovery_engine import (
    find_conserved_quantities, verify_conserved, reduce_powers,
)


def format_proposal(p):
    """Render legible de una propuesta (dict)."""
    lines = [
        f"CLAIM  : {p['claim']}",
        f"SCOPE  : {p['scope']}",
        f"STATUS : {p['status']}",
        f"CERT   : {p['certificate']}",
        f"GAP    : {p['gap']}",
    ]
    return "\n".join(lines)


# ===========================================================================
#  (A) BANDAS CERTIFICADAS de problemas ABIERTOS  (testigos / UNSAT)
# ===========================================================================

def goldbach_band(N):
    """Goldbach fuerte hasta N: todo par 4<=2n<=N es suma de dos primos.
    Certificado = un par (p,q) por cada par; re-verificable con primalidad."""
    witnesses = {}
    primes = _sieve(N)
    for m in range(4, N + 1, 2):
        for p in primes:
            if p > m // 2:
                break
            if (m - p) in primes_set(primes):
                witnesses[m] = (p, m - p)
                break
        if m not in witnesses:
            return None  # contraejemplo: Goldbach fallaría (no ocurre para N razonable)
    return {
        'claim': 'Todo entero par >= 4 es suma de dos primos (Goldbach fuerte).',
        'scope': f'Demostrado para todo par 2n con 4 <= 2n <= {N}.',
        'status': 'teorema acotado certificado',
        'certificate': f'{len(witnesses)} testigos (p,q); re-verificación: p+q=2n y p,q primos (Baillie-PSW).',
        'gap': 'El caso general (todo par, sin cota) permanece ABIERTO.',
        'witnesses': witnesses,
    }


def verify_goldbach_band(proposal):
    """Re-verificador PORTABLE: comprueba cada testigo sin confiar en el emisor."""
    for m, (p, q) in proposal['witnesses'].items():
        if p + q != m or not baillie_psw(p) or not baillie_psw(q):
            return False
    return True


def erdos_straus_band(N):
    """Erdős–Straus hasta N: para todo n>=2, 4/n = 1/x + 1/y + 1/z con x,y,z>=1.
    Certificado = una terna (x,y,z) por cada n; re-verificable con fracciones."""
    witnesses = {}
    for n in range(2, N + 1):
        t = _erdos_straus_witness(n)
        if t is None:
            return None
        witnesses[n] = t
    return {
        'claim': 'Para todo n >= 2, 4/n se escribe como 1/x + 1/y + 1/z (Erdős–Straus).',
        'scope': f'Demostrado para todo n con 2 <= n <= {N}.',
        'status': 'teorema acotado certificado',
        'certificate': f'{len(witnesses)} ternas (x,y,z); re-verificación: 1/x+1/y+1/z = 4/n (exacto).',
        'gap': 'El caso general (todo n) permanece ABIERTO.',
        'witnesses': witnesses,
    }


def verify_erdos_straus_band(proposal):
    """Re-verificador PORTABLE: fracciones exactas, sin solver."""
    for n, (x, y, z) in proposal['witnesses'].items():
        if min(x, y, z) < 1:
            return False
        if Fraction(1, x) + Fraction(1, y) + Fraction(1, z) != Fraction(4, n):
            return False
    return True


def collatz_convergence_band(N, max_steps=100000):
    """Convergencia de Collatz hasta N: todo 1<=n<=N alcanza 1. Certificado = el
    número de pasos por cada n; re-verificable iterando la órbita (finito)."""
    witnesses = {}
    for n in range(1, N + 1):
        steps = _collatz_steps(n, max_steps)
        if steps is None:
            return None
        witnesses[n] = steps
    return {
        'claim': 'La órbita de Collatz de todo entero >= 1 alcanza 1.',
        'scope': f'Demostrado para todo n con 1 <= n <= {N}.',
        'status': 'teorema acotado certificado',
        'certificate': f'{len(witnesses)} cuentas de pasos; re-verificación: iterar la órbita hasta 1.',
        'gap': 'Convergencia para todo n (y ausencia de divergencia) permanece ABIERTA.',
        'witnesses': witnesses,
    }


def verify_collatz_convergence_band(proposal, max_steps=100000):
    """Re-verificador PORTABLE: re-ejecuta cada órbita."""
    for n, steps in proposal['witnesses'].items():
        if _collatz_steps(n, max_steps) != steps:
            return False
    return True


def collatz_cycle_band(L, timeout_ms=15000):
    """No-existencia de ciclos no triviales de Collatz hasta longitud L.
    Certificado = veredicto UNSAT de Z3 por cada longitud (resultado conocido,
    reproducido como insatisfacibilidad de un sistema diofántico concreto)."""
    from src.analysis.collatz_cycles import certify_up_to
    proven, results = certify_up_to(L, timeout_ms)
    if proven == 0:
        return None
    return {
        'claim': 'Collatz no tiene ciclos no triviales (salvo {1,2}).',
        'scope': f'Demostrado para toda longitud de ciclo 1 <= len <= {proven}.',
        'status': 'teorema acotado certificado',
        'certificate': f'UNSAT de Z3 para longitudes 1..{proven} (sistema diofántico del ciclo).',
        'gap': 'Ausencia de ciclos de CUALQUIER longitud (y de divergencia) permanece ABIERTA.',
        'results': results,
        'proven': proven,
    }


# ===========================================================================
#  (B) ESTRUCTURA CERTIFICADA (invariante global) donde existe
# ===========================================================================

def structural_proposal(transition_exprs, var_names, claim, max_deg=2, eigenvalues=(1,)):
    """Intenta DESCUBRIR un invariante/cantidad conservada global del mapa y, si lo
    halla, lo verifica IDÉNTICAMENTE. Propuesta de clase (B) o (C) según resultado."""
    import sympy
    syms = sympy.symbols(var_names)
    res = find_conserved_quantities(transition_exprs, var_names, max_deg, eigenvalues)
    # Sólo invariantes NO triviales: el constante Q=1 satisface Q(T)=Q para λ=1
    # siempre y no aporta estructura; se descarta.
    verified = [(lam, Q) for lam, Q in res
                if verify_conserved(Q, transition_exprs, var_names, lam)
                and sympy.Poly(Q, *syms).total_degree() > 0]
    reduced = reduce_powers([Q for _, Q in verified], var_names) if verified else []
    if not reduced:
        return {
            'claim': claim,
            'scope': f'Búsqueda de invariante polinómico de grado <= {max_deg}.',
            'status': 'sin estructura (None)',
            'certificate': None,
            'gap': 'No hay invariante polinómico de bajo grado: régimen no integrable / caótico.',
        }
    lam_of = {Q: lam for lam, Q in verified}
    inv = reduced[0]
    return {
        'claim': claim,
        'scope': f'Invariante global de grado <= {max_deg}, verificado IDÉNTICAMENTE (∀ semilla).',
        'status': 'estructura certificada',
        'certificate': f'Q = {inv}  (λ = {lam_of.get(inv, "?")}); Q(T(s)) = λ·Q(s) exacto.',
        'gap': 'Es una identidad del mapa, no la resolución de un problema abierto.',
        'invariant': inv,
    }


# ===========================================================================
#  Helpers PORTABLES (aritmética elemental)
# ===========================================================================

def _sieve(N):
    sieve = bytearray([1]) * (N + 1)
    sieve[0:2] = b'\x00\x00'
    for i in range(2, int(N ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
    return [i for i in range(2, N + 1) if sieve[i]]


_PRIMES_SET_CACHE = {}

def primes_set(primes):
    key = id(primes)
    s = _PRIMES_SET_CACHE.get(key)
    if s is None:
        s = set(primes)
        _PRIMES_SET_CACHE[key] = s
    return s


def _erdos_straus_witness(n):
    """Busca (x,y,z) con 4/n = 1/x+1/y+1/z. Búsqueda acotada y exacta."""
    target = Fraction(4, n)
    # x: 1/x < 4/n  =>  x > n/4 ; 1/x >= (4/n)/3 => x <= 3n/4
    x_lo = n // 4 + 1
    x_hi = (3 * n) // 4 + 1
    for x in range(max(1, x_lo), x_hi + 1):
        r = target - Fraction(1, x)
        if r <= 0:
            continue
        # 1/y >= r/2 => y <= 2/r ; 1/y < r => y > 1/r
        y_lo = int(1 / r) + 1
        y_hi = int(2 / r) + 1
        for y in range(max(x, y_lo), y_hi + 1):
            rz = r - Fraction(1, y)
            if rz <= 0:
                continue
            if rz.numerator == 1:           # 1/z exacto
                return (x, y, rz.denominator)
    return None


def _collatz_steps(n, max_steps):
    """Pasos hasta alcanzar 1, o None si no en max_steps."""
    c = 0
    while n != 1 and c < max_steps:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        c += 1
    return c if n == 1 else None
