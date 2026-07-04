"""
================================================================================
   DIOPHANTUS - EXPORTADOR A QUBO (backend de optimización binaria / annealing)
================================================================================
Tercer backend del compilador, junto a LaTeX y CAS:
convierte un sistema diofántico {p_i(v)=0} en un problema QUBO

        minimizar  x^T Q x + c     sobre  x ∈ {0,1}^n

cuyos MÍNIMOS GLOBALES (energía 0) son EXACTAMENTE las soluciones del sistema.
Es el formato que consumen los annealers (D-Wave) y QAOA. NO es "programación
cuántica" ni la democratiza; es un exportador honesto y citable que conecta la
arithmetización con la optimización combinatoria.

Construcción (estándar, exacta):
  1. Cada variable entera v_j con rango [lo,hi] se codifica en binario:
        v_j = lo + Σ_b 2^b · x_{j,b}      (x binarios)
  2. El sistema se satisface  ⟺  H(v) = Σ_i w_i · p_i(v)² = 0, y como cada término
     es ≥ 0, los mínimos de H (valor 0) son justo las soluciones.
  3. Sustituyendo la codificación e imponiendo idempotencia x²=x se obtiene un
     PUBO (polinomio en binarios). Si su grado > 2 se CUADRATIZA (reducción de
     Rosenberg: cada producto x_a·x_b se sustituye por un auxiliar y con una
     penalización P·(x_a x_b − 2x_a y − 2x_b y + 3y), nula sii y = x_a·x_b).
  4. Se emite la matriz Q (dict {(i,j):coef}) y el offset c.

Garantía: para instancias acotadas, `verify_qubo` comprueba por fuerza bruta que
argmin(QUBO) ⟺ soluciones del sistema (la corrección del exportador es auditable).
"""

import itertools

import sympy


# ---------------------------------------------------------------------------
#  1-2. Codificación binaria y objetivo H = Σ w_i p_i²
# ---------------------------------------------------------------------------

def binary_encoding(var_names, bounds):
    """bounds: {var: (lo, hi)}. Devuelve (enc, bin_names) donde enc[var] es la
    expresión binaria lo + Σ 2^b x_b y bin_names la lista ordenada de binarios."""
    enc = {}
    bin_names = []
    for v in var_names:
        lo, hi = bounds[v]
        span = hi - lo
        nbits = max(1, span.bit_length()) if span > 0 else 1
        bits = []
        for b in range(nbits):
            name = f"{v}__{b}"
            bits.append(sympy.Symbol(name))
            bin_names.append(name)
        enc[sympy.Symbol(v)] = lo + sum((1 << b) * bits[b] for b in range(nbits))
    return enc, bin_names


def objective(polys, var_names, bounds, weights=None):
    """H = Σ w_i p_i² sustituyendo la codificación binaria. Devuelve (H_expr, bin_names)."""
    enc, bin_names = binary_encoding(var_names, bounds)
    local = {n: sympy.Symbol(n) for n in var_names}
    weights = weights or [1] * len(polys)
    H = sympy.Integer(0)
    for w, p in zip(weights, polys):
        pe = p if isinstance(p, sympy.Expr) else sympy.sympify(str(p), locals=local)
        H += w * pe.subs(enc) ** 2
    return sympy.expand(H), bin_names


# ---------------------------------------------------------------------------
#  3. PUBO (idempotencia x²=x) y cuadratización de Rosenberg
# ---------------------------------------------------------------------------

def to_pubo(H_expr, bin_names):
    """Convierte H en PUBO: dict {frozenset(indices): coef entero} aplicando
    idempotencia (cada binario aparece a lo sumo una vez por monomio)."""
    syms = [sympy.Symbol(n) for n in bin_names]
    P = sympy.Poly(H_expr, *syms) if H_expr != 0 else None
    pubo = {}
    if P is None:
        return pubo
    for expo, c in zip(P.monoms(), P.coeffs()):
        key = frozenset(i for i, e in enumerate(expo) if e > 0)
        pubo[key] = pubo.get(key, 0) + int(c)
    return {k: v for k, v in pubo.items() if v != 0}


def _penalty(pubo):
    return 1 + sum(abs(v) for v in pubo.values())


def quadratize(pubo, n_vars):
    """Reduce un PUBO a QUBO (grado ≤ 2) por reducción de Rosenberg. Devuelve
    (qubo, n_total) con qubo dict {frozenset: coef} de grado ≤ 2 y n_total el nº
    de binarios tras añadir auxiliares."""
    pubo = dict(pubo)
    n = n_vars
    while True:
        high = [k for k in pubo if len(k) >= 3]
        if not high:
            break
        # par (a,b) más frecuente entre los monomios de alto grado
        from collections import Counter
        pairs = Counter()
        for k in high:
            for a, b in itertools.combinations(sorted(k), 2):
                pairs[(a, b)] += 1
        (a, b), _ = pairs.most_common(1)[0]
        y = n
        n += 1
        P = _penalty(pubo)
        # sustituir {a,b} por {y} en todo monomio que contenga ambos
        new = {}
        for k, c in pubo.items():
            if a in k and b in k:
                k2 = (k - {a, b}) | {y}
                new[frozenset(k2)] = new.get(frozenset(k2), 0) + c
            else:
                new[k] = new.get(k, 0) + c
        # penalización P·(x_a x_b − 2x_a y − 2x_b y + 3y)
        for key, coef in [(frozenset({a, b}), P), (frozenset({a, y}), -2 * P),
                          (frozenset({b, y}), -2 * P), (frozenset({y}), 3 * P)]:
            new[key] = new.get(key, 0) + coef
        pubo = {k: v for k, v in new.items() if v != 0}
    return pubo, n


