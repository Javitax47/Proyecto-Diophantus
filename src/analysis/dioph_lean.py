"""
================================================================================
   DIOPHANTUS - GENERADOR DE LEAN 4 A PARTIR DE UN SISTEMA DIOFANTICO
================================================================================
Emite la equivalencia "sistema aplanado <=> sistema original" como un fichero
Lean 4 que el nucleo puede verificar.

POR QUE SE GENERA Y NO SE ESCRIBE A MANO. La equivalencia son ~29 ecuaciones con
16 nombres; transcribirlas a mano es exactamente el sitio donde se cuela un signo,
y en Lean un signo mal produce un teorema que SIGUE COMPILANDO y ya no dice lo
mismo. Generando desde el MISMO objeto que produce la cifra, el enunciado no puede
divergir del sistema medido.

LA CONVERSION A ℕ, que es la parte delicada. Las ecuaciones viven sobre ℤ con
variables en ℕ y tienen coeficientes negativos. Lean sobre `Nat` tiene resta
TRUNCADA: `3 - 5 = 0`. Escribir `a - b = c` en Lean no dice lo que parece. Por eso
cada ecuacion `E = 0` se parte en `P - N` con `P` y `N` de coeficientes >= 0 y se
emite como `P = N`. Es la misma ecuacion sobre ℤ y es ℕ-segura por construccion.

QUE SE DEMUESTRA, en dos teoremas:

  * `aplanado_implica_original`  (SOUNDNESS). De una solucion del aplanado sale
    una del original. Es la direccion critica: si falla, el generador emite
    numeros que no son del conjunto.
  * `original_implica_aplanado`  (COMPLETITUD). De una solucion del original sale
    una del aplanado, tomando como testigos las propias definiciones de los
    nombres. Aqui es donde importa que cada definicion sea >= 0 sobre ℕ: los
    testigos son terminos de `Nat` y no pueden ser negativos.
"""

import sympy


def _a_lean(e):
    """Expresion sympy -> sintaxis Lean, sin restas."""
    e = sympy.expand(e)
    return _termino(e)


def _termino(e):
    if e.is_Add:
        return " + ".join(_termino(t) for t in e.args)
    if e.is_Mul:
        partes = []
        for f in e.args:
            s = _termino(f)
            partes.append(f"({s})" if (f.is_Add) else s)
        return " * ".join(partes)
    if e.is_Pow:
        b, ex = e.args
        sb = _termino(b)
        return f"({sb}) ^ {ex}" if not b.is_Symbol else f"{sb} ^ {ex}"
    if e.is_Integer:
        return str(int(e))
    return str(e)


def ecuacion_nat(e):
    """`E = 0` (sobre ℤ) -> par de cadenas Lean `(P, N)` tal que la ecuacion es
    `P = N` con P y N de coeficientes NO NEGATIVOS.

    Es lo que hace la traduccion segura: sobre `Nat` la resta es truncada, asi que
    los terminos negativos DEBEN pasar al otro lado en vez de escribirse con `-`.
    """
    e = sympy.expand(e)
    pos, neg = [], []
    for t in (e.args if e.is_Add else [e]):
        coef = t.as_coeff_Mul()[0]
        (neg if coef < 0 else pos).append(-t if coef < 0 else t)
    izq = sympy.Add(*pos) if pos else sympy.Integer(0)
    der = sympy.Add(*neg) if neg else sympy.Integer(0)
    return _a_lean(izq), _a_lean(der)


def _nombre_definido(e, nombres):
    """Si `e` es la ecuacion definitoria de un nombre, devuelve cual; si no, None.

    Es definitoria cuando algun nombre aparece con coeficiente +-1, sin cuadrado,
    y no vuelve a aparecer en el resto: entonces la ecuacion DETERMINA ese nombre
    y se puede emitir como `w = cuerpo`.
    """
    ex = sympy.expand(e)
    for w in sorted(nombres):
        sw = sympy.Symbol(w, integer=True)
        if ex.coeff(sw, 1) in (1, -1) and ex.coeff(sw, 2) == 0:
            resto = sympy.expand(ex - ex.coeff(sw, 1) * sw)
            if sw not in resto.free_symbols:
                return w
    return None


def _una_por_nombre(eqs, nombres):
    """Indices de UNA ecuacion definitoria por cada nombre, no de todas.

    Una misma incognita puede aparecer con coeficiente 1 en varias ecuaciones
    --`q` esta asi en la (1) y en la (13) de JSWW-- y las dos parecen definirla.
    Emitir `subst` para las dos falla: la segunda vez la variable ya no existe.
    Se coge la PRIMERA de cada una.
    """
    pendientes, idx = set(nombres), []
    for i, e in enumerate(eqs):
        w = _nombre_definido(e, pendientes)
        if w is not None:
            pendientes.discard(w)
            idx.append(i)
    return idx


