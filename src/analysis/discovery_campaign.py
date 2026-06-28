"""
================================================================================
   DIOPHANTUS - CAMPAÑA DE DESCUBRIMIENTO (barrido de familias paramétricas)
================================================================================
El test de capacidad prueba INSTANCIAS sueltas. Esto barre FAMILIAS paramétricas
enteras: para cada valor del parámetro corre el motor de descubrimiento, CERTIFICA
el invariante hallado (verificación simbólica idéntica), lo normaliza y deduplica,
y produce un CATÁLOGO. Es la infraestructura para una contribución real de
matemática experimental: descubrir+certificar estructura de forma autónoma y luego
contrastar NOVEDAD (OEIS / literatura) sobre los candidatos.

Garantía honesta: TODO invariante reportado está verificado idénticamente
(Q(T(s)) = λ·Q(s) como identidad polinómica). El catálogo no afirma novedad por sí
mismo —eso requiere el contraste externo—, sólo certeza de conservación.
"""

import sympy

from src.analysis.discovery_engine import (
    find_conserved_quantities, verify_conserved, reduce_powers,
)


def _canonical(poly, syms):
    """Normaliza un invariante para deduplicar: contenido entero 1 y signo fijo
    (primer coeficiente no nulo positivo)."""
    p = sympy.expand(poly)
    P = sympy.Poly(p, *syms)
    c = sympy.gcd(list(P.coeffs())) if P.coeffs() else sympy.Integer(1)
    if c == 0:
        return p
    p = sympy.expand(p / c)
    P = sympy.Poly(p, *syms)
    lead = P.coeffs()[0] if P.coeffs() else 1
    if lead < 0:
        p = sympy.expand(-p)
    return p


def scan_instances(instances, eigenvalues=(1,)):
    """instances: lista de (label, transition_exprs, var_names, max_deg).
    Devuelve lista de hits {label, lam, invariant, verified}. Sólo se reportan
    invariantes VERIFICADOS idénticamente."""
    hits = []
    for label, T, vn, deg in instances:
        syms = sympy.symbols(vn)
        res = find_conserved_quantities(T, vn, deg, eigenvalues)
        nz = [(l, Q) for l, Q in res if sympy.Poly(Q, *syms).total_degree() > 0]
        essentials = reduce_powers([Q for _, Q in nz], vn)
        lam_of = {}
        for l, Q in nz:
            lam_of[_canonical(Q, syms)] = l
        for Q in essentials:
            cQ = _canonical(Q, syms)
            lam = lam_of.get(cQ, 1)
            if verify_conserved(Q, T, vn, lam):
                hits.append({'label': label, 'lam': lam, 'invariant': cQ, 'verified': True})
    return hits


# ---------------------------------------------------------------------------
#  Familias paramétricas
# ---------------------------------------------------------------------------

def family_norm_form(kmax=6):
    """Vieta/forma norma 2D, versión que MUEVE ambas coordenadas (companion):
    T=(y, k·y - x) conserva x²-k·x·y+y² (λ=1). Sin coordenadas fijas -> sin
    invariantes triviales. k=1 (~gato), k=3 (Markov-Fibonacci), etc."""
    x, y = sympy.symbols('x y')
    return [(f"norm k={k}", [y, k * y - x], ['x', 'y'], 2) for k in range(1, kmax + 1)]


def family_markov3(kmax=5):
    """Markov-Hurwitz 3D cíclico (Vieta+permutación, mueve todo):
    T=(y, z, k·y·z - x) conserva x²+y²+z²-k·x·y·z (λ=1)."""
    x, y, z = sympy.symbols('x y z')
    return [(f"markov3 k={k}", [y, z, k * y * z - x], ['x', 'y', 'z'], 3)
            for k in range(1, kmax + 1)]


def family_markov4(kmax=3):
    """Markov-Hurwitz 4D cíclico: T=(y,z,w,k·y·z·w - x) conserva
    x²+y²+z²+w²-k·x·y·z·w (λ=1)."""
    x, y, z, w = sympy.symbols('x y z w')
    return [(f"markov4 k={k}", [y, z, w, k * y * z * w - x], ['x', 'y', 'z', 'w'], 4)
            for k in range(1, kmax + 1)]