# ---------------------------------------------------------------------------
#  4. Matriz QUBO
# ---------------------------------------------------------------------------

def to_qubo_matrix(qubo):
    """De un dict {frozenset: coef} de grado ≤ 2 a (Q, offset) con Q={(i,j):coef}
    (i≤j; lineal en la diagonal) y offset la constante."""
    Q = {}
    offset = 0
    for k, c in qubo.items():
        if len(k) == 0:
            offset += c
        elif len(k) == 1:
            (i,) = tuple(k)
            Q[(i, i)] = Q.get((i, i), 0) + c
        elif len(k) == 2:
            i, j = sorted(k)
            Q[(i, j)] = Q.get((i, j), 0) + c
        else:
            raise ValueError("QUBO requiere grado ≤ 2; cuadratiza primero")
    return Q, offset


def export_qubo(polys, var_names, bounds, weights=None):
    """Pipeline completo: sistema diofántico -> QUBO. Devuelve dict con
    {'Q','offset','n_vars','bin_names','pubo_degree'}."""
    H, bin_names = objective(polys, var_names, bounds, weights)
    pubo = to_pubo(H, bin_names)
    deg = max((len(k) for k in pubo), default=0)
    qubo, n_total = quadratize(pubo, len(bin_names))
    Q, offset = to_qubo_matrix(qubo)
    return {'Q': Q, 'offset': offset, 'n_vars': n_total,
            'bin_names': bin_names, 'pubo_degree': deg}


# ---------------------------------------------------------------------------
#  Validación (auditable): energía y fuerza bruta
# ---------------------------------------------------------------------------

def energy(Q, offset, bits):
    """Energía x^T Q x + offset para un vector de bits."""
    e = offset
    for (i, j), c in Q.items():
        e += c * bits[i] * bits[j]
    return e


def brute_force_min(Q, offset, n):
    """Mínimo de la energía sobre {0,1}^n (sólo para n pequeño). Devuelve
    (energia_min, [estados que la alcanzan])."""
    best = None
    argmins = []
    for bits in itertools.product([0, 1], repeat=n):
        e = energy(Q, offset, bits)
        if best is None or e < best:
            best = e
            argmins = [bits]
        elif e == best:
            argmins.append(bits)
    return best, argmins


def decode(bits, var_names, bounds, bin_names):
    """Recupera los valores enteros de un vector de bits."""
    out = {}
    pos = {n: i for i, n in enumerate(bin_names)}
    for v in var_names:
        lo, hi = bounds[v]
        span = hi - lo
        nbits = max(1, span.bit_length()) if span > 0 else 1
        val = lo
        for b in range(nbits):
            val += (1 << b) * bits[pos[f"{v}__{b}"]]
        out[v] = val
    return out


def verify_qubo(polys, var_names, bounds, weights=None):
    """Auditoría por fuerza bruta: comprueba que argmin(QUBO) con energía 0 son
    EXACTAMENTE las soluciones (acotadas) del sistema. Devuelve (ok, detalle)."""
    res = export_qubo(polys, var_names, bounds, weights)
    Q, offset, n = res['Q'], res['offset'], res['n_vars']
    emin, argmins = brute_force_min(Q, offset, n)
    local = {nm: sympy.Symbol(nm) for nm in var_names}
    pexprs = [p if isinstance(p, sympy.Expr) else sympy.sympify(str(p), locals=local) for p in polys]

    def is_solution(assign):
        subs = {sympy.Symbol(k): v for k, v in assign.items()}
        return all(sympy.expand(pe.subs(subs)) == 0 for pe in pexprs)

    # soluciones reales por enumeración del dominio entero
    ranges = [range(bounds[v][0], bounds[v][1] + 1) for v in var_names]
    real_sol = set()
    for combo in itertools.product(*ranges):
        assign = dict(zip(var_names, combo))
        if is_solution(assign):
            real_sol.add(tuple(combo))

    # estados de mínimo (sólo los de energía 0 cuentan como solución del sistema)
    qubo_sol = set()
    if emin == 0:
        for bits in argmins:
            dec = decode(bits, var_names, bounds, res['bin_names'])
            qubo_sol.add(tuple(dec[v] for v in var_names))

    ok = (emin == 0) == (len(real_sol) > 0) and qubo_sol == real_sol
    return ok, {'energy_min': emin, 'qubo_solutions': sorted(qubo_sol),
                'real_solutions': sorted(real_sol), 'n_vars': n, 'pubo_degree': res['pubo_degree']}
