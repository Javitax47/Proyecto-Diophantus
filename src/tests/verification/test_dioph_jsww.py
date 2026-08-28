#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - JONES-SATO-WADA-WIENS 1976 COMO PATRON DE MEDIDA EXTERNO
================================================================================
Es el unico punto de la literatura contra el que este proyecto puede medirse SIN
depender de que su propia cadena de Wilson sea correcta: su sistema esta escrito
explicitamente en el paper y se transcribe entero.

Comprueba:
  - la TRANSCRIPCION es fiel: reproduce (26 variables, grado 25), las cifras
    publicadas. Si alguien altera una ecuacion, esto lo detecta;
  - el coste de NUESTRO aplanado sobre SU sistema, frente a las 16 incognitas que
    ellos anadieron con la sustitucion de Skolem. Es un marcador honesto de una
    pieza que todavia va por detras;
  - que la forma factorizada importa: aplanar el arbol gana solo si no se expando
    antes.

Fuente PRIMARIA cotejada: J. P. Jones, D. Sato, H. Wada, D. Wiens, "Diophantine
representation of the set of prime numbers", Amer. Math. Monthly 83:6 (1976)
449-464, p. 450.
"""

import sys
import os

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import (
    sistema, sistema_desplazado, no_negativos_desplazados, FACTOR, PUBLICADO,
    INCOGNITAS, NO_NEGATIVOS_DEMOSTRADOS, COTA_A, COTA_N, ECUACIONES,
)
from src.analysis.dioph_degree import (
    flatten_greedy, flatten_tree, to_generator, max_equation_degree,
    eliminar_lineales, eliminar_maximo,
)
from src.analysis.dioph_optflat import (
    Z3_DISPONIBLE, aplanado_minimo_compuesto, materializar, no_negativo_sobre_N,
    barrido_pareto, aplanado_y_eliminacion,
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


#: EL PIPELINE PUBLICADO, calculado UNA vez. Lo usan [4] (la cifra) y [5] (la
#: equivalencia), y tienen que ver EXACTAMENTE el mismo sistema: cuando cada test
#: lo recalculaba por su cuenta, el optimo --que no es unico-- salia distinto en
#: cada uno y los dos publicaban cifras que no casaban, (36,5) y (38,5). Ademas
#: sobre el sistema desplazado cada solve cuesta minutos.
_PIPELINE = None


#: MEJOR CIFRA CONSTRUIBLE a grado 5, y por tanto el umbral de regresion de [4]
#: y [9]. NO es 42. Este proyecto llego a publicar (33,5) y hubo que retirarlo:
#: salia de la ruta de reescritura, que certifica conjuntos de nombres que luego
#: NO se pueden materializar. Poner aqui el 42 de JSWW convertiria el test en una
#: aspiracion en vez de en una guarda: fallaria hoy sin que nada se haya roto.
MEJOR_GRADO_5 = 44


def pipeline_publicado():
    """Sistema desplazado (`a = A+2`, cota demostrada) aplanado y post-eliminado.

    `k_optimos=1` basta porque `aplanado_y_eliminacion` corre DOS tandas --libre y
    forzando las definiciones lineales-- y la que gana es la forzada. Subirlo solo
    puede mejorar la cifra; se deja en 1 para que la suite termine.
    """
    global _PIPELINE
    if _PIPELINE is None:
        S = sistema_desplazado(COTA_A)
        _PIPELINE = (S, aplanado_y_eliminacion(
            S, 2, k_optimos=1, solo_eliminar=list(S.unknowns),
            demostrados=no_negativos_desplazados(COTA_A)))
    return _PIPELINE


def test_transcripcion(stats):
    """[1] La transcripcion debe reproducir las cifras PUBLICADAS: (26, 25)."""
    print(f"\n{Colors.HEADER}[1] Fidelidad de la transcripcion de (1){Colors.ENDC}")
    S = sistema()
    _, g = to_generator(S, FACTOR)
    esperado = PUBLICADO["generador"]
    print(f"  medido: ({g['variables']} variables, grado {g['grado']})   "
          f"publicado: ({esperado[0]}, {esperado[1]})")
    if (g["variables"], g["grado"]) == esperado:
        print(f"  {Colors.OKGREEN}OK{Colors.ENDC} 14 ecuaciones, 25 incognitas + el parametro k")
        stats.ok()
    else:
        stats.fail(f"la transcripcion no reproduce {esperado}: alguna ecuacion esta mal copiada")


def test_marcador_de_aplanado(stats):
    """[2] Cuanto nos cuesta a NOSOTROS lo que a ellos les costo 16 incognitas.

    Este test no exige ganar: exige MEDIR y dejar la brecha por escrito. Un
    marcador que solo se publica cuando favorece no es un marcador.
    """
    print(f"\n{Colors.HEADER}[2] Aplanado a grado 2 sobre SU sistema (= Skolem){Colors.ENDC}")
    base = len(INCOGNITAS)
    Se = sistema(expandir=True)
    Sf = sistema(expandir=False)
    filas = [
        ("voraz sobre expandido", flatten_greedy(Se, 2)),
        ("Skolem sobre expandido", flatten_tree(Se, 2)),
        ("Skolem sobre factorizado", flatten_tree(Sf, 2)),
    ]
    mejor = None
    for etiqueta, F in filas:
        _, g = to_generator(F, FACTOR)
        anadidas = F.cost() - base
        if max_equation_degree(F) > 2:
            stats.fail(f"{etiqueta}: no llego a grado 2 por ecuacion")
            return
        if g["grado"] != 5:
            stats.fail(f"{etiqueta}: generador de grado {g['grado']}, se esperaba 5")
            return
        mejor = anadidas if mejor is None else min(mejor, anadidas)
        print(f"  {etiqueta:<26} +{anadidas:2d} incognitas -> "
              f"({g['variables']} variables, grado {g['grado']})")
    print(f"  {Colors.BOLD}JSWW 1976 (publicado){Colors.ENDC}      +16 incognitas -> (42 variables, grado 5)")
    if mejor <= 16:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} igualamos o mejoramos su sustitucion de Skolem")
    else:
        print(f"  {Colors.WARN}Vamos {mejor - 16} incognitas POR DETRAS de lo que ellos "
              f"hicieron a mano en 1976.{Colors.ENDC}")
        print(f"  {Colors.WARN}-> nuestro generador de primos queda por debajo de 42 por partir de "
              f"una representacion mas barata, NO por aplanar mejor.{Colors.ENDC}")
    stats.ok()


def test_grado_menor_que_5(stats):
    """[3] Que grado < 5 sigue ABIERTO lo dicen los propios autores."""
    print(f"\n{Colors.HEADER}[3] Grado < 5: problema abierto, no descartado{Colors.ENDC}")
    print("  JSWW 1976, p. 450, textual:")
    print("    \"We do not know whether there is a prime representing polynomial")
    print("     of degree < 5.\"")
    print(f"  {Colors.WARN}Concuerda con el argumento estructural: Q = n(1 - sum P_i^2) tiene")
    print(f"  grado 1 + 2*max deg(P_i), y un sistema lineal define un conjunto")
    print(f"  semilineal, que los primos no son. Pero eso solo acota ESTA")
    print(f"  construccion, no todas.{Colors.ENDC}")
    if PUBLICADO["grado_menor_que_5"].startswith("abierto"):
        stats.ok()
    else:
        stats.fail("se ha alterado la nota sobre el estado del problema")


def test_aplanado_optimo(stats):
    """[4] El aplanado OPTIMO, con cota inferior demostrada y sistema materializado.

    Las heuristicas dicen "he encontrado 46"; el optimizador dice ademas cuanto
    es lo mejor que SU codificacion sabe certificar, y `materializar` convierte
    esa eleccion en un sistema real. Sin materializar, la cifra es un numero de un
    solucionador y no un resultado.

    OJO CON LA PALABRA MINIMO. Este test decia "46 es el minimo" y era falso por
    dos motivos distintos, ambos hallados por revision adversarial:
      * la cota que devuelve el optimizador es de su CODIFICACION, no del
        problema -- hay contraejemplo, ver el comentario en `dioph_optflat`;
      * su objetivo minimiza NOMBRES con las incognitas originales congeladas, de
        modo que ni siquiera puede representar "eliminar una incognita", que es
        justo lo que baja la cifra de 46 a 44 al final de este mismo test.
    Lo que se afirma ahora es: esta es la mejor cifra CONSTRUIDA, y sigue abierto
    que se pueda bajar.

    Se comprueba: el optimizador alcanza su cota (optimo demostrado), el sistema
    materializado tiene grado <= 2 por ecuacion, y las cifras salen donde deben.

    RESTRICCION QUE NO ES OPCIONAL. El optimizador corre con `solo_no_negativos`,
    de modo que solo puede nombrar subexpresiones que sean >= 0 sobre N por
    estructura o que esten en `NO_NEGATIVOS_DEMOSTRADOS` con su demostracion
    escrita. Sin esa restriccion Z3 tambien alcanza 20 nombres, pero a veces
    eligiendo el modulo de Davis `2a(n+1)-(n+1)^2-1`, que NO se ha demostrado
    no negativo: la cifra seria la misma y la garantia, menor. Y el optimo NO es
    unico, asi que sin fijar el criterio la cifra publicada dependeria de que
    modelo devolviera Z3 ese dia. Resulta que la restriccion sale gratis: sigue
    saliendo 20. Ver [6] para las tres medidas y la demostracion.
    """
    print(f"\n{Colors.HEADER}[4] Aplanado optimo sobre el sistema de JSWW{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    S, best = pipeline_publicado()
    if best is None:
        stats.fail("el optimizador no alcanzo su cota en ninguna tanda")
        return
    dem = no_negativos_desplazados(COTA_A)
    loc = {str(x): x for x in S.params + S.unknowns}
    M, E = best["materializado"], best["sistema"]
    usadas = sum(1 for u in S.unknowns if u in M.unknowns)
    print(f"  partida: sistema (1) con a = A+{COTA_A} (cota demostrada, ver [8])")
    print(f"  optimizador: {best['nombres']} nombres (cota inferior {best['cota']}), "
          f"forzando definiciones: {best['forzado']}")
    print(f"  materializado: {M.cost()} incognitas ({usadas} originales + "
          f"{M.cost()-usadas} nombres), grado maximo {max_equation_degree(M)}")
    quitadas = sorted(str(u) for u, _ in best["eliminadas"])
    print(f"  + post-eliminacion de {quitadas}: {E.cost()} incognitas, "
          f"grado {max_equation_degree(E)}")
    print(f"  {Colors.BOLD}GENERADOR: ({best['variables']} variables, grado "
          f"{best['grado']}){Colors.ENDC}     JSWW 1976: (42, 5)")

    sin_probar = [c for c in best["elegidos"]
                  if not no_negativo_sobre_N(sympy.sympify(c, locals=loc))
                  and c not in dem]
    negativas = [str(u) for u, v in best["eliminadas"]
                 if not no_negativo_sobre_N(sympy.expand(v))]
    if max_equation_degree(M) > 2:
        stats.fail(f"el sistema materializado tiene grado {max_equation_degree(M)}, no 2")
    elif sin_probar:
        stats.fail(f"se nombro sin demostrar que sea >= 0 sobre N: {sin_probar}")
    elif negativas:
        stats.fail(f"se elimino una incognita cuya definicion puede ser negativa: {negativas}")
    elif best["grado"] != 5:
        stats.fail(f"generador de grado {best['grado']}, se esperaba 5")
    elif best["variables"] > MEJOR_GRADO_5:
        stats.fail(f"({best['variables']}, 5) empeora la mejor cifra construida "
                   f"({MEJOR_GRADO_5}, 5): esto es una REGRESION")
    else:
        print(f"  {Colors.WARN}Distancia al (42,5) anunciado: "
              f"{best['variables'] - 42:+d} variables — POR ENCIMA, no por debajo.")
        print(f"  El umbral de este test NO es 42. Se llego a anunciar (33,5), y")
        print(f"  era falso: venia de la ruta de reescritura, cuyos certificados no")
        print(f"  son materializables (ver el noveno defecto en el informe). Lo que")
        print(f"  se protege aqui es que la mejor cifra CONSTRUIBLE no empeore.")
        print(f"  Y NO esta demostrado que no se pueda mejorar. La cota del")
        print(f"  optimizador es de su CODIFICACION, no del problema, y ademas su")
        print(f"  objetivo minimiza NOMBRES con las incognitas originales congeladas,")
        print(f"  asi que no ve ninguna de las eliminaciones que acaba de hacer.")
        print(f"  Y hay un tercer motivo, que costo cuatro cifras: la cota certifica")
        print(f"  CONJUNTOS DE NOMBRES, no construcciones. La codificacion con")
        print(f"  reescritura certificaba 15 nombres y esos 15 NO se pueden")
        print(f"  materializar -- sin la autorreferencia sus cuerpos no reducen a")
        print(f"  grado 2. Un numero mas bajo del optimizador no es una cifra mejor")
        print(f"  mientras no exista el sistema. Esta cifra es la mejor CONSTRUIDA.{Colors.ENDC}")
        stats.ok()


def test_equivalencia_por_sustitucion(stats):
    """[5] El sistema materializado ES el de JSWW: sustitución hacia atrás.

    POR QUÉ HACE FALTA ESTE TEST Y NO BASTA EL DEL CATALOGO. La materialización
    se verifica en el catalogo comprobando que el testigo se extiende y anula el
    sistema. Con JSWW eso NO se puede hacer: no tenemos testigo, y encontrarlo es
    el reto famoso del paper (los valores son astronomicos). Sin esta comprobacion,
    la equisatisfacibilidad de nuestro (46,5) con el original quedaba SIN VERIFICAR.

    Lo que se hace en su lugar es simbolico y mas fuerte que cualquier muestreo:
    cada incognita nueva `w` viene con su ecuacion definitoria `w = d`. Sustituyendo
    en cascada hacia atras, las ecuaciones no definitorias deben devolver
    EXACTAMENTE las 14 originales -- ninguna de menos, ninguna de mas. Si eso se
    cumple, el sistema aplanado es el mismo objeto matematico escrito de otra forma.
    """
    print(f"\n{Colors.HEADER}[5] Equivalencia simbólica con el sistema original{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    import sympy
    # EL MISMO OBJETO QUE PUBLICA [4], no una reconstruccion. Cuando cada test
    # llamaba al optimizador por su cuenta, el optimo --que no es unico-- salia
    # distinto en cada uno: [4] publicaba una cifra y [5] verificaba OTRO sistema.
    S, best = pipeline_publicado()
    if best is None:
        stats.fail("el optimizador no alcanzo su cota en ninguna tanda")
        return
    M0, M = best["materializado"], best["sistema"]

    # El sistema desplazado tiene que SER el (1) de JSWW con a = A+COTA_A. Si no,
    # todo lo demas verifica un objeto que no es el de la literatura.
    A = sympy.Symbol('A', integer=True)
    a = INCOGNITAS[0]
    if any(sympy.expand(sd - so.subs(a, A + COTA_A)) != 0
           for sd, so in zip(S.eqs, ECUACIONES)):
        stats.fail("sistema_desplazado no coincide con ECUACIONES sustituyendo a")
        return
    print(f"  el sistema de partida ES el (1) de JSWW con a = A+{COTA_A} "
          f"(y a >= {COTA_A} esta demostrado, ver [8])")

    # HASTA PUNTO FIJO: una definicion puede mencionar una incognita eliminada
    # DESPUES (`e = 2n+p+q+z` con `q` eliminada luego), y una sola pasada de
    # `subs` dejaria `q` viva en el sistema recuperado.
    quitadas = {u: v for u, v in best["eliminadas"]}
    for _ in range(len(quitadas)):
        quitadas = {u: sympy.expand(v.subs(quitadas)) for u, v in quitadas.items()}

    # LAS DEFINICIONES SE PIDEN, NO SE ADIVINAN. Re-derivarlas leyendo las
    # ecuaciones funciona solo mientras cada definitoria mencione un unico nombre,
    # y deja de funcionar con la reescritura activa (`m5 = m4^2 + 2*e*m4`).
    # Y con la MISMA sustitucion aplicada: una definicion guardada ANTES de
    # eliminar esta obsoleta, y comparar dos fotos tomadas en momentos distintos
    # ya dio un fallo falso.
    defs = {w: sympy.expand(c.subs(quitadas)) for w, c in M0.definiciones}

    def desnombrar(e):
        prev = None
        while prev != e:
            prev = e
            e = sympy.expand(e.subs(defs))
        return e

    desnombradas = [desnombrar(e) for e in M.eqs]
    definitorias = [x for x in desnombradas if x == 0]
    vivas = [x for x in desnombradas if x != 0]
    # LAS ORIGINALES TAMBIEN SE DESNOMBRAN. `quitadas` puede mapear una incognita
    # a un NOMBRE --`z -> m1` cuando se ha forzado nombrar la definicion de `z`--,
    # y entonces el lado "original" lleva un nombre que el lado recuperado ya no
    # tiene: la comparacion se hace entre dos representaciones distintas y falla
    # sin que el sistema tenga nada malo. Es la TERCERA vez que un comprobador de
    # este proyecto da un fallo falso por comparar dos fotos tomadas en momentos
    # distintos; conviene que quede escrito.
    originales = [desnombrar(sympy.expand(x.subs(quitadas))) for x in S.eqs]
    consumidas = [i for i, o in enumerate(originales) if o == 0]
    originales = [o for o in originales if o != 0]

    def casa(u, v):
        return sympy.expand(u - v) == 0 or sympy.expand(u + v) == 0

    # EMPAREJAMIENTO 1 A 1, no "existe alguna que case": dos ecuaciones vivas
    # iguales taparian que falta una original distinta.
    pendientes, faltan = list(vivas), []
    for o in originales:
        for i, vv in enumerate(pendientes):
            if casa(o, vv):
                pendientes.pop(i); break
        else:
            faltan.append(o)
    print(f"  {len(defs)} nombres, {len(definitorias)} ecuaciones se anulan al "
          f"desnombrar, {len(vivas)} quedan vivas (originales: {len(originales)})")
    print(f"  eliminadas por sustitucion: {sorted(str(k) for k in quitadas)} "
          f"-> consumen las originales {consumidas} (se vuelven 0 == 0)")
    print(f"  originales no recuperadas: {len(faltan)}   "
          f"recuperadas que no son originales: {len(pendientes)}")
    if faltan or pendientes:
        stats.fail(f"la sustitucion hacia atras no devuelve el sistema original "
                   f"({len(faltan)} faltan, {len(pendientes)} sobran)")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} el sistema aplanado es el de JSWW "
              f"escrito de otra forma")
        stats.ok()


def test_no_negatividad_de_los_nombres(stats):
    """[6] EL REQUISITO QUE FALTABA: cada nombre nuevo tambien vive en N.

    QUE SE NOS ESCAPO. El generador `Q = (k+2)(1 - sum P_i^2)` representa el
    conjunto **sobre variables no negativas** -- asi lo enuncian JSWW. Cada
    subexpresion que el optimizador decide nombrar anade una incognita que
    tambien vive en N. Por tanto, para que un primo se siga emitiendo, hace falta
    que en la solucion original de JSWW **cada nombre valga >= 0**.

    Nombrar algo que puede ser negativo NO rompe la soundness (toda solucion del
    aplanado sigue siendo solucion del original, verificado en [5]) pero puede
    romper la COMPLETITUD: el primo deja de emitirse. Y esa direccion no se
    comprobaba, porque el sistema de JSWW se transcribe sin testigo --sus valores
    son astronomicos-- y `witness_is_nonnegative` no llega a ejecutarse.

    QUE SALE AL COMPROBARLO. De los 20 nombres del optimo, **18 son >= 0 por
    estructura** (productos y potencias pares de variables de N). Quedan dos:

      * `a + u^2(u^2 - a)`  -- DEMOSTRABLE, y se demuestra aqui. La ecuacion (7)
        da `u^2 = 16r^2y^4(a^2-1) + 1`. Si `u^2 = 1`, la expresion vale 1. Si
        `u^2 >= 2`, entonces `16r^2y^4(a^2-1) >= 1` obliga a `a >= 2` y `r,y >= 1`,
        luego `u^2 >= 16(a^2-1)+1 = 16a^2-15 > a`, y la expresion es `> 0`.
        Asi que vale **>= 1 siempre**. Se comprueba ademas por barrido.

      * `2a(n+1) - (n+1)^2 - 1` -- NO se demuestra aqui. Es el **modulo de la
        congruencia de Davis** de la ecuacion (12), y en la solucion que JSWW
        construyen es positivo porque un modulo lo es. Pero eso descansa en SU
        construccion, no en nada que este test verifique.

    POR ESO SE DAN DOS CIFRAS, y la segunda es la que no debe nadie nada:

        (46, 5)  optimo, pero su completitud depende de que ese modulo sea >= 0
                 en la solucion de JSWW;
        (47, 5)  optimo restringido a nombres demostrablemente >= 0. Una variable
                 mas, cero suposiciones.

    Ambas siguen siendo de grado 5, que es lo que se estaba midiendo.
    """
    print(f"\n{Colors.HEADER}[6] Los nombres nuevos tambien viven en N{Colors.ENDC}")
    from src.analysis.dioph_optflat import (aplanado_minimo_compuesto, materializar,
                                            no_negativo_sobre_N)
    from src.analysis.dioph_degree import to_generator

    S = sistema(expandir=False)
    # LAS TRES CONFIGURACIONES DE ESTE TEST VAN SIN REESCRITURA, y a proposito.
    # Lo que compara es un invariante entre ellas --restringir el espacio no puede
    # dar un optimo menor-- asi que tienen que ser homogeneas. Con reescritura
    # activa, `materializar` no converge para el conjunto libre (>20 min), de modo
    # que la comparacion no se podria completar. La cifra PUBLICADA sale del
    # pipeline con reescritura y se mide en [4]; aqui se vigila la coherencia del
    # criterio de no-negatividad, que es otra cosa.
    libre = aplanado_minimo_compuesto(S, 2, timeout_s=600)
    if libre.get("elegidos") is None:
        print("  (el optimizador no concluyo: omitido)"); return

    gens = {str(g): g for g in S.params + S.unknowns}
    dudosos = [c for c in libre["elegidos"]
               if not no_negativo_sobre_N(sympy.sympify(c, locals=gens))]
    print(f"  de {len(libre['elegidos'])} nombres del optimo, "
          f"{len(libre['elegidos']) - len(dudosos)} son >= 0 POR ESTRUCTURA")
    for d in dudosos:
        print(f"    {Colors.WARN}exige demostracion: {d}{Colors.ENDC}")

    # La demostracion de `a + u^2(u^2-a) >= 1`, comprobada por barrido sobre la
    # ecuacion (7), que es la unica que hace falta.
    casos = fallos = 0
    for av in range(0, 45):
        for rv in range(0, 30):
            for yv in range(0, 30):
                t = 16 * rv * rv * yv ** 4 * (av * av - 1) + 1
                if t < 0:
                    continue
                raiz, exacto = sympy.integer_nthroot(t, 2)
                if not exacto:
                    continue
                casos += 1
                if av + t * (t - av) < 1:
                    fallos += 1
    print(f"  {Colors.OKGREEN if not fallos else Colors.FAIL}a+u^2(u^2-a) >= 1 "
          f"en las {casos} ternas (a,r,y) que satisfacen la ec.(7); "
          f"{fallos} fallos{Colors.ENDC}")

    # LAS TRES MEDIDAS. La tercera es la que vale, y es la que usa [4].
    medidas = {}
    for etiqueta, kw in (("estructural",            dict(solo_no_negativos=True)),
                         ("estructural+demostrado", dict(solo_no_negativos=True,
                                                         demostrados=NO_NEGATIVOS_DEMOSTRADOS))):
        rr = aplanado_minimo_compuesto(S, 2, timeout_s=600, **kw)
        if rr.get("elegidos") is None:
            stats.fail(f"el aplanado '{etiqueta}' no concluyo: {rr['estado']}")
            return
        _, gg = to_generator(materializar(S, rr["elegidos"], 2), FACTOR)
        medidas[etiqueta] = (rr, gg)

    _, g_libre = to_generator(materializar(S, libre["elegidos"], 2), FACTOR)
    r_est, g_est = medidas["estructural"]
    r_dem, g_dem = medidas["estructural+demostrado"]
    print(f"  {Colors.BOLD}({g_libre['variables']}, {g_libre['grado']}){Colors.ENDC} "
          f"sin restringir           -- el optimo NO es unico y algunos nombres no "
          f"estan demostrados")
    print(f"  {Colors.BOLD}({g_est['variables']}, {g_est['grado']}){Colors.ENDC} "
          f"solo >= 0 por estructura -- cero suposiciones, una variable de mas")
    print(f"  {Colors.BOLD}({g_dem['variables']}, {g_dem['grado']}){Colors.ENDC} "
          f"estructura + la demostrada -- {Colors.OKGREEN}sale gratis{Colors.ENDC}")
    print(f"  {Colors.WARN}Estas tres van SIN reescritura, para ser homogeneas entre "
          f"si. La cifra PUBLICADA la mide [4].{Colors.ENDC}")

    problemas = []
    if fallos:
        problemas.append("la demostracion de a+u^2(u^2-a) >= 1 tiene contraejemplos")
    for et, (rr, gg) in medidas.items():
        if rr["estado"] != "optimo_del_encoding":
            problemas.append(f"'{et}' no es un optimo demostrado: {rr['estado']}")
        if gg["grado"] != 5:
            problemas.append(f"'{et}' da grado {gg['grado']}, no 5")
        if gg["variables"] < g_libre["variables"]:
            problemas.append(f"'{et}' restringe el espacio y da un optimo MENOR: "
                             "imposible, el encoding esta mal")
    # Lo que de verdad se afirma: admitir la UNICA expresion demostrada recupera
    # la cifra sin restringir. Si dejara de ser cierto, la cifra publicada tendria
    # que subir a la estructural, y eso hay que enterarse.
    if g_dem["variables"] != g_libre["variables"]:
        problemas.append(f"la cifra demostrada ({g_dem['variables']}) ya no iguala "
                         f"a la libre ({g_libre['variables']}): hay que publicar "
                         f"{g_est['variables']}, no {g_libre['variables']}")
    if problemas:
        for pr in problemas[:3]:
            print(f"  {Colors.FAIL}{pr}{Colors.ENDC}")
        stats.fail(problemas[0])
    else:
        stats.ok()


def test_esquina_de_variables(stats):
    """[7] LA OTRA ESQUINA: quitar variables pagando grado.

    Es el dual exacto del aplanado. Aplanar baja el grado introduciendo nombres;
    ELIMINAR quita incognitas a costa de subirlo. El sistema (1) de JSWW tiene
    incognitas que estan LINEALMENTE determinadas por una ecuacion, y cuatro de
    ellas con miembro derecho de coeficientes TODOS positivos --luego >= 0 sobre N
    automaticamente, y la equisatisfacibilidad vale en las dos direcciones sin
    ninguna suposicion--:

        e = 2n + p + q + z          (alpha_2)
        q = h + j + w*z             (alpha_0)
        y = l + n + v               (alpha_8)
        z = (gk+2g+k+1)(h+j) + h    (alpha_1)

    Dos puntos que salen de ahi, y los dos mejoran cifras de la literatura:

      * eliminando e, q, y  -> 22 incognitas, grado 12 => GENERADOR (23, 25).
        JSWW PUBLICAN (26, 25): mismo grado, TRES variables menos.
      * eliminando ademas z -> 21 incognitas, grado 18 => GENERADOR (22, 37).
        Matiyasevich 1971 anuncia (24, 37): mismo grado, DOS menos.

    Lo llamativo es lo barato que es: son sustituciones lineales, no hay
    optimizacion ni SMT. Que nadie las escribiera encaja con el patron ya
    documentado --estas cifras se anunciaban, no se exhibian--, pero conviene no
    deducir de ahi mas de lo que hay: es una operacion elemental.

    NO mejora el (19, 29) que JSWW tambien anuncian: por esa via se llega a
    (24, 29), cinco por encima. Esa sigue siendo la cifra a batir en esta esquina.
    """
    print(f"{Colors.HEADER}[7] La otra esquina: quitar variables pagando grado{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)")
    S = sistema(expandir=False)
    esperado = {("e", "q", "y"): (23, 25), ("e", "q", "y", "z"): (22, 37)}
    problemas = []
    for combo, (v_esp, g_esp) in sorted(esperado.items(), key=lambda kv: len(kv[0])):
        E = eliminar_lineales(S, 99, solo=list(combo))
        hechas = sorted(str(a) for a, _ in getattr(E, "eliminadas", []))
        gd = max_equation_degree(E)
        variables, grado = E.cost() + 1, 1 + 2 * gd
        ok = (variables, grado) == (v_esp, g_esp) and hechas == sorted(combo)
        marca = Colors.OKGREEN + "OK" + Colors.ENDC if ok else Colors.FAIL + "MAL" + Colors.ENDC
        print(f"  {marca} eliminar {'+'.join(sorted(combo)):<9} -> {E.cost()} incognitas, "
              f"grado {gd} => GENERADOR ({variables}, {grado})")
        if not ok:
            problemas.append(f"{combo}: esperado ({v_esp},{g_esp}), medido ({variables},{grado})")
    print(f"  {Colors.BOLD}(23, 25){Colors.ENDC} frente al (26, 25) PUBLICADO por JSWW: "
          f"3 variables menos al mismo grado")
    print(f"  {Colors.BOLD}(22, 37){Colors.ENDC} frente al (24, 37) que anuncia Matiyasevich 1971: "
          f"2 menos")
    print(f"  {Colors.WARN}No mejora el (19, 29) que JSWW tambien anuncian: por esta via se")
    print(f"  llega a (24, 29). Esa sigue siendo la cifra a batir en esta esquina.{Colors.ENDC}")
    if problemas:
        stats.fail(problemas[0])
    else:
        stats.ok()


def test_cota_a_mayor_igual_2(stats):
    """[8] DEMOSTRACION, no muestreo: el sistema de JSWW implica n >= 2 y a >= 2.

    POR QUE HACE FALTA. `eliminar_lineales` solo quita una incognita si el miembro
    derecho tiene todos los coeficientes >= 0, porque sobre N hay que poder
    reconstruir un valor no negativo. La ecuacion (11) define `l = k+1+i(a-1)`,
    con un `-i`, y por eso quedaba bloqueada. La forma limpia de usar una cota NO
    es relajar el criterio --que es lo unico que impide aceptar sistemas falsos--
    sino REPARAMETRIZAR: con `a >= 2` demostrado, `a = A+2` es un cambio de
    variable biyectivo y `l = k+1+i(A+1)` pasa el criterio sin tocarlo.

    LO QUE SE COMPRUEBA AQUI son los CERTIFICADOS de la demostracion, no casos
    sueltos. Cada paso es un encaje estricto entre dos cuadrados consecutivos, y
    que la diferencia sea > 0 para todo K >= 1 se certifica sustituyendo K = KK+1
    y viendo que el polinomio resultante tiene todos los coeficientes >= 0 y no es
    identicamente nulo. Eso es una demostracion completa, no una comprobacion en
    un rango.
    """
    print(f"\n{Colors.HEADER}[8] Cota demostrada: n >= 2 y a >= 2{Colors.ENDC}")
    K = sympy.Symbol('K', positive=True, integer=True)
    KK = sympy.Symbol('KK', nonnegative=True, integer=True)
    fallos = []

    def positivo_para_K_ge_1(expr, var, sustituto):
        """Certifica expr > 0 para var >= 1 via coeficientes no negativos."""
        pol = sympy.Poly(sympy.expand(expr.subs(var, sustituto + 1)), sustituto)
        cs = pol.all_coeffs()
        return all(c >= 0 for c in cs) and any(c > 0 for c in cs)

    # Paso 1: la ec.(4) no tiene solucion con n = 0 ni con n = 1.
    for N, lo, hi in [(1, 4*K**2 + 2*K - 1, 4*K**2 + 2*K),
                      (2, 8*K**2 + 4*K - 1, 8*K**2 + 4*K)]:
        F2 = sympy.expand(16 * K**3 * (K + 1) * N**2 + 1)
        ok_lo = positivo_para_K_ge_1(F2 - lo**2, K, KK)
        ok_hi = positivo_para_K_ge_1(hi**2 - F2, K, KK)
        print(f"  n = {N-1}: ({lo})^2 < f^2 < ({hi})^2 para todo K>=1 -> "
              f"{ok_lo and ok_hi}")
        if not (ok_lo and ok_hi):
            fallos.append(f"el encaje de la ec.(4) falla para n={N-1}")
    print(f"  => n = 0 y n = 1 imposibles, luego {Colors.BOLD}n >= {COTA_N}{Colors.ENDC}")

    # Paso 2: a = 0 da x^2 + y^2 = 1, luego y <= 1, y la ec.(9) fuerza n <= 1.
    e6 = sympy.expand(ECUACIONES[5].subs(INCOGNITAS[0], 0))   # ec.(6) con a=0
    if sympy.expand(e6 + sympy.Symbol('x', integer=True)**2
                    + sympy.Symbol('y', integer=True)**2 - 1) != 0:
        fallos.append("la ec.(6) con a=0 no es x^2+y^2=1")
    print(f"  a = 0: ec.(6) queda {e6} = 0  =>  y <= 1, y la ec.(9) da n <= 1: "
          f"contradice n >= {COTA_N}")

    # Paso 3: a = 1 obliga a e = 0 (otro encaje), y la ec.(3) da n = 0.
    ee = sympy.Symbol('ee', positive=True, integer=True)
    EE = sympy.Symbol('EE', nonnegative=True, integer=True)
    O2 = sympy.expand(4 * ee**4 + 8 * ee**3 + 1)
    ok = (positivo_para_K_ge_1(O2 - (2*ee**2 + 2*ee - 1)**2, ee, EE) and
          positivo_para_K_ge_1((2*ee**2 + 2*ee)**2 - O2, ee, EE))
    print(f"  a = 1: ec.(5) queda o^2 = 4e^4+8e^3+1, sin cuadrado para e>=1 -> {ok}")
    if not ok:
        fallos.append("el encaje de la ec.(5) con a=1 falla")
    print(f"  => e = 0, y la ec.(3) (2n+p+q+z = e) da n = 0: contradice n >= {COTA_N}")
    print(f"  {Colors.BOLD}CONCLUSION: a >= {COTA_A} en toda solucion sobre N{Colors.ENDC}")

    # La reparametrizacion desbloquea exactamente UNA eliminacion mas: `l`.
    base = sorted(str(t) for t, _ in
                  getattr(eliminar_lineales(sistema(expandir=False), 99), "eliminadas", []))
    desp = sorted(str(t) for t, _ in
                  getattr(eliminar_lineales(sistema_desplazado(COTA_A), 99), "eliminadas", []))
    print(f"  eliminables sin desplazar: {base}")
    print(f"  eliminables con a = A+{COTA_A}: {desp}")
    if set(desp) - set(base) != {'l'}:
        fallos.append(f"se esperaba desbloquear solo 'l', se desbloqueo {set(desp)-set(base)}")

    # Y la guarda: no se puede pedir un desplazamiento sin demostracion.
    try:
        sistema_desplazado(COTA_A + 1)
        fallos.append("sistema_desplazado acepto un desplazamiento no demostrado")
    except ValueError:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} `sistema_desplazado({COTA_A+1})` "
              f"se rechaza: no hay demostracion de a >= {COTA_A+1}")

    print(f"  {Colors.WARN}LO QUE ESTO NO DA: las otras tres eliminaciones (l, m, p, x")
    print(f"  en las ec. 12-14) necesitan a >= n+1, a >= p+1 y a >= p, que son")
    print(f"  relaciones ENTRE incognitas y no se arreglan desplazando. Siguen")
    print(f"  abiertas.{Colors.ENDC}")
    if fallos:
        stats.fail(fallos[0])
    else:
        stats.ok()


def test_frontera_de_pareto(stats):
    """[9] La FRONTERA COMPLETA (variables, grado), no dos esquinas sueltas.

    Hay dos palancas y son opuestas: aplanar a grado `d` da un generador de grado
    `1+2d` y cuanto mas alto `d` menos nombres hacen falta; eliminar una incognita
    lineal quita una variable y sube el grado. Juntas barren una CURVA.

    Y la zona intermedia de esa curva esta VACIA en la literatura: entre el (42,5)
    de JSWW y su (26,25) no hay ningun par publicado. Los puntos de en medio son
    mecanicos --nadie los reclamo porque nadie los escribio-- pero exhibirlos
    cuesta lo mismo que exhibir uno solo, y sin ellos se estaba publicando menos
    de lo que se tiene.

    Se exige: la frontera esta ordenada (grado creciente, variables decrecientes)
    y ningun punto es dominado por una cifra de la literatura.
    """
    print(f"\n{Colors.HEADER}[9] Frontera de Pareto (variables, grado){Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    S = sistema(expandir=False)
    # SOBRE EL SISTEMA SIN DESPLAZAR, y hay que decirlo porque la frontera que
    # PUBLICA el informe es la del sistema desplazado y es mejor en su tramo alto
    # --gana los puntos (24,21), (22,29) y (21,37), que la version sin desplazar no
    # alcanza--. Aqui se mide la version rapida porque cada solve del sistema
    # desplazado cuesta ~4 min y la suite no terminaria. Lo que este test protege
    # es la MAQUINARIA: que cada punto publicado equivalga al original y que
    # ninguno este dominado por la literatura. La cifra concreta de portada la
    # miden [4] y [5], y esos si van sobre el sistema desplazado.
    #
    # `k_optimos=1` mantiene la suite ejecutable: cada grado ya corre DOS tandas
    # (libre y forzando definiciones). Subirlo solo puede mejorar los puntos, nunca
    # empeorarlos, asi que la frontera que sale es una cota superior -- que es justo
    # lo que se afirma de ella.
    frontera = barrido_pareto(S, grados=(2, 3, 4, 5, 6), k_optimos=1,
                              demostrados=NO_NEGATIVOS_DEMOSTRADOS)
    #: pares PUBLICADOS o anunciados, para comprobar dominancia.
    literatura = [(26, 25), (42, 5), (19, 29), (12, 13697), (10, 6001)]
    fallos = []
    prev_v, prev_g = None, None
    for v, g, receta, ver in frontera:
        dominado = [(lv, lg) for lv, lg in literatura if lv <= v and lg <= g
                    and (lv, lg) != (v, g)]
        marca = (Colors.FAIL + f"dominado por {dominado}" + Colors.ENDC if dominado
                 else Colors.OKGREEN + "no dominado" + Colors.ENDC)
        sello = (Colors.OKGREEN + "equivalente" + Colors.ENDC if ver["ok"]
                 else Colors.FAIL + f"NO VERIFICADO ({ver['faltan']}/{ver['sobran']})" + Colors.ENDC)
        print(f"  ({v:3d} variables, grado {g:3d})  {marca:<40s} {sello:<32s} {receta}")
        # CADA PUNTO PUBLICADO CON SU VEREDICTO. Antes solo se verificaba el de
        # grado 5, y los demas figuraban en la misma tabla con una garantia menor
        # sin que la tabla lo dijera: materializados y con el grado medido, pero
        # sin comprobar que fueran el mismo objeto que el sistema (1).
        if not ver["ok"]:
            fallos.append(f"({v},{g}) no equivale al original: "
                          f"faltan {ver['faltan']}, sobran {ver['sobran']}")
        if prev_v is not None and not (v < prev_v and g > prev_g):
            fallos.append(f"la frontera no esta ordenada en ({v},{g})")
        prev_v, prev_g = v, g
    # El punto de grado 5 es la cifra de portada y no puede empeorar.
    g5 = [v for v, g, _, _ in frontera if g == 5]
    if not g5 or g5[0] > MEJOR_GRADO_5:
        fallos.append(f"el punto de grado 5 salio {g5}, se esperaba "
                      f"<= {MEJOR_GRADO_5} (la mejor cifra construible)")
    else:
        print(f"  {Colors.BOLD}grado 5: {g5[0]} variables{Colors.ENDC}   "
              f"JSWW 1976 anuncio 42 — seguimos {g5[0]-42:+d} por encima")
    if fallos:
        stats.fail(fallos[0])
    else:
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== JSWW 1976: PATRON DE MEDIDA EXTERNO ==={Colors.ENDC}")
    stats = Stats()
    test_transcripcion(stats)
    test_marcador_de_aplanado(stats)
    test_grado_menor_que_5(stats)
    test_aplanado_optimo(stats)
    test_equivalencia_por_sustitucion(stats)
    test_no_negatividad_de_los_nombres(stats)
    test_esquina_de_variables(stats)
    test_cota_a_mayor_igual_2(stats)
    test_frontera_de_pareto(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — medido contra la "
              f"literatura, con la brecha declarada.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
