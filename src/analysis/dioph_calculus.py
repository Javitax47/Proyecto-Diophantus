"""
================================================================================
   DIOPHANTUS - CALCULO DE CONSTRUCCIONES DIOFANTICAS (ataque al record)
================================================================================
Objetivo: representaciones diofanticas con el MINIMO numero de incognitas.

    n in S   <=>   exists x_1..x_v :  P(n, x_1..x_v) = 0

El record conocido para el conjunto de los PRIMOS es 10 variables (9 incognitas
mas el parametro), de Matiyasevich (1975, prueba completa de Jones); no ha sido
mejorado en ~48 anos. Minimizar ese numero es un PROBLEMA ABIERTO declarado.

POR QUE ESTE MODULO Y NO EL COMPILADOR:
El pipeline C -> ecuaciones produce miles de incognitas porque ANADE variables
por cada operacion: va en direccion contraria al record por construccion. Los
records no se obtuvieron compilando, sino COMPONIENDO REDUCCIONES certificadas
(exponenciacion -> ecuacion de Pell, etc.). Este modulo implementa ese calculo:

  1. una BIBLIOTECA de lemas, cada uno verificado y con su COSTE declarado;
  2. COMBINADORES que componen lemas con contabilidad exacta de incognitas;
  3. un TESTIGO constructivo por lema (completitud verificable por evaluacion).

GARANTIAS (el motivo de que esto sea sondeable y no palabreria):
  * CORRECCION POR CONSTRUCCION: si cada lema es correcto, su composicion lo es.
  * COSTE EXACTO Y COMPUTABLE: cost() cuenta incognitas distintas; compartir
    incognitas entre sub-sistemas es exactamente donde se gana el record.
  * VERIFICACION BARATA: el testigo se construye y se evalua; la direccion
    inversa se sondea por busqueda exhaustiva en rangos pequenos.
Objetivo barato + verificacion exacta es el perfil que hace viable una busqueda
automatica sobre el espacio de composiciones.

HONESTIDAD (limites, importantes):
  * Este modulo NO bate el record. Construye la infraestructura que hace que el
    intento este BIEN PLANTEADO y con MARCADOR. Batir 10 es una apuesta abierta.
  * La verificacion por rango es CONDICION NECESARIA, no demostracion. La
    correccion real descansa en que cada lema sea un teorema citado.
  * conj() combina en una sola ecuacion por SUMA DE CUADRADOS: no cuesta
    incognitas pero SI sube el grado. El record juega con ambos ejes.
"""

import sympy


# ---------------------------------------------------------------------------
#   NUCLEO: sistema diofantico con contabilidad de coste
# ---------------------------------------------------------------------------

class Dioph:
    """Sistema diofantico:  exists <unknowns> : todas las ecuaciones == 0.

    params   : simbolos LIBRES (la entrada; p. ej. n). No cuentan como coste.
    unknowns : simbolos EXISTENCIALES. Su numero es el coste a minimizar.
    eqs      : lista de expresiones sympy que deben anularse simultaneamente.
    witness  : callable(dict de params) -> dict de unknowns, o None.
               Da COMPLETITUD constructiva: permite verificar sin buscar.
    """

    def __init__(self, params, unknowns, eqs, witness=None, name=""):
        self.params = list(params)
        self.unknowns = list(unknowns)
        self.eqs = list(eqs)
        self.witness = witness
        self.name = name

    # --- el objetivo a minimizar -------------------------------------------
    def cost(self):
        """Numero de incognitas: la magnitud del record."""
        return len(self.unknowns)

    def degree(self):
        """Grado de la ecuacion unica equivalente (el segundo eje del record)."""
        single = self.single_equation()
        allsyms = self.params + self.unknowns
        if not allsyms:
            return 0
        try:
            return sympy.Poly(single, *allsyms).total_degree()
        except sympy.PolynomialError:
            return -1

    def single_equation(self):
        """Une todas las ecuaciones en UNA por suma de cuadrados (coste 0)."""
        if not self.eqs:
            return sympy.Integer(0)
        return sum(sympy.expand(e ** 2) for e in self.eqs)

    # --- verificacion -------------------------------------------------------
    def holds(self, assign):
        """True si TODAS las ecuaciones se anulan con la asignacion dada."""
        for e in self.eqs:
            if sympy.simplify(e.subs(assign)) != 0:
                return False
        return True

    def check_witness(self, param_vals):
        """Construye el testigo y verifica que satisface el sistema.

        Devuelve (ok, asignacion) o (False, None) si no hay constructor o el
        testigo no existe para esos valores.
        """
        if self.witness is None:
            return False, None
        w = self.witness(param_vals)
        if w is None:
            return False, None
        assign = dict(param_vals)
        assign.update(w)
        return self.holds(assign), assign

    def search_witness(self, param_vals, bound):
        """Busqueda exhaustiva de testigo con incognitas en [0, bound].

        Sirve para SONDEAR la direccion inversa (no deberia existir testigo
        cuando el parametro no esta en el conjunto). Exponencial: solo para
        sistemas pequenos.
        """
        import itertools
        if not self.unknowns:
            return dict(param_vals) if self.holds(param_vals) else None
        for combo in itertools.product(range(bound + 1), repeat=len(self.unknowns)):
            assign = dict(param_vals)
            assign.update(dict(zip(self.unknowns, combo)))
            if self.holds(assign):
                return assign
        return None

    def __repr__(self):
        return (f"<Dioph {self.name or '?'} | incognitas={self.cost()} "
                f"grado={self.degree()} ecuaciones={len(self.eqs)}>")


