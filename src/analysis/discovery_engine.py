"""
================================================================================
   DIOPHANTUS - MOTOR DE DESCUBRIMIENTO ALGEBRAICO (Fase 4, §10 del informe)
================================================================================
Invierte la flecha: en vez de INYECTAR una identidad (Weierstrass, Dickson...)
como plantilla, DESCUBRE automaticamente identidades polinomicas cerradas que
satisface la trayectoria de un programa, por pura algebra lineal.

Metodo (sin plantilla): dada una sucesion de vectores de estado s_0, s_1, ...,
se forman todos los monomios de las variables de estado hasta grado d; un
polinomio P(vars) = sum c_m * monomio_m se ANULA en TODA la trayectoria sii el
vector de coeficientes (c_m) esta en el NUCLEO de la matriz [monomio_m(s_j)]_{j,m}.
Cada vector del nucleo es un INVARIANTE descubierto. Se valida fuera de muestra
(en puntos de la trayectoria no usados para descubrirlo) para descartar
artefactos de muestreo finito.

Esto realiza el criterio de exito de la Fase 4: para una recurrencia no trivial
(p. ej. Pell -> x^2-2y^2=1 ; Fibonacci -> identidad de Matiyasevich) el motor
devuelve una identidad cerrada que NADIE inyecto.
"""

from itertools import combinations_with_replacement

import sympy


def monomial_exponents(n_vars, max_deg):
    """Exponentes de todos los monomios en n_vars variables hasta grado max_deg
    (incluido el término constante, grado 0)."""
    exps = []
    for deg in range(max_deg + 1):
        for combo in combinations_with_replacement(range(n_vars), deg):
            e = [0] * n_vars
            for c in combo:
                e[c] += 1
            exps.append(tuple(e))
    return exps


def _eval_monomials(state, exps):
    row = []
    for e in exps:
        v = 1
        for var_idx, power in enumerate(e):
            if power:
                v *= state[var_idx] ** power
        row.append(v)
    return row


def find_invariants(states, var_names, max_deg):
    """Descubre invariantes polinomicos (hasta grado max_deg) que se anulan en
    TODOS los `states`. Devuelve (invariantes, exps): invariantes es una lista de
    expresiones SymPy con coeficientes enteros."""
    n = len(var_names)
    exps = monomial_exponents(n, max_deg)
    M = sympy.Matrix([_eval_monomials(s, exps) for s in states])
    syms = sympy.symbols(var_names)

    invariants = []
    for vec in M.nullspace():
        # limpiar denominadores -> coeficientes enteros
        dens = [sympy.fraction(sympy.nsimplify(c))[1] for c in vec]
        scale = sympy.ilcm(*[int(d) for d in dens]) if dens else 1
        coeffs = [sympy.Integer(c * scale) for c in vec]
        g = sympy.igcd(*[int(c) for c in coeffs]) or 1
        coeffs = [c / g for c in coeffs]
        poly = sum(coeffs[i] * sympy.prod([syms[v] ** exps[i][v] for v in range(n)])
                   for i in range(len(exps)))
        invariants.append(sympy.expand(poly))
    return invariants, exps


def find_transition_invariants(states, state_var_names, max_deg):
    """Descubre invariantes de TRANSICION: polinomios P(x, x') que se anulan en
    TODOS los pares de estados consecutivos (x_i, x_{i+1}). Mucho mas general que
    los invariantes de un solo estado: captura la relacion de transicion incluso
    de programas A TROZOS / no lineales (p. ej. collatz, cuya transicion
    par/impar es el producto de las relaciones de cada rama).

    Las variables del siguiente estado se nombran `<v>p`. Devuelve
    (invariantes, exps, combined_names)."""
    pairs = []
    for i in range(len(states) - 1):
        cur = states[i] if isinstance(states[i], (list, tuple)) else (states[i],)
        nxt = states[i + 1] if isinstance(states[i + 1], (list, tuple)) else (states[i + 1],)
        pairs.append(tuple(cur) + tuple(nxt))
    combined = list(state_var_names) + [v + "p" for v in state_var_names]
    invs, exps = find_invariants(pairs, combined, max_deg)
    return invs, exps, combined


