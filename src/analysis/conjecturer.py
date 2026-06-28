"""
================================================================================
   DIOPHANTUS - CONJETURADOR (generación automática de conjeturas, estilo Ramanujan)
================================================================================
Genera CONJETURAS matemáticas nuevas (no las demuestra) buscando fracciones
continuas polinómicas (PCF) que igualen, a altísima precisión, una transformación
de Möbius de una constante fundamental (π, e, ζ(3), Catalan, ln2, γ, ...). Es el
método de la Ramanujan Machine (PNAS 2024, NeurIPS 2024), aquí sobre la maquinaria
del proyecto (recurrencias/precisión arbitraria).

PCF:  b0 + a1/(b1 + a2/(b2 + ...)),  con a(n), b(n) polinomios de coeficientes
enteros pequeños. Se evalúa a `dps` dígitos y se IDENTIFICA su límite L: si PSLQ
halla una relación entera pequeña  p0 + p1·L + p2·c + p3·L·c = 0  para alguna
constante c, entonces  L = −(p0 + p2·c)/(p1 + p3·c)  (Möbius de c) — una conjetura.

Garantías honestas:
  - SÓLIDO numéricamente: una conjetura emitida coincide con su forma cerrada a
    `dps` dígitos (re-verificable subiendo la precisión). NO es una demostración.
  - La NOVEDAD (¿es una identidad ya conocida?) la decide la comparación externa
    con la literatura / base de la Ramanujan Machine — igual que OEIS. La mayoría
    de hits serán identidades clásicas (rediscovery); un hit no catalogado es un
    candidato a conjetura nueva.
"""

import sys as _sys
import time as _time
from itertools import product as _product, islice as _islice

import mpmath as mp


def _write_checkpoint(path, done, total, payload):
    """Escribe un checkpoint JSON de forma ATÓMICA (escribe a .tmp y renombra), para que
    un corte a mitad de escritura no corrompa el fichero. `payload`: dict serializable."""
    import json as _json
    import os as _os
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        _json.dump({'done': int(done), 'total': int(total), **payload}, f)
    _os.replace(tmp, path)


def _hms(s):
    """Segundos -> 'H:MM:SS'."""
    s = int(max(0, s))
    return f"{s // 3600:d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


class _Progress:
    """Barra de progreso ligera (a stderr, en sitio con '\\r'): porcentaje, hechos/total,
    velocidad, transcurrido, ETA y un texto extra (p.ej. hits en vivo). Silenciosa si
    enabled=False (uso como librería / tests)."""

    def __init__(self, total, label="caza", every=2.0, enabled=True, stream=None):
        self.total = max(1, int(total))
        self.label = label
        self.every = every
        self.enabled = enabled
        self.stream = stream or _sys.stderr
        self.t0 = _time.time()
        self.last = 0.0
        self.done = 0

    def update(self, done, extra=""):
        if not self.enabled:
            return
        self.done = done
        now = _time.time()
        if now - self.last < self.every and done < self.total:
            return
        self.last = now
        el = now - self.t0
        rate = done / el if el > 0 else 0.0
        frac = min(1.0, done / self.total)
        eta = (self.total - done) / rate if rate > 0 else 0.0
        filled = int(24 * frac)
        bar = "#" * filled + "." * (24 - filled)
        self.stream.write(
            f"\r[{self.label}] |{bar}| {frac * 100:5.1f}%  {done:,}/{self.total:,}  "
            f"{rate:,.0f}/s  transcurrido {_hms(el)}  ETA {_hms(eta)}{extra}   ")
        self.stream.flush()

    def close(self, extra=""):
        if not self.enabled:
            return
        self.update(self.done, extra)
        self.stream.write("\n")
        self.stream.flush()


def _poly(coeffs):
    """Devuelve la función n -> sum coeffs[i]*n^i (coeficientes enteros)."""
    def f(n):
        x = mp.mpf(0)
        p = mp.mpf(1)
        for c in coeffs:
            x += c * p
            p *= n
        return x
    return f


def pcf_value(a_coeffs, b_coeffs, depth=400, dps=60):
    """Evalúa la PCF b0 + a1/(b1+a2/(b2+...)) con a(n)=poly(a_coeffs), b(n)=poly(b_coeffs).
    Devuelve mpmath.mpf o None si degenera (división por ~0 / no converge)."""
    with mp.workdps(dps):
        a = _poly(a_coeffs)
        b = _poly(b_coeffs)
        try:
            val = mp.mpf(0)
            for n in range(depth, 0, -1):
                den = b(n) + val
                if den == 0:
                    return None
                val = a(n) / den
            res = b(0) + val
            if not mp.isfinite(res):
                return None
            return +res
        except (ZeroDivisionError, ValueError, OverflowError):
            return None


def _poly_int(coeffs, n):
    """Evalúa sum coeffs[i]*n^i en ARITMÉTICA ENTERA EXACTA (coeffs y n enteros)."""
    x = 0
    p = 1
    for c in coeffs:
        x += int(c) * p
        p *= n
    return x


def pcf_convergents(a_coeffs, b_coeffs, depth=400):
    """Convergentes ENTEROS EXACTOS p_n/q_n de la PCF b0 + a1/(b1+a2/(b2+...)).
    Recurrencia de los numeradores/denominadores (Wallis): con a(n),b(n) enteros,
    p_n y q_n son enteros exactos (bigints de Python). Devuelve (p_n, q_n) finales
    o None si q_n se anula. Base: p_{-1}=1, p_0=b(0); q_{-1}=0, q_0=1."""
    b0 = _poly_int(b_coeffs, 0)
    p_prev, p_cur = 1, b0          # p_{-1}, p_0
    q_prev, q_cur = 0, 1           # q_{-1}, q_0
    for n in range(1, depth + 1):
        an = _poly_int(a_coeffs, n)
        bn = _poly_int(b_coeffs, n)
        p_prev, p_cur = p_cur, bn * p_cur + an * p_prev
        q_prev, q_cur = q_cur, bn * q_cur + an * q_prev
    if q_cur == 0:
        return None
    return p_cur, q_cur


