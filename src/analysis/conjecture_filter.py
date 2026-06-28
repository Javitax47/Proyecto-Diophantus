"""
================================================================================
   DIOPHANTUS - FILTRO DE NOVEDAD / INTERÉS DE CONJETURAS
================================================================================
Aproxima el "contraste con la literatura" para las conjeturas del conjeturador,
de forma HONESTA y sin acceso externo (OEIS/Ramanujan DB están bloqueados aquí).
Combina tres señales legítimas:

  (1) BASE DE DATOS CLÁSICA: marca como CONOCIDA toda PCF que coincida (salvo
      reescala trivial) con una fórmula famosa hardcodeada (Brouncker, CFs de e).
  (2) PRIOR POR CONSTANTE: las fracciones continuas de e y π están exhaustivamente
      catalogadas; ζ(3), Catalan, γ NO -> un hit en una constante poco charteada es
      mucho más probablemente novedoso. Se pondera con un prior por constante.
  (3) TASA DE CONVERGENCIA: criterio del paper NeurIPS 2024 de la Ramanujan Machine
      -- las fórmulas interesantes convergen rápido (muchos dígitos correctos por
      paso). Se mide dígitos/paso.

Salida: conjeturas DEDUPLICADAS por clase de Möbius, sin las clásicas, ordenadas
por una puntuación de interés. ADVERTENCIA HONESTA: "no clásica conocida aquí" NO
es "demostrada nueva"; la verificación autoritativa de novedad sigue siendo el
contraste externo con la literatura (paso humano).
"""

import mpmath as mp

from src.analysis.conjecturer import pcf_value, named_constants


# (1) Prior de novedad por constante: 0 = exhaustivamente catalogada, 1 = poco charteada.
CONSTANT_NOVELTY_PRIOR = {
    'sqrt2': 0.02, 'pi': 0.10, 'e': 0.10, 'ln2': 0.30, 'pi^2': 0.35,
    'euler_gamma': 0.80, 'zeta3': 0.85, 'catalan': 0.90,
}

# (2) PCFs clásicas conocidas (a_coeffs, b_coeffs, constante). Conservador: solo
# fórmulas genuinamente de libro de texto.
CLASSICAL_DB = [
    ([0, 0, 1], [1, 2], 'pi'),     # Brouncker: a(n)=n², b(n)=2n+1 -> 4/π
    ([0, -1, 0], [3, 1], 'e'),     # familia de Euler para e
    ([0, -1, 0], [2, 1], 'e'),
    ([0, -1, 0], [1, 1], 'e'),
]


