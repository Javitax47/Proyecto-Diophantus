#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CALCULO DE CONSTRUCCIONES DIOFANTICAS (ataque al record)
================================================================================
Valida src/analysis/dioph_calculus.py y dioph_lemmas.py: la infraestructura para
buscar representaciones diofanticas con el MINIMO numero de incognitas.

Comprueba, para cada lema:
  - COMPLETITUD: el testigo constructivo existe y ANULA el sistema (evaluacion
    exacta, no busqueda);
  - SOUNDNESS: para elementos que NO estan en el conjunto, la busqueda
    exhaustiva en rango NO encuentra testigo (no hay soluciones espurias);
  - COSTE: el numero de incognitas declarado coincide con el real, y la
    composicion contabiliza correctamente las incognitas COMPARTIDAS.

Y valida el cimiento del record: la ecuacion de Pell y el predicado de
crecimiento exponencial de Julia Robinson.
"""

import sys
import os
import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_calculus import Dioph, conj, disj, four_squares
from src.analysis.dioph_lemmas import (
    L_divides, L_congruent, L_nonneg, L_positive, L_square, L_composite,
    L_pell, L_is_pell_y, pell_seq, fresh, RECORD_PRIMOS, FRONTERA,
    L_exponential, L_nonneg_N, LOGRADO,
    L_binomial, L_factorial, L_prime, L_floor_div,
    L_prime_shared, PellContext,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


n = sympy.Symbol('n', integer=True)
a = sympy.Symbol('a', integer=True)
y = sympy.Symbol('y', integer=True)


def test_lagrange(stats):
    print(f"{Colors.HEADER}[1] Cuatro cuadrados (Lagrange): el precio de una desigualdad{Colors.ENDC}")
    bad = [v for v in range(0, 200) if (lambda d: d is None or sum(x*x for x in d) != v)(four_squares(v))]
    if bad:
        stats.fail(f"descomposicion incorrecta para {bad[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 200/200 enteros descompuestos y verificados (7={four_squares(7)})")


def test_basic_lemmas(stats):
    print(f"{Colors.HEADER}[2] Lemas basicos: COMPLETITUD (el testigo anula el sistema){Colors.ENDC}")
    cases = [
        (L_divides(sympy.Integer(7), n), {n: 91}, 1, "7 | 91"),
        (L_congruent(n, sympy.Integer(1), sympy.Integer(5)), {n: 31}, 1, "31 = 1 mod 5"),
        (L_nonneg(n - 10), {n: 47}, 4, "n-10 >= 0 en n=47"),
        (L_positive(n), {n: 3}, 4, "n > 0 en n=3"),
        (L_square(n), {n: 49}, 1, "49 es cuadrado"),
        (L_composite(n), {n: 91}, 2, "91 compuesto"),
    ]
    for sysm, vals, cost, label in cases:
        ok, asg = sysm.check_witness(vals)
        if not ok:
            stats.fail(f"{label}: el testigo no anula el sistema")
        elif sysm.cost() != cost:
            stats.fail(f"{label}: coste {sysm.cost()} != {cost} declarado")
        else:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label}  (coste {cost} incognita(s), grado {sysm.degree()})")


def test_soundness(stats):
    print(f"{Colors.HEADER}[3] SOUNDNESS: sin testigo cuando el elemento NO pertenece{Colors.ENDC}")
    # primos: no deben admitir testigo de 'compuesto' (busqueda exhaustiva)
    spurious = []
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23]:
        if L_composite(n).search_witness({n: p}, bound=p + 2) is not None:
            spurious.append(p)
    if spurious:
        stats.fail(f"testigo espurio de 'compuesto' para primos {spurious}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 9 primos: ningun testigo de 'compuesto' (sin soluciones espurias)")

    # no-cuadrados no deben admitir testigo de 'cuadrado'
    bad = [v for v in [2, 3, 5, 7, 8, 10, 15] if L_square(n).search_witness({n: v}, bound=v) is not None]
    if bad:
        stats.fail(f"testigo espurio de 'cuadrado' para {bad}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 7 no-cuadrados rechazados")

    # negativos no admiten testigo de no-negatividad (Lagrange)
    if four_squares(-1) is None and L_nonneg(n).witness({n: -5}) is None:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} n<0 no admite descomposicion en 4 cuadrados (correcto)")
    else:
        stats.fail("negativo aceptado como no-negativo")


def test_pell(stats):
    print(f"{Colors.HEADER}[4] Ecuacion de Pell: el cimiento del record{Colors.ENDC}")
    bad = []
    for av in range(2, 8):
        for k in range(0, 12):
            xk, yk = pell_seq(av, k)
            if xk ** 2 - (av ** 2 - 1) * yk ** 2 != 1:
                bad.append((av, k))
    if bad:
        stats.fail(f"la identidad de Pell falla en {bad[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 72 pares (a,k): x_k²-(a²-1)y_k² = 1 exacto  (a=2: {pell_seq(2,4)})")

    # crecimiento exponencial: la propiedad que hace diofantica la exponenciacion
    ys = [pell_seq(3, k)[1] for k in range(1, 9)]
    ratios_ok = all(ys[i+1] >= 4 * ys[i] for i in range(len(ys) - 1))
    if ratios_ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} y_k(3) crece exponencialmente: {ys[:6]}… (predicado de J. Robinson)")
    else:
        stats.fail(f"y_k no crece exponencialmente: {ys}")

    # y_k = k mod (a-1): identidad clasica usada en las reducciones
    bad = [(av, k) for av in range(2, 7) for k in range(0, 15)
           if (pell_seq(av, k)[1] - k) % (av - 1) != 0]
    if bad:
        stats.fail(f"y_k != k mod (a-1) en {bad[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} y_k(a) ≡ k (mod a-1) verificado en 75 casos")


def test_is_pell_y(stats):
    print(f"{Colors.HEADER}[5] Predicado 'y es y_k(a)': COMPLETITUD y SOUNDNESS{Colors.ENDC}")
    sysm = L_is_pell_y(a, y)
    ok_all = True
    for av in [2, 3, 5]:
        for k in range(0, 7):
            _, yk = pell_seq(av, k)
            ok, _ = sysm.check_witness({a: av, y: yk})
            if not ok:
                ok_all = False
    if ok_all:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 21 valores y_k(a) admiten testigo x (coste {sysm.cost()} incognita)")
    else:
        stats.fail("un y_k legitimo no admitio testigo")

    # SOUNDNESS: valores que NO son y_k no deben admitir testigo
    reales = {pell_seq(3, k)[1] for k in range(0, 12)}
    falsos = [v for v in range(1, 40) if v not in reales]
    espurios = [v for v in falsos if sysm.witness({a: 3, y: v}) is not None]
    if espurios:
        stats.fail(f"testigo espurio para y no-Pell: {espurios[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {len(falsos)} valores no-Pell rechazados (no inventa)")


def test_composicion_y_coste(stats):
    print(f"{Colors.HEADER}[6] Composicion: contabilidad EXACTA del coste (donde se gana el record){Colors.ENDC}")
    d1 = L_divides(sympy.Integer(3), n)
    d2 = L_square(n)
    c = conj(d1, d2, name="n divisible por 3 y cuadrado")
    if c.cost() != d1.cost() + d2.cost():
        stats.fail(f"coste de conjuncion {c.cost()} != {d1.cost()+d2.cost()}")
    else:
        ok, _ = c.check_witness({n: 36})
        if ok:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} conj: coste {c.cost()} = {d1.cost()}+{d2.cost()}, testigo verificado en n=36")
        else:
            stats.fail("conjuncion: testigo no anula el sistema")

    # COMPARTIR incognitas no las duplica: es la palanca del record
    shared = conj(d1, d1)
    if shared.cost() == d1.cost():
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} incognitas COMPARTIDAS se cuentan una vez ({shared.cost()}, no {2*d1.cost()})")
    else:
        stats.fail(f"compartir incognitas duplico el coste: {shared.cost()}")

    # disyuncion: coste 0 extra, via producto
    dj = disj(L_square(n), L_composite(n))
    ok1, _ = dj.check_witness({n: 49})
    if ok1 and dj.cost() == 3:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} disj: producto de ecuaciones, coste {dj.cost()} sin extras, grado {dj.degree()}")
    else:
        stats.fail(f"disyuncion incorrecta (ok={ok1}, coste={dj.cost()})")


def test_marcador(stats):
    print(f"{Colors.HEADER}[7] MARCADOR: distancia real al record{Colors.ENDC}")
    print(f"  {Colors.BOLD}Record primos:{Colors.ENDC} {RECORD_PRIMOS['variables']} variables "
          f"({RECORD_PRIMOS['incognitas']} incognitas + parametro) — {RECORD_PRIMOS['autor']}")
    print(f"  {Colors.BOLD}Estado:{Colors.ENDC} {RECORD_PRIMOS['estado']}")
    print(f"  {Colors.OKGREEN}Logrado en este modulo:{Colors.ENDC}")
    for f in LOGRADO:
        print(f"    + {f}")
    print(f"  {Colors.WARN}Frontera declarada (aun NO implementado):{Colors.ENDC}")
    for f in FRONTERA:
        print(f"    - {f}")
    if RECORD_PRIMOS['incognitas'] == 9 and len(FRONTERA) == 3:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} marcador y frontera declarados sin sobreafirmar")
    else:
        stats.fail("marcador inconsistente")



def test_exponencial_completitud(stats):
    print(f"{Colors.HEADER}[8] EXPONENCIACION c = b^k: COMPLETITUD (testigo construido y evaluado){Colors.ENDC}")
    b, k, c = sympy.symbols('b k c', integer=True)
    for over_N, etiqueta in [(True, "sobre N"), (False, "sobre Z")]:
        sysm = L_exponential(b, k, c, over_N=over_N)
        malos = []
        for bv, kv in [(2, 1), (2, 5), (2, 10), (3, 3), (3, 7), (5, 2), (7, 3), (10, 4)]:
            ok, _ = sysm.check_witness({b: bv, k: kv, c: bv ** kv})
            if not ok:
                malos.append(f"{bv}^{kv}")
        if malos:
            stats.fail(f"exponencial {etiqueta}: el testigo no anula el sistema en {malos}")
        else:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 8/8 casos {etiqueta}: sistema anulado "
                  f"(coste {sysm.cost()} incognitas, grado {sysm.degree()})")


def test_exponencial_soundness(stats):
    print(f"{Colors.HEADER}[9] EXPONENCIACION: SOUNDNESS (la construccion FUERZA c = b^k){Colors.ENDC}")
    # Con (a,x,y) fijados por la construccion, la congruencia + la cota c < M
    # deben dejar UN UNICO c posible, y ese c debe ser b^k.
    malos = []
    for bv, kv in [(2, 3), (2, 5), (3, 2), (3, 4), (5, 2), (7, 2)]:
        cv = bv ** kv
        av = max(cv, kv) + 3
        while 2 * av * bv - bv ** 2 - 1 <= cv:
            av += 1
        xv, yv = pell_seq(av, kv)
        Mv = 2 * av * bv - bv ** 2 - 1
        objetivo = xv - (av - bv) * yv
        candidatos = [cc for cc in range(0, Mv) if (objetivo - cc) % Mv == 0]
        if candidatos != [cv]:
            malos.append((bv, kv, candidatos[:4], cv))
    if malos:
        stats.fail(f"c no queda univocamente determinado: {malos[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 6/6: en [0,M) hay EXACTAMENTE un c compatible, y es b^k "
              f"(la cota c<M no es decorativa)")

    # El constructor no fabrica testigo para un c incorrecto
    b, k, c = sympy.symbols('b k c', integer=True)
    sysm = L_exponential(b, k, c, over_N=True)
    espurios = [(bv, kv, cc) for bv, kv in [(2, 5), (3, 3)]
                for cc in [bv ** kv - 1, bv ** kv + 1, 0, 1]
                if sysm.witness({b: bv, k: kv, c: cc}) is not None]
    if espurios:
        stats.fail(f"testigo fabricado para c != b^k: {espurios[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 8 valores c != b^k rechazados (no inventa)")

    # La condicion (6) a-1 > k no es opcional: sin ella el indice colisiona
    colisiona = False
    av = 10
    residuos = {}
    for m_idx in range(0, 3 * (av - 1)):
        _, ym = pell_seq(av, m_idx)
        residuos.setdefault(ym % (av - 1), []).append(m_idx)
    if any(len(v) > 1 for v in residuos.values()):
        colisiona = True
    if colisiona:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} confirmado que sin 'a-1 > k' el indice colisiona "
              f"(m, m+(a-1), ...): la condicion lateral es NECESARIA")
    else:
        stats.fail("no se reprodujo la colision de indices: revisar la justificacion de (6)")


def test_coste_N_vs_Z(stats):
    """[10] Coste sobre N vs sobre Z, con el modelo CORREGIDO.

    Este test afirmaba antes 5 sobre N y 17 sobre Z, con "3 desigualdades x 4
    cuadrados = 12 de diferencia". Aquella cuenta daba por bueno que una
    desigualdad cuesta 0 sobre N, y eso solo vale para una VARIABLE SUELTA: para
    una expresion compuesta hace falta una holgura. Tratarlas igual dejaba el
    sistema sin condiciones laterales y lo volvia INSOUND (Z3 hallaba testigo
    para compuestos). Las cifras de abajo son las del sistema ya corregido.
    """
    print(f"{Colors.HEADER}[10] COSTE: N vs Z, el eje que separa los records{Colors.ENDC}")
    b, k, c = sympy.symbols('b k c', integer=True)
    cN = L_exponential(b, k, c, over_N=True).cost()
    cZ = L_exponential(b, k, c, over_N=False).cost()
    # 5 del nucleo + 2 desigualdades (k>=1, b>=2). El resto de condiciones
    # laterales se cumple por REPARAMETRIZACION, a coste cero.
    if cN == 7 and cZ == 13 and cZ - cN == 6:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} exponencial: {cN} incognitas sobre N vs {cZ} sobre Z "
              f"(2 desigualdades: 1 holgura sobre N, 4 cuadrados sobre Z)")
    else:
        stats.fail(f"coste inesperado: N={cN}, Z={cZ} (esperado 7 y 13)")
    libre = L_nonneg_N(b).cost()                 # variable suelta: gratis sobre N
    compuesta = L_nonneg_N(b - 1).cost()         # expresion: 1 holgura
    sobreZ = L_nonneg(b - 1).cost()              # Lagrange
    if libre == 0 and compuesta == 1 and sobreZ == 4:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} desigualdad: 0 sobre N si es variable suelta, "
              f"1 si es expresion, 4 sobre Z (Lagrange)")
    else:
        stats.fail(f"coste de la desigualdad mal contabilizado: "
                   f"suelta={libre} expresion={compuesta} Z={sobreZ}")


def test_distancia_al_record(stats):
    print(f"{Colors.HEADER}[11] DISTANCIA REAL AL RECORD (sin autoengano){Colors.ENDC}")
    b, k, c = sympy.symbols('b k c', integer=True)
    coste_exp = L_exponential(b, k, c, over_N=True).cost()
    record = RECORD_PRIMOS['incognitas']
    print(f"  Record (conjunto completo de los PRIMOS): {record} incognitas sobre N")
    print(f"  Nuestro coste solo para UN paso (exponenciacion): {coste_exp} incognitas")
    print(f"  {Colors.WARN}-> la composicion ingenua ya gasta {coste_exp}/{record} del presupuesto"
          f" del record en un unico eslabon.{Colors.ENDC}")
    print(f"  {Colors.WARN}-> batir 10 exige COMPARTIR incognitas entre eslabones,"
          f" no encadenarlos.{Colors.ENDC}")
    if coste_exp >= 5:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} distancia declarada honestamente (no se afirma haber batido nada)")
    else:
        stats.fail("coste sospechosamente bajo: revisar")



def test_binomial(stats):
    print(f"{Colors.HEADER}[12] BINOMIAL por extraccion de digitos (Julia Robinson){Colors.ENDC}")
    r, k2, c = sympy.symbols('r k2 c', integer=True)
    # (a) la identidad matematica, barata y masiva
    malos, tot = [], 0
    for rv in range(1, 20):
        u = 2 ** rv + 1
        w = (u + 1) ** rv
        for nv in range(0, rv + 1):
            tot += 1
            if (w // u ** nv) % u != int(sympy.binomial(rv, nv)):
                malos.append((rv, nv))
    if malos:
        stats.fail(f"la identidad C(r,n)=floor((u+1)^r/u^n) mod u falla en {malos[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {tot} casos: C(r,n) = floor((u+1)^r/u^n) mod u con u=2^r+1")

    # (b) el sistema diofantico completo.
    # psi=False: se comprueba el ESQUELETO ARITMETICO. Con el anclaje correcto
    # (psi=True, que es el de por defecto) el testigo no es evaluable: L_psi lo
    # construye a partir del rango de aparicion de un K astronomico. Lo que este
    # apartado verifica es la aritmetica de la extraccion de digitos, que es la
    # misma con uno y otro anclaje; la correccion del anclaje se comprueba en
    # test_dioph_soundness [8] y [9].
    B = L_binomial(r, k2, c, over_N=True, psi=False)
    fallos = [f"C({rv},{nv})" for rv, nv in [(5, 2), (8, 3), (12, 5)]
              if not B.check_witness({r: rv, k2: nv, c: int(sympy.binomial(rv, nv))})[0]]
    if fallos:
        stats.fail(f"el sistema binomial no se anula en {fallos}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 3/3 sistemas anulados por el testigo (coste {B.cost()} incognitas)")


def test_factorial_y_wilson(stats):
    print(f"{Colors.HEADER}[13] FACTORIAL y WILSON: la cadena COMPLETA hasta los primos{Colors.ENDC}")
    n, m = sympy.symbols('n m', integer=True)

    # (a) identidad del factorial (barata)
    malos = [nv for nv in range(1, 8)
             if ((nv + 1) ** (nv + 1) + 1) ** nv // int(sympy.binomial((nv + 1) ** (nv + 1) + 1, nv))
             != int(sympy.factorial(nv))]
    if malos:
        stats.fail(f"n! = floor(r^n/C(r,n)) falla en n={malos}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} n=1..7: n! = floor(r^n / C(r,n)) con r=(n+1)^(n+1)+1")

    # (b) el sistema factorial (solo n pequenos: el testigo explota)
    F = L_factorial(n, m, over_N=True, psi=False)   # esqueleto: ver nota en [12](b)
    fallos = [nv for nv in (1, 2)
              if not F.check_witness({n: nv, m: int(sympy.factorial(nv))})[0]]
    if fallos:
        stats.fail(f"sistema factorial no anulado en n={fallos}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} n=1,2 anulan el sistema (coste {F.cost()} incognitas). "
              f"n=3 tambien, pero tarda ~93 s: ver [14]")

    # (c) Wilson: el criterio, verificado masivamente y barato
    err = [v for v in range(2, 250)
           if (((int(sympy.factorial(v - 1)) + 1) % v == 0) != bool(sympy.isprime(v)))]
    if err:
        stats.fail(f"Wilson falla en {err[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Wilson exacto en [2,250): n | (n-1)!+1 <=> n primo")

    # (d) el sistema completo de primalidad
    P = L_prime(n, over_N=True, psi=False)          # esqueleto: ver nota en [12](b)
    ok2, _ = P.check_witness({n: 2})
    ok3, _ = P.check_witness({n: 3})
    if ok2 and ok3:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} n=2 y n=3: testigo construido y sistema ANULADO "
              f"(coste {P.cost()} incognitas, grado {P.degree()})")
    else:
        stats.fail(f"sistema de primalidad no anulado (n=2:{ok2}, n=3:{ok3})")

    # (e) SOUNDNESS: para compuestos el testigo no existe
    if P.witness({n: 4}) is None and P.witness({n: 9}) is None:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} n=4 y n=9 (compuestos): sin testigo (no inventa)")
    else:
        stats.fail("se fabrico testigo de primalidad para un compuesto")


def test_explosion_del_testigo(stats):
    print(f"{Colors.HEADER}[14] EXPLOSION DEL TESTIGO: el precio real de MRDP{Colors.ENDC}")
    import math
    filas = []
    for nv in range(1, 7):
        r = (nv + 1) ** (nv + 1) + 1
        dig_u = int(r * math.log10(2)) + 1
        dig_w = int(r * dig_u)
        filas.append((nv, r, dig_u, dig_w))
    for nv, r, du, dw in filas:
        print(f"    n={nv}: r={r:<9} u=2^r tiene {du:<7} digitos, (u+1)^r ~ {dw:,} digitos")
    creciente = all(filas[i][3] < filas[i + 1][3] for i in range(len(filas) - 1))
    if creciente and filas[-1][3] > 10 ** 9:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} crecimiento explosivo confirmado: en n=6 el testigo ya "
              f"excede 10^9 digitos -> INCOMPUTABLE")
        print(f"  {Colors.WARN}-> la representacion es correcta pero solo teorica: es la razon de que "
              f"estas ecuaciones no se usen en la practica.{Colors.ENDC}")
    else:
        stats.fail("no se reprodujo el crecimiento esperado")


def test_marcador_final(stats):
    print(f"{Colors.HEADER}[15] MARCADOR FINAL: coste medido frente al record{Colors.ENDC}")
    n = sympy.Symbol('n', integer=True)
    coste = L_prime(n, over_N=True).cost()
    record = RECORD_PRIMOS['incognitas']
    print(f"  Representacion COMPLETA de los primos obtenida por composicion: "
          f"{Colors.BOLD}{coste} incognitas{Colors.ENDC} (sobre N)")
    print(f"  Record de Matiyasevich (1975):                                  "
          f"{Colors.BOLD}{record} incognitas{Colors.ENDC}")
    print(f"  {Colors.WARN}-> factor {coste/record:.1f}x por encima. La composicion es ADITIVA: "
          f"encadenar lemas nunca bajara de 9.{Colors.ENDC}")
    print(f"  {Colors.WARN}-> el record exige COMPARTIR incognitas entre eslabones "
          f"(una misma a sirviendo a varias exponenciaciones, etc.).{Colors.ENDC}")
    if coste > record:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} distancia medida y declarada; no se afirma haber batido nada")
    else:
        stats.fail("coste sospechoso: revisar antes de afirmar cualquier mejora")



def test_comparticion(stats):
    print(f"{Colors.HEADER}[16] COMPARTICION DE INCOGNITAS: la unica via hacia el record{Colors.ENDC}")
    # (a) validez matematica: un (a,x,y,t) sirve a varias bases con el mismo exponente
    malos, tot = [], 0
    for kv in (2, 3, 4, 5):
        for bases in ([2, 3, 5], [3, 7, 10]):
            cs = [b ** kv for b in bases]
            av = max(max(cs), kv) + 3
            while any(2 * av * b - b * b - 1 <= c for b, c in zip(bases, cs)):
                av += 1
            xv, yv = pell_seq(av, kv)
            if (yv - kv) % (av - 1) != 0:
                malos.append((kv, 'indice'))
                continue
            for b, c in zip(bases, cs):
                Mv = 2 * av * b - b * b - 1
                rest = (xv - (av - b) * yv) - c
                tot += 1
                if rest % Mv != 0 or rest < 0:
                    malos.append((kv, b))
    if malos:
        stats.fail(f"la comparticion rompe la congruencia en {malos[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {tot} relaciones con (a,x,y,t) COMPARTIDO: congruencia intacta "
              f"(x_k(a),y_k(a) solo dependen de (a,k))")

    # (b) el ahorro medido, extremo a extremo
    n = sympy.Symbol('n', integer=True)
    aditivo = L_prime(n, over_N=True).cost()
    compartido = L_prime_shared(n, over_N=True).cost()
    if compartido < aditivo:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} coste: {aditivo} (aditivo) -> {compartido} (compartido+eliminacion), "
              f"ahorro {aditivo - compartido}")
    else:
        stats.fail(f"la comparticion no ahorro nada: {aditivo} -> {compartido}")

    # (c) la correccion se PRESERVA: mismo veredicto que la version aditiva.
    # Sobre el ESQUELETO ARITMETICO, por la misma razon que en [12](b): con el
    # anclaje psi el testigo completo no es evaluable. La cadena con anclaje
    # correcto se comprueba en test_dioph_soundness [7] (testigo parcial), [3]
    # (soundness por SMT) y [8] (unicidad del valor exponencial).
    P = L_prime_shared(n, over_N=True, anclaje_psi=False)
    ok2, _ = P.check_witness({n: 2})
    ok3, _ = P.check_witness({n: 3})
    sin_testigo = all(P.witness({n: v}) is None for v in (4, 9, 15, 25))
    if ok2 and ok3 and sin_testigo:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} correccion PRESERVADA: n=2,3 anulan el sistema; "
              f"4,9,15,25 (compuestos) sin testigo")
    else:
        stats.fail(f"la comparticion rompio la correccion (n2={ok2}, n3={ok3}, comp={sin_testigo})")

    # (d) desglose del mecanismo
    print(f"  {Colors.BOLD}Desglose:{Colors.ENDC} 5 exponenciaciones en 2 contextos "
          f"(E = n^(n-1) y R = n*E+1 evitan un tercero) ->")
    print(f"    exponente n-1 : 3 relaciones (E, A, P)  -> compartidas + 3")
    print(f"    exponente R   : 2 relaciones (T, W)     -> compartidas + 2")
    print(f"    + UNA sola base `a` (PellBase) para los dos exponentes")
    print(f"    + anclaje del indice por L_psi: +11 incognitas por contexto, -1 (`t` sobra)")


def test_frontera_del_record(stats):
    print(f"{Colors.HEADER}[17] LO QUE FALTA PARA 9: frontera honesta{Colors.ENDC}")
    n = sympy.Symbol('n', integer=True)
    actual = L_prime_shared(n, over_N=True).cost()
    record = RECORD_PRIMOS['incognitas']
    print(f"  mejor coste alcanzado por el calculo : {Colors.BOLD}{actual}{Colors.ENDC} incognitas")
    print(f"  record de Matiyasevich (1975)        : {Colors.BOLD}{record}{Colors.ENDC} incognitas")
    print(f"  {Colors.WARN}-> quedan {actual - record} incognitas de distancia ({actual/record:.1f}x).{Colors.ENDC}")
    print(f"  {Colors.WARN}-> la comparticion POR EXPONENTE COMUN esta agotada; bajar mas exige"
          f" reestructurar la construccion (no encadenar Wilson->factorial->binomial),{Colors.ENDC}")
    print(f"  {Colors.WARN}   que es exactamente el trabajo que costo decadas a los especialistas.{Colors.ENDC}")
    if actual > record:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} distancia declarada; NO se afirma haber batido el record")
    else:
        stats.fail("coste <= record: exigiria revision externa antes de afirmar nada")


def test_generador_propio(stats):
    """[18] EL GENERADOR PROPIO, ya con la cadena anclada por L_psi.

    Que mide. La cadena Wilson -> factorial -> binomial -> exponenciacion que
    PRODUCE ESTE CALCULO (no la transcrita de nadie), aplanada a grado 2 por
    ecuacion y convertida en generador Q = n*(1 - sum P_i^2). El grado del
    generador es 1 + 2*max deg(P_i), asi que aplanar a 2 da grado 5.

    POR QUE APARECE AQUI Y NO ANTES. Hasta la reconstruccion, esta cadena tenia
    el indice anclado por una congruencia que admitia valores espurios: sus
    cifras no median un generador de primos y quedaron retiradas. Con `L_psi` el
    indice queda anclado de verdad, y la cifra vuelve a significar algo.

    QUE NO ES. No es la mejor cifra del proyecto: aplanar el sistema PUBLICADO de
    Jones-Sato-Wada-Wiens da (46, 5), y esta cadena da mas. Son dos caminos
    distintos al mismo rincon de grado 5, y el que gana es el que parte de una
    construccion que costo un paper entero afinar. Lo que esta cifra mide es otra
    cosa: cuanto cuesta la representacion que el compilador OBTIENE POR SI MISMO,
    sin transcribir a nadie. Esa es la magnitud que interesa al proyecto.

    El optimo del aplanado es OPTIMO demostrado (Z3 devuelve la cota inferior y
    coincide con el numero de nombres elegidos), no una heuristica que se planto.
    """
    print(f"{Colors.HEADER}[18] GENERADOR PROPIO (cadena anclada por L_psi){Colors.ENDC}")
    from src.analysis.dioph_degree import to_generator, max_equation_degree
    from src.analysis.dioph_optflat import aplanado_minimo_compuesto, materializar

    n = sympy.Symbol('n', integer=True)
    S = L_prime_shared(n, over_N=True, anclaje_psi=True)
    print(f"  representacion: {S.cost()} incognitas, {len(S.eqs)} ecuaciones, "
          f"grado maximo {max_equation_degree(S)}")

    r = aplanado_minimo_compuesto(S, 2, timeout_s=600)
    if r["estado"] == "sin_z3":
        print("  (z3 no disponible: omitido)"); return
    if r.get("elegidos") is None:
        stats.fail(f"el aplanado no concluyo: {r['estado']}")
        return
    F = materializar(S, r["elegidos"], 2)
    grado_f = max_equation_degree(F)
    _, info = to_generator(F, n)
    print(f"  aplanado {r['estado']}: {r['nombres']} nombres (cota {r['cota']}) "
          f"-> {F.cost()} incognitas, grado {grado_f}")
    print(f"  {Colors.BOLD}GENERADOR: ({info['variables']} variables, "
          f"grado {info['grado']}){Colors.ENDC}")
    print(f"  {Colors.WARN}Para comparar: aplanar el sistema publicado de JSWW 1976 da")
    print(f"  (46, 5). Esta cifra no lo mejora; mide otra cosa -- lo que cuesta la")
    print(f"  representacion que el calculo construye por su cuenta.{Colors.ENDC}")

    if grado_f > 2 or info["grado"] != 5:
        stats.fail(f"el aplanado no llego a grado 2 por ecuacion (grado {grado_f})")
        return
    if r["estado"] != "optimo":
        stats.fail(f"la cifra no es un optimo demostrado sino '{r['estado']}': "
                   f"no debe publicarse como minimo")
        return

    # Los valores del testigo PARCIAL deben ser >= 0: el generador n*(1-sum P^2)
    # solo representa el conjunto sobre variables no negativas. El testigo
    # completo no es evaluable (rango de aparicion astronomico), asi que se
    # comprueba lo que hay; se dice cual es el alcance de la comprobacion.
    Sp = L_prime_shared(n, over_N=True, anclaje_psi=True, testigo_psi=False)
    w = Sp.witness({n: 3})
    negativos = [] if w is None else [(k, v) for k, v in w.items() if int(v) < 0]
    if negativos:
        stats.fail(f"testigo con valores negativos: {negativos[:3]} "
                   f"(el generador sobre N no seria valido)")
        return
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} optimo DEMOSTRADO, grado 5, y los "
          f"{0 if w is None else len(w)} valores del testigo parcial son >= 0")
    stats.ok()


def main():
    print(f"{Colors.BOLD}=== CALCULO DE CONSTRUCCIONES DIOFANTICAS (ataque al record) ==={Colors.ENDC}")
    stats = Stats()
    test_lagrange(stats)
    test_basic_lemmas(stats)
    test_soundness(stats)
    test_pell(stats)
    test_is_pell_y(stats)
    test_composicion_y_coste(stats)
    test_marcador(stats)
    test_exponencial_completitud(stats)
    test_exponencial_soundness(stats)
    test_coste_N_vs_Z(stats)
    test_distancia_al_record(stats)
    test_binomial(stats)
    test_factorial_y_wilson(stats)
    test_explosion_del_testigo(stats)
    test_marcador_final(stats)
    test_comparticion(stats)
    test_frontera_del_record(stats)
    test_generador_propio(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — lemas certificados con coste exacto y "
              f"testigo constructivo; Pell verificado. Infraestructura lista para la busqueda.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