def irrationality_delta(a_coeffs, b_coeffs, depth=200, dps=200, value=None):
    """Mide la calidad DIOFÁNTICA de la PCF: la medida de irracionalidad efectiva
        δ = -ln|q̃_n·L - p̃_n| / ln|q̃_n|,
    con convergentes enteros exactos p_n/q_n REDUCIDOS por su gcd (p̃,q̃ = p/g, q/g) y
    L el límite a alta precisión. Criterio del paper Arnold Math. J. 2024 (Ramanujan
    Machine):  δ > 0  =>  L es IRRACIONAL  y  μ(L) ≲ 1 + 1/δ.

    CLAVE: (1) la reducción por gcd es imprescindible -- los convergentes crudos de una
    PCF comparten un factor común enorme (lcm) y sin reducir δ sale negativo aunque la
    PCF pruebe irracionalidad (caso Apéry). (2) Se muestrea δ a la mayor profundidad cuyo
    error siga por encima del suelo de precisión (si no, |L-p/q| se satura y δ colapsa).
    Devuelve float δ (estimación a la profundidad válida más honda) o None si degenera.
    δ≈0 (Brouncker) = sin info de irracionalidad; δ>0 (Apéry/ζ(3)) = prueba."""
    from math import gcd
    with mp.workdps(dps):
        L = value if value is not None else pcf_value(
            a_coeffs, b_coeffs, depth=max(depth * 3, dps * 4), dps=dps)
        if L is None or not mp.isfinite(L):
            return None
        floor = mp.mpf(10) ** -(int(dps * 0.85))   # por encima de esto el error es fiable
        b0 = _poly_int(b_coeffs, 0)
        p_prev, p_cur = 1, b0
        q_prev, q_cur = 0, 1
        best = None
        for n in range(1, depth + 1):
            an = _poly_int(a_coeffs, n)
            bn = _poly_int(b_coeffs, n)
            p_prev, p_cur = p_cur, bn * p_cur + an * p_prev
            q_prev, q_cur = q_cur, bn * q_cur + an * q_prev
            if q_cur == 0:
                break
            if n % 4 and n < depth:           # muestrea cada pocas profundidades
                continue
            g = gcd(p_cur, q_cur) or 1
            qr = abs(q_cur) // g
            if qr <= 1:
                continue
            err = abs(L - mp.mpf(p_cur) / q_cur)
            if err <= floor:                  # error saturado por la precisión -> parar
                break
            resid = qr * err                  # = |q̃ L - p̃|
            if resid <= 0 or not mp.isfinite(resid):
                continue
            best = float(-mp.log(resid) / mp.log(qr))
        return best


def annotate_delta(records, depth=150, dps=220, cap=None, progress=False):
    """Añade a cada record (dict con 'a_coeffs','b_coeffs') su medida de irracionalidad
    δ en la clave 'delta' (float, o None si no aplica). Se aplica SOLO a los hits ya
    deduplicados (no al bucle caliente), así que el coste alto-dps es asumible.
    `cap`: si se da, solo anota los primeros `cap` records (el resto delta=None)."""
    prog = _Progress(len(records) or 1, label="δ irracionalidad", every=1.0, enabled=progress)
    for i, r in enumerate(records):
        if cap is not None and i >= cap:
            r['delta'] = None
            continue
        try:
            r['delta'] = irrationality_delta(r['a_coeffs'], r['b_coeffs'], depth=depth, dps=dps)
        except (ValueError, RuntimeError, OverflowError):
            r['delta'] = None
        prog.update(i + 1)
    prog.close()
    return records


def analyze_linear_forms(records, basis_names=None, dps=120, depth=None,
                         min_constants=2, extra_basis=None, progress=False):
    """POST-PROCESO: para cada record (con 'a_coeffs','b_coeffs'), RECOMPUTA el límite L
    a ALTA precisión y prueba si es una FORMA LINEAL entera de varias constantes
    (identify_linear). Devuelve la lista de hallazgos {a_coeffs,b_coeffs,value,...lineal}
    con al menos `min_constants` constantes en juego. Pensado para correr sobre el JSON
    de una caza ya hecha (no hace falta re-ejecutar la caza).

    `basis_names`: nombres de named_constants() a usar (None = todas). `extra_basis`:
    lista de (nombre, valor mpmath) extra, p.ej. ('pi^3', mp.pi**3)."""
    base = None
    if basis_names is not None:
        allc = named_constants()
        base = [n for n in basis_names if n in allc]
    out = []
    prog = _Progress(len(records) or 1, label="formas lineales", every=1.0, enabled=progress)
    for i, r in enumerate(records):
        a, b = r.get('a_coeffs'), r.get('b_coeffs')
        if a is None or b is None:
            prog.update(i + 1)
            continue
        d = depth if depth is not None else max(600, dps * 6)
        L = pcf_value(a, b, depth=d, dps=dps)
        lin = identify_linear(L, constants=base, dps=dps, extra_basis=extra_basis)
        if lin is not None and len(lin['constants']) >= min_constants:
            out.append({'a_coeffs': a, 'b_coeffs': b, 'value': mp.nstr(L, min(dps, 40)), **lin})
        prog.update(i + 1)
    prog.close()
    return out


def named_constants():
    """Constantes fundamentales para identificar (nombre -> valor mpmath).
    ζ(5)/ζ(7): su irracionalidad es un PROBLEMA ABIERTO -> objetivos de conjetura de
    alto valor (un δ>0 los probaría)."""
    return {
        'pi': mp.pi, 'e': mp.e, 'zeta3': mp.zeta(3), 'catalan': mp.catalan,
        'ln2': mp.ln(2), 'euler_gamma': mp.euler, 'pi^2': mp.pi**2, 'sqrt2': mp.sqrt(2),
        'zeta5': mp.zeta(5), 'zeta7': mp.zeta(7),
    }