def generar(original, aplanado, definiciones, eliminadas=(), nombre_modulo="Equivalencia",
            titulo="", contexto=""):
    """Emite el fichero Lean completo.

    `original`   : el `Dioph` de partida (el sistema publicado).
    `aplanado`   : el `Dioph` final (materializado y post-eliminado).
    `definiciones`: lista (simbolo_nombre, expresion) de `materializar`.
    `eliminadas` : lista (simbolo, valor) de la post-eliminacion.
    """
    orig_vars = [str(v) for v in original.params + original.unknowns]
    apl_vars = [str(v) for v in aplanado.params + aplanado.unknowns]
    quitadas = {str(u): v for u, v in eliminadas}

    # LAS ELIMINADAS NO SE CUANTIFICAN, SE SUSTITUYEN. Este generador las metia
    # como parametros universales del teorema, y eso lo volvia INDEMOSTRABLE: el
    # sistema aplanado no dice nada sobre `q` ni sobre `y` --se eliminaron-- asi
    # que "para todo q, y: si M entonces S(..., q, ..., y, ...)" es falso. Lo que
    # hay que hacer es exhibirlas: cada una vale su definicion, resuelta hasta
    # punto fijo porque una eliminada puede mencionar a otra.
    todas = list(apl_vars)
    quitadas_res = dict(quitadas)
    for _ in range(len(quitadas_res) + 1):
        sub = {sympy.Symbol(u, integer=True): v for u, v in quitadas_res.items()}
        quitadas_res = {u: sympy.expand(v.subs(sub)) for u, v in quitadas_res.items()}
    huerfanas = sorted(set(quitadas_res) & {str(x) for v in quitadas_res.values()
                                            for x in v.free_symbols})
    if huerfanas:
        raise ValueError(f"definiciones eliminadas que siguen mencionandose entre si "
                         f"tras el punto fijo: {huerfanas}")
    orig_args = [f"({_a_lean(quitadas_res[v])})" if v in quitadas_res else v
                 for v in orig_vars]

    # GUARDA DE SOMBRAS. `h` es una INCOGNITA de JSWW y este generador la usaba
    # como nombre de la hipotesis: el teorema emitido no compilaba, y con otra
    # eleccion de letras habria compilado diciendo otra cosa.
    reservados = {"hsol"} | {"h%d" % i for i in range(max(len(original.eqs),
                                                          len(aplanado.eqs)))}
    choque = reservados & set(orig_vars + apl_vars)
    if choque:
        raise ValueError(f"el nombre de hipotesis chocaria con variables del "
                         f"sistema: {sorted(choque)}")

    L = []
    A = L.append
    A("/-")
    A(f"  DIOPHANTUS — {titulo}")
    A("  " + "=" * 72)
    A(contexto.rstrip())
    A("")
    A("  FICHERO GENERADO por `src/analysis/dioph_lean.py` a partir del MISMO objeto")
    A("  que produce la cifra. No se transcribe a mano: un signo mal escrito daria un")
    A("  teorema que compila y no dice lo mismo.")
    A("")
    A("  SOBRE ℤ, con las incognitas en ℕ por hipotesis SEPARADA. Las ecuaciones de")
    A("  coeficientes no negativos. La resta de `Nat` es truncada (`3 - 5 = 0`), asi")
    A("  que escribirla seria decir otra cosa.")
    A("-/")
    A("")
    A(f"namespace {nombre_modulo}")
    A("")

    # ---- las dos familias de ecuaciones ----
    defs_lean = [(str(w), _a_lean(c)) for w, c in definiciones]
    nombres = {w for w, _ in defs_lean}
    vivas = []
    definitorias = []
    for e in aplanado.eqs:
        (definitorias if _nombre_definido(e, nombres) else vivas).append(e)
    # Y con el INDICE, que es lo que hace falta para el guion de la prueba: las
    # definitorias son `m_i = cuerpo`, o sea `subst`-ables, y vienen en orden de
    # dependencia. Sustituirlas deja cada ecuacion como una identidad polinomica
    # en las variables originales, que es lo unico que `grind` sabe cerrar. Sin
    # esto le pasabamos 34 hipotesis y una meta de grado 12 y se rendia.
    idx_definitorias = _una_por_nombre(aplanado.eqs, nombres)

    A("/-! ## El sistema ORIGINAL (el publicado), sobre ℕ sin restas -/")
    A("")
    A("/-- Las ecuaciones del sistema de partida. `S k a b … z` dice que esa tupla")
    A("    es solucion. -/")
    A(f"def S ({' '.join(orig_vars)} : Int) : Prop :=")
    partes = []
    for e in original.eqs:
        izq, der = ecuacion_nat(e)
        partes.append(f"  {izq} = {der}")
    A(" ∧\n".join(partes))
    A("")
    A("/-! ## El sistema APLANADO (grado ≤ 2 por ecuacion) -/")
    A("")
    A(f"def M ({' '.join(todas)} : Int) : Prop :=")
    partes = []
    for e in aplanado.eqs:
        w = _nombre_definido(e, nombres)
        if w is not None:
            # DEFINITORIA: se emite `w = cuerpo`, no `P = N`. Sobre Nat hay que
            # pasar los terminos negativos al otro lado, y entonces `m20 + a*m11
            # = a + m11^2` deja de ser una definicion y `subst` no puede usarla.
            # Es un problema REAL, no de formato: `a + u^2(u^2-a)` tiene un
            # coeficiente negativo. Sobre Int no aparece.
            sw = sympy.Symbol(w, integer=True)
            ex = sympy.expand(e)
            cuerpo = sympy.expand(sw - ex / ex.coeff(sw, 1))
            partes.append(f"  {w} = {_a_lean(cuerpo)}")
        else:
            izq, der = ecuacion_nat(e)
            partes.append(f"  {izq} = {der}")
    A(" ∧\n".join(partes))
    # TESTIGOS de completitud: cada nombre resuelto hasta quedar SOLO en variables
    # originales. Una definicion puede mencionar otros nombres (la reescritura lo
    # hace), asi que se sustituye hasta punto fijo; si no, el testigo mencionaria
    # una variable que en ese punto todavia no existe.
    mapa = {(w if isinstance(w, sympy.Symbol) else sympy.Symbol(str(w), integer=True)): c
            for w, c in definiciones}
    resueltas = {}
    for w, c in definiciones:
        prev, cur = None, c
        for _ in range(len(mapa) + 1):
            if prev == cur:
                break
            prev, cur = cur, sympy.expand(cur.subs(mapa))
        resueltas[str(w)] = cur
    testigos_ordenados = []
    for v in todas:
        if v in resueltas:
            testigos_ordenados.append(f"({_a_lean(resueltas[v])})")
        else:
            testigos_ordenados.append(v)

    A("")
    A("/-! ## Los dos teoremas -/")
    A("")
    A("/-- **SOUNDNESS.** Toda solucion del sistema aplanado da una del original.")
    A("")
    A("    Es la direccion critica: si fallara, el generador emitiria numeros que no")
    A("    pertenecen al conjunto. Los nombres `m…` estan ligados por sus ecuaciones")
    A("    definitorias dentro de `M`, asi que basta sustituir y normalizar. -/")
    A(f"theorem aplanado_implica_original ({' '.join(todas)} : Int)")
    A(f"    (hsol : M {' '.join(todas)}) : S {' '.join(orig_args)} := by")
    A("  unfold M at hsol")
    A("  unfold S")
    A(f"  obtain ⟨{', '.join('h' + str(i) for i in range(len(aplanado.eqs)))}⟩ := hsol")
    if idx_definitorias:
        A("  -- cada nombre vale su definicion: se sustituyen y lo que queda son")
        A("  -- identidades polinomicas en las variables ORIGINALES")
        A("  subst " + " ".join("h%d" % i for i in idx_definitorias))
    A(f"  refine ⟨{', '.join(['?_'] * len(original.eqs))}⟩ <;> grind")
    A("")
    A("/-- **COMPLETITUD.** Toda solucion del original se extiende a una del aplanado.")
    A("")
    A("    Los testigos de los nombres son sus PROPIAS definiciones, resueltas hasta")
    A("    quedar en terminos de las variables originales. Que sean terminos de `Nat`")
    A("    es justo lo que exige la construccion del generador: un nombre que pudiera")
    A("    ser negativo romperia la completitud (el elemento dejaria de emitirse), y")
    A("    aqui eso ni siquiera se puede escribir. -/")
    A(f"theorem original_implica_aplanado ({' '.join(orig_vars)} : Int)")
    A(f"    (hsol : S {' '.join(orig_vars)}) :")
    A(f"    M {' '.join(testigos_ordenados)} := by")
    A("  unfold S at hsol")
    A("  unfold M")
    A(f"  obtain ⟨{', '.join('h' + str(i) for i in range(len(original.eqs)))}⟩ := hsol")
    # LO MISMO EN ESTA DIRECCION, y por la misma razon. El sistema aplanado se
    # enuncia con las eliminadas ya sustituidas --`y` es `l+n+v`--, mientras que
    # la hipotesis habla de `y`. `grind` no mete esa igualdad DENTRO de un
    # cuadrado: sin el `subst`, la ecuacion (6) se le queda a un paso.
    elim_names = {str(u) for u, _ in eliminadas}
    idx_elim = _una_por_nombre(original.eqs, elim_names)
    if idx_elim:
        A("  -- las eliminadas valen su definicion: se sustituyen en las hipotesis")
        A("  subst " + " ".join("h%d" % i for i in idx_elim))
    A(f"  refine ⟨{', '.join(['?_'] * len(aplanado.eqs))}⟩ <;> grind")
    A("")
    A(f"end {nombre_modulo}")
    return "\n".join(L) + "\n"
