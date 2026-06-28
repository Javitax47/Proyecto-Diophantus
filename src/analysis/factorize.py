"""
================================================================================
   DIOPHANTUS - FACTORIZACIÓN DE ENTEROS QUANTUM-READY (vía annealing)
================================================================================
Resuelve la ecuación diofántica  N = p · q  (p,q > 1) reduciéndola a la misma
formulación QUBO que se envía a un annealer cuántico (D-Wave), y la resuelve aquí
con RECOCIDO SIMULADO clásico sobre esa energía. Devuelve los factores y un
CERTIFICADO trivialmente re-verificable (p·q = N), comprobable por terceros con
`src.product.recheck` sin confiar en este solver.

  energía(p,q) = (N − p·q)²   (mínimo 0  ⟺  p·q = N)

con p, q impares ≥ 3 codificados en binario (N impar compuesto). El recocido usa,
además de los volteos de bit estándar, un MOVIMIENTO DE REPARACIÓN específico del
problema (fijado p, el mejor q es round(N/p)) que acelera mucho la convergencia.

Encuadre honesto (sin sensacionalismo):
  * El QUBO generado es EXACTAMENTE el input de un annealer cuántico: por eso
    "quantum-ready". El recocido aquí es CLÁSICO; no se ejecuta hardware cuántico.
  * Es la demo canónica de factorización por annealing (cf. trabajos D-Wave). NO
    bate a Pollard-rho/GNFS a escala criptográfica; los semiprimos BALANCEADOS
    (p≈q≈√N) son el caso duro, igual que en la factorización real.
  * Lo sólido y vendible: pipeline end-to-end ecuación→QUBO→solución→certificado
    re-verificable, y la conexión con la primalidad (Baillie-PSW) del proyecto.
"""

import math
import random

import sympy


def _build(N):
    pa = max(1, (int(math.isqrt(N)) + 1).bit_length())   # bits del factor pequeño
    qb = max(1, (N // 3 + 1).bit_length())               # bits del factor grande
    return pa, qb


def simulated_anneal_factor(N, restarts=60, iters=20000, repair_prob=0.35,
                            p_flip_bias=0.7, seeds=4):
    """Recocido simulado sobre energía (N−pq)². Devuelve (p, q, energy, stats).
    energy==0 ⟺ factorización exacta encontrada.

    Mejoras que rompen la pared estocástica: (a) movimiento de REPARACIÓN
    q:=round(N/p); (b) volteos SESGADOS a los bits de p (el factor pequeño manda,
    q se deriva); (c) BARRIDO DE SEMILLAS (reinicios aleatorios independientes)."""
    if N % 2 == 0:
        return 2, N // 2, 0, {'trivial': 'par'}
    pa, qb = _build(N)
    n = pa + qb

    def val(b, o, nb):
        return sum((1 << i) for i in range(nb) if b[o + i])

    def setval(b, o, nb, v):
        for i in range(nb):
            b[o + i] = (v >> i) & 1

    def pq(b):
        return 3 + 2 * val(b, 0, pa), 3 + 2 * val(b, pa, qb)

    def energy(b):
        p, q = pq(b)
        d = N - p * q
        return d * d

    best, bestbits, total_restarts = None, None, 0
    for s in range(seeds):
        rng = random.Random(s + 1)
        for r in range(restarts):
            total_restarts += 1
            b = [rng.randint(0, 1) for _ in range(n)]
            e = energy(b)
            T0 = float(N * N)
            for it in range(iters):
                T = T0 * ((1 - it / iters) ** 2) + 1e-9
                if rng.random() < repair_prob:                # reparación: q := round(N/p)
                    p, _ = pq(b)
                    Q = max(0, round((N / p - 3) / 2))
                    old = b[:]
                    setval(b, pa, qb, Q)
                    e2 = energy(b)
                    if e2 <= e:
                        e = e2
                    else:
                        b[:] = old
                else:
                    i = rng.randrange(pa) if rng.random() < p_flip_bias else rng.randrange(n)
                    b[i] ^= 1
                    e2 = energy(b)
                    if e2 <= e or rng.random() < math.exp(-min(50, (e2 - e) / T)):
                        e = e2
                    else:
                        b[i] ^= 1
                if e == 0:
                    break
            if best is None or e < best:
                best, bestbits = e, b[:]
            if best == 0:
                break
        if best == 0:
            break
    p, q = pq(bestbits)
    return p, q, best, {'n_vars': n, 'restarts_used': total_restarts}


def to_qubo(N, pmax=None):
    """Emite el QUBO quantum-ready de la factorización (lo que recibiría un
    annealer): sistema {p·q − N = 0} con p,q acotados, vía el exportador QUBO.
    Devuelve el dict de export_qubo. (El tamaño crece con N; para envío real.)"""
    from src.analysis.qubo import export_qubo
    pmax = pmax or (int(math.isqrt(N)) + 1)
    return export_qubo([f'p*q-{N}'], ['p', 'q'], {'p': (2, pmax), 'q': (2, N // 2 + 1)})


def factorize(N, **kw):
    """Factorización COMPLETA en primos (recursiva). Usa el recocido para partir
    compuestos y Baillie-PSW para reconocer primos. Devuelve lista de primos."""
    from src.analysis.primality import baillie_psw
    if N <= 1:
        return []
    factors = []
    stack = [N]
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if baillie_psw(m):
            factors.append(m)
            continue
        # sacar factores 2 triviales
        if m % 2 == 0:
            factors.append(2)
            stack.append(m // 2)
            continue
        p, q, e, _ = simulated_anneal_factor(m, **kw)
        if e != 0 or p <= 1 or q <= 1:
            # no se pudo partir dentro del presupuesto: se reporta como pendiente
            factors.append(('?', m))
            continue
        stack.extend([p, q])
    return sorted(factors, key=lambda x: (isinstance(x, tuple), x))


def solve_and_certify(N, **kw):
    """Factoriza N=p·q y emite un CERTIFICADO portable (testigo) re-verificable.
    Devuelve dict {found, p, q, certificate, prime_factors}."""
    from src.product import verifier
    from src.analysis.primality import baillie_psw
    p, q, e, stats = simulated_anneal_factor(N, **kw)
    if e != 0:
        return {'found': False, 'stats': stats}
    cert = verifier.certify_witness([f'p*q-{N}'], ['p', 'q'], {'p': p, 'q': q},
                                    f"{N} = {p}·{q} (factorización por annealing)")
    return {
        'found': True, 'p': p, 'q': q,
        'p_prime': bool(baillie_psw(p)), 'q_prime': bool(baillie_psw(q)),
        'certificate': cert, 'stats': stats,
    }