def identify(value, constants=None, dps=60, maxcoeff=10**5, maxsteps=10**4):
    """Intenta identificar `value` como Möbius de una constante c vía PSLQ sobre
    [1, value, c, value*c]. Devuelve dict {constant, relation, closed_form} o None."""
    if value is None:
        return None
    with mp.workdps(dps):
        # CRÍTICO: calcular las constantes DENTRO del contexto de precisión; si no,
        # named_constants() las computaría a la precisión ambiente (p.ej. 15 dígitos)
        # y PSLQ infra-detectaría relaciones a `dps` dígitos.
        constants = constants if constants is not None else named_constants()
        for name, c in constants.items():
            try:
                rel = mp.pslq([mp.mpf(1), value, c, value * c],
                              maxcoeff=maxcoeff, maxsteps=maxsteps)
            except (ValueError, RuntimeError):
                rel = None
            if rel and (rel[1] != 0 or rel[3] != 0):
                p0, p1, p2, p3 = rel
                # NO degenerada: si p0*p3 == p1*p2, la constante se cancela y value es
                # racional (no es una identidad genuina sobre c) -> se descarta.
                if p0 * p3 - p1 * p2 == 0:
                    continue
                # forma cerrada: value = -(p0 + p2*c)/(p1 + p3*c)
                closed = f"-({p0} + {p2}*{name}) / ({p1} + {p3}*{name})"
                # verificación numérica del ajuste
                cf = -(mp.mpf(p0) + p2 * c) / (mp.mpf(p1) + p3 * c)
                if mp.almosteq(cf, value, rel_eps=mp.mpf(10) ** -(dps - 8)):
                    return {'constant': name, 'relation': [int(x) for x in rel],
                            'closed_form': closed}
    return None


def identify_linear(value, constants=None, dps=80, maxcoeff=10**4, maxsteps=10**4,
                    extra_basis=None):
    """Identifica `value` como FORMA LINEAL entera de varias constantes a la vez:
    busca p0 + p1·value + Σ qᵢ·cᵢ = 0  vía PSLQ sobre [1, value, c1, c2, ...].
    Entonces  value = -(p0 + Σ qᵢ cᵢ)/p1  -- una combinación racional-lineal de las
    constantes (p.ej. value = π + ζ(3), o 2·value = π² − 7·ζ(3)). Generaliza `identify`
    (Möbius de UNA constante) a relaciones MULTI-constante: un generador de conjeturas
    de 'formas lineales' (clase a la que pertenecen ζ(3), ζ(5) en la teoría de Apéry/
    Zudilin). `extra_basis`: lista de (nombre, valor) extra (p.ej. ('pi^3', mp.pi**3)).
    Devuelve {kind:'linear', constants:[...], relation:[...], closed_form} o None.

    HONESTO: con base grande PSLQ puede dar falsos positivos -> se re-verifica el ajuste
    a `dps` dígitos y se exige que ≥2 constantes (o 1 constante no trivial) intervengan."""
    if value is None:
        return None
    with mp.workdps(dps):
        if not mp.isfinite(value):
            return None
        # CRÍTICO (como en identify): recalcular constantes A ESTA precisión. Acepta
        # dict {nombre: valor}, lista de nombres, o None (=todas). Las constantes
        # conocidas se RECOMPUTAN a `dps` aunque el dict venga a baja precisión.
        allc = named_constants()
        if constants is None:
            base = dict(allc)
        elif isinstance(constants, dict):
            base = {k: (allc[k] if k in allc else v) for k, v in constants.items()}
        else:
            base = {k: allc[k] for k in constants}
        if extra_basis:
            for nm, val in extra_basis:
                base[nm] = val
        names = list(base.keys())
        vec = [mp.mpf(1), value] + [base[n] for n in names]
        try:
            rel = mp.pslq(vec, maxcoeff=maxcoeff, maxsteps=maxsteps)
        except (ValueError, RuntimeError):
            return None
        if not rel:
            return None
        p0, p1 = rel[0], rel[1]
        qs = rel[2:]
        if p1 == 0:                       # value debe intervenir
            return None
        if all(q == 0 for q in qs):       # alguna constante debe intervenir (si no, racional)
            return None
        # re-verificación numérica del ajuste
        approx = -(mp.mpf(p0) + sum(mp.mpf(q) * base[n] for q, n in zip(qs, names))) / p1
        if not mp.almosteq(approx, value, rel_eps=mp.mpf(10) ** -(dps - 10)):
            return None
        used = [n for q, n in zip(qs, names) if q != 0]
        terms = [f"{p0}"] + [f"{q:+d}*{n}" for q, n in zip(qs, names) if q != 0]
        closed = f"({' '.join(terms)}) / {-p1}"
        return {'kind': 'linear', 'constants': used, 'relation': [int(x) for x in rel],
                'basis': names, 'closed_form': closed}


# ---------------------------------------------------------------------------
#  Identificación SIN OBJETIVO (target-free): descubre la estructura del límite
#  sin especificar una constante. ¿Es racional? ¿algebraico? ¿Möbius de algo
#  conocido? ¿o un candidato a constante NUEVA (transcendental no catalogado)?
# ---------------------------------------------------------------------------

def _poly_eval_int(coeffs_high_first, x):
    """Evalúa un polinomio entero (coeficientes de mayor a menor grado) por Horner."""
    r = mp.mpf(0)
    for c in coeffs_high_first:
        r = r * x + c
    return r


def value_fingerprint(v, dps=40, skip=2, take=15):
    """Huella robusta de un real arbitrario (sin constante): la cola de su fracción
    continua REGULAR. Dos PCFs que convergen al MISMO número comparten esta huella
    -> permite detectar COLISIONES (identidades PCF↔PCF) sin saber qué es el número."""
    with mp.workdps(dps):
        x = +v
        cf = []
        for _ in range(skip + take + 6):
            fl = mp.floor(x)
            cf.append(int(fl))
            frac = x - fl
            if abs(frac) < mp.mpf(10) ** -(dps - 6):
                break
            x = 1 / frac
        return tuple(cf[skip:skip + take])


