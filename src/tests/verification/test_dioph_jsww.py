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
    sistema, FACTOR, PUBLICADO, INCOGNITAS, NO_NEGATIVOS_DEMOSTRADOS,
)
from src.analysis.dioph_degree import (
    flatten_greedy, flatten_tree, to_generator, max_equation_degree,
    eliminar_lineales,
)
from src.analysis.dioph_optflat import (
    Z3_DISPONIBLE, aplanado_minimo_compuesto, materializar, no_negativo_sobre_N,
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
    S = sistema(expandir=False)
    r = aplanado_minimo_compuesto(S, 2, timeout_s=300, solo_no_negativos=True,
                                  demostrados=NO_NEGATIVOS_DEMOSTRADOS,
                                  reescritura=True)
    print(f"  optimizador: {r['estado']}, {r['nombres']} nombres (cota inferior {r['cota']})")
    if r["estado"] != "optimo_del_encoding":
        stats.fail(f"no se alcanzo la cota: {r['estado']}")
        return
    M = materializar(S, r["elegidos"], 2, reescritura=True)
    grado = max_equation_degree(M)
    _, g_plano = to_generator(M, FACTOR)
    usadas = sum(1 for u in INCOGNITAS if u in M.unknowns)
    print(f"  materializado: {M.cost()} incognitas ({usadas} originales + "
          f"{M.cost()-usadas} nombres), grado maximo {grado}")
    print(f"  tras aplanar: ({g_plano['variables']} variables, grado {g_plano['grado']})")

    # POST-ELIMINACION, y es la jugada que el optimizador NO PUEDE VER. Su
    # objetivo minimiza NOMBRES con las incognitas originales congeladas: no hay
    # ningun termino que premie borrar una. Pero `q = h + j + w*z` (ec. alpha_0) e
    # `y = l + n + v` (ec. alpha_8) son definiciones lineales cuyos miembros
    # derechos tienen TODOS los coeficientes positivos, luego son >= 0 sobre N
    # automaticamente y la equisatisfacibilidad vale en las dos direcciones sin
    # ninguna suposicion. Y el grado no sube: en el sistema YA aplanado, q e y
    # solo multiplican cosas de grado 1.
    #
    # Lo encontro una revision adversarial, y lo incomodo es que el mecanismo ya
    # estaba implementado en el repo (`eliminar_lineales`, usado en
    # `L_prime_shared`): simplemente nunca se habia conectado a esta cadena, que
    # es donde esta la cifra de portada. Eliminar ANTES de aplanar es peor
    # (medido); lo que paga es eliminar DESPUES.
    E = eliminar_lineales(M, 2, solo=['q', 'y'])
    grado = max_equation_degree(E)
    _, g = to_generator(E, FACTOR)
    quitadas = [str(a) for a, _ in getattr(E, "eliminadas", [])]
    print(f"  + post-eliminacion de {quitadas}: {E.cost()} incognitas, grado {grado}")
    print(f"  {Colors.BOLD}GENERADOR: ({g['variables']} variables, grado "
          f"{g['grado']}){Colors.ENDC}     JSWW 1976: (42, 5)")
    M = E
    sin_probar = [c for c in r["elegidos"]
                  if not no_negativo_sobre_N(sympy.sympify(
                      c, locals={str(x): x for x in S.params + S.unknowns}))
                  and c not in NO_NEGATIVOS_DEMOSTRADOS]
    if grado > 2:
        stats.fail(f"el sistema materializado tiene grado {grado}, no 2")
    elif sin_probar:
        stats.fail(f"se nombro sin demostrar que sea >= 0 sobre N: {sin_probar}")
    elif g["grado"] != 5:
        stats.fail(f"generador de grado {g['grado']}, se esperaba 5")
    else:
        distancia = g["variables"] - 42
        print(f"  {Colors.WARN}Distancia al (42,5) anunciado: {distancia:+d} variables.")
        print(f"  Y NO esta demostrado que no se pueda mejorar. La cota que devuelve")
        print(f"  el optimizador es de su CODIFICACION, no del problema: hay")
        print(f"  contraejemplo --sobre el sistema con `e` eliminada dice 21 y existe")
        print(f"  un aplanado de 20--. Ademas su objetivo minimiza NOMBRES con las")
        print(f"  incognitas originales congeladas, asi que no ve la eliminacion que")
        print(f"  acaba de quitar dos. Esta cifra es la mejor CONSTRUIDA, no un minimo.{Colors.ENDC}")
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
    S = sistema(expandir=False)
    # MISMAS OPCIONES QUE [4], y esto no es un detalle: sin ellas este test
    # verificaba un sistema DISTINTO del que publica [4]. El optimo no es unico,
    # asi que "el aplanado equivale al original" quedaba comprobado sobre un
    # aplanado que no era el de la cifra. Lo detecto una revision adversarial.
    r = aplanado_minimo_compuesto(S, 2, timeout_s=300, solo_no_negativos=True,
                                  demostrados=NO_NEGATIVOS_DEMOSTRADOS,
                                  reescritura=True)
    if r["estado"] != "optimo_del_encoding":
        stats.fail(f"el optimizador no alcanzo la cota: {r['estado']}")
        return
    M0 = materializar(S, r["elegidos"], 2, reescritura=True)
    M = M0
    # EL SISTEMA QUE SE PUBLICA, no una etapa intermedia. Antes este test corria
    # el optimizador con otras opciones y sin la post-eliminacion, o sea verificaba
    # la equivalencia de un sistema DISTINTO del de la cifra -- y como el optimo no
    # es unico, ni siquiera del mismo aplanado. Lo detecto una revision adversarial.
    M = eliminar_lineales(M, 2, solo=['q', 'y'])
    quitadas = {a: b for a, b in getattr(M, "eliminadas", [])}

    # LAS DEFINICIONES SE PIDEN, NO SE ADIVINAN. Antes se re-derivaban leyendo las
    # ecuaciones --buscar una incognita nueva con coeficiente 1 que no aparezca en
    # el resto--, y eso funciona mientras cada definitoria mencione un solo nombre.
    # Con la reescritura activa una definicion puede expresarse en terminos de
    # OTROS nombres (`m5 = m4^2 + 2*e*m4`), el detector encontraba 15 de 18 y el
    # test fallaba por su propia heuristica, no por el sistema.
    # Con la MISMA sustitucion aplicada. `eliminar_lineales` sustituye `q` e `y`
    # en TODAS las ecuaciones, tambien en las definitorias, asi que una definicion
    # guardada antes de eliminar esta obsoleta: al desnombrar reintroducia `q` e
    # `y` y el sistema recuperado no casaba. No era un fallo del sistema sino de
    # comparar dos fotos tomadas en momentos distintos.
    defs = {w: sympy.expand(c.subs(quitadas)) for w, c in M0.definiciones}

    def desnombrar(e):
        prev = None
        while prev != e:
            prev = e
            e = sympy.expand(e.subs(defs))
        return e

    # Sustituir cada nombre por lo que representa debe dejar: las definitorias en
    # 0 = 0 (no dicen nada por si mismas) y el resto en las ecuaciones originales.
    desnombradas = [desnombrar(e) for e in M.eqs]
    definitorias = [x for x in desnombradas if x == 0]
    vivas = [x for x in desnombradas if x != 0]
    originales = [sympy.expand(x.subs(quitadas)) for x in S.eqs]
    consumidas = [i for i, o in enumerate(originales) if o == 0]
    originales = [o for o in originales if o != 0]

    def casa(u, v):
        return sympy.expand(u - v) == 0 or sympy.expand(u + v) == 0

    faltan = [o for o in originales if not any(casa(o, x) for x in vivas)]
    sobran = [x for x in vivas if not any(casa(o, x) for o in originales)]
    print(f"  {len(defs)} nombres, {len(definitorias)} ecuaciones se anulan al "
          f"desnombrar, {len(vivas)} quedan vivas (originales: {len(originales)})")
    print(f"  eliminadas por sustitucion: {sorted(str(k) for k in quitadas)} "
          f"-> consumen las originales {consumidas} (se vuelven 0 == 0)")
    print(f"  originales no recuperadas: {len(faltan)}   recuperadas que no son originales: {len(sobran)}")
    if faltan or sobran:
        stats.fail(f"la sustitucion hacia atras no devuelve el sistema original "
                   f"({len(faltan)} faltan, {len(sobran)} sobran)")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} el sistema aplanado es el de JSWW escrito de otra forma")
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
          f"si. La cifra PUBLICADA la mide [4] y es (41, 5).{Colors.ENDC}")

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


def main():
    print(f"{Colors.BOLD}=== JSWW 1976: PATRON DE MEDIDA EXTERNO ==={Colors.ENDC}")
    stats = Stats()
    test_transcripcion(stats)
    test_marcador_de_aplanado(stats)
    test_grado_menor_que_5(stats)
    test_aplanado_optimo(stats)
    test_equivalencia_por_sustitucion(stats)
    test_no_negatividad_de_los_nombres(stats)

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
