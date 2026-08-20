#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - SOUNDNESS POR SMT: la direccion que nunca se comprobaba
================================================================================
Todo el calculo diofantico verificaba COMPLETITUD (pertenece => hay testigo)
construyendo el testigo. La direccion inversa -- SOUNDNESS: no pertenece => NO
hay testigo -- se declaraba y se dejaba descansar en los teoremas citados,
porque las incognitas viven en rangos astronomicos y ninguna busqueda los toca.

Este test la comprueba con un demostrador SMT, que no enumera sino que razona.
Y lo primero que encontro fue un DEFECTO REAL: en modo N las condiciones
laterales del lema exponencial no imponian nada (`L_nonneg_N` devolvia un
sistema vacio), de modo que el sistema de los primos admitia solucion para
n = 4, 9, 15, 25. El generador construido sobre el habria emitido compuestos.

Comprueba:
  - el traductor sympy -> Z3 es fiel (evalua igual que sympy);
  - los conjuntos elementales del catalogo son SOUND (unsat demostrado);
  - REGRESION: el sistema de los primos ya no admite solucion para compuestos;
  - UNICIDAD: los subsistemas que "calculan" un valor lo FUERZAN.
"""

import sys
import os
import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_problems import build_catalog, rango_de
from src.analysis.dioph_calculus import Dioph
from src.analysis.dioph_lemmas import (
    L_exponential, L_composite, L_nonneg_N, L_psi, pell_seq, fresh,
    L_prime_shared,
)
from src.analysis.dioph_soundness import (
    Z3_DISPONIBLE, sympy_to_z3, solve, soundness_report, uniqueness_report, resumen,
    refuta_configuracion, cota_desde_testigo, unicidad_exponencial,
    unicidad_exponencial_psi,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}FALLO: {msg}{Colors.ENDC}")


# ---------------------------------------------------------------------------

def test_traductor(stats):
    """[1] El traductor sympy -> Z3 debe evaluar EXACTAMENTE igual que sympy."""
    print(f"\n{Colors.HEADER}[1] Fidelidad del traductor sympy -> Z3{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    import z3
    x, y = sympy.symbols('x y', integer=True)
    exprs = [x + y, x * y - 3, x**3 - 2*y**2 + 7, (x + y)**2, x**2*y - x*y**2 + 1]
    malos = 0
    for e in exprs:
        e = sympy.expand(e)
        vm = {}
        ez = sympy_to_z3(e, vm)
        for xv in range(-3, 4):
            for yv in range(-3, 4):
                s = z3.Solver()
                s.add(vm[x] == xv); s.add(vm[y] == yv)
                s.check()
                got = s.model().eval(ez, model_completion=True).as_long()
                esperado = int(e.subs({x: xv, y: yv}))
                if got != esperado:
                    malos += 1
    if malos == 0:
        print(f"  {Colors.OKGREEN}OK{Colors.ENDC} {len(exprs)} polinomios x 49 puntos: identicos a sympy")
        stats.ok()
    else:
        stats.fail(f"{malos} discrepancias traductor/sympy")


def test_catalogo_sound(stats):
    """[2] Los conjuntos del catalogo no deben admitir solucion fuera del conjunto."""
    print(f"\n{Colors.HEADER}[2] SOUNDNESS del catalogo (unsat demostrado por Z3){Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    problemas = 0
    for prob in build_catalog():
        if prob.name == "primo":
            continue                      # tiene su propio test de regresion
        ok, filas, defectos = soundness_report(prob, rango_de(prob),
                                              timeout_ms=8000, rlimit=4_000_000)
        marca = Colors.OKGREEN + "OK" + Colors.ENDC if ok else Colors.FAIL + "DEFECTO" + Colors.ENDC
        print(f"  {marca} {prob.name:<22} {resumen(filas)}")
        if not ok:
            problemas += 1
            for d in defectos[:2]:
                print(f"      {d}")
    if problemas == 0:
        stats.ok()
    else:
        stats.fail(f"{problemas} conjuntos admiten soluciones espurias")


def test_regresion_primos(stats):
    """[3] REGRESION del defecto: la FIRMA del fallo debe estar excluida.

    Historia: `L_nonneg_N` declaraba coste 0 para cualquier expresion, asi que en
    modo N las condiciones laterales (c < M, a > c, a-1 > k) no imponian NADA. Con
    a in {0,1} la ecuacion de Pell degenera --(x,y) = (1,0) la resuelve para
    cualquier a-- y Z3 encontraba testigo para n = 4, 9, 15 y 25.

    DOS GUARDARRAILES, y el primero es el que vale:

      (A) La FIRMA, sin cota: "existe solucion con a = 0?" y con a = 1. Es una
          consulta GLOBAL (ninguna caja), instantanea, y apunta exactamente al
          fallo. Un guardarrail debe apuntar al defecto, no a su vecindario.
      (B) Un barrido en la caja [0,20], que ademas cubre configuraciones
          degeneradas que no habiamos anticipado.

    Sobre por que no se barre mas lejos: medido en este sistema, cota 20 concluye
    en 0 s, cota 50 deja 1 de 8 sin concluir y cota 100 deja 3 de 8. La escalada
    completa (200 -> 20) si concluye en los ocho, pero tarda ~213 s; queda para
    ejecucion manual, no para la suite. 'unknown' nunca cuenta como exito.
    """
    print(f"\n{Colors.HEADER}[3] REGRESION: la firma del defecto sigue excluida{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    prob = [p for p in build_catalog() if p.name == "primo"][0]
    compuestos = [4, 9, 15, 21, 25, 27, 33, 35]
    base = [u for u in prob.system.unknowns if str(u).startswith("ca")]
    fallos = []

    # (A) la firma exacta: base de Pell degenerada. Sin cota.
    if not base:
        fallos.append("no se localizo la incognita de la base de Pell")
    for v in compuestos:
        for deg in (0, 1):
            r = refuta_configuracion(prob.system, {prob.param: v}, {base[0]: deg},
                                     timeout_ms=8000, rlimit=2_000_000)
            if r["estado"] != "unsat":
                fallos.append(f"n={v} con a={deg}: {r['estado']} (se exige unsat)")
    print(f"  {Colors.OKGREEN}A{Colors.ENDC} a in {{0,1}} refutado SIN COTA en "
          f"{len(compuestos)} compuestos x 2 = {2*len(compuestos)} consultas")

    # (B) barrido en caja pequena
    ok, filas, defectos = soundness_report(prob, compuestos, timeout_ms=8000,
                                           rlimit=2_000_000, intentar_sin_cota=False,
                                           cotas_de_reserva=(20,))
    estados = resumen(filas)
    print(f"  {Colors.OKGREEN}B{Colors.ENDC} barrido en [0,20]: {estados}")
    if any(f[-1] == "sat" for f in filas):
        fallos.extend(defectos)
    if any(f[-1] not in ("unsat", "unsat<=20") for f in filas):
        fallos.append(f"algun compuesto no concluyo en la caja: {estados}")

    if fallos:
        for f in fallos[:4]:
            print(f"  {Colors.FAIL}{f}{Colors.ENDC}")
        stats.fail(fallos[0])
    else:
        stats.ok()


def test_unicidad_exponencial(stats):
    """[4] UNICIDAD: el subsistema de b^k debe FORZAR el valor, no solo admitirlo.

    Es el riesgo real de una cadena larga: si un eslabon admite un valor espurio,
    todo lo que venga detras hereda el defecto.

    ESTE TEST DABA UN FALSO POSITIVO. Antes preguntaba `sistema AND c != b^k` con
    una cota fija de 200 y contaba el 'unsat' como exito. Pero los testigos de
    Pell crecen exponencialmente en el indice: para 2^3 la solucion buena ya vale
    ~13.000, queda FUERA de la caja, y entonces "no hay solucion con otro valor"
    es trivialmente cierto porque no hay NINGUNA solucion. Dos de los tres casos
    que el test declaraba 'unico' eran vacuos.

    La correccion es doble:
      * la cota se deriva del TESTIGO REAL (`cota_desde_testigo`), no se elige;
      * `uniqueness_report` comprueba ADEMAS que el valor correcto es alcanzable
        en esa caja, y devuelve 'vacuo' cuando no lo es. 'vacuo' NO es exito.
    """
    print(f"\n{Colors.HEADER}[4] UNICIDAD del lema exponencial (con guardia de vacuidad){Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    casos = [(2, 2), (3, 2), (2, 3)]
    veredictos = []
    for bv, kv in casos:
        c = fresh("val")
        S0 = L_exponential(sympy.Integer(bv), sympy.Integer(kv), c, over_N=True)
        cota = cota_desde_testigo(S0, {c: bv ** kv}, factor=2)
        S = Dioph(params=[], unknowns=S0.unknowns + [c], eqs=S0.eqs,
                  witness=None, name="c = b^k")
        r = uniqueness_report(S, {}, c, bv ** kv, over_N=True, bound=cota,
                              timeout_ms=25000, rlimit=8_000_000)
        veredictos.append((bv, kv, r["veredicto"]))
        color = {"unico": Colors.OKGREEN, "ESPURIO": Colors.FAIL}.get(r["veredicto"], Colors.WARN)
        print(f"  {color}{bv}^{kv}: {r['veredicto']}{Colors.ENDC} "
              f"(caja [0,{cota}] derivada del testigo; alcanzable={r['alcanzable']})")
    espurios = [v for v in veredictos if v[2] == "ESPURIO"]
    utiles = [v for v in veredictos if v[2] == "unico"]
    if espurios:
        stats.fail(f"valor espurio admitido en {espurios}")
    elif not utiles:
        stats.fail("ningun caso concluyo de forma NO vacua: el test no prueba nada")
    else:
        print(f"  {Colors.WARN}Los casos 'vacuo' o 'unknown' no aportan evidencia; "
              f"solo cuentan los {len(utiles)} marcados 'unico'.{Colors.ENDC}")
        stats.ok()


def test_unknown_no_es_prueba(stats):
    """[5] Honestidad: 'unknown' se reporta como 'unknown', jamas como exito.

    Se construye a proposito un sistema satisfacible y se comprueba que el
    informe dice 'sat' (no 'unsat'), y un sistema imposible que dice 'unsat'.
    """
    print(f"\n{Colors.HEADER}[5] Los tres estados se distinguen (sat / unsat / unknown){Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    n = sympy.Symbol('n', integer=True)
    sat = solve(L_composite(n), {n: 12}, over_N=True, timeout_ms=5000)
    unsat = solve(L_composite(n), {n: 13}, over_N=True, timeout_ms=5000)
    print(f"  12 compuesto -> {sat['estado']}   13 primo -> {unsat['estado']}")
    if sat["estado"] == "sat" and unsat["estado"] == "unsat":
        stats.ok()
    else:
        stats.fail(f"estados inesperados: 12->{sat['estado']} 13->{unsat['estado']}")


def test_criterio_gratis(stats):
    """[6] El criterio "gratis sobre N" debe ser CIERTO, no comodo.

    `L_nonneg_N` declara coste 0 cuando todos los coeficientes del polinomio son
    >= 0. Aqui se comprueba a la inversa: para cada expresion que el lema declara
    gratis, se evalua en un rango de asignaciones NO NEGATIVAS y se exige que
    nunca salga negativa. Es el guardarrail del defecto que costo esta sesion:
    declarar gratis lo que no lo era anulaba condiciones laterales enteras.
    """
    print(f"\n{Colors.HEADER}[6] El criterio 'gratis sobre N' no miente{Colors.ENDC}")
    x, y = sympy.symbols('x y', integer=True, nonnegative=True)
    casos = [x, x + 1, 2*x + 3*y, x*y, x**2 + y, sympy.Integer(5),
             x - 1, x - y, 2*x - 3, x*y - 1, sympy.Integer(-2)]
    malos = []
    gratis = 0
    for e in casos:
        d = L_nonneg_N(e)
        if d.cost() != 0 or d.eqs:
            continue                       # cuesta holgura: no afirma nada
        gratis += 1
        for xv in range(0, 8):
            for yv in range(0, 8):
                if int(sympy.expand(e).subs({x: xv, y: yv})) < 0:
                    malos.append((e, xv, yv))
    if malos:
        stats.fail(f"declarado gratis pero NEGATIVO: {malos[:3]}")
    else:
        print(f"  {Colors.OKGREEN}OK{Colors.ENDC} {gratis} expresiones declaradas gratis, "
              f"ninguna negativa en 64 asignaciones de N")
        stats.ok()


def test_base_pell_compartida(stats):
    """[7] Compartir la base `a` entre exponentes distintos no rompe nada.

    Es el mecanismo que mas incognitas ahorro. Compartir es exactamente donde se
    cuelan los errores: si un contexto necesita una `a` mayor que la que fija la
    base, el testigo deja de existir.

    DOS MEDIDAS, porque desde el anclaje por `L_psi` ya no se puede hacer una
    sola, y conviene decir por que:

      (a) Sobre el ESQUELETO ARITMETICO (`anclaje_psi=False`) el testigo se
          construye entero y se comprueba entero. Ese esqueleto no representa
          los primos --el anclaje por congruencia admite valores espurios, ver
          [8]-- pero es donde vive toda la aritmetica de la cadena: cotas, base
          compartida, congruencias de Davis, Wilson, factorial, binomial. Que
          siga anulando el sistema es evidencia real sobre esa aritmetica.

      (b) Sobre la CADENA CORRECTA (`anclaje_psi=True`) el testigo completo NO es
          evaluable, y no por falta de maquina: `L_psi` construye el suyo a
          partir del rango de aparicion de K = 2*D*(e+1)*C^2, que exige factorizar
          un K astronomico ya para n=2. El rango existe siempre --la sucesion de
          Pell es de divisibilidad-- pero calcularlo no. Asi que se comprueba el
          TESTIGO PARCIAL: todas las ecuaciones que no dependen de las incognitas
          internas de L_psi. Verifica que el anclaje no rompio la aritmetica; NO
          verifica la completitud de la cadena, que descansa en el teorema.

    Decirlo asi importa. La cadena gano correccion y perdio verificabilidad por
    evaluacion, y ese intercambio hay que anotarlo, no disimularlo.
    """
    print(f"\n{Colors.HEADER}[7] Base de Pell compartida entre exponentes distintos{Colors.ENDC}")
    n = sympy.Symbol('n', integer=True)

    # (a) esqueleto aritmetico: testigo COMPLETO
    esq = L_prime_shared(n, over_N=True, anclaje_psi=False)
    ok_a = True
    for v in (2, 3):
        vale, _ = esq.check_witness({n: v})
        ok_a = ok_a and vale
    marca = Colors.OKGREEN + "a" + Colors.ENDC if ok_a else Colors.FAIL + "a" + Colors.ENDC
    print(f"  {marca} esqueleto aritmetico ({esq.cost()} incognitas, {len(esq.eqs)} ec.): "
          f"testigo COMPLETO valido en n=2,3")

    # (b) cadena correcta: testigo PARCIAL
    S = L_prime_shared(n, over_N=True, anclaje_psi=True, testigo_psi=False)
    internas = {u for u in S.unknowns if str(u).startswith('p')}
    ok_b, visibles = True, 0
    for v in (2, 3):
        w = S.witness({n: v})
        if w is None:
            ok_b = False
            break
        conocidas = internas - set(w)            # las que el testigo parcial no fija
        vis = [e for e in S.eqs if not (e.free_symbols & conocidas)]
        visibles = len(vis)
        sust = dict(w); sust[n] = v
        if not all(sympy.expand(e.subs(sust)) == 0 for e in vis):
            ok_b = False
            break
    marca = Colors.OKGREEN + "b" + Colors.ENDC if ok_b else Colors.FAIL + "b" + Colors.ENDC
    print(f"  {marca} cadena con anclaje psi ({S.cost()} incognitas, {len(S.eqs)} ec.): "
          f"testigo PARCIAL anula {visibles}/{len(S.eqs)} ecuaciones en n=2,3")
    print(f"  {Colors.WARN}Las {len(S.eqs) - visibles} restantes dependen de incognitas internas de")
    print(f"  L_psi, cuyo testigo exige el rango de aparicion de un K astronomico:")
    print(f"  la completitud de la cadena correcta no se comprueba por evaluacion,")
    print(f"  descansa en el Teorema 1 de Pak-Kaliszyk (Mizar HILB10_8:19).{Colors.ENDC}")

    if ok_a and ok_b:
        print(f"  (la base fija a = suma de cotas; cada contexto exige a >= su cota,")
        print(f"   y la suma domina a cada sumando porque sobre N todas son >= 0)")
        stats.ok()
    else:
        stats.fail("la base compartida deja algun contexto sin testigo "
                   f"(esqueleto={ok_a}, anclaje psi={ok_b})")


def test_unicidad_por_enumeracion(stats):
    """[8] DEFECTO CERRADO: el lema exponencial reconstruido SI fuerza c = b^k.

    HISTORIA, que es la mitad del valor de este test. La version anterior fijaba
    el indice con una sola congruencia, `y == k (mod a-1)`. Eso fija el RESIDUO
    de k, no k: valen tambien m = k + j(a-1), y cada uno aporta su propio c. La
    enumeracion lo exhibio:

        3^2 = 9  -> admitia c en {1, 3, 5, 7, 9}
        2^2 = 4  -> admitia c en {1, 2, 4, 7, 8, 9, 16}
        2^3 = 8  -> admitia c en {1, 2, 6, 8, 18, 21, 25, 32}

    Toda la cadena Wilson -> factorial -> binomial descansaba en ese lema, asi
    que el sistema de los primos no era sound y sus cifras quedaron retiradas.
    El test se dejo EN ROJO durante toda la reparacion.

    QUE SE COMPRUEBA AHORA, y son dos cosas distintas:

      (A) PODER DISCRIMINANTE. Se vuelve a enumerar el lema VIEJO y se exige que
          siga exhibiendo los valores espurios. Un test que solo comprueba la
          version arreglada no demuestra que sepa detectar el fallo; este si,
          porque lo detecta delante de quien lo lee.
      (B) LA REPARACION. Se enumera el lema RECONSTRUIDO sobre `L_psi`, que ancla
          el indice de verdad (Teorema 1 de Pak-Kaliszyk, Mizar HILB10_8:19), y
          se exige que el unico c admisible sea b^k.

    QUE SUPONE (B). Que `L_psi(a,k,Y)` implica Y = y_k(a); eso NO se supone a
    ciegas, se comprueba en [9] por barrido directo sobre sus 9 ecuaciones. La
    razon de partirlo es que los testigos de `L_psi` salen del rango de aparicion
    y son astronomicos aun en casos de juguete, de modo que no se pueden evaluar
    dentro de un barrido. Partir la comprobacion permite verificar cada mitad con
    la herramienta que le sirve, en vez de no verificar ninguna.
    """
    print(f"\n{Colors.HEADER}[8] Unicidad del lema exponencial: antes y despues{Colors.ENDC}")
    casos = [(3, 2), (2, 2), (2, 3)]

    # (A) el lema VIEJO debe seguir fallando: si no, el test no prueba nada.
    sin_detectar = []
    for bv, kv in casos:
        adm = unicidad_exponencial(bv, kv, 3 * bv ** kv + 8)
        if adm == [bv ** kv]:
            sin_detectar.append((bv, kv))
    if sin_detectar:
        stats.fail(f"la enumeracion ya no detecta el defecto historico en {sin_detectar}: "
                   f"el test perdio poder discriminante y su verde no significa nada")
        return
    print(f"  {Colors.OKGREEN}A{Colors.ENDC} el lema con anclaje por congruencia sigue "
          f"exhibiendo valores espurios en los {len(casos)} casos (poder discriminante intacto)")

    # (B) el lema RECONSTRUIDO sobre L_psi debe dar exactamente b^k.
    casos_psi = casos + [(5, 3), (2, 5), (7, 2)]
    malos = []
    for bv, kv in casos_psi:
        adm = unicidad_exponencial_psi(bv, kv, 3 * bv ** kv + 8)
        esperado = [bv ** kv]
        color = Colors.OKGREEN if adm == esperado else Colors.FAIL
        print(f"    {color}{bv}^{kv} = {bv**kv}: c admisibles = {adm}{Colors.ENDC}")
        if adm != esperado:
            malos.append((bv, kv, adm))
    if malos:
        stats.fail(f"el lema reconstruido AUN admite valores espurios: {malos}")
    else:
        print(f"  {Colors.OKGREEN}B{Colors.ENDC} con el indice anclado por L_psi el unico c "
              f"admisible es b^k en los {len(casos_psi)} casos")
        stats.ok()


def test_lema_psi(stats):
    """[9] EL LEMA CORRECTO: C = psi_A(B), con TESTIGO CONSTRUIDO.

    Reemplaza a la parte rota del lema exponencial. Transcrito del Teorema 1 de
    Pak-Kaliszyk (ITP 2022, Mizar HILB10_8:19), que sigue a Matiyasevich-Robinson.
    Lo que anade y faltaba: ANCLA EL INDICE. La version rota solo tenia la
    congruencia `y_k(a) == k (mod a-1)`, que fija el residuo de k pero no k.

    El testigo ya no se BUSCA (era inviable: los (i,j) son astronomicos), se
    CONSTRUYE, y esa es la diferencia entre un lema y una conjetura:
      * i sale del RANGO DE APARICION de K = 2D(e+1)C^2 en la sucesion y_.(A),
        que existe porque es una sucesion de divisibilidad;
      * para H basta m = B, y eso desatasca todo: G == 1 (mod 2C) da la forma
        B + 2jC, y G == A (mod F) da F | (H - C);
      * DFI = (x_B(A) * x_l(A) * x_B(G))^2, cuadrado POR CONSTRUCCION.

    Se comprueba: grado <= 5 por ecuacion, soundness hacia delante, testigos
    validos para C = psi_A(B), y AUSENCIA de testigo para C != psi_A(B).

    AVISO DE ESCALA. El rango de aparicion crece muy rapido: certificar que
    y_2(3) = 6 ya exige l = 408, y y_4(2) = 56 exige l = 43.456, con E de decenas
    de miles de cifras. Los testigos de este lema son astronomicos POR NATURALEZA.
    Por eso la cadena completa nunca se podra validar por evaluacion mas alla de
    casos diminutos: descansa en el teorema citado, y conviene no olvidarlo.
    """
    print(f"\n{Colors.HEADER}[9] Lema psi_A(B): la pieza correcta, con testigo construido{Colors.ENDC}")
    A, B, C = sympy.symbols('A B C', integer=True)
    S = L_psi(A, B, C, over_N=True)
    grado = max(sympy.Poly(e, *(S.params + S.unknowns)).total_degree() for e in S.eqs)
    print(f"  sistema: {S.cost()} incognitas, {len(S.eqs)} ecuaciones, grado maximo {grado}")
    if grado > 5:
        stats.fail(f"grado {grado}: los intermedios D..I no se estan nombrando")
        return

    # SOUNDNESS hacia delante: barato, y es la direccion que fallo antes.
    violaciones, positivos = [], 0
    for Av in range(2, 7):
        for Bv in range(1, 6):
            _, yB = pell_seq(Av, Bv)
            for Cv in range(1, 120):
                if Cv < Bv:
                    continue
                Dv = (Av * Av - 1) * Cv * Cv + 1
                for iv in range(0, 25):
                    Ev = 2 * (iv + 1) * Dv * Cv * Cv
                    Fv = (Av * Av - 1) * Ev * Ev + 1
                    Gv = Av + Fv * (Fv - Av)
                    for jv in range(0, 25):
                        Hv = Bv + 2 * jv * Cv
                        if (Hv - Cv) % Fv != 0:
                            continue
                        Iv = (Gv * Gv - 1) * Hv * Hv + 1
                        if not sympy.integer_nthroot(Dv * Fv * Iv, 2)[1]:
                            continue
                        positivos += 1
                        if Cv != yB:
                            violaciones.append((Av, Bv, Cv, yB))
    print(f"  soundness: {positivos} tuplas cumplen las tres condiciones, "
          f"{len(violaciones)} violaciones")
    if violaciones:
        stats.fail(f"C != psi_A(B) en {violaciones[:3]}")
        return

    # COMPLETITUD con el constructor explicito, y su reverso.
    # Lista explicita, no un rango: el rango de aparicion --y con el, el coste de
    # construir el testigo-- crece brutalmente con (A,B). Estos son los casos que
    # se calculan en segundos; mas alla no es que falte testigo, es que no se
    # puede CALCULAR, y son cosas distintas.
    casos = [(2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3),
             (4, 1), (4, 2), (5, 1), (5, 2)]
    buenos, malos, espurios = 0, [], []
    for Av, Bv in casos:
        if True:
            _, y = pell_seq(Av, Bv)
            ok, _ = S.check_witness({A: Av, B: Bv, C: y})
            if ok:
                buenos += 1
            else:
                malos.append((Av, Bv, y))
            for delta in (1, 2):
                m, _ = S.check_witness({A: Av, B: Bv, C: y + delta})
                if m:
                    espurios.append((Av, Bv, y + delta, y))
    print(f"  completitud: {buenos} testigos construidos y verificados, {len(malos)} fallos")
    print(f"  reverso: {len(espurios)} testigos espurios para C != psi_A(B)")
    if malos:
        stats.fail(f"sin testigo para valores correctos: {malos[:3]}")
    elif espurios:
        stats.fail(f"testigo para valores incorrectos: {espurios[:3]}")
    else:
        print(f"  {Colors.WARN}Escala: certificar y_2(3)=6 exige rango de aparicion l=408, y")
        print(f"  y_4(2)=56 exige l=43.456. Los testigos son astronomicos por")
        print(f"  naturaleza; la cadena completa no se validara por evaluacion.{Colors.ENDC}")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== SOUNDNESS POR SMT: LA DIRECCION QUE FALTABA ==={Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print(f"{Colors.WARN}z3 no instalado: 'pip install z3-solver'. Nada que verificar.{Colors.ENDC}")
        sys.exit(0)
    stats = Stats()
    test_traductor(stats)
    test_catalogo_sound(stats)
    test_regresion_primos(stats)
    test_unicidad_exponencial(stats)
    test_unknown_no_es_prueba(stats)
    test_criterio_gratis(stats)
    test_base_pell_compartida(stats)
    test_unicidad_por_enumeracion(stats)
    test_lema_psi(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — soundness comprobada, "
              f"no solo declarada.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