def identify_open(value, dps=60, max_alg_degree=4, alg_maxcoeff=10**6,
                  try_named=True, constants=None, linear_basis=None, linear_maxcoeff=2000):
    """Identificación SIN especificar objetivo. Determina la NATURALEZA del límite L:
      kind='rational'  -> raíz de polinomio entero de grado 1 (se descarta: aburrido).
      kind='algebraic' -> raíz de polinomio entero de grado 2..max_alg_degree (φ, √2,
                          raíces de x³−x−1, ...). Descubrimiento sin objetivo.
      kind='named'     -> (etiqueta opcional) Möbius de una constante conocida.
      kind='linear'    -> (si linear_basis) FORMA LINEAL entera de varias constantes
                          (p.ej. value = π + ζ(3)); la clase tipo-Apéry/Zudilin.
      kind='unknown'   -> converge, finito, pero nada de lo anterior: CANDIDATO a
                          constante nueva (sospechoso, NO probado).
    Devuelve dict {kind, ...} o None si degenera/no converge."""
    if value is None:
        return None
    with mp.workdps(dps):
        if not mp.isfinite(value):
            return None
        tol = mp.mpf(10) ** -(int(dps * 0.8))
        # valor ~0 -> racional trivial (findpoly rechazaría el vector [1,0,...,0])
        if abs(value) < mp.mpf(10) ** -(dps // 2):
            return {'kind': 'rational', 'poly': [1, 0], 'value': '0'}

        def _fp(v, d):
            try:
                return mp.findpoly(v, d, maxcoeff=alg_maxcoeff, tol=tol)
            except (ValueError, RuntimeError):
                return None

        # 1) ¿racional? (grado 1) -> aburrido
        p1 = _fp(value, 1)
        if p1:
            return {'kind': 'rational', 'poly': [int(c) for c in p1],
                    'value': mp.nstr(value, min(dps, 40))}
        # 2) ¿algebraico de grado MÍNIMO 2..max? (raíz de polinomio entero)
        for d in range(2, max_alg_degree + 1):
            p = _fp(value, d)
            if p and int(p[0]) != 0:                      # líder no nulo => grado real d
                resid = _poly_eval_int([mp.mpf(c) for c in p], value)
                if abs(resid) < tol * 1000:               # raíz confirmada
                    return {'kind': 'algebraic', 'degree': d, 'poly': [int(c) for c in p],
                            'value': mp.nstr(value, min(dps, 40))}
        # 3) etiqueta amable (opcional): Möbius de constante conocida
        if try_named:
            ident = identify(value, constants, dps=dps)
            if ident is not None:
                return {'kind': 'named', 'value': mp.nstr(value, min(dps, 40)), **ident}
        # 4) (opcional) forma LINEAL multi-constante (clase tipo-Apéry/Zudilin)
        if linear_basis:
            lin = identify_linear(value, constants=linear_basis, dps=dps,
                                  maxcoeff=linear_maxcoeff)
            if lin is not None:
                return {'value': mp.nstr(value, min(dps, 40)), **lin}
        # 5) desconocido: converge pero no es racional/algebraico-bajo/nombrado/lineal
        return {'kind': 'unknown', 'value': mp.nstr(value, min(dps, 40))}


def search(a_degree=2, b_degree=1, coeff_range=(-3, 3), depth=300, dps=50,
           constants=None, max_hits=None):
    """Barre PCFs con coeficientes enteros pequeños y devuelve las conjeturas
    (PCF -> forma cerrada en una constante) halladas. Deduplicadas por forma cerrada."""
    constants = constants or named_constants()
    lo, hi = coeff_range
    rng = list(range(lo, hi + 1))
    hits = []
    seen = set()
    a_space = list(_product(rng, repeat=a_degree + 1))
    b_space = list(_product(rng, repeat=b_degree + 1))
    for ac in a_space:
        if all(v == 0 for v in ac):
            continue
        for bc in b_space:
            if bc[0] == 0 and len(bc) == 1:
                continue
            val = pcf_value(list(ac), list(bc), depth=depth, dps=dps)
            ident = identify(val, constants, dps=dps)
            if ident is None:
                continue
            key = (ident['constant'], tuple(ident['relation']))
            if key in seen:
                continue
            seen.add(key)
            hits.append({'a_coeffs': list(ac), 'b_coeffs': list(bc),
                         'value': mp.nstr(val, 20), **ident})
            if max_hits and len(hits) >= max_hits:
                return hits
    return hits


# ---------------------------------------------------------------------------
#  Pre-cribado en FLOAT64 (etapa rápida; la GPU-portable)
# ---------------------------------------------------------------------------
import math as _math


def _poly_f(coeffs):
    def f(n):
        x = 0.0
        p = 1.0
        for c in coeffs:
            x += c * p
            p *= n
        return x
    return f


def pcf_value_float(a_coeffs, b_coeffs, depth=400):
    """Evalúa la PCF en doble precisión NATIVA (rápida, ~15-16 dígitos). Devuelve
    float o None si degenera/diverge. NOTA: solo alcanza ~15 dígitos y las PCF de
    convergencia LENTA (p.ej. Brouncker ~1/n) no llegan a ese límite -> el cribado
    favorece las de convergencia RÁPIDA (justo las 'interesantes')."""
    a = _poly_f(a_coeffs)
    b = _poly_f(b_coeffs)
    val = 0.0
    for n in range(depth, 0, -1):
        den = b(n) + val
        if abs(den) < 1e-290:
            return None
        val = a(n) / den
        if abs(val) > 1e150:
            return None
    r = b(0) + val
    return r if _math.isfinite(r) else None


def _screen_hit(value_f, const_floats, screen_maxcoeff=64, dps=15):
    """Criba barata: ¿es `value_f` (float) una Möbius de pequeño coeficiente de
    alguna constante? Usa PSLQ a baja precisión. True si pasa (candidata a etapa 2)."""
    if value_f is None or not _math.isfinite(value_f):
        return False
    with mp.workdps(dps):
        v = mp.mpf(value_f)
        for c in const_floats:
            try:
                rel = mp.pslq([mp.mpf(1), v, c, v * c],
                              maxcoeff=screen_maxcoeff, maxsteps=200)
            except (ValueError, RuntimeError):
                rel = None
            if rel and (rel[1] != 0 or rel[3] != 0):
                p0, p1, p2, p3 = rel
                if p0 * p3 - p1 * p2 != 0:     # no degenerada
                    return True
    return False


# ---------------------------------------------------------------------------
#  Barrido PARALELO (multiproceso; la caza es embarrassingly parallel)
# ---------------------------------------------------------------------------

_WORKER_CONSTS = None
_WORKER_DPS = None


def _init_worker(const_names, dps):
    """Inicializa cada proceso: fija precisión y cachea las constantes una sola vez."""
    global _WORKER_CONSTS, _WORKER_DPS
    _WORKER_DPS = dps
    mp.mp.dps = dps + 10
    allc = named_constants()
    _WORKER_CONSTS = {k: allc[k] for k in const_names} if const_names else allc


def _pcf_job(args):
    a_coeffs, b_coeffs, depth = args
    val = pcf_value(a_coeffs, b_coeffs, depth=depth, dps=_WORKER_DPS)
    if val is None:
        return None
    ident = identify(val, _WORKER_CONSTS, dps=_WORKER_DPS)
    if ident is None:
        return None
    return {'a_coeffs': list(a_coeffs), 'b_coeffs': list(b_coeffs),
            'value': mp.nstr(val, 20), **ident}


_WORKER_CONST_FLOATS = None
_WORKER_SCREEN_DEPTH = None


def _init_worker_screened(const_names, dps, screen_depth):
    """Inicializa worker para el barrido en DOS ETAPAS (cribado float64 + verificación)."""
    global _WORKER_CONSTS, _WORKER_DPS, _WORKER_CONST_FLOATS, _WORKER_SCREEN_DEPTH
    _WORKER_DPS = dps
    _WORKER_SCREEN_DEPTH = screen_depth
    mp.mp.dps = dps + 10
    allc = named_constants()
    _WORKER_CONSTS = {k: allc[k] for k in const_names} if const_names else allc
    _WORKER_CONST_FLOATS = [_WORKER_CONSTS[k] for k in _WORKER_CONSTS]


def _pcf_job_screened(args):
    a_coeffs, b_coeffs, depth = args
    # ETAPA 1 (barata, float64): ¿pasa la criba?
    vf = pcf_value_float(a_coeffs, b_coeffs, depth=_WORKER_SCREEN_DEPTH)
    if not _screen_hit(vf, _WORKER_CONST_FLOATS):
        return None
    # ETAPA 2 (cara, mpmath): verificación rigurosa
    val = pcf_value(a_coeffs, b_coeffs, depth=depth, dps=_WORKER_DPS)
    if val is None:
        return None
    ident = identify(val, _WORKER_CONSTS, dps=_WORKER_DPS)
    if ident is None:
        return None
    return {'a_coeffs': list(a_coeffs), 'b_coeffs': list(b_coeffs),
            'value': mp.nstr(val, 20), **ident}


def search_screened(a_degree=2, b_degree=2, coeff_range=(-5, 5), depth=400, dps=60,
                    screen_depth=400, const_names=None, workers=None, chunksize=200,
                    progress=False, checkpoint=None, checkpoint_every=300,
                    resume_from=0, resume_hits=None):
    """Barrido en DOS ETAPAS: criba float64 nativa (rápida) y solo los supervivientes
    pasan a la verificación mpmath/PSLQ (cara). Pensado para cazas GRANDES. Multiproceso.
    Favorece PCFs de convergencia rápida (las interesantes). Soporta checkpoint/resume
    (ver search_structured)."""
    from concurrent.futures import ProcessPoolExecutor
    lo, hi = coeff_range
    rng = list(range(lo, hi + 1))
    a_space = [ac for ac in _product(rng, repeat=a_degree + 1) if any(v != 0 for v in ac)]
    b_space = list(_product(rng, repeat=b_degree + 1))
    total = len(a_space) * len(b_space)
    jobs = ((ac, bc, depth) for ac in a_space for bc in b_space)
    if resume_from:
        jobs = _islice(jobs, resume_from, None)
    hits = list(resume_hits) if resume_hits else []
    seen = {(h['constant'], tuple(h['relation'])) for h in hits}
    prog = _Progress(total, label="cribada", enabled=progress)
    done = resume_from
    last_ck = _time.time()
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker_screened,
                             initargs=(const_names, dps, screen_depth)) as ex:
        for res in ex.map(_pcf_job_screened, jobs, chunksize=chunksize):
            done += 1
            if res is not None:
                key = (res['constant'], tuple(res['relation']))
                if key not in seen:
                    seen.add(key)
                    hits.append(res)
            prog.update(done, extra=f"  hits: {len(hits)}")
            if checkpoint and _time.time() - last_ck >= checkpoint_every:
                _write_checkpoint(checkpoint, done, total, {'hits': hits})
                last_ck = _time.time()
    prog.close(extra=f"  hits: {len(hits)}")
    if checkpoint:
        _write_checkpoint(checkpoint, done, total, {'hits': hits})
    return hits