def _reduced(coeffs):
    """Coeficientes normalizados por su gcd con signo (para comparar salvo reescala)."""
    from math import gcd
    g = 0
    for c in coeffs:
        g = gcd(g, int(c))
    if g == 0:
        return tuple(int(c) for c in coeffs)
    first_nz = next((int(c) for c in coeffs if c != 0), 0)
    sign = -1 if first_nz < 0 else 1
    return tuple(sign * (int(c) // g) for c in coeffs)


def is_classical(hit):
    """True si el hit coincide (salvo reescala de a) con una PCF clásica conocida."""
    a = _reduced(hit['a_coeffs'])
    b = tuple(int(c) for c in hit['b_coeffs'])
    for ca, cb, const in CLASSICAL_DB:
        if hit['constant'] == const and _reduced(ca) == a and tuple(cb) == tuple(b):
            return True
    return False


def convergence_digits_per_step(a_coeffs, b_coeffs, d1=40, d2=120, dps=80):
    """Dígitos correctos por paso de profundidad: (corr(d2)-corr(d1))/(d2-d1).
    Mayor = convergencia más rápida = más interesante (criterio Ramanujan/NeurIPS)."""
    with mp.workdps(dps):
        L = pcf_value(a_coeffs, b_coeffs, depth=max(400, d2 * 3), dps=dps)
        if L is None:
            return 0.0
        v1 = pcf_value(a_coeffs, b_coeffs, depth=d1, dps=dps)
        v2 = pcf_value(a_coeffs, b_coeffs, depth=d2, dps=dps)
        if v1 is None or v2 is None:
            return 0.0

        def corr(v):
            err = abs(v - L)
            if err == 0:
                return dps
            return float(-mp.log10(err))
        return max(0.0, (corr(v2) - corr(v1)) / (d2 - d1))


def mobius_class(hit):
    """Clave de deduplicación por clase de Möbius: misma constante + relación
    reducida por gcd con signo. Conjeturas proporcionales colapsan a una."""
    rel = hit['relation']
    return (hit['constant'], _reduced(rel))


def mobius_value_class(hit, dps=40, skip=6, take=12):
    """Clave de dedup por VALOR NUMÉRICO (huella robusta a precisión vía la cola de la
    fracción continua regular): colapsa identificaciones distintas (a,b diferentes) que
    convergen al MISMO número, de-inflando el recuento de candidatas. Es una huella de
    valor, no una canonicalización GL(2,Z) completa (las variantes de signo, con cola
    desplazada, pueden quedar separadas)."""
    p0, p1, p2, p3 = hit['relation']
    name = hit['constant']
    if name not in CONSTANT_NOVELTY_PRIOR and name not in named_constants():
        return (name, _reduced(hit['relation']))
    with mp.workdps(dps):
        c = named_constants()[name]
        den = mp.mpf(p1) + p3 * c
        if den == 0:
            return (name, _reduced(hit['relation']))
        v = -(mp.mpf(p0) + p2 * c) / den
        x = v
        cf = []
        for _ in range(skip + take + 4):
            fl = mp.floor(x)
            cf.append(int(fl))
            frac = x - fl
            if abs(frac) < mp.mpf(10) ** (-(dps - 6)):
                break
            x = 1 / frac
        tail = tuple(cf[skip:skip + take])
        return (name, tail)


def score(hit, conv_rate):
    """Puntuación de interés: prior de la constante * (1 + tasa de convergencia)."""
    prior = CONSTANT_NOVELTY_PRIOR.get(hit['constant'], 0.5)
    return prior * (1.0 + conv_rate)


def rank_candidates(hits, compute_convergence=True, strong_dedup=True):
    """Deduplica por clase de Möbius, descarta clásicas conocidas, puntúa y ordena.
    Con strong_dedup=True usa la clase de Möbius del VALOR (colapsa variantes
    triviales que inflan el recuento). Devuelve dicts {hit, status, convergence, score}."""
    seen = set()
    out = []
    for h in hits:
        key = mobius_value_class(h) if strong_dedup else mobius_class(h)
        if key in seen:
            continue
        seen.add(key)
        if is_classical(h):
            out.append({'hit': h, 'status': 'CONOCIDA (clásica)', 'convergence': None, 'score': 0.0})
            continue
        conv = convergence_digits_per_step(h['a_coeffs'], h['b_coeffs']) if compute_convergence else 0.0
        out.append({'hit': h, 'status': 'CANDIDATA (no contrastada con literatura)',
                    'convergence': round(conv, 3), 'score': round(score(h, conv), 4)})
    candidates = [o for o in out if o['status'].startswith('CANDIDATA')]
    known = [o for o in out if o['status'].startswith('CONOCIDA')]
    candidates.sort(key=lambda o: o['score'], reverse=True)
    return candidates + known


def format_ranked(ranked, top=15):
    lines = [f"{'#':>2}  {'score':>7}  {'conv':>5}  {'const':<12}  {'estado':<34}  fórmula"]
    for i, o in enumerate(ranked[:top], 1):
        h = o['hit']
        conv = '' if o['convergence'] is None else f"{o['convergence']:.2f}"
        lines.append(f"{i:>2}  {o['score']:>7}  {conv:>5}  {h['constant']:<12}  "
                     f"{o['status']:<34}  a={h['a_coeffs']} b={h['b_coeffs']} = {h['closed_form']}")
    return "\n".join(lines)