# ---------------------------------------------------------------------------
#   COMBINADORES: componer sin perder la cuenta
# ---------------------------------------------------------------------------

def conj(*systems, name=""):
    """Conjuncion: todos los sistemas se cumplen a la vez.

    Coste = numero de incognitas DISTINTAS (las compartidas se cuentan una vez:
    ahi esta el juego del record). No introduce incognitas nuevas.
    """
    params, unknowns, eqs = [], [], []
    for s in systems:
        for p in s.params:
            if p not in params:
                params.append(p)
        for u in s.unknowns:
            if u not in unknowns:
                unknowns.append(u)
        eqs.extend(s.eqs)
    # un parametro de un sistema puede ser incognita de otro: prevalece incognita
    params = [p for p in params if p not in unknowns]

    def w(param_vals):
        assign = dict(param_vals)
        for s in systems:
            if s.witness is None:
                return None
            sub = s.witness(assign)
            if sub is None:
                return None
            assign.update(sub)
        return {u: assign[u] for u in unknowns if u in assign}

    return Dioph(params, unknowns, eqs,
                 witness=w, name=name or " AND ".join(s.name for s in systems))


def disj(a, b, name=""):
    """Disyuncion: A o B, via PRODUCTO de sus ecuaciones unicas. Coste 0 extra."""
    cand = [p for p in a.params + b.params if p not in a.unknowns + b.unknowns]
    params = list(dict.fromkeys(cand))
    unknowns = list(dict.fromkeys(a.unknowns + b.unknowns))
    eq = sympy.expand(a.single_equation() * b.single_equation())

    def w(param_vals):
        for s in (a, b):
            if s.witness is None:
                continue
            sub = s.witness(param_vals)
            if sub is not None:
                out = {u: 0 for u in unknowns}
                out.update(sub)
                return out
        return None

    return Dioph(params, unknowns, [eq], witness=w,
                 name=name or f"({a.name} OR {b.name})")


# ---------------------------------------------------------------------------
#   UTILIDAD: descomposicion en cuatro cuadrados (Lagrange)
# ---------------------------------------------------------------------------

def four_squares(n):
    """Devuelve (a,b,c,d) con a^2+b^2+c^2+d^2 = n, o None si n < 0.

    Teorema de Lagrange: existe para todo n >= 0. Busqueda directa; suficiente
    para los rangos de verificacion de este modulo.
    """
    if n < 0:
        return None
    n = int(n)
    a = 0
    while a * a <= n:
        r1 = n - a * a
        b = 0
        while b * b <= r1:
            r2 = r1 - b * b
            c = 0
            while c * c <= r2:
                r3 = r2 - c * c
                d = sympy.integer_nthroot(r3, 2)
                if d[1]:
                    return (a, b, c, int(d[0]))
                c += 1
            b += 1
        a += 1
    return None