def _structured_a_forms(a_max_degree, a_lead_range):
    """Genera formas MONOMIALES a(n) = L·n^k (k = 1..a_max_degree, L != 0 en el rango).
    Este es el régimen de las CF de ζ(3)/Catalan (Apéry: a(n) = -n⁶), que el barrido
    de grado bajo / coeficiente pequeño NO puede alcanzar. Forma cerrada como lista de
    coeficientes [c0, c1, ...]: L·n^k = [0]*k + [L]."""
    lo, hi = a_lead_range
    leads = [L for L in range(lo, hi + 1) if L != 0]
    forms = []
    for k in range(1, a_max_degree + 1):
        for L in leads:
            forms.append(tuple([0] * k + [L]))
    return forms


def search_structured(a_max_degree=6, a_lead_range=(-2, 2), b_degree=3,
                      b_coeff_range=(-15, 15), depth=500, dps=60, screen_depth=700,
                      const_names=None, workers=None, chunksize=200, progress=False,
                      checkpoint=None, checkpoint_every=300, resume_from=0, resume_hits=None):
    """Barrido ESTRUCTURADO hacia el régimen de Apéry (donde viven ζ(3), Catalan).
    a(n) = L·n^k monomial de grado ALTO (hasta a_max_degree; contiene el -n⁶ de Apéry),
    b(n) polinomio completo de grado b_degree con coeficientes moderados. Dos etapas
    (criba float64 + verificación mpmath), multiproceso. Es el espacio que la fuerza
    bruta de grado bajo no puede tocar y donde un hit en ζ(3)/Catalan sería genuinamente
    nuevo. Devuelve hits deduplicados por (constante, relación).

    Checkpoint/resume: si `checkpoint` (ruta), vuelca {done,total,hits} cada
    `checkpoint_every` s (atómico). `resume_from`/`resume_hits` reanudan saltando los
    primeros N combos y precargando hits (un corte a la hora 7 ya no pierde nada)."""
    from concurrent.futures import ProcessPoolExecutor
    a_space = _structured_a_forms(a_max_degree, a_lead_range)
    lo, hi = b_coeff_range
    b_rng = list(range(lo, hi + 1))
    b_space = list(_product(b_rng, repeat=b_degree + 1))
    total = len(a_space) * len(b_space)
    jobs = ((ac, bc, depth) for ac in a_space for bc in b_space)
    if resume_from:
        jobs = _islice(jobs, resume_from, None)
    hits = list(resume_hits) if resume_hits else []
    seen = {(h['constant'], tuple(h['relation'])) for h in hits}
    prog = _Progress(total, label="estructurada", enabled=progress)
    done = resume_from
    last_ck = _time.time()
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker_screened,
                             initargs=(const_names, dps, screen_depth)) as ex:
        for res in ex.map(_pcf_job_screened, jobs, chunksize=chunksize):
            done += 1
            if res is not None:
                key = (res['constant'], tuple(res['relation']))
                if key not in seen:
                    seen.add(key)
                    hits.append(res)
            prog.update(done, extra=f"  hits: {len(hits)}")
            if checkpoint and _time.time() - last_ck >= checkpoint_every:
                _write_checkpoint(checkpoint, done, total, {'hits': hits})
                last_ck = _time.time()
    prog.close(extra=f"  hits: {len(hits)}")
    if checkpoint:
        _write_checkpoint(checkpoint, done, total, {'hits': hits})
    return hits