def family_symplectic2(mats=None):
    """Mapas lineales 2D con det=1 (simplécticos): conservan una forma cuadrática."""
    if mats is None:
        mats = [[[2, 1], [1, 1]], [[3, 2], [1, 1]], [[1, 1], [1, 2]], [[3, 1], [2, 1]]]
    x, y = sympy.symbols('x y')
    out = []
    for A in mats:
        det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        out.append((f"linmap {A} (det={det})",
                    [A[0][0] * x + A[0][1] * y, A[1][0] * x + A[1][1] * y], ['x', 'y'], 2))
    return out


def default_families():
    """Todas las familias del barrido por defecto."""
    return {
        'norm_form': family_norm_form(),
        'markov3': family_markov3(),
        'markov4': family_markov4(),
        'symplectic2': family_symplectic2(),
    }


# ---------------------------------------------------------------------------
#  Caza ampliada (familias menos charteadas) + censo
# ---------------------------------------------------------------------------

def family_generalized_markov(kmax=3, jmax=3):
    """Markov 2-parámetros T=(y,z, k·y·z - j·x). RESULTADO experimental: sólo j=1
    (la involución de Vieta que preserva el volumen) admite invariante; j!=1 rompe
    la integrabilidad y el motor no halla nada -> precisión de la frontera."""
    x, y, z = sympy.symbols('x y z')
    return [(f"genmarkov k={k},j={j}", [y, z, k * y * z - j * x], ['x', 'y', 'z'], 3)
            for k in range(1, kmax + 1) for j in range(1, jmax + 1)]


def scan_matrices(mats, max_deg=2):
    """Censo de mapas LINEALES enteros: para cada matriz, invariantes polinómicos
    certificados. instances etiquetadas por la matriz."""
    x, y, z = sympy.symbols('x y z')
    insts = []
    for A in mats:
        n = len(A)
        syms = [x, y, z][:n]
        T = [sum(A[i][j] * syms[j] for j in range(n)) for i in range(n)]
        vn = [s.name for s in syms]
        insts.append((f"mat {A}", T, vn, max_deg))
    return scan_instances(insts)


def det3(A):
    return (A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1])
            - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
            + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]))


def census_sl3z(bound=1, max_deg=2, limit=None):
    """Censo determinista de SL(3,Z) con entradas en [-bound,bound]: cuántas
    matrices det=1 admiten invariante cuadrático certificado.

    RESULTADO experimental (bound=2, muestreo amplio): ~54/130 con invariante,
    todos formas cuadráticas CLÁSICAS preservadas por el mapa lineal (teoría de
    formas bajo GL(n,Z)); muchas degeneradas (x², y²) por autovalores ±1.
    Conclusión honesta de la CAZA: el barrido amplio NO escapa de la estructura
    clásica — evidencia empírica de que los invariantes polinómicos de bajo grado
    de mapas enteros simples están agotados por la teoría conocida."""
    from itertools import product
    rng = range(-bound, bound + 1)
    total = 0
    hits = []
    count = 0
    for entries in product(rng, repeat=9):
        A = [list(entries[0:3]), list(entries[3:6]), list(entries[6:9])]
        if det3(A) != 1:
            continue
        total += 1
        e = scan_matrices([A], max_deg)
        if e:
            hits.append((A, [h['invariant'] for h in e]))
        count += 1
        if limit and count >= limit:
            break
    return {'total_det1': total, 'with_invariant': len(hits), 'examples': hits[:10]}


def run_campaign(families=None):
    """Corre el barrido y devuelve {familia: [hits...]} con todo verificado."""
    families = families or default_families()
    return {name: scan_instances(insts) for name, insts in families.items()}


def format_campaign(catalog):
    lines = []
    total = 0
    for fam, hits in catalog.items():
        lines.append(f"[{fam}]  {len(hits)} invariante(s) certificado(s)")
        for h in hits:
            lines.append(f"    {h['label']:18} -> Q = {h['invariant']}  (λ={h['lam']}, verificado)")
            total += 1
    lines.append(f"TOTAL: {total} invariantes certificados en {len(catalog)} familias.")
    return "\n".join(lines)