def find_conserved_quantities(transition_exprs, var_names, max_deg, eigenvalues=(1, -1)):
    """Descubre PRIMERAS INTEGRALES del mapa de transicion: polinomios Q tales que
    Q(T(s)) = lambda * Q(s) IDENTICAMENTE (no solo en una orbita), para lambda en
    `eigenvalues`. lambda=1 -> cantidad conservada; lambda=-1 -> conservada salvo
    signo (su cuadrado se conserva). Mucho mas fuerte que un invariante de orbita:
    vale para CUALQUIER semilla.

    `transition_exprs[v]` es la expresion del siguiente valor de la variable v
    (en terminos de var_names) — la transicion compilada del programa.

    Devuelve lista de (lambda, Q) con Q expresion SymPy de coeficientes enteros.
    Metodo: Q = sum c_m * monomio_m; Q(T(s)) - lambda*Q debe ser el polinomio
    cero -> sus coeficientes (lineales en c_m) forman un sistema homogeneo cuyo
    nucleo da las Q conservadas."""
    n = len(var_names)
    syms = sympy.symbols(var_names)
    exps = monomial_exponents(n, max_deg)
    monos = [sympy.prod([syms[v] ** e[v] for v in range(n)]) for e in exps]
    cs = sympy.symbols(f'c0:{len(exps)}')
    Q = sum(cs[i] * monos[i] for i in range(len(monos)))
    subs = {syms[v]: transition_exprs[v] for v in range(n)}
    # simultaneous=True es CRITICO: subs por defecto es secuencial y cascadea
    # (x->3x+4y y luego y->... reemplazaria las y recien introducidas),
    # corrompiendo Q(T). Con simultaneous se sustituye el estado completo a la vez.
    Qnext = Q.subs(subs, simultaneous=True)

    found = []
    for lam in eigenvalues:
        E = sympy.expand(Qnext - lam * Q)
        # coeficientes de E como polinomio en las variables de estado:
        # cada uno es lineal en los c_i; igualarlos a 0 da el sistema homogeneo.
        polyE = sympy.Poly(E, *syms) if E != 0 else None
        lin_eqs = polyE.coeffs() if polyE is not None else []
        # matriz [d(eq)/d(c_i)]
        rows = [[sympy.diff(eq, ci) for ci in cs] for eq in lin_eqs]
        if not rows:
            continue
        Mc = sympy.Matrix(rows)
        for vec in Mc.nullspace():
            dens = [sympy.fraction(sympy.nsimplify(c))[1] for c in vec]
            scale = sympy.ilcm(*[int(d) for d in dens]) if dens else 1
            coeffs = [sympy.Integer(c * scale) for c in vec]
            g = sympy.igcd(*[int(c) for c in coeffs]) or 1
            poly = sympy.expand(sum((coeffs[i] / g) * monos[i] for i in range(len(monos))))
            if poly != 0:
                found.append((lam, poly))
    return found


def reduce_powers(invariants, var_names):
    """Filtro de PRESENTACION (modesto y correcto): de un conjunto de invariantes
    quita los que son potencia pura `c·Q^k` de otro de menor grado ya presente
    (p. ej. (x²-2y²)² si x²-2y² esta). NO intenta el conjunto generador minimo del
    algebra de invariantes (eso es teoria de invariantes; una reduccion ingenua
    por base de Groebner del IDEAL seria INCORRECTA, ya que las cantidades
    conservadas forman un algebra, no un ideal)."""
    syms = sympy.symbols(var_names)
    nz = [i for i in invariants
          if i != 0 and sympy.Poly(i, *syms).total_degree() > 0]
    nz.sort(key=lambda p: sympy.Poly(p, *syms).total_degree())
    kept = []
    for P in nz:
        dP = sympy.Poly(P, *syms).total_degree()
        is_power = False
        for Q in kept:
            dQ = sympy.Poly(Q, *syms).total_degree()
            if 0 < dQ < dP and dP % dQ == 0:
                r = sympy.cancel(P / Q ** (dP // dQ))
                if not r.free_symbols and r != 0:
                    is_power = True
                    break
        if not is_power:
            kept.append(P)
    return kept


def verify_conserved(Q, transition_exprs, var_names, lam):
    """True si Q(T(s)) == lam*Q(s) IDENTICAMENTE (verificacion simbolica exacta).
    Confirma que Q es una primera integral (lam=1) o anti-integral (lam=-1)."""
    syms = sympy.symbols(var_names)
    subs = {syms[v]: transition_exprs[v] for v in range(len(var_names))}
    return sympy.expand(Q.subs(subs, simultaneous=True) - lam * Q) == 0


def affine_transition_exprs(A, d, var_names):
    """Construye las expresiones de transicion de un mapa afin x'=A x + d."""
    syms = sympy.symbols(var_names)
    n = len(var_names)
    return [sum(A[j][l] * syms[l] for l in range(n)) + d[j] for j in range(n)]


def invariant_holds_on(invariant, states, var_names):
    """True si `invariant` se anula en todos los `states` (validacion exacta)."""
    syms = sympy.symbols(var_names)
    for s in states:
        subs = {syms[i]: s[i] for i in range(len(var_names))}
        if sympy.expand(invariant.subs(subs)) != 0:
            return False
    return True