def search_parallel(a_degree=2, b_degree=1, coeff_range=(-3, 3), depth=200, dps=42,
                    const_names=None, workers=None, chunksize=100, progress=False):
    """Igual que `search` pero reparte las PCFs entre procesos (escala ~lineal con
    núcleos). `const_names`: lista de nombres a enfocar (None = todas). Devuelve los
    hits deduplicados por (constante, relación)."""
    from concurrent.futures import ProcessPoolExecutor
    lo, hi = coeff_range
    rng = list(range(lo, hi + 1))
    a_space = [ac for ac in _product(rng, repeat=a_degree + 1) if any(v != 0 for v in ac)]
    b_space = list(_product(rng, repeat=b_degree + 1))
    jobs = ((ac, bc, depth) for ac in a_space for bc in b_space)
    hits, seen = [], set()
    prog = _Progress(len(a_space) * len(b_space), label="paralela", enabled=progress)
    done = 0
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker,
                             initargs=(const_names, dps)) as ex:
        for res in ex.map(_pcf_job, jobs, chunksize=chunksize):
            done += 1
            if res is not None:
                key = (res['constant'], tuple(res['relation']))
                if key not in seen:
                    seen.add(key)
                    hits.append(res)
            prog.update(done, extra=f"  hits: {len(hits)}")
    prog.close(extra=f"  hits: {len(hits)}")
    return hits


# ---------------------------------------------------------------------------
#  Barrido ABIERTO (target-free): no se fija constante. Clasifica cada límite
#  como racional/algebraico/nombrado/desconocido y detecta colisiones PCF↔PCF.
# ---------------------------------------------------------------------------

_WORKER_OPEN = None


def _init_worker_open(dps, max_alg_degree, screen_depth, try_named, const_names, linear_basis):
    """Inicializa worker para el barrido ABIERTO: precisión, grado algebraico máximo,
    profundidad de criba, constantes para la etiqueta amable y (opcional) base de
    formas lineales multi-constante."""
    global _WORKER_OPEN
    mp.mp.dps = dps + 10
    allc = named_constants()
    consts = {k: allc[k] for k in const_names} if const_names else allc
    lb = [n for n in linear_basis if n in allc] if linear_basis else None
    _WORKER_OPEN = {'dps': dps, 'maxdeg': max_alg_degree, 'screen_depth': screen_depth,
                    'try_named': try_named, 'consts': consts, 'linear_basis': lb}


def _pcf_job_open(args):
    a_coeffs, b_coeffs, depth = args
    cfg = _WORKER_OPEN
    # ETAPA 1 (barata, float64): ¿converge a un valor finito y acotado?
    vf = pcf_value_float(a_coeffs, b_coeffs, depth=cfg['screen_depth'])
    if vf is None or abs(vf) > 1e6:
        return None
    # ETAPA 2 (cara, mpmath): valor exacto + identificación SIN objetivo
    val = pcf_value(a_coeffs, b_coeffs, depth=depth, dps=cfg['dps'])
    if val is None:
        return None
    info = identify_open(val, dps=cfg['dps'], max_alg_degree=cfg['maxdeg'],
                         try_named=cfg['try_named'], constants=cfg['consts'],
                         linear_basis=cfg['linear_basis'])
    if info is None or info['kind'] == 'rational':
        return None
    fp = value_fingerprint(val)
    return {'a_coeffs': list(a_coeffs), 'b_coeffs': list(b_coeffs),
            'fingerprint': list(fp), **info}


def search_open(a_degree=2, b_degree=2, coeff_range=(-5, 5), depth=400, dps=60,
                screen_depth=500, max_alg_degree=4, try_named=True,
                const_names=None, workers=None, chunksize=200,
                a_forms=None, b_coeff_range=None, progress=False, linear_basis=None):
    """Barrido ABIERTO: sin fijar constante objetivo. Para cada PCF que converge,
    clasifica su límite (algebraico / nombrado / desconocido) y agrupa por VALOR para
    detectar COLISIONES (PCFs distintas -> mismo número = identidad descubierta).
    Devuelve dict con listas: 'algebraic', 'named', 'unknown', y 'collisions'
    (huellas de valor alcanzadas por ≥2 PCFs distintas).

    Si `a_forms` se da (lista de tuplas de coeficientes), se usa ese espacio de a(n)
    -- p.ej. las formas estructuradas del régimen de Apéry -- en lugar de la rejilla;
    `b_coeff_range` controla el rango de b(n) (por defecto = coeff_range)."""
    from concurrent.futures import ProcessPoolExecutor
    lo, hi = coeff_range
    rng = list(range(lo, hi + 1))
    if a_forms is not None:
        a_space = [tuple(f) for f in a_forms]
    else:
        a_space = [ac for ac in _product(rng, repeat=a_degree + 1) if any(v != 0 for v in ac)]
    blo, bhi = b_coeff_range if b_coeff_range is not None else coeff_range
    b_space = list(_product(range(blo, bhi + 1), repeat=b_degree + 1))
    jobs = ((ac, bc, depth) for ac in a_space for bc in b_space)
    algebraic, named, linear, unknown = [], [], [], []
    seen_alg, seen_named, seen_lin = set(), set(), set()
    by_value = {}                      # huella de valor -> lista de records (para colisiones)
    prog = _Progress(len(a_space) * len(b_space), label="abierta", enabled=progress)
    done = 0
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker_open,
                             initargs=(dps, max_alg_degree, screen_depth, try_named,
                                       const_names, linear_basis)) as ex:
        for res in ex.map(_pcf_job_open, jobs, chunksize=chunksize):
            done += 1
            if res is not None:
                fp = tuple(res['fingerprint'])
                by_value.setdefault(fp, []).append(res)
                kind = res['kind']
                if kind == 'algebraic':
                    key = tuple(res['poly'])
                    if key not in seen_alg:
                        seen_alg.add(key)
                        algebraic.append(res)
                elif kind == 'named':
                    key = (res['constant'], tuple(res['relation']))
                    if key not in seen_named:
                        seen_named.add(key)
                        named.append(res)
                elif kind == 'linear':
                    key = tuple(res['relation'])
                    if key not in seen_lin:
                        seen_lin.add(key)
                        linear.append(res)
                elif kind == 'unknown':
                    unknown.append(res)
            prog.update(done, extra=f"  alg:{len(algebraic)} nom:{len(named)} lin:{len(linear)} "
                                    f"desc:{len(unknown)} col:{sum(1 for v in by_value.values() if len(v) > 1)}")
    prog.close(extra=f"  alg:{len(algebraic)} nom:{len(named)} lin:{len(linear)} desc:{len(unknown)}")
    # colisiones: una misma huella de valor alcanzada por ≥2 PCFs (a,b) distintas
    collisions = []
    for fp, recs in by_value.items():
        uniq = {(tuple(r['a_coeffs']), tuple(r['b_coeffs'])) for r in recs}
        if len(uniq) >= 2:
            collisions.append({'fingerprint': list(fp), 'kind': recs[0]['kind'],
                               'count': len(uniq), 'value': recs[0].get('value'),
                               'members': [{'a_coeffs': r['a_coeffs'], 'b_coeffs': r['b_coeffs']}
                                           for r in recs]})
    # deduplica 'unknown' por huella de valor (cada constante candidata una vez)
    seen_fp = set()
    uniq_unknown = []
    for r in unknown:
        fp = tuple(r['fingerprint'])
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        uniq_unknown.append(r)
    return {'algebraic': algebraic, 'named': named, 'linear': linear,
            'unknown': uniq_unknown, 'collisions': collisions}


# ---------------------------------------------------------------------------
#  ACELERACIÓN estructural (Apéry): a partir de la forma factorizada descubierta
#  b(n)=(2n+1)(α n²+β n+γ) [o cuadrática], a(n)=L·n^k, busca PCFs que sean Möbius
#  del target con δ>0 (prueban irracionalidad). En vez de fuerza bruta en un espacio
#  gigante, barre los pocos parámetros que la estructura descubierta deja libres.
# ---------------------------------------------------------------------------

def accel_b_coeffs(form, lin, quad):
    """Coeficientes de b(n) según la forma estructural:
      'factored':  (c·n+d)(α n²+β n+γ)  -> cúbico (estilo Apéry/ζ(3), lin=(2,1) => 2n+1)
      'quadratic':  α n²+β n+γ           -> cuadrático (estilo semilla de Catalan)."""
    al, be, ga = quad
    if form == 'quadratic':
        return [ga, be, al]
    c, d = lin
    # (c n + d)(α n² + β n + γ)
    return [d * ga, c * ga + d * be, c * be + d * al, c * al]


def _poly_mul(p, q):
    """Multiplica dos polinomios dados por coeficientes [c0,c1,...] (grado ascendente)."""
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] += a * b
    return r


def accel_b_space(form, ranges, lin_factors=((2, 1),)):
    """Genera coeficientes de b(n) para la búsqueda de aceleración, GENERALIZANDO la
    forma estructural más allá de la fija de Apéry. `ranges` = (lo, hi) para los
    coeficientes libres. Formas soportadas (rinde tuplas de coef [c0,c1,...]):
      'quadratic'   : α n²+β n+γ                       (3 libres)
      'factored'    : (c·n+d)(α n²+β n+γ)  con (c,d) en lin_factors  (3 libres × factores)
      'biquadratic' : (α n²+β n+γ)(α' n²+β' n+γ')      (6 libres; usar rango pequeño)
      'lin_quad_free': (c·n+d)(α n²+β n+γ)  con (c,d) TAMBIÉN barridos en ranges
    Solo deduplica b idénticos (mismo polinomio); NO salvo escala, porque escalar b
    cambia el valor de la PCF (b y k·b son PCFs distintas)."""
    lo, hi = ranges
    rng = range(lo, hi + 1)
    seen = set()
    out = []

    def emit(coeffs):
        # quita ceros de cabeza por la derecha (grado real) y deduplica EXACTOS.
        # OJO: NO se deduplica salvo escala -- escalar b(n) CAMBIA el valor de la PCF,
        # así que b y k·b son PCFs DISTINTAS (las primitivas como (-1,-3,-3) son justo
        # las interesantes y se perderían con dedup por gcd).
        c = list(coeffs)
        while len(c) > 1 and c[-1] == 0:
            c.pop()
        if all(v == 0 for v in c):
            return
        key = tuple(c)
        if key in seen:
            return
        seen.add(key)
        out.append(key)

    if form == 'quadratic':
        for al in rng:
            for be in rng:
                for ga in rng:
                    emit([ga, be, al])
    elif form == 'factored':
        for (c, d) in lin_factors:
            for al in rng:
                for be in rng:
                    for ga in rng:
                        emit(_poly_mul([d, c], [ga, be, al]))
    elif form == 'lin_quad_free':
        for c in rng:
            for d in rng:
                if c == 0 and d == 0:
                    continue
                for al in rng:
                    for be in rng:
                        for ga in rng:
                            emit(_poly_mul([d, c], [ga, be, al]))
    elif form == 'biquadratic':
        for al in rng:
            for be in rng:
                for ga in rng:
                    q1 = [ga, be, al]
                    if all(v == 0 for v in q1):
                        continue
                    for al2 in rng:
                        for be2 in rng:
                            for ga2 in rng:
                                emit(_poly_mul(q1, [ga2, be2, al2]))
    else:
        raise ValueError(f"forma de b desconocida: {form}")
    return out


_WORKER_ACCEL = None


def _init_worker_accel(target, dps, delta_depth, delta_dps, depth):
    global _WORKER_ACCEL
    mp.mp.dps = max(dps, delta_dps) + 10
    _WORKER_ACCEL = {'target': target, 'cval': named_constants()[target], 'dps': dps,
                     'dd': delta_depth, 'ddps': delta_dps, 'depth': depth}


def _pcf_job_accel(args):
    a_coeffs, b_coeffs = args
    cfg = _WORKER_ACCEL
    vf = pcf_value_float(a_coeffs, b_coeffs, depth=min(cfg['depth'], 500))
    if vf is None or abs(vf) > 1e6:
        return None
    v = pcf_value(a_coeffs, b_coeffs, depth=cfg['depth'], dps=cfg['dps'])
    if v is None:
        return None
    ident = identify(v, {cfg['target']: cfg['cval']}, dps=cfg['dps'])
    if ident is None:
        return None
    d = irrationality_delta(a_coeffs, b_coeffs, depth=cfg['dd'], dps=cfg['ddps'])
    return {'a_coeffs': list(a_coeffs), 'b_coeffs': list(b_coeffs),
            'value': mp.nstr(v, 20), 'delta': d, **ident}


def search_accelerated(target='zeta3', form='factored', a_powers=(6,), a_leads=(-1,),
                       lin_factor=(2, 1), lin_factors=None, quad_range=(-20, 20),
                       depth=400, dps=90, delta_depth=160, delta_dps=320,
                       workers=None, chunksize=100, progress=False,
                       checkpoint=None, checkpoint_every=300, resume_from=0, resume_hits=None):
    """Búsqueda de ACELERACIÓN estructural. Barre a(n)=L·n^k (L en a_leads, k en a_powers)
    y b(n) de forma `form` (ver accel_b_space: quadratic/factored/lin_quad_free/biquadratic)
    con coeficientes libres en quad_range, quedándose con las PCFs que son Möbius de
    `target` y midiendo su δ (irracionalidad). Devuelve hits ordenados por δ descendente
    (las de δ>0 PRUEBAN irracionalidad del target).

    Validado: con target='zeta3', form='factored', a_powers=(6,), a_leads=(-1,), recupera
    la fórmula de Apéry (α,β,γ)=(17,17,5) con δ>0. Para target='catalan'/'zeta5'
    (irracionalidad ABIERTA) es un intento genuino de hallar una PCF que la pruebe.
    Soporta checkpoint/resume (ver search_structured)."""
    from concurrent.futures import ProcessPoolExecutor
    lfs = lin_factors if lin_factors is not None else (tuple(lin_factor),)
    b_space = accel_b_space(form, quad_range, lin_factors=lfs)
    combos = []
    for k in a_powers:
        for L in a_leads:
            if L == 0:
                continue
            a_coeffs = tuple([0] * k + [L])
            for b_coeffs in b_space:
                combos.append((a_coeffs, b_coeffs))
    total = len(combos)
    work = combos[resume_from:] if resume_from else combos
    hits = list(resume_hits) if resume_hits else []
    seen = {(h['constant'], tuple(h['relation'])) for h in hits}
    prog = _Progress(total, label=f"aceleración {target}", enabled=progress)
    done = resume_from
    last_ck = _time.time()
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker_accel,
                             initargs=(target, dps, delta_depth, delta_dps, depth)) as ex:
        for res in ex.map(_pcf_job_accel, work, chunksize=chunksize):
            done += 1
            if res is not None:
                key = (res['constant'], tuple(res['relation']))
                if key not in seen:
                    seen.add(key)
                    hits.append(res)
            npos = sum(1 for h in hits if (h.get('delta') or 0) > 0)
            prog.update(done, extra=f"  hits:{len(hits)} δ>0:{npos}")
            if checkpoint and _time.time() - last_ck >= checkpoint_every:
                _write_checkpoint(checkpoint, done, total, {'hits': hits})
                last_ck = _time.time()
    prog.close()
    if checkpoint:
        _write_checkpoint(checkpoint, done, total, {'hits': hits})
    hits.sort(key=lambda h: -(h.get('delta') if h.get('delta') is not None else -9))
    return hits


def verify_conjecture(a_coeffs, b_coeffs, constant_name, relation, dps=120):
    """Re-verifica una conjetura a ALTA precisión (independiente del barrido):
    recomputa la PCF y comprueba la relación entera p0+p1·L+p2·c+p3·L·c ≈ 0."""
    val = pcf_value(a_coeffs, b_coeffs, depth=max(600, dps * 6), dps=dps)
    if val is None:
        return False
    with mp.workdps(dps):
        c = named_constants()[constant_name]      # recalculada a esta precisión
        p0, p1, p2, p3 = relation
        residual = p0 + p1 * val + p2 * c + p3 * val * c
        return abs(residual) < mp.mpf(10) ** -(dps - 12)
