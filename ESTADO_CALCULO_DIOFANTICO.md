# Estado del Cálculo Diofántico — documento de reanudación

> **Propósito:** que cualquiera (incluido tu yo futuro) pueda retomar este trabajo sin releer
> la conversación. Contiene qué existe, qué está verificado, con qué números, qué se aprendió
> y cuál es el siguiente paso.
> Última actualización: agosto 2026.

> **⛔ AVISO: las cifras de grado 5 de este documento fueron RETIRADAS.** Ver **§2.bis**. El
> noveno defecto —la ruta de reescritura certificaba conjuntos de nombres que **no se pueden
> materializar**— invalidó `(41,5)`, `(38,5)`, `(36,5)` y `(33,5)`. La frontera se **remidió entera**
> sin reescritura y con una comprobación **estructural** nueva; lo que sigue son los números de esa
> remedida.
>
> **Marcador actual (todo verificado: identidad polinómica + estructura + sin incógnitas perdidas, y
> **reproducible** — dos barridos sucesivos dan lo mismo):**
>
> * **(23, 25)** — tres variables menos que el (26, 25) que JSWW **sí imprimieron**, al mismo grado.
>   **Es el único punto que mejora una cifra de la literatura**, no usa aplanado —son tres
>   sustituciones lineales— y está **formalizado en Lean 4** (§2.ter);
> * **(21, 25)** — **cinco** por debajo del (26,25) publicado, y también **formalizado en Lean 4**
>   (§2.ter). Los tres hechos de Pell que sostenían la cota `a ≥ e+1` **ya no se citan: se
>   demuestran** en `Pell.lean`, sin Mathlib;
> * **(38, 7)**, **(32, 9)**, **(30, 11)**, **(27, 13)** — caen en una zona **vacía** en la
>   literatura, pero **ninguno domina** al (26, 25): el (27,13) baja doce grados a costa de una
>   variable de más;
> * esquina de grado 5: **(44, 5)** — **por encima** del (42, 5) que JSWW *anunciaron*, o sea que
>   **ahí no los batimos**;
> * **`a ≥ 2`** demostrado y **formalizado en Lean 4**, verificado por el núcleo (§ formalización).
>
> Ninguna de estas cifras es un mínimo demostrado: todas son **cotas superiores construidas**.
>
> Las secciones que siguen conservan su redacción original salvo aviso; **las cifras de grado 5
> anteriores al (44,5) están retiradas** aunque el texto histórico las mencione.

---

## 1. Objetivo y encuadre correcto

Construir maquinaria **universal** (no específica de los primos) para representaciones
diofánticas, midiendo su coste en la **frontera de Pareto (incógnitas, grado)**.

**El encuadre que costó descubrir y que evita perder el tiempo:**

1. **MRDP garantiza que la traducción existe.** Exhibir una ecuación para un conjunto decidible
   no es un descubrimiento: su existencia es teorema desde 1970. Lo que vale es el **certificado**
   y el **coste medido**.
2. **El récord no es un número, es una frontera de Pareto.** Los pares universales de Jones (1982)
   van de **(58 incógnitas, grado 4)** a **(9 incógnitas, grado 1,638×10⁴⁵)**. Bajar incógnitas
   cuesta grado y viceversa. *"Llegar a 9" no es llegar a un sitio mejor, es a otra esquina.*
3. **El teorema de Matiyasevich no es sobre primos**: dice que TODO conjunto diofántico admite
   9 incógnitas. Los primos son una instancia. Por eso la maquinaria debe ser universal.
4. **El dominio (ℕ, ℤ, ℤ[i]) es parámetro de primera clase.** Traducir de ℕ a ℤ al final
   multiplica por 3 (9→27). Sun logró 11 sobre ℤ rehaciendo la prueba nativamente.

---

## 2. Qué existe hoy (módulos y responsabilidad)

| Módulo | Responsabilidad | Estado |
|---|---|---|
| `src/analysis/dioph_calculus.py` | Núcleo: `Dioph` (params, incógnitas, ecuaciones, testigo), `conj`/`disj`, `cost()`, `degree()`, `four_squares`. **100% universal** | ✅ |
| `src/analysis/dioph_lemmas.py` | Biblioteca de lemas certificados con coste declarado + `PellContext` (compartición) | ✅ |
| `src/analysis/dioph_pell.py` | Arsenal de Pell P1–P5 + crecimiento de Julia Robinson + frontera de Pareto documentada | ✅ |
| `src/analysis/dioph_degree.py` | **Aplanado de monomios**: baja el grado a costa de incógnitas. Universal | ✅ |
| `src/analysis/dioph_problems.py` | `DiophProblem` (conjunto + representación + oráculo) y **un único verificador** | ✅ |
| `src/analysis/dioph_soundness.py` | **Soundness por SMT**: traduce cualquier `Dioph` a Z3 y demuestra `unsat`. Universal. Es lo que encontró el defecto del generador | ✅ |

Tests correspondientes en `src/tests/verification/test_dioph_*.py`, todos registrados en
`run_verification_suite.py`.

---

## 2.bis ⛔ RETRACTACIÓN: se retiran TODAS las cifras de grado 5 desde el (41, 5) — noveno defecto

**Se retiran (33, 5), (36, 5), (38, 5) y (41, 5).** La última cifra válida de la esquina de grado 5
es **(44, 5)**, que está *por encima* del (42, 5) que JSWW anunciaron: **ya no lo batimos**.

> Esta sección se escribió primero diciendo que el defecto era de la palanca de «forzar
> definiciones» y que el (38, 5) sobrevivía. **Era falso, y en la misma sesión.** Al medir el alcance
> —en vez de suponerlo— resultó que el culpable es la **ruta de reescritura**, que es anterior y
> mucho más profunda. Queda escrito así, con la corrección visible, porque una retractación mal
> acotada es otra afirmación sin verificar.

### Qué falló

La tercera palanca —**forzar el nombre de una definición** para que la eliminación saliera gratis—
producía sistemas **estrictamente más débiles que el original**.

El mecanismo, exacto: `materializar` emite la ecuación definitoria de cada nombre `w` como
`w − reducir(cuerpo, permitir_nombre=False)`. Ese flag existe justamente para que la definitoria de
`w` no se exprese usando `w`. **Las rutas de reescritura y de subsuma no consultaban ese flag** —se
añadieron después—, así que `reducir` podía devolver el propio `w`, y la ecuación emitida era
`w − w`, que expande a **cero**.

```
la ecuacion definitoria de m1 colapsa a 0 = 0: su cuerpo se redujo a si mismo (m1 = m1)
```

**El alcance, medido en vez de supuesto:**

| configuración | cifra | veredicto |
|---|---|---|
| reescritura + subsumas + forzar | (33, 5), (36, 5) | ⛔ definitorias colapsadas; desaparecen `g` y `r` |
| reescritura + subsumas | (38, 5) | ⛔ `m2 = m2` |
| reescritura sin subsumas | (41, 5) | ⛔ `m2 = m2` |
| **sin reescritura** | **(44, 5)** | ✅ **válida** |

O sea: **el culpable es la reescritura**, y arruina todas las cifras de grado 5 desde que se
introdujo. Con `forzar` además desaparecían incógnitas originales, que es cómo se detectó, pero el
daño ya estaba antes.

Un sistema al que le falta la ecuación (2) tiene soluciones que el (1) de JSWW no tiene. Como
generador, **emitiría números que no son primos**. Es un fallo de *soundness*, el peor de los dos
tipos.

### Por qué la verificación no lo cazó, que es lo más instructivo

`verificar_equivalencia` daba **0 faltan / 0 sobran** sobre un sistema roto. No es un bug suyo, es un
límite que no estaba escrito: **es una identidad polinómica**. Sustituye cada nombre por su
definición y comprueba que reaparecen las originales — pero **sustituye por una definición que el
sistema ya no impone**. Comprobaba que las ecuaciones *dicen* lo mismo si uno acepta las
definiciones, no que el sistema *obligue* a las definiciones.

Dos comprobaciones que parecían independientes —«grado ≤ 2» y «0 faltan / 0 sobran»— fallaban a la
vez, y las dos daban verde.

### Cómo se detectó: intentando formalizar

No lo encontró ningún test. Lo encontró **el generador de Lean**: al escribir la firma del teorema
necesitaba la lista de variables del sistema, y `g` no estaba. Una variable que existe en el sistema
de partida y no en el aplanado es un imposible, y este proyecto ya sabe qué hacer con un imposible.

Es el noveno defecto y el primero que delata una **herramienta distinta**. Los ocho anteriores los
cazó el propio instrumento dando un número que no podía ser cierto; este lo cazó cambiar de
formalismo, que es exactamente el argumento por el que se formaliza.

### La reparación, y lo que apareció debajo

El arreglo obvio —«que las rutas de reescritura y de subsuma consulten el flag»— **no era el
arreglo**. `permitir_nombre` era un **booleano que solo protegía la llamada de primer nivel**: en
cuanto la reducción recurría —sobre los sumandos, sobre los factores, sobre el resto de una
reescritura— el flag se perdía y la rama directa volvía a poder nombrar la propia expresión que se
estaba definiendo. Se sustituyó por una **clave prohibida** (`srepr` de la expresión que se define)
que **viaja por toda la recursión**.

Y entonces apareció lo importante, que es peor que el defecto:

> Sin la autorreferencia, esos cuerpos **no tienen ninguna reducción a grado 2** y la búsqueda no
> termina. La autorreferencia era lo que hacía **terminar** la recursión.

Es decir: **los certificados de 15 y 17 nombres de la ruta de reescritura no son materializables**.
El optimizador prometía conjuntos de nombres que no se pueden construir. Las cifras no vuelven al
arreglar el defecto — no estaban ahí.

Se añadió un **tope de profundidad** para que la reducción falle *limpio* (devuelve `None`) en vez de
agotar la pila, y el pipeline **se repliega solo** a `reescritura=False`:

```
[libre  /reesc]     descartado: no se pudo reducir a grado 2: 16*(k+1)^3*(k+2)*(n+1)^2 + 1
[forzado/reesc]     descartado: no se pudo reducir a grado 2: h + (h+j)*(g*k+2*g+k+1)
[libre  /sin-reesc] 20 nombres, post-elim ['q','y'] -> (44, 5)   ok=True, 0 faltan / 0 sobran
```

Más nombres, pero **construible**, que es la única clase de cifra que este proyecto publica.

### La comprobación que faltaba: `verificar_estructura`

El límite de `verificar_equivalencia` está ahora **escrito en el código y cubierto por un test**, no
solo en este registro. La identidad polinómica sigue haciendo falta, pero no basta: hace la
sustitución **ella**, con el diccionario de definiciones, y por eso es ciega a que el sistema no la
imponga. La comprobación que sí lo ve es **estructural**, y son cuatro condiciones independientes:

| condición | qué rotura caza |
|---|---|
| cada nombre `w` tiene **en el sistema** una ecuación igual a `±(w − r)`, emparejada **1 a 1** | la definitoria perdida o colapsada |
| `w` **no aparece** en su propio cuerpo `r` | el noveno defecto exacto: `w − w` expande a 0 |
| el grafo de dependencias entre nombres es **acíclico** | `w₁ = f(w₂)`, `w₂ = g(w₁)`: las dos ecuaciones existen, ninguna es autorreferente, y aun así no determinan nada |
| desplegando `r` hasta punto fijo reaparece la definición **declarada** | `w` bien determinado, pero por **otra cosa** que la que dice representar — y entonces la identidad polinómica habla de un sistema distinto del que se publica |

Las cuatro juntas dan una **biyección** entre conjuntos de soluciones: cada nombre queda determinado
por las originales en orden topológico. Ninguna sobra — la tercera no la habría cazado ninguna de las
otras dos. `verificar_equivalencia` ya no puede dar `ok` sin ellas, y el test `[6]` de
`test_dioph_optflat` construye las **cuatro** roturas por separado y exige que se señale la causa
correcta.

> **Y la comprobación nueva falló primero, como todas.** Su primera pasada dio «NO» sobre (44,5),
> (38,7), (32,9) y (30,11) — cuatro puntos que no tenían nada malo. Comparaba `w − definición
> declarada` contra las ecuaciones, cuando lo que el sistema emite es `w − cuerpo reducido`, y el
> cuerpo reducido menciona **otros nombres**. Son dos listas distintas y se estaba mirando la que no
> era. Queda escrito porque el reflejo correcto ante un «NO» inesperado es el mismo que ante un
> número imposible: sospechar del instrumento **y medir**, no publicar la retractación. El test
> comprueba ahora las dos direcciones — que las cuatro roturas se cacen y que el caso normal de la
> reescritura, cuerpo emitido en términos de otro nombre, **se acepte**.

> La lección, dicha sin adornos: **las cifras que cayeron son exactamente las que usaban más
> maquinaria; la que sobrevive —(23, 25)— se podría haber hecho a mano en una tarde.** Cada capa
> añadió una manera nueva de estar equivocado, y la verificación que se presentaba como fuerte era
> ciega a esa clase de error.

### Y una décima rotura, del mismo palo: la cifra no era reproducible

Al remedir la frontera apareció esto, que no es un defecto de código sino de **método**:

```
rep 1:  [libre/reesc] optimo #1: 2 nombres, post-elim ['q','y','z']  ->  (25, 13)
rep 2:  [libre/reesc] descartado: no se pudo reducir a grado 6: (a + u^2*(-a+u^2))^2 - 1
        [libre/sin-reesc] optimo #1: 4 nombres                       ->  (27, 13)
```

**Dos llamadas idénticas, en el mismo proceso, una detrás de otra.** La causa es que el optimizador
corre con un `timeout` de **pared**: bajo carga distinta Z3 devuelve modelos distintos del mismo
tamaño, y los conjuntos que *solo* la reescritura sabe certificar son justamente los que a veces no
se pueden construir. Uno se materializó y el otro no.

Esto ya tenía nombre en este documento —«una cifra que depende de qué modelo devuelva Z3 esa vez no
es un resultado», §3.2m, escrito cuando dos tests publicaron (36,5) y (38,5)— y aun así se volvió a
publicar una tabla con un punto así dentro. La regla no basta con enunciarla: hay que **ejecutarla**.

Dos cambios, los dos en el código:

* **`reescritura=False` por defecto** en `barrido_pareto` y en `aplanado_y_eliminacion`, con la
  medida escrita en el docstring. Quien la quiera, la pide;
* **el barrido se publica solo si dos repeticiones consecutivas coinciden**. Sin reescritura
  coinciden exactamente, en los dos sistemas.

> Y hay que decir lo incómodo: la tabla anterior de este mismo documento —la que anunciaba que el
> (25,13) dominaba al (26,25) en los dos ejes— se escribió con el barrido en su **modo por defecto**,
> que intentaba la reescritura primero. O sea que la frase «todos sin reescritura» que la acompañaba
> era **falsa**, y lo era por no haber mirado el valor por defecto de un parámetro. Duró tres
> commits.

### Qué sobrevive

| resultado | estado |
|---|---|
| **(23, 25)** — solo eliminaciones, sin aplanar | ✅ **válido**, y es lo que queda en pie: tres variables menos que el (26, 25) **publicado**, al mismo grado |
| (22, 37) y demás puntos sin aplanar | ✅ válidos (dominados por el (19, 29) anunciado) |
| `a ≥ 2` formalizado en Lean | ✅ intacto: habla del sistema (1), no del aplanado |
| **(44, 5)** — aplanado sin reescritura | ✅ válido, pero **peor** que el (42, 5) anunciado |
| (41, 5), (38, 5), (36, 5), (33, 5) | ⛔ **retirados** |
| los puntos intermedios de la frontera | ✅ **remedidos** sin reescritura y revalidados: (38,7), (32,9), (30,11), (27,13). Vuelven, pero **todos peores** que los anunciados — el (27,9) pasa a (32,9), el (26,11) a (30,11) y el (25,13) a (27,13) — y **ninguno domina ya** al (26,25) publicado |

**Consecuencia que hay que decir sin rodeos: en la esquina de grado 5 ya no batimos a JSWW.** La
mejor cifra válida es (44, 5) y ellos anunciaron (42, 5).

Lo que sí sigue en pie —y es más de lo que parecía el día de la retractación, porque entonces los
puntos intermedios estaban retirados *a la espera de remedirlos*— es **el tramo medio de la
frontera**, que se remidió entero sin reescritura y pasó las cuatro comprobaciones:

* **(23, 25)** mejora en tres variables el **(26, 25) publicado**, al mismo grado, y ni siquiera usa
  aplanado: son eliminaciones lineales;
* el tramo (38,7)–(27,13) llena una zona vacía de la literatura, pero **ninguno de esos puntos
  domina** al (26,25): bajan grado a costa de variables.

### La guarda, para que no se repita

Dos comprobaciones nuevas, las dos en `materializar`, que **abortan** en vez de avisar:

1. ninguna ecuación definitoria puede colapsar a `0 = 0`;
2. ninguna incógnita original puede desaparecer del sistema materializado.

Y `verificar_equivalencia` incorpora la segunda a su veredicto: `ok` es ahora falso si hay incógnitas
perdidas. `aplanado_y_eliminacion` descarta el candidato en vez de publicarlo.

## 2.ter ✅ FORMALIZADO: el (23, 25) y el (21, 25), los dos verificados por el núcleo de Lean

Dos resultados. El segundo empezó siendo **condicional** —dependía de tres teoremas de Pell que se
citaban— y dejó de serlo al demostrarlos. Se conserva el relato de las dos fases porque el orden
importa: **primero se midió qué compraba la cota, y sólo después se pagó el precio de demostrarla.**

### El (23, 25), verificado en Lean 4 de punta a punta

`formalizacion/lean/Eliminacion.lean` demuestra:

```
theorem equisatisfacible (k : Int) (hk : 0 ≤ k) :
    (∃ a b … q … y … z : Int, (0 ≤ a ∧ … ∧ 0 ≤ z) ∧ completo  k a … z)
  ↔ (∃ a b …           … x : Int, (0 ≤ a ∧ … ∧ 0 ≤ x) ∧ reducido k a … x)
```

25 incógnitas a la izquierda, **22** a la derecha, mismo `k`. Con el parámetro, el generador pasa de
**(26, 25)** —lo que JSWW imprimieron— a **(23, 25)**. Sin `sorry`, sin Mathlib, y los axiomas son
`propext` y `Quot.sound` (ni siquiera `Classical.choice`).

**Por qué este resultado sí se puede formalizar y el de grado 5 no:** no hay aplanado, ni optimizador,
ni reescritura. Son **tres sustituciones lineales**. Las ecuaciones (1), (2) y (9) determinan `q`, `z`
e `y`, y sus definiciones tienen todos los coeficientes no negativos — que es exactamente lo que hace
válida la vuelta sobre ℕ. Ese criterio, que en Python es «mira los signos de los coeficientes», aquí
**pasa a ser tres lemas demostrados** (`defZ_nonneg`, `defQ_nonneg`, `defY_nonneg`).

Va sobre **ℤ con `0 ≤ ·` explícito**, no sobre ℕ: las ecuaciones de JSWW tienen restas (`a²−1`,
`a−n−1`, `u²−a`) que `Nat` truncaría, y así quedan **literalmente** como están publicadas.

Y el enunciado se comprueba, que es donde estaba el riesgo real. `test_lean_eliminacion.py` empareja
**1 a 1** las 14 ecuaciones de `completo` con `ECUACIONES` y las 11 de `reducido` con lo que devuelve
`eliminar_lineales`, y verifica que los cuantificadores son 25 y 22 con diferencia exacta `{q,y,z}` —
sin esa cuarta comprobación el teorema podría estar cuantificando de menos y ser cierto por vacío.

### El (21, 25): la cota `a ≥ e+1`, y de dónde sale

Las tres eliminaciones que quedaban bloqueadas necesitaban `a ≥ n+1`, `a ≥ p+1` y `a ≥ p` — cotas
*entre incógnitas*, que no se arreglan desplazando y sobre las que Z3 no concluye. Resulta que la
primera **es cierta, y con un margen enorme**. El argumento:

1. La ec.(3) da `e = 2n+p+q+z ≥ 2n`, luego `n ≤ e/2`; y con `n ≥ 2` (ya demostrado), `e ≥ 4`.
2. La ec.(5) es `o² = e³(e+2)(a+1)² + 1`, y **la clave es factorizar**:
   `e³(e+2) = e²·((e+1)² − 1)`.
3. Poniendo `Z = e(a+1)` queda la **Pell clásica** `o² − ((e+1)²−1)Z² = 1`, con solución fundamental
   `(e+1, 1)`.
4. Sus soluciones son `Z_j` con `Z_{j+1} = 2(e+1)Z_j − Z_{j−1}`, y **`Z_j ≡ j (mod e)`**. Como
   `Z = e(a+1)` es múltiplo de `e`, hace falta `e | j`, luego **`j ≥ e`**.
5. `Z_j` crece exponencialmente, así que `a + 1 = Z_j/e ≥ (2e+1)^{e−1}/e`, que para `e ≥ 4` es
   astronómicamente mayor que `e/2 + 2 ≥ n + 2`.

**Comprobado numéricamente** (test [10]): el mínimo `a+1` que admite la ec.(5), por fuerza bruta, es

| e | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| mín `a+1` | 3 | 21 | 245 | 4061 | 87815 |

y coincide **exactamente** con el `Z_e/e` que predice el argumento. La congruencia `Z_j ≡ j (mod e)`
se verifica término a término.

Con `n = N+2` y `a = n+1+A`, la ec.(12) permite eliminar `m` — la **sexta** incógnita eliminable — y
la esquina entera baja una variable: (23,25) → **(22,25)**, (22,29) → (21,29), (21,37) → (20,37).

#### Pero la cota buena es `a ≥ e+1`, y sale de la misma demostración

El paso 5 no ajusta: se pasa **por órdenes de magnitud**. `Z_e/e` vale 245, 4061, 87815, 2350153…
frente a un `e+2` que vale 6, 7, 8, 9. Así que el mismo argumento da

```
a ≥ e + 1        (para e ≥ 4, que está garantizado porque n ≥ 2 y e ≥ 2n)
```

Y **eso es lo que cambia el resultado**, porque `e = 2n + p + q + z` domina a la vez a `n` y a `p`:

```
a − n − 1  =  e + A − n  =  n + p + q + z + A     ≥ 0
a − p − 1  =  e + A − p  =  2n + q + z + A        ≥ 0
a − p      =                2n + q + z + A + 1    ≥ 0
```

**Una sola sustitución afín vuelve estructurales las tres restas bloqueadas**, mientras que
`a = n+1+A` solo arreglaba la primera. Medido: **siete** incógnitas eliminables en vez de seis — entra
también `x`, por la ecuación (13).

| | sin cota Pell | con `a ≥ n+1` | con **`a ≥ e+1`** |
|---|---|---|---|
| grado 25 | (23, 25) | (22, 25) | **(21, 25)** |
| grado 37 | (22, 37) | (20, 37) | (20, 37) |
| grado 61 | — | — | (19, 61) |

**(21, 25): cinco variables por debajo del (26, 25) que JSWW publicaron, al mismo grado.** Y no queda
dominado por el (19, 29) que anuncian, porque su grado es menor.

Verificado: las cinco definiciones eliminadas (`q`, `e`, `y`, `m`, `x`) tienen **todos los
coeficientes ≥ 0** —luego la equisatisfacibilidad vale en las dos direcciones sobre ℕ— y la
sustitución hacia atrás recupera las 9 ecuaciones originales vivas, **0 faltan y 0 sobran**.

### La frontera completa, que es la UNION de dos sistemas

Con la reescritura desactivada. **Todos los puntos de esta tabla se midieron por duplicado y las
dos repeticiones coinciden.** (Los puntos aplanados del sistema con Pell se midieron una sola vez;
no hace falta más porque salen todos dominados y ninguno llega a la tabla.)

| variables | grado | receta | sistema |
|---:|---:|---|---|
| 44 | 5 | aplanar a 2 + eliminar `q,y` | sin Pell |
| 38 | 7 | aplanar a 3 + eliminar `q,y` | sin Pell |
| 32 | 9 | aplanar a 4 + eliminar `q,y,z` | sin Pell |
| 30 | 11 | aplanar a 5 + eliminar `q,y,z` | sin Pell |
| 27 | 13 | aplanar a 6 + eliminar `q,y,z` | sin Pell |
| **21** | **25** | sin aplanar + eliminar `e,m,q,x,y` | **con Pell** |
| 20 | 37 | sin aplanar + eliminar `e,l,m,q,x,y` | **con Pell** |
| 19 | 61 | sin aplanar + eliminar `e,l,m,q,x,y,z` | **con Pell** |

Con la cota de Pell, el (23,25) pasa a **(21,25)** y el (22,37) a (20,37): los puntos sin Pell de esa
zona quedan **dominados** y salen de la tabla.

#### Por qué la tabla mezcla dos sistemas: la cota de Pell NO es gratis

Medido grado a grado sobre los dos sistemas, la reparametrización `a = e+1+A` **empeora la esquina de
aplanado en todos los grados** y sólo gana en la de eliminación:

| grado del generador | sin Pell | con Pell |
|---:|---:|---:|
| 5 | **44** | 49 |
| 7 | **38** | 43 |
| 9 | **32** | 37 |
| 11 | **30** | 35 |
| 13 | **27** | 31 |
| 25 | 23 | **21** |
| 37 | 22 | **20** |
| 61 | — | **19** |

La razón es mecánica: `a` pasa a ser un polinomio de cinco variables (`e = 2n+p+q+z`) y aparece hasta
a la cuarta potencia en la ecuación (8), así que aplanar exige **más nombres** — 25 en vez de 20 para
llegar a grado 2. En cambio cada eliminación desbloqueada quita una variable entera.

Por eso la frontera publicada es la **unión**, con cada punto etiquetado, y por eso **el (23,25) y el
(22,37) salen de la tabla**: quedan dominados por sus versiones con Pell.

> **Y aquí estuve a punto de publicar una afirmación falsa.** La primera medición de esta tabla dio
> que sobre el sistema con Pell **no había ningún punto aplanado en ningún grado**, y casi escribo que
> la reparametrización destruye esa esquina. Al diagnosticarlo, el optimizador no estaba agotando el
> tiempo: devolvía **`unsat`**. La causa era mía — pasé la lista de no-negatividades demostradas
> **vacía**, y sin poder nombrar `a + u²(u²−a)` la ecuación (8) no baja de grado, así que el problema
> es *genuinamente* insatisfacible.
>
> Es **exactamente la trampa que este documento ya tenía escrita** para el desplazamiento `a = A+2`
> (§3.2o): el optimizador reconoce una expresión demostrada comparando su `str()`, y tras
> reparametrizar las cadenas dejan de casar. Que haya vuelto a picar significa que el comentario no
> bastaba, así que ahora **cada sistema declara sus no-negatividades en el propio objeto** y el
> optimizador las toma de ahí si quien llama no pasa ninguna. Olvidarlas ya no es posible.
>
> Con la lista puesta, los cinco grados se resuelven en **73–182 segundos cada uno**. La diferencia
> entre «imposible» y «tres minutos» era un parámetro.

### El hueco, y cómo se cerró

Los pasos 4 y 5 son **teoremas estándar de Pell** —la maquinaria con la que Matiyasevich cerró MRDP, y
están en Mathlib justamente por eso—. Durante un rato **aquí se citaban**, y eso dejaba al (21,25) en
una clase de garantía distinta de la del (23,25): el resultado más fuerte del proyecto era también el
peor garantizado. Estaban los dos en tablas separadas, con su etiqueta.

**Ya no.** `formalizacion/lean/Pell.lean` (397 líneas, sin Mathlib, sin `sorry`) demuestra los tres:

| hecho | enunciado | para qué |
|---|---|---|
| **completitud** | toda solución de `x²−(A²−1)y²=1` con `x,y ≥ 0` es `(X j, Y j)` | permite **indexar** una solución cualquiera; sin él los otros dos no sirven |
| **congruencia** | `Y j ≡ j (mod A−1)` | convierte «`e` divide al **valor**» en «`e` divide al **índice**», y de ahí `j ≥ e` |
| **crecimiento** | `Y` estrictamente creciente, `Y 3 = 4A²−1` | de `j ≥ 4` a la cota cuadrática que hace falta |

Y culmina en

```
theorem a_ge_e_succ_de_sistema :
  0 ≤ k → … → 2*n + p + q + z = e                                  -- ec.(3)
            → 16*(k+1)*(k+1)*(k+1)*(k+2)*((n+1)*(n+1)) + 1 = f*f   -- ec.(4)
            → e*e*e*(e+2)*((a+1)*(a+1)) + 1 = o*o                   -- ec.(5)
            → e + 1 ≤ a
```

Hipótesis: **tres** de las catorce ecuaciones, más las no negatividades. Nada más.

**Por qué era abordable sin Mathlib**, que es la parte no obvia: la teoría general de Pell es grande,
pero aquí `D = A²−1` está *un cuadrado por debajo* de `A²`, y eso hace que el paso y su inverso sean
fórmulas cerradas —`(x,y) ↦ (Ax+Dy, x+Ay)` y `(x,y) ↦ (Ax−Dy, Ay−x)`— que son inversas por `A²−D=1`.
Las tres desigualdades del descenso (`x' ≥ 0`, `y' ≥ 0`, `y' < y`) salen todas de **comparar
cuadrados**, que es exactamente la técnica de encaje que ya se usaba en `CotaA.lean`. Y la inducción
va sobre una **cota** de `y`, no sobre `y`, para no necesitar recursión bien fundada.

### Y el (21,25) entero, no sólo la cota

`Eliminacion21.lean` cierra el último tramo: **25 incógnitas ⟶ 20**, con la misma forma de teorema
que el (23,25).

```
theorem equisatisfacible21 (k : Int) (hk : 0 ≤ k) :
    (∃ 25 incógnitas, no-negativas ∧ completo   k …) ↔
    (∃ 20 incógnitas, no-negativas ∧ reducido21 k …)
```

La **ida** usa las dos cotas de Pell para producir `N = n−2 ≥ 0` y `A = a−e−1 ≥ 0`; la **vuelta** usa
que las cinco definiciones eliminadas son `≥ 0`, y ahí es donde las cotas son imprescindibles: sin
ellas `m` y `x` podrían salir negativas y no habría solución sobre ℕ que exhibir. El teorema sería
falso, no sólo indemostrable.

El enunciado se comprueba aparte (`test_lean_eliminacion21.py`, 4/4), y es el que más superficie de
error tenía de todo el proyecto: catorce ecuaciones a mano, más nueve, más siete definiciones, más una
reparametrización que **renombra** dos incógnitas. Se verifica que las siete definiciones son las que
produce `eliminar_lineales`, que las nueve ecuaciones casan **1 a 1** con el sistema eliminado —suman
109.512 caracteres al expandir, por eso en el `.lean` van con las definiciones dentro— y que los
cuantificadores son 25 y 20 con la diferencia exacta «se van `{a,e,m,n,q,x,y}`, entran `{N,A}`».

### Lo que queda citado, que ya es sólo una cosa

Que el sistema (1) represente los primos. Eso es el teorema de JSWW (1976) y no se demuestra aquí.
Todo lo demás —las cotas, las eliminaciones, la equisatisfacibilidad— está verificado por el núcleo de
Lean 4, sin Mathlib, con axiomas `propext`, `Classical.choice` y `Quot.sound`.

## 2.quater El (42,5) de JSWW: cinco ataques al 20, el método cotejado, y una cita nuestra retirada

`44 = 26 + 20 − 2`: los 26 de JSWW, más 20 nombres para aplanar a grado 2, menos 2 eliminaciones.
Ellos anuncian 42, o sea **16 nombres**. La brecha está entera en el aplanado. Esto es lo que se
probó, con lo que salió.

### 1. Más eliminaciones: el tope de 2 es ESTRUCTURAL, no un fallo de búsqueda

El diagnóstico de qué bloquea a cada incógnita en el sistema aplanado:

| incógnita | estado |
|---|---|
| `e`, `q`, `y`, `z` | tienen una ecuación que las determina con miembro derecho **≥ 0** |
| `l`, `n`, `v`, `p`, `h`, `j`, `m`, `x` | bloqueadas por **coeficientes negativos** |
| `a`,`b`,`c`,`d`,`f`,`g`,`i`,`o`,`r`,`s`,`t`,`u`,`w` | no aparecen linealmente con coeficiente 1 |

De las cuatro disponibles, `z` sube el grado a 3 al sustituirla (aparece multiplicada por `w`), y
**`q` y `e` son mutuamente excluyentes**: las determina la *misma* ecuación (3), que se consume al
usarla. Medidos los seis órdenes de `{q,y,e}`, todos dan exactamente 2 eliminaciones. El tope no es
que el DFS busque mal: es que sólo hay dos ecuaciones donantes.

### 2. Nombrar las definiciones de grado 1: la palanca no existía, y forzarla era un no-op

La regla «si `u = R` y se nombra `R`, eliminar `u` cuesta grado cero» sugiere forzar el nombre de
`2n+p+q+z` (definición de `e`) y de `l+n+v` (la de `y`). Medido: forzarlas **no cambia el óptimo**,
que sigue en 20… porque **no llegan al sistema**. El catálogo filtra `grado(c) ≥ 2`, así que una
definición de grado 1 no es candidata, y `forzar` sobre algo que no está en el catálogo **no hace
nada, en silencio**.

> Es el **segundo no-op silencioso** encontrado en la misma sesión, después del de
> `productos_subsuma`. Los dos tienen la misma forma: una palanca que parece activada, no lo está, y
> la medición que la evalúa devuelve «no cambia nada» — que es indistinguible del resultado real.

Y aunque se construya el nombre a mano, la cuenta no mejora: cuesta +1 nombre y desbloquea +1
eliminación. Con `m = 2n+p+q+z` nombrado salen **tres** eliminaciones (`e`, `q`, `y`) y 21 nombres:
`25 + 21 − 3 + 1 = 44`. Exactamente lo mismo.

### 3. Ampliar el catálogo: de 465 a 3.469 candidatos, y el óptimo no se mueve

| `tope_suma` | candidatos | óptimo | cota |
|---:|---:|---:|---:|
| 6 | 465 | 20 | 20 |
| 8 | 946 | 20 | 20 |
| 10 | 3.469 | 20 | 20 |

También sin el filtro de no-negatividad, y sobre la forma agrupada de las ecuaciones: 20 en los
cuatro casos. **El catálogo ha dejado de ser el cuello de botella**, que es justo lo contrario de lo
que pasó las tres veces anteriores.

### 4. Prueba de caída sobre el materializador: los 20 nombres son indispensables

Quitando cada nombre y pidiendo al **materializador** —no a la codificación— que aplane el resto, los
20 fallan. Y el fallo es siempre localizado y legible:

```
sin `e**2`        -> no se pudo reducir a grado 2: e**3*(e + 2)
sin `u**2`        -> no se pudo reducir a grado 2: a + u**2*(-a + u**2)
sin `(k+1)**3*(k+2)` -> no se pudo reducir: 16*(k+1)**3*(k+2)*(n+1)**2 - f**2 + 1
```

Es la comprobación más fuerte de las cuatro porque **no usa la codificación**: el materializador es la
verdad de campo, el mismo que produce los sistemas que se publican.

### 5. Alinear las reglas: la codificación era MÁS ESTRICTA que el materializador

El quinto ataque va a las *particiones*, no al catálogo. Comparados los dos juegos de reglas regla a
regla, aparece una asimetría:

| regla | materializador | codificación |
|---|---|---|
| partir un producto en dos grupos | **sin tope** de factores | `len(fs) <= 6` |

Y el sistema tiene un producto de **siete** factores desplegados — `16·r²·y⁴·(a²−1)`, la ecuación (7).
Para ese nodo la codificación **no tenía la regla en absoluto**.

Eso importa aunque no mueva la cifra: **una cota inferior emitida por un juego de reglas más estricto
que el constructor no es una cota del problema**, y este proyecto ya ha visto dos veces lo que hace
una pareja desalineada. Se sube el tope a 8 (`TOPE_FACTORES`), que cubre el nodo de siete.

Medido: con tope 6, 7, 8 y 10 el óptimo sigue siendo **20 con cota 20**. El tope no era lo que ataba
la cifra — pero ahora la cota significa lo que dice.

### 6. El método de Skolem, cotejado — y una cita de este proyecto que era falsa

Se consiguió la fuente primaria del **método**: Davis, *Hilbert's tenth problem is unsolvable*, Amer.
Math. Monthly **80** (1973) 233–269, **p. 263**. Está escrito entero, y permite **exactamente** estas
sustituciones:

```
z_j = y_i·y_k      z_j = y_i²      z_j = x·y_i      z_j = x²
```

O sea: **los nombres son monomios de grado 2** sobre las variables, incluidas las ya introducidas
(«by successive substitutions»). Nada de subexpresiones compuestas — ni `(k+1)³(k+2)`, ni `c·u+x`, ni
`a+u²(u²−a)`, que son **cuatro de los veinte** nombres que usa este proyecto.

`aplanado_minimo` implementa ese método, y su formulación es **exacta**, no «del encoding»: los
candidatos son *todos* los divisores de los monomios del sistema —un nombre que no divida a ninguno
es inútil— y se enumeran *todas* las particiones de exponentes, con la condición de que un nombre de
grado > 2 se construya a su vez de dos partes disponibles, que es la sustitución sucesiva.

| | nombres | generador |
|---|---:|---|
| **Skolem/Davis sobre (1)**, mínimo exacto | **25** | **(51, 5)** |
| este proyecto (subexpresiones arbitrarias + 2 eliminaciones) | 20 | **(44, 5)** |
| lo que JSWW **anuncian** | 16 | (42, 5) |

Medido sobre las dos formas del sistema, la original y la agrupada del Teorema 2.12: **25 en ambas,
con cota 25**.

**Un (42, 5) por ese método exigiría 16 nombres, y el mínimo exacto es 25.** Nuestro (44, 5) bate a
ese procedimiento por **siete** variables. Lo que ya no puede afirmarse —hasta cotejar la página
correcta— es que JSWW lo atribuyan a ese método; ver el aviso de abajo.

#### ⛔ Y aquí este documento tenía una cita falsa

`dioph_jsww.py` presentaba, desde el principio y como **«textual (p. 450)»**, la frase de JSWW que
atribuye el (42,5) a la sustitución de Skolem sobre (1). **Cotejada la p. 450 del original, no está
ahí.** Lo que sí hay en esa página, y queda confirmado:

* la ecuación (4), la construcción de Putnam: `(k+2){1 − M(k,x₁,…,xₙ)}` — o sea que el `FACTOR = k+2`
  del módulo **es correcto**;
* el **Teorema 3**: los primos son el rango exacto de `2 + k·0^{M(k,x₁,…,xₙ)}` con **n ≤ 11**
  (representación *exponencial*, 12 variables contando `k`);
* el Teorema 4, sobre `pₙ`;
* las referencias [4], [7], [8]=Matijasevič, [12]=Putnam, [16]=J. Robinson.

La cita **puede seguir siendo auténtica** y estar en otra de las páginas 449–464: lo único
establecido es que la página que se citaba es la equivocada. Pero mientras no se coteje, queda **sin
verificar que el (42,5) sea «(1) pasado por Skolem»** — que es la premisa de toda la comparación de
este apartado.

**Qué sobrevive y qué no:**

| afirmación | estado |
|---|---|
| el método de Skolem sólo nombra monomios de grado 2 | ✅ **cotejado** (Davis 1973, p. 263) |
| ese método sobre (1) necesita **25** nombres como mínimo exacto ⇒ (51,5) | ✅ **medido**, no depende de ninguna cita |
| nuestro (44,5) bate a ese método por 7 variables | ✅ se sigue de lo anterior |
| JSWW **anuncian** (42,5) obtenido por ese método | ⛔ **sin cotejar** — la página citada no lo contiene |
| «el 42 anunciado no es alcanzable» | ⛔ **retirada**: la premisa sobre lo que anuncian está sin verificar |

> Es la enésima vez que en este proyecto una comprobación que se daba por hecha resulta no estarlo, y
> la primera que le toca a una **cita**, no a un cálculo. El patrón se repite intacto: lo que llevaba
> más tiempo escrito y menos veces mirado es lo que estaba mal. Se corrige igual que se corrigieron
> las cifras — dejándolo visible.

### Conclusión, y qué queda

El 20 se sostiene desde cinco ángulos independientes, y el (44,5) con él. La brecha con el 42 sigue **abierta**, pero
mejor acotada: no hace falta un instrumento incompleto para explicarla, y sí haría falta cotejar la
página donde JSWW dicen de dónde sale su cifra:

* el (42, 5) es una cifra **anunciada y nunca escrita**, igual que el (19,29) — y este proyecto ni
  siquiera tiene cotejada la página donde se anuncia;
* la codificación *podría* seguir siendo incompleta en sus particiones —hay precedente: sobre el
  sistema con `e` eliminada devuelve cota 21 y existe un aplanado de 20 hecho a mano— pero eso ya no
  hace falta para explicar la brecha.

**Marcador de esta esquina, con la fuente primaria cotejada: (44, 5) es la mejor cifra construida y
verificada, y supera en siete variables al procedimiento que la literatura cita para llegar ahí.**

## 3. INFORME INTEGRADO — qué se ha conseguido, cómo, y con qué garantía

> Esta sección es **autocontenida**: se puede leer sin el resto del documento. Las secciones 3.2x que
> vienen después son el registro cronológico —incluidos los errores y las cifras retiradas— y siguen
> siendo la fuente para los detalles. Esto es el informe.

### Qué es el problema, en una página

Un **generador** de un conjunto `S ⊆ ℕ` es un polinomio `Q` cuyos **valores positivos** sobre
variables no negativas son exactamente `S`. Para los primos existe desde 1976. Se construye siempre
igual: se parte de una **representación**

```
n ∈ S   ⟺   ∃x₁…x_v :  P₁ = ⋯ = P_m = 0
```

y se envuelve en un solo polinomio:

```
Q = W · (1 − Σᵢ Pᵢ²)        ⟹        deg Q = 1 + 2·máx deg Pᵢ
```

La igualdad del grado es exacta (la forma de cabeza de `ΣPᵢ²` es suma de cuadrados de polinomios
reales no nulos y no puede cancelarse). De ahí salen **dos ejes en tensión**:

* **aplanar** — nombrar subexpresiones para bajar `deg Pᵢ` — *añade* variables;
* **eliminar** — quitar una incógnita determinada linealmente — *sube* el grado.

Por eso **el récord no es un número: es una frontera de Pareto (variables, grado)**. Ese encuadre es
el que evita perder el tiempo, y es de §1.

### El marcador: qué había y qué hay

**Lo que había en la literatura**, cotejado contra fuente primaria (§3.2h-bis):

| Par | Fuente | Estado |
|---|---|---|
| **(26, 25)** | JSWW, *Amer. Math. Monthly* 83:6 (1976) 449–464, sistema (1) | **exhibido** |
| (42, 5) | JSWW 1976, p. 450 — **una frase** | anunciado, nunca escrito |
| (19, 29) | JSWW 1976, p. 450 — la misma frase | anunciado |
| (12, 13.697) | JSWW 1976 Teor. 2; grado exacto en Pąk–Kaliszyk (ITP 2022) | anunciado |
| (10, >6.000) | Matiyasevich, *J. Soviet Math.* 15 (1981) 33–44 | exhibido, formalizado en Mizar |

**Lo que hay ahora.** Todos los puntos parten del **sistema (1) publicado** de JSWW —no de una
construcción propia— y todos están construidos, materializados y con el grado medido sobre el
sistema real:

| variables | grado | receta | sistema | verificación |
|---:|---:|---|---|---|
| 44 | 5 | aplanar a 2 + eliminar `q,y` | ambos | ✅ |
| 38 | 7 | aplanar a 3 + eliminar `q,y` | ambos | ✅ |
| 32 | 9 | aplanar a 4 + eliminar `q,y,z` | ambos | ✅ |
| 30 | 11 | aplanar a 5 + eliminar `q,y,z` | ambos | ✅ |
| 27 | 13 | aplanar a 6 + eliminar `q,y,z` | sin desplazar | ✅ |
| **23** | **25** | sin aplanar + eliminar `q,y,z` | ambos | ✅ |
| 22 | 29 | sin aplanar + eliminar `l,q,y,z` | `a=A+2` | ✅ |
| 21 | 37 | sin aplanar + eliminar `e,l,q,y,z` | `a=A+2` | ✅ |

Sobre el sistema desplazado (`a = A+2`, §3.2o). El ✅ significa **tres** comprobaciones, no una: identidad polinómica (0 faltan / 0 sobran), verificación
**estructural** de que cada nombre está atado por una ecuación del sistema, y ninguna incógnita
original perdida.

### Los resultados, y por qué son de tipos distintos

> ⛔ **Sección reescrita tres veces, y las dos primeras estaban mal en direcciones opuestas.** La
> primera presentaba (33,5), (25,13) y (24,15): las tres venían de la reescritura y cayeron. La
> segunda, escrita el día de la retractación, decía que **solo** sobrevivía el (23,25), y era
> pesimista de más: los puntos intermedios estaban retirados *a la espera de remedirlos*. La tercera
> los recuperó… **usando otra vez la reescritura sin darse cuenta**, y anunció que el (25,13) dominaba
> al (26,25) en los dos ejes. Medido después: **dos llamadas idénticas daban (25,13) y (27,13)**.
> Esta es la cuarta y va con la reescritura desactivada y el barrido repetido dos veces.

**El único punto que mejora una cifra de la literatura: (23, 25).** El (26, 25) es el polinomio que
JSWW **sí imprimieron**, el que se cita desde hace cincuenta años. El (23, 25) tiene **tres variables
menos al mismo grado**, y **sin aplanado en absoluto**: sale de eliminar `q`, `y` y `z`, tres sustituciones lineales con todos los
coeficientes positivos. Ni nombres, ni reescritura, ni optimizador. Es el único punto que no ha
cambiado ni una vez en nueve rondas de defectos, precisamente porque es el que menos maquinaria usa.

**En la esquina de grado 5 ya no batimos a JSWW.** La mejor cifra construible y verificada es
**(44, 5)**; ellos anunciaron **(42, 5)**. Estamos dos por encima. El (41,5) y todo lo que vino
después dependían de la reescritura y no eran materializables: el sistema que se construía era más
débil que el original.

**El tramo medio vuelve, pero peor, y no bate a nadie.** (38,7), (32,9), (30,11) y (27,13) caen en
una región donde la literatura no tiene **ningún** par publicado —entre el grado 5 y el grado 25—,
así que exhibirlos vale algo. Pero **ninguno domina al (26,25)**: el (27,13) baja doce grados a costa
de una variable de más. Y comparados con lo que se llegó a anunciar, todos son peores: el (27,9) es
ahora (32,9), el (26,11) es (30,11), el (25,13) es (27,13).

**La lección de escala, que conviene no perder.** Las cifras que cayeron son exactamente las que
usaban más maquinaria, y la que nunca se movió es la que se podría haber hecho a mano en una tarde.
No es casualidad: **cada capa de maquinaria añadió una forma nueva de estar equivocado**, y la
verificación que se creía fuerte —«0 faltan / 0 sobran»— resultó ser ciega a esa clase de error. Y
hubo una forma más, descubierta al remedir: la reescritura no solo certificaba conjuntos **no
materializables**, sino que su resultado **no era reproducible** —dos llamadas idénticas, en el mismo
proceso, daban (25,13) y (27,13)—, porque el optimizador corre con un `timeout` de pared. Por eso
ahora está **desactivada por defecto** y el barrido solo se publica si dos repeticiones coinciden.

### Cómo se hizo: cinco palancas

Ninguna es «buscar mejor». Todas son **cambiar el espacio en el que se busca**, que es donde ha
estado siempre el problema.

**1. Aplanado como optimización exacta, no como heurística.** Aplanar es elegir qué subexpresiones
nombrar. Se codifica en SMT (Tseitin sobre los nodos del árbol y los monomios) y `z3.Optimize` da
modelo **y cota inferior**. Antes había ~2.000 reinicios aleatorios que encontraban 46; el
optimizador demostró que 46 era el mínimo *de esa base* y con eso quedó claro que el problema no era
la búsqueda sino la **formulación**.

**2. Reescritura: expresar en términos de los nombres ya elegidos.** Con `m = E²` nombrado,
`E³(E+2) = m² + 2mE` baja a grado 2 — y **ninguna partición** de `[E,E,E,E+2]` deja los dos grupos en
grado 1. Hacía falta la identidad algebraica, que se obtiene por reducción polinómica con la regla
orientada `c → marca` bajo grevlex. (`sympy.div` no sirve: devuelve el cociente desarrollado y
destruye la estructura que el nombre captura. `subs` tampoco: no dispara en potencias parciales.)

**3. Subsumas en el catálogo.** `g·k + k + 1` dentro de `g·k + 2g + k + 1` no es nodo del árbol ni
monomio de ningún desarrollo: no estaba en **ninguno** de los dos espacios de candidatos. Añadirlas
—con su regla espejo en optimizador y materializador— bajó el óptimo de 17 a 15 nombres.

**4. Cota demostrada `a ≥ 2`, usada REPARAMETRIZANDO.** Se demuestra (§3.2o) que toda solución del
sistema (1) cumple `n ≥ 2` y `a ≥ 2`. La forma limpia de aprovecharlo **no** es aflojar el criterio
de no-negatividad —que es lo único que impide aceptar sistemas falsos— sino escribir `a = A + 2` con
`A ∈ ℕ`, que es un cambio de variable biyectivo. Entonces `l = k+1+i(A+1)` pasa el criterio **sin
tocarlo**.

**5. Forzar las definiciones para que la eliminación salga gratis.** Regla general:

> si una ecuación dice `u = R` con `R ≥ 0`, y se **nombra** `R` como `m`, la ecuación pasa a ser
> `m − u = 0`; entonces eliminar `u` la sustituye por **un símbolo**, a coste de grado cero.

Sin ese nombre, sustituir `u` mete `R` entera donde `u` aparecía: eliminar `z` sin nombrar su
definición sube las ecuaciones de grado 2 a grado 4 y la eliminación se descarta. El optimizador no
puede descubrir esto solo — su objetivo cuenta **nombres** con las incógnitas originales congeladas,
así que nunca gastará un nombre para habilitar una eliminación aunque el balance neto sea favorable.

### Qué garantiza cada cifra (y qué no)

Cada punto publicado pasa **cinco comprobaciones**. Ninguna es un muestreo:

| # | Comprobación | Qué descartaría |
|---|---|---|
| 0 | el sistema de partida **es** el (1) de JSWW (con `a = A+2` si se desplaza) | trabajar sobre otro objeto |
| 1 | grado ≤ *target* por ecuación en el sistema **materializado** | una cifra de solucionador sin sistema detrás |
| 2 | cada nombre nuevo es **≥ 0 sobre ℕ** (estructural o con demostración escrita) | pérdida de **completitud**: el primo deja de emitirse |
| 3 | **equivalencia simbólica**: al deshacer los nombres, las definitorias se anulan y el resto recupera *exactamente* las originales, 0 faltan y 0 sobran | que el sistema aplanado no sea el mismo objeto |
| 4 | cada post-eliminación tiene miembro derecho con **todos los coeficientes ≥ 0** | pérdida de completitud en la dirección de vuelta |

**Por qué la [3] es una identidad polinómica y no un muestreo:** el sistema de JSWW se transcribe
**sin testigo** —sus valores son astronómicos y encontrar uno es el reto abierto del propio paper—,
así que no se puede verificar por evaluación. Sustituir cada nombre por lo que representa, en
cascada hasta punto fijo, y exigir que reaparezcan las 14 ecuaciones originales es más fuerte que
cualquier barrido.

**Lo que descansa en terceros y no se demuestra aquí:** que el sistema (1) de JSWW represente los
primos. Es resultado de 1976, con cincuenta años de citas y linaje de formalización. Se **cita**.

**Lo que NO se afirma:**

* **No es un mínimo.** La cota que devuelve el optimizador es de **su codificación**, y ha caído
  tres veces al ampliar el catálogo: 46 → 17 → 15 nombres. Ese historial es la prueba, no una
  precaución retórica.
* **No es un récord de grado.** El 5 lo anunciaron JSWW y es alcanzable mecánicamente; es una
  **meseta compartida**. Toda la partida ahí es número de variables.
* **Nadie externo lo ha revisado.** Es la salvedad que más pesa y la única que no se puede levantar
  desde dentro.

### El método que produjo todo esto: el resultado imposible como informe de error

Es la parte transferible, y la única lección que sobreviviría aunque las cifras se retirasen.
**Ninguno de los ocho defectos se encontró leyendo el código.** A los siete primeros los delató
un resultado que no podía ser cierto; al octavo, un test al ejecutarse:

| # | Defecto | El imposible que lo delató |
|---|---|---|
| 1 | una desigualdad sobre ℕ costaba 0 para *cualquier* expresión | el sistema admitía 4, 9, 15 y 25 como primos |
| 2 | índice anclado por congruencia, no por valor | `3² = 9` admitía `c ∈ {1,3,5,7,9}` |
| 3 | nombres que podían ser negativos | *ninguno* — rompe completitud, no soundness. Se encontró razonando, no midiendo |
| 4 | expandir destruye el árbol | los nodos útiles caían de 40 a 13 y la «cota» dejaba de significar nada |
| 5 | nombrar en grado 0 | una ruta nueva «mejoraba» de 20 a 17 nombres; la mejora entera era el bug |
| 6 | `sympy.Poly` lee los marcadores como coeficientes | el optimizador certificaba 16 donde el materializador construía 18 |
| 7 | al catálogo le faltaban las subsumas | **cota inferior 17 > construcción publicada 16**. Una resta |
| 8 | la semilla de Z3 aterrizó en la función equivocada | un `NameError` al ejecutar la suite |

**Tres de los siete primeros comparten causa raíz**, y no está en el código propio:
`sympy.Poly(e, *gens)` no falla cuando `e` contiene símbolos ajenos a `gens` — los trata como
**coeficientes**, en silencio y con resultado plausible.

**El octavo es de otra clase, y por eso vale la pena separarlo.** Los siete primeros eran *encodings
mal pensados* que un resultado imposible delató. El octavo fue una **edición que aterrizó en el sitio
equivocado**: un `replace(..., 1)` pegó `opt.set("random_seed", …)` en la primera de las dos
coincidencias de `opt = z3.Optimize()` del fichero, o sea en `aplanado_minimo` en vez de en
`aplanado_minimo_compuesto`. Dos efectos, y el segundo es el interesante:

* `aplanado_minimo` reventaba con `NameError` —no tiene ese parámetro— y la suite lo cazó;
* en `aplanado_minimo_compuesto` la semilla **nunca se aplicaba**, así que la medida anotada
  —«cambiar la semilla no mueve nada»— comparaba **ocho ejecuciones idénticas**.

La conclusión resultó ser correcta (rehecha con la semilla puesta: las ocho dan (36,5)), pero *eso da
igual*: **una conclusión correcta obtenida de una medida vacía sigue siendo una medida vacía**, y si
la cifra hubiera dependido de ella habría sido otro (40,5) retirado. La lección tampoco es la misma
que la de los siete: aquí no falló el razonamiento, falló **no ejecutar la suite después de tocar el
fichero**.

**Y dos de los imposibles apuntaban a cifras MEJORES que la publicada.** El defecto 6 daba 16 nombres
y habría dado (40, 5); no se sostuvo y hubo que retirarlo. La misma disciplina que retiró el (41,5)
y el (40,5) en agosto, aplicada a números que favorecían.

**Los comprobadores también fallan, y han fallado tres veces**, siempre por lo mismo: **comparar dos
fotos tomadas en momentos distintos**. Un detector de definiciones que encontraba 15 de 18. Unas
definiciones tomadas *antes* de eliminar comparadas con ecuaciones tomadas *después*. Y en esta
ronda, un lado con nombres comparado contra otro sin ellos, que dio un «NO VERIFICADO» sobre un
sistema impecable.

### El único cambio metodológico que hubo que hacer al pipeline

Dos tests llamaban al optimizador con **los mismos argumentos** y publicaban **(36,5)** y **(38,5)**.
Un óptimo exacto no puede hacer eso.

El diagnóstico: el tamaño del óptimo *sí* es estable (15 nombres, cota 15, con cualquier `timeout`),
pero **el óptimo no es único** y el número de nombres **no es la cifra final** — después viene la
post-eliminación, que el objetivo no puede ver. Dos aplanados de 15 nombres admiten distinto número
de eliminaciones.

Se corrigió de raíz: el pipeline enumera varios óptimos (cláusula de bloqueo + semilla) **y** corre
dos tandas (libre y forzando definiciones), y se queda con el mejor. La cifra pasa a depender de un
**parámetro declarado** (`k_optimos`) y no del modelo que devuelva Z3 esa vez. Sigue siendo una cota
superior: subir `k_optimos` solo puede mejorarla.

> Anotación honesta: la cláusula de bloqueo fuerte —«omite al menos uno de los ya usados»— **puede
> saltarse óptimos legítimos**. Es una fuente de diversidad, no un recorrido exhaustivo.

### Lo que se descubrió y no es una cifra

Tres cosas que salieron de cotejar la literatura contra **fuente primaria**, y que circulan mal:

**1. El «(10, ~1,6·10⁴⁵) de Matiyasevich» funde dos objetos distintos.** El 1,638·10⁴⁵ es el grado
del par **universal** (9, ·)ℕ de Jones (1982). El polinomio de primos de 10 variables que construyó
Matiyasevich tiene grado **> 6.000**, cifra de quienes lo formalizaron en Mizar.

**2. El (12, «grado enorme») tiene grado exacto: 13.697.** Lo publican Pąk–Kaliszyk (arXiv:2204.12311,
ITP 2022, introducción: *«the rank of the polynomial is 13,697»*). Test de consistencia:
`13.697 = 1 + 2·6.848`, impar, luego se lee como **generador** — todo grado de generador citado en la
literatura es impar, y eso sirve para detectar confusiones de unidades.

**3. El (58, 4) no es de primos ni es un generador.** Es un par **universal** y como
**representación**. Instanciado para primos daría 59 variables y, como generador, **grado 9** —
dominado en ambos ejes. (Ningún par universal puede bajar de grado 2: las ecuaciones cuadráticas son
decidibles.)

**Y el patrón de fondo, que es lo que hace posible todo esto:** en esta literatura **se anuncian
cifras que no se exhiben**. No es una hipótesis excéntrica; está documentado por los propios autores.
JSWW escriben (42, 5) y (19, 29) en una frase sin construcción. Y en 2025, Bayer y David publican
deliberadamente un par **peor** para no depender de uno de esos anuncios:

> «the second pair depends on Jones' universal pair (32, 12)ℕ of which there is no published proof in
> the literature»
> — Bayer–David, ITP 2025 (verificado palabra por palabra en arXiv:2505.16963)

Ahí está la explicación de por qué se puede mejorar el (42, 5) con operaciones elementales: **no es
que nadie supiera hacerlo, es que nadie lo escribió**. Escribir un polinomio de 42 variables y grado
5 en el *Monthly* de 1976 significaba componer del orden de mil monomios, y la matemática está en la
reducción, no en el polinomio. Era una barrera **tipográfica**, no matemática.

Lo que sí es nuevo hoy: que la equivalencia esté **verificada a máquina** y que exista un marco de
optimización con cotas. Eso no se podía hacer a mano.

### El frente lineal está agotado, y ahora por CENSO en vez de por impresión

Se venía diciendo «no quedan más eliminaciones gratis» sin haberlo comprobado incógnita a incógnita.
Hecho el censo de las 25 sobre los dos sistemas —dónde aparece cada una, con qué grado, y si alguna
ecuación la despeja linealmente— el resultado es limpio:

| grupo | cuántas | cuáles | por qué |
|---|---:|---|---|
| **eliminables** (RHS con todos los coeficientes ≥ 0) | **5** | `e, q, y, z` + `l` con `a = A+2` | ya se eliminan las cinco |
| despejables pero con signos mezclados | 8 | `h, j, m, n, p, v, x` | ver abajo |
| **ninguna ecuación las despeja linealmente** | 12 | `a, b, c, d, f, g, i, o, r, s, t, u, w` | fuera de alcance por estructura |

**La lectura, que es más fuerte que «no encontramos más».** El sistema tiene exactamente **cinco
ecuaciones lineales** —(1), (2), (3), (9) y (11)— y cada una aporta **exactamente una** incógnita
despejable con todo positivo: `q`, `z`, `e`, `y`, `l`. Las cinco están explotadas. No es que no
hayamos mirado: es que **no hay más ecuaciones lineales de las que sacar nada**.

**Y una corrección.** Se venía diciendo que las tres eliminaciones restantes —`m`, `p`, `x`— estaban
bloqueadas por los módulos de Davis. Es cierto para `m` y `x` (ecuaciones 12 y 13), **pero no para
`p`**: `p` se despeja de la ecuación (3), `p = e − 2n − q − z`, y lo que la bloquea es
`−2n − q − z`, que no tiene nada que ver con Davis. Es el fenómeno trivial de que de una ecuación
`A = B + C + D` solo se puede eliminar la de la izquierda: o `e` o `p`, no las dos. Se elimina `e`,
que es la que sale con signo bueno. Lo mismo pasa con `h`/`j` en la (1), y con `n`/`v` en la (9).

Así que el inventario real es: **dos** eliminaciones bloqueadas por matemática (`m` y `x`, ambas por
Davis), no tres, y la ganancia máxima por esa vía es de **2 variables**, no de 3.

### El Teorema de Combinación de Relaciones: medido el techo ANTES de implementarlo, y no sale

Estaba declarado como **«la única pieza que reduce el conteo»** en la esquina de pocas variables, y
era la recomendación para seguir. Antes de gastar una sesión implementándolo se midió **cuánto podría
comprar como máximo**. No sale, y conviene que quede escrito por qué.

**Qué hace el teorema (Matiyasevich–Robinson):** colapsa `q` condiciones del tipo «A es un cuadrado»
y «S divide a T» en **una sola ecuación al coste de una incógnita**.

**El ahorro NO es `q − 1`.** Es `(incógnitas dedicadas a esas condiciones) − 1`, que es bastante
menor porque una misma incógnita sirve a varias condiciones. Confundir las dos cosas infla el techo
y hace parecer viable lo que no lo es. Medido con `techo_combinacion_relaciones`:

| sistema | incógnitas | colapsables | ahorro máx. | **techo** |
|---|---:|---:|---:|---|
| cadena propia (`L_prime_shared`) | 49 | 15 | 14 | **(36, ?)** |
| sistema (1) de JSWW | 25 | 10 | 9 | **(17, ?)** |

**La primera fila descarta la cadena propia.** Su techo *teórico* —36 variables— es **peor que el
(23, 25) que ya está construido y verificado**. Implementar el teorema ahí sería trabajo garantizado
en pérdida. Esto invalida la recomendación que se había dado, y es exactamente el motivo de medir
antes de construir.

**La segunda fila parece prometedora y es una trampa.** 17 variables batiría al (19, 29) que JSWW
anuncian. Pero el techo es en **variables** y no dice nada del **grado**, y ahí está el problema:

> el punto (17, D) solo vale algo si **D < 13.697**; si no, lo domina el (12, 13.697) de la
> literatura — y también lo dominaría el (10, >6.000).

Los grados que produce este teorema son **astronómicos por construcción** (el propio documento
anotaba ~10⁴⁵ para la aplicación que da el par universal de Jones). Así que el punto resultante sería
con casi total seguridad **dominado**: 17 variables no sirven de nada a grado 10⁴⁵.

**Y no se puede afinar más, por una razón concreta.** El enunciado exacto de `M_q` —y por tanto su
grado— **no es accesible desde este entorno**: la política de egress rechaza `arxiv.org` y
`en.wikipedia.org`, además de los `math.umd.edu` y `ericzheng.org` ya anotados. Escribir `M_q` de
memoria sería exactamente el error que este proyecto ha pagado ocho veces: un polinomio mal recordado
produce un sistema **insound**, y esta vez ni siquiera habría un resultado imposible que lo delatara,
porque no hay testigo con el que evaluarlo.

**Conclusión operativa:** no implementar el teorema. Queda la función `techo_combinacion_relaciones`
para que, el día que el enunciado esté disponible, la decisión se tome con el número delante y no con
una intuición.

### ✅ FORMALIZADO EN LEAN 4: `a ≥ 2` verificado por el núcleo

La salvedad que más pesaba sobre todo lo hecho era que **nadie externo lo ha revisado**, y es la
única que no se puede levantar desde dentro… salvo sustituyendo al revisor por un núcleo de
demostración. Hecho, para el teorema que se podía hacer.

**Qué está formalizado** (`formalizacion/lean/CotaA.lean`):

```
theorem a_ge_two {a e f k l n o p q v x y z : Nat}
    (h3 : 2 * n + p + q + z = e)
    (h4 : ec4 k n f)                            -- 16(k+1)³(k+2)(n+1)² + 1 = f²
    (h5 : ec5 e a o)                            -- e³(e+2)(a+1)² + 1 = o²
    (h6 : a ^ 2 * y ^ 2 + 1 = y ^ 2 + x ^ 2)    -- (a²−1)y² + 1 = x²
    (h9 : n + l + v = y) : 2 ≤ a
```

**Por qué este teorema y no otro.** Es **el único resultado propio del proyecto que no depende de
que el sistema (1) represente los primos**: habla de las soluciones del sistema, sea cual sea el
conjunto que represente. Todo lo demás se apoya en el teorema de JSWW, que se *cita*. Este no
depende de nadie, así que es lo único verificable de arriba abajo. Y no es decorativo: es lo que
justifica la reparametrización `a = A + 2`, que es la que da los puntos **(24, 21)**, **(22, 29)** y
**(21, 37)** del tramo alto de la frontera. (Se escribió aquí que justificaba «el (33, 5)»; esa cifra
está retirada, §2.bis, y de hecho la reparametrización **no** mejora la esquina de grado 5.)

| garantía | estado |
|---|---|
| compila con Lean 4.33.1 | ✅ |
| `sorry` / `admit` / `axiom` / `native_decide` | **ninguno** |
| axiomas de los que depende | `propext`, `Classical.choice`, `Quot.sound` — los tres estándar |
| dependencias externas | **ninguna**; sin Mathlib |
| **el enunciado es el que se cree** | comprobado por `test_lean_cota_a.py` |

**Esa última fila es la que suele faltar, y es la que importa.** Que un fichero compile garantiza
que la *demostración* es correcta, no que el *enunciado* sea el que uno quería — y un teorema
formal de un enunciado equivocado parece más fuerte y vale menos. El test extrae las cinco
hipótesis del `.lean` y comprueba **con sympy** que cada una equivale a su ecuación en
`dioph_jsww.ECUACIONES`, y que aparecen literalmente en el fichero. Es la misma disciplina de
`verificar_equivalencia` —0 faltan, 0 sobran— aplicada al puente entre los dos mundos.

**Dónde estaba el riesgo concreto.** Las ecuaciones de JSWW están sobre ℤ con variables en ℕ; en
Lean se escriben sobre ℕ **sin restas** (`(a²−1)y² + 1 − x² = 0` pasa a `a²y² + 1 = y² + x²`). Ese
paso a mano es exactamente donde se cuela un signo, y **la resta truncada de ℕ convierte un error de
signo en un teorema que sigue compilando y ya no dice lo mismo**. Por eso el puente se comprueba a
máquina y no a ojo.

**Detalles que ahorran tiempo a quien lo retome:**

* **Sin Mathlib, y no hace falta.** El núcleo de Lean 4.33 trae **`grind`**, que normaliza anillos y
  cierra solo las identidades polinómicas de grado 4 del encaje. `ring` sí es de Mathlib. Eso evita
  descargar y construir Mathlib, que en este entorno habría sido el verdadero obstáculo.
* **Cinco hipótesis de catorce.** El teorema usa solo (3), (4), (5), (6) y (9): menos hipótesis,
  teorema más fuerte.
* **La única ayuda manual** es la monotonía del cuadrado en el paso `a = 0`: `grind` no la aplica
  sola, y sin ella `2 ≤ y` no contradice `y² + x² = 1`.

**Reproducir:** `formalizacion/lean/verificar.sh` — descarga Lean si hace falta (~570 MB, sin
Mathlib), compila, audita los axiomas y corre la comprobación del enunciado.

**Lo que NO queda formalizado, y es mucho:** la equivalencia del sistema aplanado con el (1) —hoy
verificada en sympy por `verificar_equivalencia`— y, por supuesto, el propio teorema de JSWW. Lo
primero es formalizable y es el siguiente paso natural; lo segundo se cita.

### Qué queda abierto

Ninguna ruta está **refutada**; todas están bloqueadas por matemática que falta o por herramienta.
Inventario detallado en §3.2r.

**Rutas que esta ronda cerró con medida** (no con suposición, porque un catálogo incompleto ya costó
tres cifras): la **forma agrupada** del paper da exactamente las mismas cifras que la desarrollada
—las subsumas ya recuperan `2a(n+1) = 2an + 2a`—; **subir el tope de subsumas** de 6 a 8 sumandos
también, a 5× el tiempo; y **demostrar más no-negatividades no baja el aplanado** (sin el filtro sale
el mismo número de nombres). Las tres estaban en la lista de «pendientes prometedores» y ya no lo
están.

Los dos cuellos reales que quedan:

**El obstáculo matemático es uno solo, y bloquea dos eliminaciones** (tres decía antes; el censo de
arriba lo corrige: `p` no está bloqueada por Davis sino por haber eliminado ya `e` de la misma
ecuación). Los dos **módulos de Davis**
`2a(n+1)−(n+1)²−1` y `2a(p+1)−(p+1)²−1` de las ecuaciones (12) y (13). Son positivos en la
construcción de JSWW porque un módulo lo es, pero eso descansa en *su* construcción. Demostrarlos
desde las ecuaciones exige `a > n` y `a > p`: relaciones **entre incógnitas**, que ningún cambio de
variable arregla —a diferencia de `a ≥ 2`, que sí se demostró y sí se absorbió reparametrizando—. El
SMT no concluye con 7 ecuaciones de grado 12 en 26 variables.

**Lo desbloquearía el texto de la demostración de JSWW**, que diría si `a > n` se *deriva* de las
ecuaciones o es solo condición de su construcción. Los dos PDF localizados (`math.umd.edu`,
`ericzheng.org`) **los rechaza la política de red de este entorno**; no se ha intentado rodear el
bloqueo.

**Y la advertencia que este propio informe justifica:** cada vez que se dijo «esto está agotado», no
lo estaba. El «óptimo» del optimizador ha caído tres veces —46 → 17 → 15 nombres— y las tres por
**ampliar el catálogo**, nunca por buscar mejor. La frase honesta no es «no queda nada», sino **«no
queda nada que sepamos formular hoy»**.

**Con un matiz nuevo, y es la primera vez que se puede decir algo así.** Se buscó un *cuarto* espacio
de candidatos, se encontró (111 productos-con-subsuma ausentes), se añadió… y la cifra **no se
movió**. Es el primer hueco del catálogo que no paga. Sigue sin demostrar nada —el quinto espacio,
si existe, tampoco lo veríamos— pero rompe la racha que hacía sospechar que siempre quedaba uno más.

### Cómo se reproduce, en cuatro líneas

Todo el pipeline está en dos funciones. No hay pasos manuales ni números escritos a mano:

```python
from src.analysis.dioph_jsww import sistema_desplazado, COTA_A, no_negativos_desplazados
from src.analysis.dioph_optflat import aplanado_y_eliminacion, barrido_pareto, verificar_equivalencia

S    = sistema_desplazado(COTA_A)                       # el (1) de JSWW con a = A+2
best = aplanado_y_eliminacion(S, 2, k_optimos=1,        # aplana, materializa y post-elimina
                              demostrados=no_negativos_desplazados(COTA_A))
ver  = verificar_equivalencia(S, best["materializado"], best["sistema"])
print(best["variables"], best["grado"], ver["ok"])      # -> 33 5 True
```

Y la frontera entera, con veredicto de equivalencia en cada punto publicado:

```python
for v, g, receta, ver in barrido_pareto(S, grados=(2,3,4,5,6), k_optimos=1,
                                        demostrados=no_negativos_desplazados(COTA_A)):
    print(v, g, ver["ok"], receta)
```

Piezas y responsabilidad:

| Función | Módulo | Qué hace |
|---|---|---|
| `sistema()` / `sistema_desplazado()` | `dioph_jsww` | el sistema (1) transcrito; el desplazado usa la cota demostrada `a ≥ 2` y **rechaza** cualquier desplazamiento sin demostración |
| `aplanado_minimo_compuesto()` | `dioph_optflat` | el SMT: elige qué nombrar y devuelve **cota inferior de su codificación** |
| `materializar()` | `dioph_optflat` | convierte la elección en un **sistema real**; sin esto una cifra es un número de un solucionador |
| `definiciones_lineales()` | `dioph_degree` | los miembros derechos a **forzar** para que la eliminación salga gratis |
| `eliminar_maximo()` | `dioph_degree` | post-elimina explorando **todos los órdenes**, exigiendo que el grado no suba |
| `aplanado_y_eliminacion()` | `dioph_optflat` | el pipeline completo: K óptimos × 2 tandas, se queda con el mejor |
| `verificar_equivalencia()` | `dioph_optflat` | el veredicto: 0 faltan / 0 sobran, o no vale |
| `barrido_pareto()` | `dioph_optflat` | la frontera entera, cada punto con su veredicto |

Los tests que lo bloquean todo: `src/tests/verification/test_dioph_jsww.py` — [4] la cifra, [5] la
equivalencia **sobre el mismo objeto que publica [4]**, [8] la demostración de `a ≥ 2`, [9] la
frontera con su comprobación de dominancia contra la literatura.

---

## 3.bis Registro cronológico — los números, con su historia

> Lo que sigue es el **registro**, escrito según fue ocurriendo: incluye las cifras que hubo
> que retirar y los defectos que las retiraron. El informe de arriba es la lectura; esto es la
> fuente. Las referencias `§3.2x` de todo el documento apuntan aquí.


### 3.1 Coste de los lemas (sobre ℕ) — **cifras corregidas**

Tres columnas, y la tercera es la única que cuenta. «Antes» son las cifras del sistema que Z3
refutó; «esqueleto» es la aritmética de la cadena con el índice anclado por congruencia —**no
representa los primos**, pero es la única versión con testigo evaluable y por eso sigue viva en
los tests; «sound» es la cadena anclada por `L_psi`.

| Lema | Antes (insound) | Esqueleto (no sound) | **Sound (`L_psi`)** | Verificación |
|---|---|---|---|---|
| `L_divides`, `L_congruent`, `L_square` | 1 | 1 | 1 | elemental |
| `L_composite` | 2 | 2 | 2 | elemental |
| `L_nonneg` (Lagrange, sobre ℤ) | 4 | 4 | 4 | 200 enteros |
| `L_nonneg_N` (sobre ℕ) | **0 ⚠️ siempre** | **0** si todos los coeficientes son ≥ 0; **1** en otro caso | ídem | — |
| `L_psi` (índice anclado) | — | — | **11** | 0 violaciones; 10/10 testigos |
| exponenciación `c = b^k` | 5 | 7 | **17** | 1368 casos (congruencia de Davis) |
| `L_binomial` | 21 | 27 | **57** | 209 casos |
| `L_factorial` | 36 | 46 | **96** | n=1..7 |
| `L_prime` (Wilson, aditivo) | 38 | 50 | **100** | Wilson en [2,250) |
| **`L_prime_shared`** (compartido) | 29 | 29 | **49** | ídem |

El salto de 29 a 49 son **+10 por exponente distinto** (11 de `L_psi` menos la `t` que sobra), y
la cadena usa dos exponentes. No es un coste de implementación: es lo que vale anclar el índice.

La fila crítica es `L_nonneg_N`. El criterio correcto sobre ℕ **no** es «una desigualdad es
gratis»: es que **un polinomio con todos los coeficientes ≥ 0 es ≥ 0 automáticamente**, porque
todas las variables lo son. Eso cubre la variable suelta, las constantes y sumas como `T+1`;
cualquier otra cosa cuesta una holgura. Declarar 0 para expresiones con coeficientes negativos
era el defecto.

### 3.2 ⚠️ EL GENERADOR (41, 5) ERA INVÁLIDO — corregido

**Qué se afirmó (agosto 2026, sesión anterior):** que `to_generator()` daba un generador
de primos con **41 variables y grado 5**, frente al récord citado de (42, 5).

**Por qué era falso.** `L_nonneg_N(e)` — «sobre ℕ la no-negatividad es gratis» — devolvía un
sistema **vacío**. Eso es cierto para una *variable suelta* (el dominio ya la hace ≥ 0), pero
**no para una expresión compuesta** como `2ab − b² − 1 − c − 1`. En modo ℕ, por tanto, las
condiciones laterales del lema exponencial (`c < M`, `a > c`, `a−1 > k`) **no imponían nada**.

Consecuencia: con `a ∈ {0,1}` la ecuación de Pell degenera —`(x,y) = (1,0)` la resuelve para
cualquier `a`— y el sistema de los primos admitía solución para **n = 4, 9, 15 y 25**. El
generador construido sobre él **habría emitido compuestos**. La cifra (41, 5) no medía nada.

**Cómo se encontró.** Con un demostrador SMT, no con más tests de testigos. La completitud
(pertenece ⟹ hay testigo) se verificaba construyendo el testigo; la **soundness** (no pertenece
⟹ **no** hay testigo) se declaraba y se dejaba descansar en los teoremas citados, porque las
incógnitas viven en rangos astronómicos y ninguna búsqueda los toca. Z3 no enumera: razona, y
demuestra `unsat`. Ver `src/analysis/dioph_soundness.py`.

**La corrección.** Las condiciones que faltaban se imponen ahora. Casi todas son **cotas
inferiores sobre la incógnita compartida `a`**, y hubo dos formas de imponerlas — con
consecuencias muy distintas:

```
(A) SUSTITUCION:      a := a' + k + 2 + Σᵢ(bᵢ + cᵢ)     coste 0 en la representación
(B) ECUACION LINEAL:  a − (k + 2 + Σᵢ(bᵢ + cᵢ)) = 0     coste 1, pero `a` sigue siendo un símbolo
```

(A) parece mejor y es **peor**. `a` aparece al cuadrado en la ecuación de Pell; elevar al
cuadrado una suma de seis símbolos genera decenas de monomios de grado 4 que el aplanado tiene
que nombrar uno a uno. (B) cuesta una incógnita en la representación y **ahorra once en el
generador**. Se usa (B).

Con `a ≥ k+2`, `a ≥ cᵢ+2`, `a ≥ bᵢ` y `bᵢ ≥ 2` se sigue `cᵢ < Mᵢ`. Y `y ≥ 1` **no hace falta
imponerlo**: la ecuación del índice da `y = k + (a−1)t` con `k ≥ 1`, `a ≥ 2`, `t ≥ 0`. Solo
quedan `k ≥ 1` y `bᵢ ≥ 2`, que no son cotas sobre incógnitas propias (en la cadena `k` y `bᵢ`
son expresiones), y se resuelven con el desplazamiento de origen de §3.2b.

| | Incógnitas | ¿Sound? |
|---|---|---|
| Antes (lo que se publicó) | 29 | **No** — Z3 halla testigo para 4, 9, 15, 25 |
| Corrección ingenua (1 holgura por condición) | 53 | Sí |
| **Diseño final** | **31** | Sí |

### 3.2b ⛔ LAS CIFRAS DEL GENERADOR QUEDAN RETIRADAS

> **Estado: DEFECTO CERRADO.** Esta sección se conserva como registro de qué falló y por qué; la
> reparación está en §3.2c-bis. Las cifras que se retiran aquí siguen retiradas — la cadena
> reconstruida da (68, 5), no (39, 5).

**El lema exponencial no es sound.** Se descubrió al intentar *validar* el récord, no al
intentar mejorarlo, y invalida (40, 5) y (39, 5).

```
3^2 = 9  -> el sistema admite c ∈ {1, 3, 5, 7, 9}
2^2 = 4  -> admite c ∈ {1, 2, 4, 7, 8, 9, 16}
2^3 = 8  -> admite c ∈ {1, 2, 6, 8, 18, 21, 25, 32}
```

Cada uno de esos valores viene con una asignación completa que **anula el sistema real**
(`Dioph.holds`), no con una heurística.

**Por qué.** Las tres ecuaciones del lema solo fuerzan

```
b^m ≡ c (mod M)     con     m ≡ k (mod a−1)
```

y eso **no fija `m = k`**: valen también `m = k + j(a−1)`, y para esos `m` el valor `b^m mod M`
es otro. La construcción clásica de Davis y Matiyasevich lleva más condiciones precisamente
para anclar el índice. Nuestra versión de tres ecuaciones era demasiado barata para ser cierta.

**Alcance.** Toda la cadena Wilson → factorial → binomial descansa en este lema, así que el
sistema de los primos **no es sound** y su conversión a generador no mide un generador de
primos. Las cifras de §3.2b anteriores —(62, 5), (51, 5), (44, 5), (40, 5), (39, 5)— **no
miden lo que decían medir**. Lo que sí sobrevive es la maquinaria: los conjuntos elementales del
catálogo (cuadrado, triangular, compuesto, suma de dos cuadrados, Fibonacci, Pell) están
verificados en ambas direcciones y no usan el lema exponencial.

**Por qué no lo cazaron las comprobaciones anteriores.** Tres razones, y las tres son lecciones:

1. **Las comprobaciones SMT del sistema de primos eran ACOTADAS** (cajas [0,20] y [0,200]).
   Las soluciones espurias viven muy por encima. Un `unsat` en una caja no dice nada fuera.
2. **El guardarraíl `a ∈ {0,1}` era demasiado específico.** Cubría la firma del defecto
   *anterior*, no una familia nueva. Un guardarraíl protege del error que ya conoces.
3. **El test de unicidad daba un falso positivo por vacuidad.** Preguntaba «¿hay solución con
   `c ≠ b^k`?» dentro de una caja donde **ni siquiera cabía la solución correcta**, y contaba
   el `unsat` como éxito. Dos de sus tres casos eran vacuos. Ahora `uniqueness_report`
   comprueba primero que el valor correcto es alcanzable y devuelve `'vacuo'` cuando no lo es.

**Lo que funcionó.** Preguntar «¿para qué valores de `c` tiene solución el sistema?» en vez de
«¿es único?». La estructura fija casi todo —`a` queda determinado por la reparametrización y las
soluciones de Pell son las `(x_m(a), y_m(a))`— así que se enumera en segundos y **cada candidato
se confirma evaluando el sistema real**. Está en `dioph_soundness.unicidad_exponencial`, y el
test [8] de `test_dioph_soundness.py` **deja la suite en rojo a propósito** hasta que el lema se
arregle: este proyecto ya tuvo una «Ecuación Suprema» con contraejemplos que sobrevivió
precisamente porque nada fallaba de forma visible.

**Qué haría falta para volver a tener una cifra.** Implementar la caracterización completa de la
exponenciación (Davis 1973, o Jones–Matiyasevich), que ancla el índice con ecuaciones
adicionales. Costará incógnitas —el lema pasará de 7 a bastante más— y **todas las cifras de la
esquina de grado bajo habrá que volver a medirlas desde cero**.

### 3.2b-bis La reconstrucción: el lema correcto ya está, de fuente primaria

`L_psi(A, B, C)` — «C = ψ_A(B) = y_B(A)» — transcrito del **Teorema 1 de Pąk–Kaliszyk (ITP
2022, formalizado en Mizar como `HILB10_8:19`)**, que sigue a Matiyasevich–Robinson:

> Sean A, B, C ∈ ℕ con A > 1, B > 0 y e ∈ ℕ. Entonces **C = ψ_A(B)** si y solo si existen
> i, j ∈ ℕ y auxiliares D, E, F, G, H, I ∈ ℤ tales que
> **`DFI = □ ∧ F | (H − C) ∧ B ≤ C`**
> donde `D = (A²−1)C²+1`, `E = 2(i+1)D(e+1)C²`, `F = (A²−1)E²+1`, `G = A+F(F−A)`,
> `H = B+2jC`, `I = (G²−1)H²+1`.

**Lo que añade y faltaba: ancla el índice.** La versión rota solo tenía `y_k(a) ≡ k (mod a−1)`,
que fija el *residuo* de k pero no k. Aquí el anclaje viene de que `D` es cuadrado exactamente
cuando `C` es un y-valor de `A`, `F` cuando lo es `E`, e `I` cuando `H` lo es de `G`.

**Se implementa como SISTEMA, no como la ecuación única del paper.** La forma compacta
`0 = (DFI−α²)² + (Fβ−H+C)²(Fβ+H−C)² + (B+γ−C)²` es elegante sobre el papel e **inviable** al
expandir: `D` es de grado 4, `E` de 7, `F` de 16, `G` de 32, `I` de ~70, y el cuadrado del primer
sumando pasa de **grado 300**. Nombrando D…I como incógnitas, **ninguna ecuación pasa de grado
4** — que además es justo lo que quiere la esquina de grado bajo. Es la misma lección que la cota
de Pell: *dónde* se paga el coste importa tanto como cuánto.

| | Incógnitas | Grado máx. | ¿Sound? |
|---|---|---|---|
| `L_exponential` (roto) | 7 | 4 | **No** |
| **`L_psi`** | **11** | **4** | soundness sin violaciones; **completitud constructiva, 10/10** |

**El testigo ya no se busca: se CONSTRUYE.** Era el bloqueo, y la salida vino de la estructura:

1. `D = x_B(A)²` automáticamente, porque `C = y_B(A)`.
2. `F` es cuadrado ⟺ `E` es un y-valor de `A`. Como `E = (i+1)·K` con `K = 2D(e+1)C²`, hace
   falta `l` con `K | y_l(A)`: el **rango de aparición** de K, que existe porque la sucesión de
   Pell es una sucesión de divisibilidad. Entonces `E = y_l(A)`, `F = x_l(A)²`, `i = y_l(A)/K − 1`.
3. Para `H` basta **`m = B`**, y eso desatasca todo: `G ≡ 1 (mod 2C)` da la forma `B + 2jC`
   exigida, y `G ≡ A (mod F)` da `F | (H − C)`. De paso `I = x_B(G)²` sale cuadrado solo.
4. Luego `DFI = (x_B(A)·x_l(A)·x_B(G))²`, **cuadrado por construcción**.

El rango de aparición se calcula factorizando `K` y tomando el mcm de los rangos de cada
potencia de primo — iterar módulo K directamente se queda corto en cuanto K pasa de unos
millones.

| Comprobación | Resultado |
|---|---|
| Soundness (enumeración hacia delante, tuplas pequeñas) | **0 violaciones** |
| Completitud: testigo construido y evaluado | **10/10** casos calculables |
| Reverso: `C ≠ ψ_A(B)` no admite testigo | **0 espurios** |

**Aviso de escala, y no es un detalle.** El rango de aparición crece brutalmente: certificar que
`y_2(3) = 6` ya exige `l = 408`; `y_4(2) = 56` exige **l = 43.456**, con `E` de decenas de miles
de cifras. Los testigos de este lema son astronómicos **por naturaleza, no por la
implementación**. Consecuencia metodológica: *la cadena completa nunca se podrá validar por
evaluación más allá de casos diminutos*. La verificación por testigo constructivo —el pilar de
este proyecto— tiene aquí su techo, y lo que quede por encima descansa en el teorema citado.

### 3.2c-bis La cadena, RECONSTRUIDA sobre `L_psi` — el defecto queda cerrado

`L_psi` existía como pieza suelta desde §3.2b-bis. Ahora la cadena entera descansa sobre él.

**Dónde estaba el agujero.** No en `L_exponential` como lema aislado, sino en `PellContext`: el
índice se fijaba con la ecuación `Y − k − (a−1)t = 0`, es decir `Y ≡ k (mod a−1)`. Barata —una
ecuación, una incógnita— y **falsa**: fija el residuo de k, no k. Valen también `m = k + j(a−1)`,
y cada uno aporta su propio `c`.

**Qué se ha hecho.** `PellContext(..., anclaje_psi=True)` sustituye esa ecuación por `L_psi(A, k, Y)`.
Con eso `Y = y_k(a)` para el k exacto, `t` sobra, y la congruencia de Davis ya dice lo que parecía
decir. Coste: **+11 −1 = +10 incógnitas por exponente distinto**.

Un detalle que no cuesta nada y ahorra grado: `L_psi` ya introduce `D = (A²−1)C²+1`, que **es**
`x_k(A)²`. Así que el contexto no repite la ecuación de Pell en grado 4, sino que escribe
`D = X²` en **grado 2** y reutiliza la que L_psi ya tenía. Nombrar las piezas sirve de poco si
luego no se dejan tocar; por eso `L_psi` expone sus intermedios.

| | Incógnitas | Ecuaciones | Grado | ¿Sound? |
|---|---|---|---|---|
| Cadena con anclaje por congruencia | 29 | 19 | 5 | **No** — admite valores espurios |
| **Cadena anclada por `L_psi`** | **49** | **35** | **5** | sí |

**Generador propio, ya válido: (68 variables, grado 5).** Aplanado **óptimo demostrado** (Z3
devuelve cota inferior 18 y elige 18 nombres). No mejora el (46, 5) que sale de aplanar el
sistema publicado de JSWW, y no pretende: son dos caminos al mismo rincón de grado 5, y gana el
que parte de una construcción que costó un paper entero afinar. Lo que esta cifra mide es otra
cosa —**cuánto cuesta la representación que el compilador obtiene por sí mismo**— y es la
magnitud que le interesa al proyecto.

#### El intercambio que hay que anotar: se ganó corrección y se perdió verificabilidad

`L_psi` construye su testigo a partir del **rango de aparición** de `K = 2D(e+1)C²`. El rango
existe siempre —la sucesión de Pell es de divisibilidad— pero calcularlo exige factorizar K, y en
esta cadena K es astronómico **ya para n = 2** (en el contexto del exponente R, K ≈ 10¹⁶⁷). No es
un problema de máquina: es la escala del teorema.

Consecuencia directa: **el testigo de la cadena correcta no es evaluable**. Lo que antes se
comprobaba de un tirón ahora se comprueba en tres piezas, cada una con la herramienta que le
sirve:

| Qué | Cómo | Resultado |
|---|---|---|
| `L_psi` ⟹ `Y = y_k(a)` | barrido directo sobre sus 9 ecuaciones (`soundness` [9]) | 0 violaciones |
| dado eso, el resto fija `c` unívocamente | enumeración con confirmación contra el sistema real (`soundness` [8]) | `c ∈ {b^k}` en 6/6 casos |
| la aritmética de la cadena no se rompió | testigo **parcial**: 19/35 ecuaciones anuladas en n=2,3 (`soundness` [7]) | ok |
| soundness de la cadena completa | SMT: firma `a ∈ {0,1}` refutada **sin cota**, + barrido en [0,20] (`soundness` [3]) | `unsat` en 16+8 consultas |

Y se conserva el **esqueleto aritmético** (`anclaje_psi=False`) precisamente porque *sí* es
evaluable: no representa los primos, pero es donde vive toda la aritmética —cotas, base
compartida, congruencias de Davis, Wilson, factorial, binomial— y su testigo completo se sigue
comprobando en `test_dioph_calculus` [12], [13] y [16].

**Lo que queda sin comprobar por evaluación, y hay que decirlo:** la **completitud** de la cadena
correcta. Descansa en el Teorema 1 de Pąk–Kaliszyk, que está formalizado en Mizar — no es poco,
pero no es lo mismo que un testigo evaluado aquí.

**Un requisito que sí queda cubierto, y por argumento en vez de por evaluación.** El generador
`Q = n·(1 − ΣPᵢ²)` solo representa el conjunto **sobre variables no negativas**, así que el
testigo debe serlo. No se puede comprobar evaluándolo entero, pero cada valor que `L_psi`
construye es ≥ 0 por su propia definición: `i = E/K − 1 ≥ 0` porque `E = y_l(A)` es múltiplo de K
y no nulo; `j = (H−B)/2C ≥ 0` porque `H = y_B(G) ≥ B`; `β = |H−C|/F ≥ 0` por el valor absoluto;
`γ = C−B ≥ 0` por la condición `B ≤ C` del propio teorema; y `α, D…I` son productos y sumas de
positivos. Evidencia adicional: los 10 testigos que **sí** se evalúan en `soundness` [9] son
todos no negativos, y los 29 valores del testigo parcial de la cadena también.

#### El test que probaba el defecto sigue probándolo

`test_dioph_soundness` [8] estuvo **en rojo a propósito** toda la reparación. Ahora está verde,
pero no se limita a comprobar la versión arreglada: **primero vuelve a enumerar la versión rota y
exige que siga exhibiendo los valores espurios** (`3² = 9 → c ∈ {1,3,5,7,9}`). Un test que solo
mira la versión buena no demuestra que sepa detectar el fallo. Este lo detecta delante de quien
lo lee, y solo después comprueba que el anclaje por `L_psi` lo cierra.

### 3.2d El ataque al récord por la vía LIMPIA: optimizar el aplanado de JSWW

**Por qué esta vía y no la nuestra.** Con el lema exponencial roto, cualquier cifra que salga de
nuestra cadena hay que retirarla. Pero el (42, 5) de JSWW es **su propio polinomio (1)** —26
variables, grado 25, publicado en 1976, con medio siglo de escrutinio y linaje de formalización
en Mizar/Coq/Isabelle— pasado por la sustitución de Skolem. Está transcrito en
`src/analysis/dioph_jsww.py` y **verificado** (reproduce (26, 25) exactamente). Si mejoramos el
aplanado sobre *su* sistema, el riesgo de corrección desaparece: la aportación es puramente la
optimización, que es para lo que sirve esta maquinaria.

| Estrategia de aplanado sobre el sistema de JSWW | Generador |
|---|---|
| voraz sobre la forma expandida | (56, 5) |
| árbol (Skolem) sobre la forma factorizada | (52, 5) |
| árbol→8 encadenado con voraz→2 | (49, 5) |
| **+ búsqueda sobre el desempate del voraz** | **(47, 5)** |
| **JSWW 1976, a mano** | **(42, 5)** |

**Nueve variables recuperadas de las catorce que separaban. Faltan cinco, y ahí hay meseta.**

**Lo que se probó y NO funcionó, que también es resultado:**

- **Eliminar incógnitas definidas linealmente.** Quita `q`, `z`, `e`, `y` (25 → 21 incógnitas) y
  **empeora el generador en todos los casos**: `q` → 64, `z` → 66, `y` → 85, frente a 49 sin
  eliminar. Es el mismo patrón que la cota de Pell: *sustituir sale barato en la representación y
  ruinoso en el generador*; la incógnita ahorrada se paga multiplicada al aplanar.
- **Aplanado híbrido** (árbol + reescritura con monomios ya nombrados). La idea era buena —el
  método por árbol nombra `(a+1)²` y `a²` por separado, cuando `(a+1)² = w+2a+1` es de grado 1 si
  `w = a²` ya existe— pero la implementación se atasca: `subs` no reduce potencias dentro de
  monomios. Arreglarlo exige trabajar con vectores de exponentes.
- **Otros criterios de puntuación del voraz** (priorizar monomios de exceso alto, priorizar
  cuadrados `x·x`, mezcla): ninguno mejora a la frecuencia simple.

**Cifras de la búsqueda:** ~2.000 reinicios sobre 8 objetivos intermedios, más 1.220 ejecuciones
sobre 5 objetivos × 4 criterios. Todas convergen a 46 incógnitas (47 variables). *Los reinicios
aleatorios están agotados.*

**Se hizo el siguiente paso: optimización exacta, con cota inferior demostrada**
(`src/analysis/dioph_optflat.py`). Aplanar restringido a nombrar monomios es un problema
combinatorio exacto y `z3.Optimize` lo resuelve dando modelo **y** cota:

| Punto de partida | Nombres | Total | Generador | Cota inferior |
|---|---|---|---|---|
| original expandido | 25 | 50 | (51, 5) | **25 — óptimo** |
| tras `flatten_tree(S, 8)` | 16 | 46 | **(47, 5)** | **16 — óptimo** |
| JSWW 1976, a mano | — | 41 | (42, 5) | — |

**Y esto reorienta el diagnóstico: nuestra búsqueda ya estaba en el óptimo.** Los ~2.000
reinicios aleatorios habían encontrado 46, y Z3 demuestra que 46 es el mínimo para esa base.
Luego el problema **no es la búsqueda: es la formulación.**

**Se extendió el optimizador a SUBEXPRESIONES COMPUESTAS**, que es donde JSWW ganan: ellos
nombran cosas como `(a + u²(u²−a))²` o `(n+4dy)²`, que no son monomios de ningún desarrollo.
`aplanado_minimo_compuesto` optimiza sobre la **unión de los dos espacios** —nodos del árbol de
cada ecuación *y* monomios del desarrollo— con codificación tipo Tseitin: cada par
(subexpresión, presupuesto de grado) recibe una variable booleana y su definición se asserta.

| Espacio de candidatos | Óptimo | Generador | Cota |
|---|---|---|---|
| solo monomios, desde el original | 25 nombres | (51, 5) | 25 |
| solo monomios, tras `flatten_tree(S,8)` | 16 nombres | (47, 5) | 16 |
| **compuestos ∪ monomios, con partición de exponentes** | **20 nombres** | **(46, 5)** | **20** |
| JSWW 1976, a mano | — | (42, 5) | — |

> ⚠️ **Retirado.** La palabra «óptimo» de este apartado no se sostiene, y la cifra bajó a **44**.
> Ver §3.2i. Se conserva el texto porque el razonamiento sobre los dos espacios de búsqueda sigue
> siendo válido; lo que cae es el superlativo.

**46 variables es el óptimo demostrado del aplanado mecánico**, y no es un número de un
solucionador: `materializar()` construye el sistema real —45 incógnitas (las 25 originales, todas
usadas, más 20 nombres), grado 2 por ecuación, 34 ecuaciones—. La materialización está verificada
en todo el catálogo: preserva la equisatisfacibilidad y además mejora a las heurísticas
(Fibonacci pasa de 12 a **10** variables).

**Conclusión, y es la que dice dónde atacar:** las cuatro variables que nos separan de JSWW
**no están en el aplanado**. Aplanar mejor es imposible —la cota inferior se alcanza—. Tienen que
salir de reestructurar el sistema de ecuaciones, que es lo que ellos hicieron a mano en 1976 con
conocimiento de su propia construcción.

**Cuatro errores de codificación, y los cuatro los cazó la misma pregunta: *¿es este resultado
posible?*** Merecen quedar escritos porque el patrón vale para cualquier optimizador:

| Fallo | Síntoma imposible |
|---|---|
| un `Mul` con un solo factor no constante (`−(cu+x)²`) no generaba particiones | **`unsat`** en un sistema que obviamente tiene solución |
| memoizar la fórmula z3 durante la recursión capturaba constantes `False` | el óptimo **empeoró** (20 → 16 nombres) al **ampliar** el espacio de candidatos |
| solo particionaba factores sintácticos, no vectores de exponentes | nuestro «óptimo» (21) era **mayor** que las 16 de JSWW, cuyo método es mecánico y por tanto una cota **superior** |
| la ruta monomial sin la guarda `d ≥ 2` partía `k²` en `k·k` como grado 1 | **cero nombres** para ecuaciones de grado 6 |

Y uno más en la materialización: `sympify("g*k")` crea símbolos **sin** `integer=True`, que en
sympy no son los mismos que los del sistema; y probar una partición lanzando excepción abortaba
la búsqueda en la primera rama muerta en vez de seguir con la siguiente.

### 3.2e ⚠️ NO CONSEGUIMOS REPRODUCIR EL (42, 5), Y EL MÉTODO CITADO DA 51

Este es el hallazgo que reorienta todo el ataque al récord. Hay que leerlo con la misma
desconfianza con la que se leyó nuestra propia cifra de agosto.

**Qué dice JSWW.** Una sola frase, sin construcción (p. 450): *«All that is necessary to reduce
the degree to 5 is the Skolem substitution method (cf. [3], p. 263). However, this procedure
increases the number of variables (to 42 when applied to (1)).»*

**Qué es exactamente ese método.** La referencia [3] es Martin Davis, «Hilbert's tenth problem is
unsolvable», *Amer. Math. Monthly* 80 (1973) 233–269. En su p. 263, Teorema 7.5, textual:

> *«The degree of P satisfying (\*) may be reduced by introducing additional variables `zⱼ`
> satisfying equations of the form `zⱼ = yᵢyₖ`, `zⱼ = xyᵢ`, `zⱼ = x²`. By successive substitutions
> of the `zⱼ`'s into P its degree can be brought down to 2. Hence the equation is equivalent to a
> system of simultaneous equations each of degree 2. Summing the squares gives an equation of
> degree 4.»*

Es **exactamente** nuestro aplanado: nombrar productos de dos variables y sustituir. Y de eso
tenemos el óptimo con **cota inferior demostrada**:

| Método | Mínimo demostrado | Cota inferior |
|---|---|---|
| **Davis p. 263 tal cual** (productos de dos variables) | **51 variables** | 25 nombres |
| **Nuestro espacio** (Davis **+** subexpresiones compuestas: un superconjunto) | **46 variables** | 20 nombres |
| **JSWW afirman** | **42 variables** | *sin construcción publicada* |

**42 < 46 < 51.** Con el método que ellos mismos citan, el mínimo es 51. Con un método
estrictamente más potente, 46. La cifra de 42 **no la sabemos reproducir**.

**Qué NO se está afirmando.** Que JSWW se equivoquen. Lo que se afirma es más modesto y más
comprobable: (a) nuestra transcripción de (1) es fiel —reproduce las (26, 25) publicadas—;
(b) sobre ella, el mínimo de nombres está demostrado por cota inferior, no estimado; (c) el
espacio de movimientos que optimizamos **contiene** el que describe Davis; y (d) la frase de JSWW
no viene acompañada de construcción, ni hemos encontrado que nadie la haya escrito después.
Es posible que aplicaran simplificaciones que no acreditan. **Hace falta revisión experta.**

**Consecuencia práctica.** Nuestro **(46, 5) materializado y verificado** podría ser el mejor
polinomio de grado 5 representador de primos **explícitamente construido**. No es «batir el
récord»: es que el récord quizá nunca se construyó. Y esa es exactamente la clase de afirmación
que este proyecto ya se equivocó una vez en dar por buena, así que va con las cuatro salvedades
de §7 intactas.

### 3.2g Qué está verificado del (46, 5), y qué no

La pregunta «¿tenemos un récord?» se contesta mejor separando lo comprobado de lo que descansa
en otros.

**Verificado por nosotros:**

| Comprobación | Cómo |
|---|---|
| La transcripción de (1) es fiel | Reproduce las **(26 variables, grado 25)** publicadas. Y coincide **carácter a carácter** con la que publica Wikipedia — verificación independiente |
| El aplanado alcanza la cota de **su codificación** | `z3.Optimize` alcanza el 20 que él mismo deriva. **No es el mínimo del problema**: hay contraejemplo, §3.2i |
| El sistema materializado **es** el de JSWW | Sustituyendo cada nombre por su definición en cascada se recuperan **exactamente** las 14 ecuaciones originales: ninguna falta, ninguna sobra |
| Grado 2 por ecuación ⇒ generador de grado 5 | Medido sobre el sistema materializado |
| El aplanado preserva la equisatisfacibilidad | Testigo extendido y evaluado en los 8 conjuntos del catálogo con testigo |
| **Cada nombre nuevo vive en ℕ** | 19 de 20 lo son **por estructura**; el vigésimo se **demuestra** (ver abajo). Sin esto la completitud del generador no estaba cubierta |

#### El requisito que faltaba: los nombres nuevos también viven en ℕ

Lo encontró una revisión adversarial de este mismo documento, y era una grieta real.

El generador `Q = (k+2)(1 − ΣPᵢ²)` representa el conjunto **sobre variables no negativas** — así
lo enuncian JSWW. Cada subexpresión que el optimizador decide nombrar añade una incógnita que
**también vive en ℕ**. Por tanto, para que un primo se siga emitiendo hace falta que en la
solución original de JSWW **cada nombre valga ≥ 0**.

Nombrar algo que puede ser negativo **no rompe la soundness** —toda solución del aplanado sigue
siéndolo del original, y eso está verificado simbólicamente— pero **puede romper la
completitud**: el primo deja de emitirse. Y esa dirección no se comprobaba, porque el sistema de
JSWW se transcribe **sin testigo** (sus valores son astronómicos) y `witness_is_nonnegative`
nunca llegaba a ejecutarse.

Al comprobarlo: de los 20 nombres, **18–19 son ≥ 0 por estructura** (productos y potencias pares
de variables de ℕ). Los que no:

- **`a + u²(u²−a)`** — se demuestra, y basta la ecuación (7). De `u² = 16r²y⁴(a²−1)+1`: si
  `u² = 1` la expresión vale 1; si `u² ≥ 2` entonces `16r²y⁴(a²−1) ≥ 1` obliga a `a ≥ 2` y
  `r,y ≥ 1`, luego `u² ≥ 16a²−15 > a` y la expresión es `≥ a+2`. Y `u² = 0` es imposible. Así que
  **vale ≥ 1 siempre**. Comprobado además por barrido: 3.528 ternas `(a,r,y)` que satisfacen (7),
  0 fallos.
- **`2a(n+1) − (n+1)² − 1`** — es el **módulo de la congruencia de Davis** de la ecuación (12).
  Es positivo en la solución que construyen JSWW porque un módulo lo es, pero eso descansa en *su*
  construcción y aquí **no se demuestra**. Queda fuera.

**Y el óptimo no es único**, lo que hacía la cifra frágil: sin fijar el criterio, Z3 devolvía unas
veces un conjunto de 20 nombres y otras veces otro, con distintas expresiones sin demostrar. Tres
medidas, todas con óptimo demostrado (cota inferior alcanzada):

| criterio para poder nombrar una subexpresión | óptimo | generador |
|---|---|---|
| ninguno | 20 nombres | (46, 5) — pero depende de qué modelo devuelva Z3 |
| solo `≥ 0` **por estructura** | 21 nombres | **(47, 5)** — cero suposiciones |
| estructura **+ la única demostrada** | 20 nombres | **(46, 5)** — la cifra publicada |

Es decir: **exigir que todo nombre sea demostrablemente no negativo sale gratis**. La cifra
publicada es la tercera fila, y el test `[4]` corre el optimizador con esa restricción para que la
cifra no dependa de la suerte del solucionador. La segunda fila queda registrada como el número
que no le debe nada a nadie, por si algún día hiciera falta.

**Descansa en terceros (y está bien que así sea):** que el sistema (1) de JSWW represente
efectivamente los primos. Es un resultado de 1976, citado durante cincuenta años, reproducido en
Wikipedia y con linaje de formalización en Mizar, Coq e Isabelle. No lo hemos verificado nosotros
—no podríamos: el testigo es astronómico y encontrarlo es el reto abierto del propio paper— y
tampoco hace falta.

**Lo que NO tenemos:**

- **No hemos batido el récord publicado.** El récord citado es (42, 5) y estamos en **(44, 5)**.
  Lo que sí tenemos es que **el (42, 5) no aparece construido en ningún sitio** y que el método
  que sus autores citan da, como mínimo demostrado, **51**.
- **Nadie con criterio lo ha revisado.** Sigue siendo la salvedad que más pesa.

**La afirmación honesta, entonces**, no es «tenemos un récord» sino: *este es un polinomio de
grado 5 representador de primos, explícitamente construido, con **44** variables, cuya reducción es
demostrablemente mínima, cuya equivalencia con el sistema de JSWW está verificada simbólicamente y
en el que **cada incógnita añadida es demostrablemente no negativa**.* Si el (42, 5) nunca se
construyó, sería el mejor construido. Eso es exhibible y comprobable por cualquiera; una frase de
1976 no lo es.

**Y conviene decir qué NO es un récord aquí: el grado 5 no lo es.** El grado 5 lo anunciaron JSWW
en 1976. No hemos bajado de 5 ni podríamos con esta construcción —el argumento de §3.2c lo cierra
para la familia `n·(1−ΣP²)`—. Lo único que puede reclamarse es la **exhibición**: tener escrito un
polinomio de grado 5 que genera los primos, cosa que hasta donde alcanza la búsqueda nadie había
publicado.

### 3.2h-bis Tabla de la literatura, cotejada contra fuente primaria

Revisión bibliográfica con las fuentes descargadas de arXiv (Pąk–Kaliszyk 2204.12311;
Bayer–David 2505.16963; Bayer–David–Hassler–Matiyasevich–Schleicher 2506.20909; Sun 1704.03504).
JSWW 1976 y Davis 1973 no están en arXiv: sus citas proceden de lo ya transcrito aquí y **no se
han podido re-verificar de forma independiente**.

**Convención sin la cual la tabla es incomparable:** una *representación* `k∈S ⟺ ∃x: P(k,x)=0`
cuenta **incógnitas** y el grado de `P`; un *generador* `S = {valores positivos de Q}` cuenta
**variables** y el grado de `Q`. La conversión estándar da `deg Q = 1+2·deg P` y `v = ν+1`, así que
**todo grado de generador citado es impar** — y eso sirve de test.

| Par | Tipo | Fuente | ¿Exhibido? |
|---|---|---|---|
| **(26, 25)** | generador | JSWW 1976, sistema (1) | **Sí**, escrito íntegro |
| **(42, 5)** | generador | JSWW 1976, p. 450, **una frase** | **No** |
| **(19, 29)** | generador | JSWW 1976, p. 450, misma frase | **No** |
| **(12, 13.697)** | generador | JSWW 1976 Teor. 2; grado exacto en Pąk–Kaliszyk | **No** («no literature is available») |
| **(24, 37)** | generador | Matiyasevich 1971, vía Pąk–Kaliszyk | No localizado |
| **(10, >6000)** | generador | Matiyasevich 1977/81 | **Sí — y formalizado en Mizar** (`POLYNOM9:85`) |
| (20, ?), (21, ?) sobre ℤ | generador | Sun, Sci. China Math. 64 (2021), Teor. 1.3(ii) | **No**, existencial |
| (58, 4) | **par universal**, no de primos | Jones 1982 | Universal sí; **instanciación para primos, nunca** |
| (9, 1.638·10⁴⁵) | **par universal** | Matiyasevich 1977 / Jones 1982 | — |
| (32, 12) | **par universal** | Jones | **Sin prueba publicada** (Bayer–David, ITP 2025) |

**Dos confusiones de unidades que circulan y que aquí se corrigen:**

1. **El «(10, ~1.6·10⁴⁵) de Matiyasevich» funde dos objetos.** El `1,638·10⁴⁵` es el grado del par
   **universal** `(9, ·)ℕ` de Jones 1982. El polinomio de primos de 10 variables que Matiyasevich
   *construyó* tiene grado **> 6000**, cifra verificada a máquina por quienes lo formalizaron. La
   frase de Wikipedia introduce el 10⁴⁵ con un «Hence» a partir del teorema de las 9 incógnitas:
   es **otro** polinomio, y no construido.
2. **El (58, 4) no es de primos ni es un generador.** Es un par universal, y como *representación*.
   Instanciado para primos daría 59 variables y, como generador, **grado 9** — dominado en ambos
   ejes. Además ningún par universal puede tener grado ≤ 2: las ecuaciones cuadráticas son
   decidibles.

**Lo que la tabla deja ver, y es el punto:** de los cuatro pares de primos por debajo de 26
variables o por debajo de grado 25 —(42,5), (19,29), (12,13697), (10,·)— **solo el de 10 variables
está construido y exhibido**, y está en el extremo opuesto de la frontera (grado > 6000). En el eje
de **grado bajo**, el único objeto exhibible por debajo de grado 25 sigue siendo el de este repo.

### 3.2i ⚠️ «Mínimo demostrado» era falso, y la cifra baja a (44, 5)

Dos hallazgos de una revisión adversarial, **ambos reproducidos aquí antes de aceptarlos**.

#### (a) La cifra baja a 44: la post-eliminación

Sobre el sistema **ya aplanado**, dos incógnitas salen sin coste:

```
q := h + j + w·z      (de α₀)
y := l + n + v        (de α₈)
```

Sus miembros derechos tienen **todos los coeficientes positivos**, luego son ≥ 0 sobre ℕ
automáticamente y la equisatisfacibilidad vale en **las dos direcciones sin ninguna suposición**.
El grado no sube: en el sistema ya aplanado, `q` e `y` solo multiplican cosas de grado 1.

Resultado: **43 incógnitas, grado 2 por ecuación ⇒ generador (44, 5)**. La distancia al (42,5)
anunciado baja de +4 a **+2**.

Lo incómodo es que el mecanismo **ya estaba implementado** en el repo —`eliminar_lineales`, en uso
dentro de `L_prime_shared`— y simplemente nunca se había conectado a la cadena de JSWW, que es
donde está la cifra de portada. Detalle que importa: **eliminar antes de aplanar es peor** (medido:
`pre=['q','e','y']` da 23 nombres y vuelve a 46). Lo que paga es eliminar **después**, que es justo
lo que el modelo de coste del optimizador no puede ver.

#### (b) La «cota inferior demostrada» no es una cota del problema

Contraejemplo, reproducido: sobre el sistema de JSWW con `e` eliminada, `aplanado_minimo_compuesto`
devuelve **cota inferior 21**, y existe —construido y comprobado, grado 2 por ecuación— un aplanado
de **20 nombres**. Luego lo que `opt.lower()` devuelve es una cota inferior **de la codificación**,
no del problema de aplanado.

Es el **cuarto** bug de este encoding, y como los tres anteriores lo delató *un resultado
imposible*, no la lectura del código. **Tres causas, las tres localizadas**, y solo las dos primeras
son arreglables sin rediseñar:

1. **`Mul.args` no despliega potencias.** Para `E³·(E+2)` la única partición generada era
   `(E³)|(E+2)`, nunca `(E·E)|(E·(E+2))`. Corregido: `_factores()` despliega las potencias.
2. **`eliminar_lineales` expandía, y el catálogo se construye de la forma sintáctica recibida.**
   Medido: el sistema de JSWW tiene 40 nodos `Add`; tras eliminar una incógnita **expandiendo**
   quedaban **13**, y desaparecían justo los útiles (`c*u+x`, `4dy+n`, `a+u²(u²−a)`,
   `gk+2g+k+1`). Ocho de los veinte nombres del contraejemplo **ni siquiera estaban en el
   catálogo**. Corregido: la eliminación mantiene dos copias, una expandida para *detectar* las
   definiciones lineales y el **árbol intacto** para devolver. Ahora son 42 nodos `Add` y los
   veinte nombres sí están en el catálogo.
3. **Y aun así el contraejemplo sobrevive** — con los 20 candidatos disponibles, Z3 sigue
   diciendo 21. La causa, verificada haciendo fallar al materializador sobre esa expresión
   exacta: **las reglas de reducción no saben re-expresar una subexpresión como polinomio en los
   nombres ya elegidos.** Con `m = E²` nombrado, reducir `E³(E+2)` exige la identidad
   `E³(E+2) = m² + 2mE`; el encoding solo sabe (a) partir el árbol en grupos de factores,
   (b) partir el vector de exponentes de un monomio **sobre los generadores originales**, y
   (c) expandir — y expandir destruye precisamente el `E²` que el nombre captura. No hay ninguna
   ruta que use un nombre como generador nuevo.

**La (3) se implementó, y la hipótesis era FALSA.** `_division(e,c,gens)` añade justo esa ruta:
si `e = q·c + r` y `c` está nombrado —luego cuenta como grado 1—, basta pedir `q` de grado ≤ d−1 y
`r` de grado ≤ d. Funciona: en un caso mínimo reduce `E³(E+2)` a grado 2 (`m1 = m2² + 2m2n + 2m2p`)
donde el camino anterior fallaba de plano. Pero **no mejora ninguna cifra**: sobre la cadena de
JSWW la cota sigue en 20, y sobre el sistema del contraejemplo sigue en 21.

Y hay una lección dentro de la lección. Al principio *sí* parecía mejorar —20 → 17 nombres, 21 →
18—, y esos números eran **falsos**: venían de un **bug latente** que la propia ruta destapó.
Nombrar una subexpresión la convierte en una incógnita, que tiene **grado 1**; pero tanto el
optimizador como el materializador permitían nombrar cuando se pedía **grado 0**. Ninguna ruta
pedía grado 0 hasta que llegó ésta (`intentar(q, d−1)` con d=1). Síntoma: **una única ecuación de
grado 3** —`16·m6·m9² − 16·m8·m9·r − u² + 1`— en un sistema que debía quedar en 2, y con ella un
generador de grado 7 en vez de 5. Con el guardarraíl `d >= 1` puesto, el 17 se convierte en 20 y
el 18 en 21: la mejora entera era el bug.

Es el **quinto** defecto de este encoding y otra vez lo delató un resultado imposible, no la
lectura del código. Y de paso deja el marcador donde estaba: **el contraejemplo sigue en pie**
—cota 21 con un aplanado de 20 exhibido—, así que la causa real de esa brecha **sigue sin
localizar**, y no es la que yo había supuesto. La palabra «mínimo» sigue retirada.

**Caracterización precisa de lo que queda abierto**, que es más útil que una hipótesis:

- El sistema de 20 nombres **existe**: 24 incógnitas originales + 20 nombres, 33 ecuaciones,
  grado 2 por ecuación. Construido a mano y comprobado.
- Nuestro `materializar` **no lo encuentra**, y falla **con la ruta de sustitución y sin ella**,
  siempre en la misma expresión: `no se pudo reducir a grado 2: (2n+p+q+z)³(2n+p+q+z+2)`.
  (Con la ruta activa tarda ~20 min en agotar las alternativas, pero acaba fallando: no es un
  problema de tiempo.)
- Y la causa concreta de ese fallo **sí** está localizada: `_division` usa `sympy.div`, que
  devuelve cociente y resto **desarrollados**. Así que el `E²` que el nombre captura se pierde
  otra vez en el cociente, y `intentar` no lo reconoce dentro. Es la misma lección de siempre
  —expandir destruye el árbol— apareciendo por tercera vez, ahora dentro de la propia ruta que
  se añadió para esquivarla. En el caso mínimo se salva porque la recursión vuelve a dividir y
  el resto ya es de grado 1; en el sistema grande, no.
- Luego la brecha **no es solo del optimizador**: optimizador y materializador comparten el
  mismo juego de reglas de reducción y **los dos** se quedan cortos ante ese conjunto. Es una
  limitación de capacidad compartida, no un error de contabilidad en la cota.

Eso acota dónde buscar: no en cómo Z3 deriva la cota, sino en el repertorio de reducciones que
`opciones_de` / `intentar` saben aplicar. Y descarta la vía que ya se probó: añadir la división
por un nombre no basta.

### 3.2j El mecanismo que faltaba: REESCRITURA. Implementado, y no baja la cifra

Se implementó lo que §3.2i señalaba, y el resultado es limpio en las dos direcciones: **cierra la
brecha conocida y no mejora el (44, 5)**.

**Qué es.** Las tres rutas del aplanado —partir el árbol en grupos de factores, partir el vector de
exponentes de un monomio, desarrollar— comparten una limitación: ninguna sabe **reescribir** una
expresión en términos de los nombres ya elegidos. Y hay casos donde no queda otra. Con `m = E²`
nombrado:

```
E³·(E+2) = E⁴ + 2E³ = m² + 2·m·E          (grado 2)
```

pero **ninguna partición de factores llega ahí**: `E³(E+2)` tiene factores `[E,E,E,E+2]` y ningún
reparto en dos grupos deja ambos en grado 1. Hace falta la identidad algebraica.

`_reescribir` la obtiene por **reducción polinómica** con la regla `c → marca`, orientada poniendo
los generadores antes que la marca en grevlex; así el término principal de `c − marca` es `c` y cada
aparición de `c` dentro de `e` se sustituye. La identidad se comprueba (`r|marca=c == e`) antes de
devolverla.

**Diagnóstico previo, que fue lo que lo hizo posible.** Con los 20 nombres del contraejemplo fijados,
se materializó cada ecuación por separado: **falla exactamente una**, la de `E³(E+2)(a+1)²+1−o²`.
No era una laguna de catálogo —los 20 nombres **sí** están entre los 640 candidatos— sino de reglas.

**Resultados medidos:**

| | Antes | Con reescritura |
|---|---|---|
| Cota sobre el sistema con `e` eliminada | 21 nombres | **19** |
| Materializar los 20 nombres del contraejemplo | falla | **grado 2, OK** |
| Cota sobre el sistema completo de JSWW | 20 nombres | **20 — sin cambio** |

**El contraejemplo de §3.2i queda RESUELTO**: donde el encoding declaraba 21 y existía un aplanado
de 20, ahora certifica 19. Pero **la cifra publicada no se mueve**: sobre el sistema completo la cota
sigue en 20, luego **(44, 5)** se mantiene.

**Dos costes que hay que anotar.**

1. **Coherencia obligatoria.** `reescritura` debe valer lo mismo en `aplanado_minimo_compuesto` y en
   `materializar`. Se rompió dos veces: con la regla solo en el materializador salía un sistema de
   grado mayor que el certificado; con la regla solo en el optimizador, el conjunto elegido no se
   podía construir (`no se pudo reducir a grado 2: q + s(2ap+2a−p²−2p−2) − x + y(a−p−1)`).
   **Un certificado solo vale para el juego de reglas con el que se emitió.**
2. **Impracticable en el materializador del sistema completo**: más de 20 minutos sin terminar,
   frente a ~20 s por el camino de siempre. Por eso la ruta queda **opt-in y desactivada por
   defecto** en ambos sitios: la cifra publicada sale del camino rápido y verificado. Un atajo que
   no se puede ejecutar no entra en la cifra.

**Y el tope cuenta INTENTOS, no éxitos.** Contando éxitos, un nodo para el que casi ningún candidato
encaja escaneaba los ~600 llamando a `sympy.reduced` en cada uno, y construir el encoding no
terminaba en 40 minutos. Con el tope sobre intentos el coste queda acotado —23 s— a cambio de que la
ruta sea **incompleta**: la cota resultante sigue siendo del encoding, no del problema.

### 3.2p ⛔→✅ La FRONTERA COMPLETA — el (33,5) retirado, el tramo medio revalidado

> **⛔ Esta sección se escribió alrededor del (33, 5) y esa cifra está RETIRADA** (§2.bis): venía de
> la ruta de reescritura, cuyos certificados no son materializables. Se conserva el texto porque el
> **razonamiento sobre las palancas sigue siendo correcto** y explica la forma de la curva; lo que se
> corrige son los **números**, remedidos sin reescritura y revalidados con la comprobación
> estructural. La tabla de más abajo es la buena. La esquina de grado 5 queda en **(44, 5)**, por
> encima del (42,5) anunciado.

La curva sale de **tres palancas**, y ninguna es «buscar mejor»:

| Paso | Resultado |
|---|---|
| Sistema (1) publicado de JSWW | 25 incógnitas, grado 12 ⇒ (26, 25) |
| Reparametrizar `a = A + 2` (cota **demostrada**, §3.2o) | mismas incógnitas, catálogo más rico |
| Aplanado a grado `d` por ecuación | generador de grado `1+2d`, tantos nombres como haga falta |
| Post-eliminar incógnitas lineales (todos los órdenes) | una variable menos cada una, a costa de grado |

**Verificado con cinco comprobaciones**, ninguna relajada:

0. el sistema de partida **es** el (1) de JSWW con `a = A+2`, comprobado ecuación a ecuación, y
   `a ≥ 2` está demostrado (§3.2o) — así que el cambio de variable es biyectivo;
1. grado ≤ 2 por ecuación en el sistema materializado;
2. los 16 nombres son ≥ 0 sobre ℕ (estructurales, más el demostrado);
3. equivalencia simbólica: al deshacer los nombres en cascada, las definitorias se anulan y el
   resto recupera **exactamente** las originales — 0 faltan, 0 sobran;
4. las cuatro definiciones eliminadas (`z = m₁`, `y = l+n+v`, `q = h+j+m₁w`, `e = h+j+m₁w+m₁+2n+p`)
   tienen todos los coeficientes positivos, luego la equisatisfacibilidad vale en las dos
   direcciones sin suponer nada.

Medido: 13 definitorias se anulan, 10 vivas recuperan las 10 originales vivas, **0 faltan y 0
sobran**.

> Y el comprobador falló primero, como siempre. La primera pasada dio «NO VERIFICADO» y el sistema
> no tenía nada malo: al eliminar `z` sustituyéndola por un NOMBRE (`z → m₁`), el lado «original»
> quedaba con un nombre dentro y el lado recuperado ya no lo tenía. Se comparaban dos
> representaciones distintas. Es la **tercera vez** en este proyecto que un comprobador da un fallo
> falso por comparar dos fotos tomadas en momentos distintos; por eso queda escrito en el test.

#### Lo que desbloqueó el salto: un resultado IMPOSIBLE, otra vez

El optimizador certificaba **17 nombres como cota inferior**. JSWW pasan de 26 a 42 variables con la
sustitución de Skolem, o sea **16 nombres**, y su método es mecánico.

> Una cota inferior por encima de una construcción publicada no puede ser cierta.

Es el mismo patrón que descubrió los seis defectos anteriores: el imposible es del instrumento, no
del problema. Y el instrumento fallaba en el **catálogo de candidatos**. Tenía dos espacios —nodos
del árbol y monomios del desarrollo— y le faltaba un tercero: las **subsumas**.

```
ec.(2):  (g·k + 2g + k + 1)·(h+j) + h − z
         `g·k + k + 1` es una SUBSUMA: ni es nodo del árbol (el nodo es la suma entera)
         ni es monomio de ningún desarrollo. No estaba en ninguno de los dos espacios.
```

Añadidas las subsumas al catálogo **y la regla espejo en las dos direcciones** (`R[e][d] ← x_c ∧
R[resto][d]` en el optimizador, y su gemela en el materializador —la pareja desalineada ya rompió la
cadena dos veces—), el óptimo cae de **17 a 15 nombres**.

Y con 15 nombres la post-eliminación admite **tres** incógnitas en vez de dos: sobre el sistema sin
desplazar eso da ya **(38, 5)**, cuatro por debajo del anunciado, antes de aplicar las otras dos
palancas.

El **orden de la post-eliminación importa** y antes se perdía: quitar `e` primero deja `q`
inutilizable (subiría el grado a 4) y quitar `q` primero deja fuera a `e`. Un recorrido voraz se
queda con lo primero que encuentra y la cifra dependía del orden de iteración. `eliminar_maximo`
explora **todas** las ramas.

#### La tercera palanca: forzar las definiciones para que la eliminación salga gratis

El optimizador minimiza **nombres** con las incógnitas originales congeladas. No puede ver que
después se eliminan incógnitas, así que nunca gastará un nombre para habilitar una eliminación —
aunque el cambio neto sea favorable.

La regla, que es general y no un truco:

> si una ecuación dice `u = R` con `R ≥ 0`, y se **nombra** `R` como `m`, la ecuación pasa a ser
> `m − u = 0`; entonces eliminar `u` la sustituye por **un símbolo**, a coste de grado cero.

Sin ese nombre, sustituir `u` mete la expresión `R` entera donde `u` aparecía. Medido: eliminar `z`
sin nombrar su definición sube las ecuaciones de grado 2 a grado 4 y la eliminación se descarta;
con el nombre, sale gratis. El balance nunca es malo — nombrar cuesta a lo sumo una incógnita y
eliminar quita una — y suele ser bueno, porque muchas de esas expresiones se iban a nombrar igual.

Medido sobre JSWW sin desplazar: **15 nombres y 3 eliminaciones ⇒ (38,5)** frente a **16 nombres y
4 eliminaciones ⇒ (36,5)**. Un nombre de más, dos variables de menos.

#### Y cómo apareció esta palanca: dos tests que se contradecían

Los tests [4] y [5] llamaban al optimizador con **los mismos argumentos** y publicaban (36,5) y
(38,5). Un óptimo exacto no puede hacer eso. La causa no era un fallo de cota —el tamaño, 15, sale
estable con cualquier `timeout`— sino que **el óptimo no es único**: Z3 devolvía conjuntos distintos
del mismo tamaño, y uno de ellos contenía por casualidad la definición de `z`.

Eso obligó a dos cosas. Primero, a **arreglar la contradicción de raíz**: la cifra ya no puede
depender de qué modelo devuelva Z3 esa vez, así que el pipeline enumera varios óptimos —con
cláusulas de bloqueo y semillas distintas— y se queda con el mejor. Y segundo, a entender *por qué*
aquel conjunto era mejor, que es de donde salió la regla de arriba.

Anotación honesta sobre la enumeración: la cláusula de bloqueo fuerte —«omite al menos uno de los
ya usados»— **puede saltarse óptimos legítimos**. Es una fuente de diversidad, no un recorrido
exhaustivo. La cifra sigue siendo una cota superior construida y verificada, nunca un mínimo.

#### La frontera de Pareto, que es el resultado que estaba sin publicar

Se venían midiendo dos esquinas —grado 5 y grado 25— como si fueran los dos únicos sitios donde hay
algo que decir. Pero hay **dos palancas continuas y opuestas**: aplanar a grado `d` por ecuación da
un generador de grado `1+2d` y cuanto más alto `d`, menos nombres hacen falta; eliminar una incógnita
lineal quita una variable y sube el grado. Barrerlas juntas da una **curva**:

**Frontera remedida (sin reescritura, `k_optimos=1`).** Cada punto está materializado y pasa las
**tres** comprobaciones: identidad polinómica (0 faltan / 0 sobran), verificación **estructural** de
los nombres, y ninguna incógnita original perdida.

| variables | grado | receta | sistema | verificación |
|---:|---:|---|---|---|
| 44 | 5 | aplanar a 2 + eliminar `q,y` | ambos | ✅ |
| 38 | 7 | aplanar a 3 + eliminar `q,y` | ambos | ✅ |
| 32 | 9 | aplanar a 4 + eliminar `q,y,z` | ambos | ✅ |
| 30 | 11 | aplanar a 5 + eliminar `q,y,z` | ambos | ✅ |
| 27 | 13 | aplanar a 6 + eliminar `q,y,z` | sin desplazar | ✅ |
| **23** | **25** | sin aplanar + eliminar `q,y,z` | ambos | ✅ |
| 22 | 29 | sin aplanar + eliminar `l,q,y,z` | `a=A+2` | ✅ |
| 21 | 37 | sin aplanar + eliminar `e,l,q,y,z` | `a=A+2` | ✅ |

La columna «sistema» importa: la reparametrización `a = A+2` (§3.2o) **no** paga en la esquina de
grado 5 —que es donde se creyó que pagaba— y de hecho **empeora** el punto de grado 13 (28 frente a
27). Lo que aporta es el **tramo alto**: (22,29) y (21,37), que el sistema sin desplazar no alcanza.

> Comparado con la tabla retirada: los puntos intermedios **siguen ahí**, pero con otras recetas y
> **todos peores** —el (27,9) pasa a (32,9), el (26,11) a (30,11), el (25,13) a (27,13)—. La esquina
> de grado 5 se hunde entera: de (33,5) a (44,5). Y **ninguno de los intermedios domina ya** al
> (26,25) publicado, que es lo que la tabla retirada afirmaba de dos de ellos.

Contra la literatura (`(10, >6000)`, `(12, 13697)`, `(19, 29)`, `(26, 25)`, `(42, 5)`):

* **(23, 25)** mejora en tres variables el **(26, 25) publicado**, al mismo grado. **Es el único
  punto del proyecto que bate una cifra de la literatura**;
* **(38, 7)**, **(32, 9)**, **(30, 11)**, **(27, 13)** caen en zona **literalmente vacía** en la
  literatura —entre el grado 5 y el grado 25 no hay ningún par publicado—, pero **ninguno domina** al
  (26, 25): bajan grado a costa de variables;
* **(44, 5)** queda **por encima** del (42, 5) que JSWW anuncian: en esa esquina **no** los batimos, y
  el punto se publica igual porque ocultarlo sería quedarse solo con lo que favorece;
* `(22, 29)` y `(21, 37)` **quedan dominados** por el (19, 29) que JSWW anuncian, y por eso tampoco se
  presentan como récord.

Los puntos intermedios son **mecánicos**: nadie los reclamó porque nadie los escribió. Exhibirlos
cuesta lo mismo que exhibir uno solo, y sin ellos se estaba publicando menos de lo que se tenía.

#### Lo que NO cambia

* **No es un mínimo demostrado.** La cota que devuelve el optimizador sigue siendo de su codificación
  —y este apartado es la prueba: la codificación anterior certificaba 17 y existía un 15—. La
  siguiente laguna del catálogo, si la hay, se detectará igual: por un resultado imposible.
* Sigue descansando en que el sistema (1) de JSWW represente los primos. Eso se cita, no se demuestra
  aquí.
* `deg < 5` sigue abierto según los propios autores.

### 3.2r Qué queda abierto tras esta ronda (inventario, con estado)

Se agotaron las opciones que se sabían formular. Estas son las que quedan, y **ninguna está
refutada** — todas están bloqueadas por matemática que falta o por herramienta:

| Ruta | Qué daría | Estado medido |
|---|---|---|
| Demostrar los **dos módulos de Davis** ≥ 0 | desbloquea eliminar `m`, `p`, `x`: hasta 3 variables | **bloqueada**. Exige `a > n` y `a > p`, relaciones ENTRE incógnitas. SMT no concluye con 7 ecuaciones de grado 12 |
| Leer la demostración de JSWW | diría si `a > n` se **deriva** o es condición de su construcción | **bloqueada por acceso**: los dos PDF localizados (`math.umd.edu`, `ericzheng.org`) los rechaza la política de red de este entorno. No se ha rodeado el bloqueo |
| Más candidatos en el catálogo | el «óptimo» ya cayó 46 → 17 → 15 al ampliarlo | **abierta**. Sin idea concreta de qué falta ahora; el aviso, si llega, será otro resultado imposible |
| Forzar más definiciones | ya aplicado a las 3 que existen | **agotada** para este sistema |
| Enumerar más óptimos (`k_optimos`) | puede mejorar cualquier punto | **abierta y barata**, solo cuesta tiempo. Los puntos intermedios de la frontera se midieron con `k_optimos=1` |
| Medir la frontera completa con las tres palancas | los puntos de grado 7–13 bajarían | **pendiente**: cada solve del sistema desplazado cuesta ~4 min |
| **Teorema de Combinación de Relaciones** | única palanca que reduce de verdad en la esquina de POCAS variables | **sin implementar**. Debe ser programa simbólico, nunca expandido (grado ~10⁴⁵) |

Y una advertencia que este mismo apartado justifica: **cada vez que se ha dicho «esto está
agotado», no lo estaba**. La frase honesta no es «no queda nada», sino «no queda nada que sepamos
formular hoy».

### 3.2o ✅ COTA DEMOSTRADA: el sistema de JSWW implica `n ≥ 2` y `a ≥ 2`

La ecuación (11) define `l = k + 1 + i·(a − 1)`. Tiene un `−i`, y por eso `eliminar_lineales` la
rechazaba: sobre ℕ hay que poder **reconstruir** un valor no negativo, y sin saber `a ≥ 1` no se
puede. Era una de las cuatro condiciones que §3.2m listaba como frontera abierta.

**Se demuestra, y es elemental.** Tres pasos, los tres verificados en `test_dioph_jsww [8]`:

**Paso 1 — `n ≥ 2`.** La ecuación (4) dice `f² = 16K³(K+1)N² + 1` con `K = k+1 ≥ 1`, `N = n+1`.

```
N = 1:   (4K² + 2K − 1)²  =  f² − 4K(K+1)     <  f²  <  f² + (2K−1)(2K+1)  =  (4K² + 2K)²
N = 2:   (8K² + 4K − 1)²  =  f² − 8K          <  f²  <  f² + (4K−1)(4K+1)  =  (8K² + 4K)²
```

`f` quedaría **estrictamente entre dos enteros consecutivos**: imposible. Que las cuatro diferencias
sean `> 0` para todo `K ≥ 1` se certifica sustituyendo `K = KK+1` y comprobando que el polinomio
resultante tiene todos los coeficientes `≥ 0` y no es idénticamente nulo. Es una demostración
completa, no una comprobación en un rango.

**Paso 2 — `a ≠ 0`.** Con `a = 0` la ecuación (6) queda `x² + y² = 1`, luego `y ≤ 1`; y la ecuación
(9) es `n + l + v = y`, luego `n ≤ 1`. Contradice el paso 1.

**Paso 3 — `a ≠ 1`.** Con `a = 1` la ecuación (5) queda `o² = 4e⁴ + 8e³ + 1`, y para `e ≥ 1` hay otro
encaje estricto: `(2e²+2e−1)² = o² − 4e < o² < o² + (4e²−1) = (2e²+2e)²`. Luego `e = 0`. Pero la
ecuación (3) es `2n + p + q + z = e`, así que `e = 0` fuerza `n = 0`. Contradice el paso 1. ∎

#### Cómo se usa una cota sin relajar el criterio

La forma limpia **no** es aflojar `_coeficientes_no_negativos_expr` —que es lo único que impide
aceptar sistemas falsos— sino **reparametrizar**: con `a ≥ 2` demostrado, `a = A + 2` con `A ∈ ℕ` es
un cambio de variable biyectivo, y entonces `l = k + 1 + i·(A + 1)` tiene todos los coeficientes
positivos y pasa el criterio **sin tocarlo**. Eso es `sistema_desplazado()`, que además **rechaza**
cualquier desplazamiento mayor que la cota demostrada.

**Qué desbloquea, medido.** Sin aplanar: una eliminación más, `l`, que da `(22, 29)` y `(21, 37)`
—ambos **dominados por el (19, 29)** de JSWW, así que no se presentan como récord—. Y `(23, 25)` no
se mueve.

Pero en la esquina de grado 5 **sí paga, y bastante**: con el catálogo corregido el aplanado del
sistema desplazado baja a **13 nombres** (frente a 15 sin desplazar). La primera vez que se midió
esto salió que el desplazamiento no cambiaba nada — y era cierto, *con el catálogo viejo*. Conviene
anotarlo: una palanca puede parecer inútil solo porque otra pieza está rota.

> Un detalle que casi cuesta la medida: tras el cambio de variable, las cadenas de
> `NO_NEGATIVOS_DEMOSTRADOS` ya no coinciden con las del sistema desplazado, y el optimizador las
> reconoce **por texto**. Las dos demostraciones se perdían en silencio y el aplanado subía de 15 a
> 20 nombres. Habría parecido que el desplazamiento empeora la cifra cuando era un fallo de
> emparejado de cadenas. Por eso existe `no_negativos_desplazados()`.

**Lo que esto NO da.** Las otras tres eliminaciones (`m`, `p`, `x`, de las ecuaciones 12–14)
necesitan `a ≥ n+1`, `a ≥ p+1` y `a ≥ p`: relaciones **entre incógnitas**, que un desplazamiento
constante no arregla.

> ✅ **RESUELTO después** (§2.ter). Las tres se siguen de `a ≥ e+1`, porque `e = 2n+p+q+z` domina a
> `n` y a `p` a la vez y por tanto **una sola sustitución afín** las vuelve estructurales. La cota sale
> de la estructura de Pell de la ec.(5), da **(21, 25)**, y está **formalizada en Lean** junto con los
> tres teoremas de Pell en que se apoya.

### 3.2q Rutas CERRADAS en esta ronda (para no volver a intentarlas)

Tres cosas que se midieron y que ya **no** hay que reintentar:

1. **El filtro de no-negatividad no cuesta nada.** Con `solo_no_negativos=False` el óptimo sigue
   siendo el mismo número de nombres; lo único que cambia es que Z3 elige el módulo de Davis
   `2ap+2a−p²−2p−2` y `y²(a²−1)`, que no están demostrados. Conclusión: **demostrar más
   no-negatividades no baja el aplanado**. La brecha estaba en el catálogo, no en el filtro.
   (Ojo con el alcance: eso dice que no bajan el *número de nombres*. Sí siguen haciendo falta para
   desbloquear **eliminaciones**, que es otra cosa y es donde queda trabajo.)
2. **El óptimo no es único, y la enumeración a ciegas no sirve para diversificar.** Se enumeraron
   12 óptimos distintos con cláusulas de bloqueo (`excluir=`) y se post-eliminó exhaustivamente
   sobre cada uno: los 12 dan la misma cifra. Y **cambiar la semilla de Z3 tampoco** — pero esta
   segunda mitad hubo que **medirla dos veces**, porque la primera no medía nada: el
   `opt.set("random_seed", …)` había aterrizado en `aplanado_minimo` en vez de en
   `aplanado_minimo_compuesto` (un `replace(..., 1)` que pegó en la primera de las dos
   coincidencias del fichero), así que las ocho «ejecuciones con semillas distintas» eran ocho
   ejecuciones idénticas. Rehecha con la semilla puesta de verdad: las ocho dan **(36, 5)**.
   Lo que sí funciona es **forzar** el candidato que hace falta (§ la tercera palanca), que es
   dirigir la búsqueda en vez de sortearla. La enumeración se conserva porque es lo que impide que la cifra
   dependa del modelo que devuelva Z3 ese día — que es como salieron (36,5) y (38,5) de dos tests
   con los mismos argumentos.
3. **La forma AGRUPADA del paper no aporta nada.** JSWW escriben `b(2a(n+1) − (n+1)² − 1)` con
   `(n+1)` agrupado; nosotros lo guardábamos desarrollado, y estaba anotado como sospechoso —la
   forma agrupada expone `(n+1)` y `(n+1)²` como subexpresiones nombrables, y `(n+1)²` ya hace falta
   en la ecuación (4)—. Medido con el catálogo actual: **exactamente las mismas cifras**, 15 nombres
   → (38,5) libre y 16 → (36,5) forzando. La razón es que las **subsumas ya recuperan** lo que la
   agrupación exponía: `2a(n+1) = 2an + 2a` es una subsuma del desarrollo. La sospecha era correcta
   en 2025 y quedó obsoleta al arreglar el catálogo.
4. **Subir el tope de las subsumas NO aporta.** `_nodos` corta en `Add` de 6 sumandos porque las
   subsumas son `2ⁿ`. Como el catálogo incompleto ya costó tres cifras, había que medirlo y no
   suponerlo: con tope 6 salen 16 nombres → **(36, 5)**; con tope 8, **exactamente lo mismo**, a
   **5× el tiempo** (50 s → 257 s). Tope 10 no se ejecutó: con 8 ya costaba cinco veces más para
   cero ganancia, y decirlo es más honesto que dejarlo corriendo una hora. Conclusión: el espacio de
   subsumas está **saturado** en este sistema; si al catálogo aún le falta algo, no es por ahí.
5. **El TERCER hueco del catálogo existe y no aporta nada — y esto es lo importante.** El censo
   encontró que faltaban **111 productos-con-un-factor-subsuma** (`(h+j)·(gk+k+1)` dentro de
   `(gk+2g+k+1)·(h+j)`), 35 de ellos nombrables sin demostración: no son nodo del árbol, ni monomio
   del desarrollo, ni subsuma de ningún `Add`. Un cuarto espacio de candidatos, real y ausente.
   Añadidos (`productos_subsuma=True`) y medido en los dos sistemas:

   | sistema | sin el hueco | con el hueco |
   |---|---|---|
   | sin desplazar | 16 nombres → **(36, 5)** en 62 s | 16 nombres → **(36, 5)** en 60 s |
   | `a = A+2` | 16 nombres → **(33, 5)** en 314 s | 16 nombres → **(33, 5)** en 313 s |

   *(Las cifras de esta tabla están **retiradas** —§2.bis— y se conservan porque lo que la medida
   establece es que las semillas **no diversifican**, y eso sigue siendo cierto.)*

   **Idéntico.** Y ese empate es la primera evidencia real de saturación que tiene este proyecto:
   las tres ampliaciones anteriores del catálogo bajaron la cifra cada vez —46 → 17 → 15 nombres—,
   y esta no la mueve ni un nombre ni un segundo. No demuestra que el catálogo esté completo (nada
   lo demuestra), pero es lo más parecido a una señal de fondo que se ha conseguido: hasta ahora,
   *cada* hueco encontrado pagaba.
6. **Pre-eliminar antes de aplanar es peor, siempre.** Medido de nuevo tras corregir el catálogo:
   pre-eliminar `l` sobre el sistema desplazado sube a 21 nombres y el resultado final es peor. Lo
   que paga es eliminar **después**.

Y una que sigue **bloqueada por acceso, no por matemáticas**: el texto de la demostración de JSWW
resolvería si `a > n` y `a > p` se **derivan** de las ecuaciones o son solo condiciones de su
construcción. Hay un PDF del paper en `www.math.umd.edu` y otro con una solución explícita en
`www.ericzheng.org`; **los dos están bloqueados por la política de red de este entorno**. No se ha
intentado rodear el bloqueo.

### 3.2n ✅ (41, 5) — POR DEBAJO del 42 anunciado, y lo desbloqueó un corolario de una línea

De las cinco no-negatividades que §3.2m listaba como pendientes, **una no requería demostración
nueva**: bastaba mirarla.

```
ya demostrado:  a + u²(u²−a) ≥ 1
corolario:      (a + u²(u²−a))² − 1 ≥ 0        porque t ≥ 1 ⟹ t² − 1 ≥ 0
```

Estaba en la lista de «exige demostración» por no haberla mirado, no por ser difícil. Añadida al
catálogo de no-negativos demostrados, el óptimo baja de 18 nombres a **17**:

| Paso | Resultado |
|---|---|
| Sistema (1) publicado de JSWW | 25 incógnitas, grado 12 |
| Aplanado con reescritura: **17 nombres** (cota inferior 17) | 42 incógnitas, grado 2 ⇒ **(43, 5)** |
| Post-eliminar `q` e `y` | 40 incógnitas ⇒ **(41, 5)** |

**Verificado igual que antes:** equivalencia simbólica con **0 faltan, 0 sobran** (17 ecuaciones se
anulan al desnombrar, las 12 restantes recuperan las 12 originales vivas); grado 2 por ecuación;
todos los nombres ≥ 0 sobre ℕ, con las dos excepciones estructurales demostradas.

**Qué cambia el signo de la afirmación.** Hasta ahora lo mejor que se podía decir era «igualamos una
cifra anunciada y nunca exhibida». Ahora es **una variable por debajo**: el (42,5) de JSWW era una
frase sin construcción, y este (41,5) está construido y verificado. Sigue **sin ser un mínimo
demostrado** —la cota es de la codificación— y sigue descansando en que el sistema (1) represente
los primos.

**Y la lección, que es la de siempre en este proyecto.** La ruta que dio el salto no fue el
optimizador ni la reescritura ni el SMT: fue **leer la lista de pendientes y darse cuenta de que una
ya estaba resuelta**. Cuatro de las cinco condiciones siguen abiertas, y §3.2m sigue siendo el mapa.

### 3.2m ¿Está agotada la esquina de grado 5? **No.** Rutas abiertas, con su estado medido

Pregunta directa —«¿seguro que hemos acabado?»— y respuesta directa: **no**. Lo que sigue es el
inventario de lo que queda, con lo que se ha llegado a medir de cada cosa. Ninguna está descartada;
varias están sin resolver por **coste de cómputo**, no por imposibilidad.

| Ruta | Qué podría dar | Estado medido |
|---|---|---|
| **Demostrar las no-negatividades restantes** | cada una puede quitar un nombre | **1 de 5 resuelta** (§3.2n, corolario) y dio (41,5) — cifra luego **retirada**. Z3 **no concluye** sobre grado 12 en 26 variables, pero las que bloqueaban *eliminaciones* se resolvieron por otra vía: `a ≥ e+1` vía Pell (§2.ter) |
| **Eliminación completa** (no solo `q` e `y`) | cada incógnita extra eliminada = −1 variable | la búsqueda exhaustiva **no termina** (medido: >40 min sobre las 43 incógnitas) |
| **Objetivo del optimizador = variables, no nombres** | podría preferir 19 nombres con 4 eliminaciones a 18 con 2 | **sin implementar** |
| **Forma agrupada del paper** (`ECUACIONES_AGRUPADAS`) | expone `(n+1)` y `(n+1)²` como nombrables | **sin medir** con reescritura |
| **Eliminar `e` antes de aplanar** | otro punto de partida | **sin medir** tras corregir el sexto defecto |
| **Hacer converger la reescritura en `materializar`** | convierte cotas en cifras | identificado, **sin resolver** |

**La más prometedora, y por qué.** El óptimo *sin* la restricción de no-negatividad es de **17
nombres**, uno menos que los 18 publicables. La diferencia son cinco expresiones que no son ≥ 0 por
estructura y que habría que **demostrar**, igual que se hizo con `a + u²(u²−a) ≥ 1`:

```
a² − 1        2ap − p² − 1        2a(n+1) − (n+1)² − 1        y⁴(a²−1)        (a+u²(u²−a))² − 1
```

Dos observaciones que las hacen plausibles: la última **ya está demostrada** —es el cuadrado de algo
que probamos ≥ 1, menos 1—, y la tercera es el **módulo de Davis** de la ecuación (12), que en la
construcción de JSWW es positivo por definición. Las tres primeras se reducen esencialmente a
`a ≥ 1`. Si caen, la cifra baja de 42.

**Por qué no están resueltas.** El intento por SMT se atasca: preguntar «¿admite el sistema una
solución sobre ℕ con esta expresión negativa?» exige a Z3 razonar sobre 14 ecuaciones de hasta grado
12 en 26 variables, y no concluye ni expandiendo ni sin expandir. La vía razonable no es fuerza
bruta sino **derivarlas a mano de las ecuaciones del propio sistema**, como se hizo con
`a + u²(u²−a)`, y dejar la comprobación numérica como respaldo.

**Regla que no cambia:** mientras una de esas cinco no esté demostrada, el nombre correspondiente no
entra, y la cifra publicada es la restringida. Igual que en agosto.

### 3.2l ✅ (42, 5) CONSTRUIDO Y VERIFICADO — se iguala la cifra anunciada en 1976

**La cifra publicada pasa de (44, 5) a (42, 5)**, que es exactamente el par que JSWW anunciaron en
una frase y que nadie había exhibido. Ahora está construido, materializado a grado 2 por ecuación y
verificado equivalente al sistema publicado.

| Paso | Resultado |
|---|---|
| Sistema (1) publicado de JSWW | 25 incógnitas, grado 12 |
| Aplanado óptimo **con reescritura**: 18 nombres | 43 incógnitas, grado 2 ⇒ **(44, 5)** |
| Post-eliminar `q = h+j+wz` e `y = l+n+v` (gratis sobre ℕ) | 41 incógnitas ⇒ **(42, 5)** |

**Verificación, la misma vara de siempre:**

- **Equivalencia simbólica**: sustituyendo cada nombre por lo que representa, 18 ecuaciones se
  anulan (las definitorias) y las 12 restantes recuperan exactamente las 12 originales vivas.
  **0 faltan, 0 sobran.** Identidad polinómica, no muestreo.
- **No-negatividad sobre ℕ**: los 18 nombres son ≥ 0; 17 por estructura y `a + u²(u²−a)`
  demostrado ≥ 1 desde la ecuación (7) y comprobado en 3.528 ternas.
- **Grado 2 por ecuación**, luego el generador es `1 + 2·2 = 5`.

#### El defecto que había que cerrar antes: el SEXTO de este encoding

La reescritura por sí sola daba una cota de 16 nombres — que era **falsa**. El materializador
construía grado 3 con esos mismos 16, y comprobado a mano: con `m4 = e²` y `m5 = (a+1)²`,
`e³(e+2)(a+1)² = m4²·m5 + 2·e·m4·m5`, y no hay nombre para `e³`; el grado 3 es inevitable.

Causa: **la misma de siempre**. `sympy.Poly(e, *gens)` no falla cuando `e` contiene símbolos
ajenos —los trata como **coeficientes**—, así que con marcadores dentro de las expresiones
`_como_monomio` leía `m4²·a²` como `a²`, la ruta monomial lo partía en `a|a` y certificaba grado 2
sobre algo de grado 4. Exigiendo explícitamente que no haya símbolos fuera de `gens`, la cota sube
de los 16 falsos a **18 reales** — y esos 18 sí se materializan.

Es la tercera vez en esta sesión que el mismo comportamiento silencioso de `Poly` produce un
defecto, y las tres veces lo delató un resultado imposible, no la lectura del código.

#### Y una convergencia que hubo que arreglar para poder verificarlo

`materializar` no terminaba con reescritura activa (>8 min). Lo resolvió **memoizar `intentar`**:
el backtracking re-exploraba las mismas ramas fallidas desde particiones distintas. Es sound porque
`intentar` es determinista y su único efecto lateral —crear el símbolo de un nombre— es idempotente.
Con la caché, 10 s. De paso, el pipeline publicado bajó de 18 s a 5 s.

#### Qué cambia y qué no

**Cambia:** el (42, 5) deja de ser una cifra anunciada y sin construcción publicada para ser un
objeto exhibible. En el eje de grado bajo, el mejor punto construido pasa de 44 a **42 variables**.

**No cambia:** sigue **sin ser un mínimo demostrado** —la cota es de la codificación, y el
contraejemplo de §3.2i sigue en pie—; sigue descansando en que el sistema (1) de JSWW represente
los primos; y sigue sin revisión experta. Igualar el 42 anunciado no lo convierte en récord de
variables: JSWW ya lo habían anunciado. Lo que aporta es que **ahora existe**.

**Limitación anotada:** la reescritura no siempre converge en `materializar` —para el conjunto
libre de 17 nombres no termina en 20 minutos—, así que sigue siendo **opt-in**. El pipeline
publicado la usa porque ahí sí converge y está verificado; el test [6], que compara tres
configuraciones entre sí, va sin ella para ser homogéneo.

### 3.2k Reescritura COMPLETA: la cota baja de 20 a 16, y ahí se queda (por ahora)

Se quitó el tope de intentos. Lo que impedía quitarlo eran tres problemas de coste, y el tercero
resultó ser el dominante y no tener nada que ver con la reescritura:

1. **Filtro exacto por monomio líder.** La regla `c → marca` dispara si y solo si algún monomio de
   `e` es divisible por el líder de `c`. Comprobarlo cuesta comparar vectores de exponentes;
   descubrirlo llamando a `sympy.reduced` costaba cuatro órdenes de magnitud más. Corta el 87 %
   de las llamadas (728 → 91 pares sobre las ecuaciones de partida).
2. **No reescribir lo ya reescrito.** `sympy.Poly(expr, *gens)` **no falla** cuando `expr` contiene
   un símbolo ajeno: lo trata como **coeficiente**. Por eso la ruta se re-aplicaba a sus propios
   resultados sin fondo —7.215 llamadas en 100 s sin terminar de construir— y además el test de
   divisibilidad sobre esos monomios no significaba lo que parecía.
3. **`grado` memoizado.** Este era el gordo, y no era de la reescritura: `grado` disparaba
   **310.923 `expand` y 282.348 `Poly`**, el 39 % del tiempo. Memoizarla dejó las llamadas a `Poly`
   en 27.690 y es lo que hizo viable todo lo demás. De paso, el pipeline publicado pasó de 18 s a 8 s.

**Resultado, con la restricción de no-negatividad puesta (que es la que cuenta):**

| | Nombres | Tiempo |
|---|---|---|
| Sin reescritura | 20 | 16 s |
| Con tope de intentos | 20 | 16 s |
| **Reescritura completa** | ~~16~~ **18** | 24 s |

> ⚠️ **El 16 era falso.** Lo refutó el materializador (grado 3 con esos mismos 16) y la causa fue el
> sexto defecto del encoding, documentado en §3.2l. Corregido, la cota real es **18**, y esos 18 sí
> se materializan y verifican: dan **(42, 5)**.

Sobre el sistema con `e` eliminada la cota baja de 21 a **15**. Y **16 nombres sobre 25 incógnitas
darían (42, 5)**, que tras post-eliminar `q` e `y` sería **(40, 5)** — por debajo del 42 anunciado.

#### Pero 16 es una COTA, no una cifra

`materializar` **no consigue construir** ese conjunto de 16 en un tiempo utilizable: más de ocho
minutos sin terminar, incluso tras trasladarle las tres optimizaciones. Y la regla de esta casa no
cambia porque el número sea atractivo: **un conjunto que no se puede materializar no se puede
verificar, y lo que no se verifica no entra en la cifra**. La publicada sigue siendo **(44, 5)**.

Es exactamente la misma disciplina que retiró el (41,5) y el (40,5) en agosto, aplicada esta vez a
un número que nos favorecía. La diferencia entre una cota y un resultado es precisamente que el
segundo se puede exhibir.

**Dónde está el bloqueo ahora**, ya acotado: no en el optimizador —que certifica 16 en 24 s— sino en
`materializar`, cuya búsqueda con reescritura activa explora un árbol que no converge. Es el mismo
tipo de problema que ya se resolvió en el optimizador con precomputos y filtros, así que la vía
está abierta; simplemente no se ha completado.

**Y la siguiente vía, ya sondeada y descartada tal cual.** Se probó sustituir en el ÁRBOL en vez de
dividir, que era lo natural tras ver que `sympy.div` desarrolla. No funciona por sí sola:
`E³.subs(E², s)` **no dispara** —sympy no sustituye potencias parciales— y `e.subs(E, s)` sí, pero
deja `s³(s+2)`, que sigue siendo de grado 4.

Lo cual señala el mecanismo que de verdad falta, y ya no es una hipótesis vaga: **la ruta monomial
parte el vector de exponentes sobre los generadores ORIGINALES, y tendría que hacerlo sobre
`generadores ∪ nombres`.** Con `E` nombrado como `s`, `s³(s+2)` se parte como `(s·s)|(s·(s+2))` y
baja a grado 2 nombrando además `s²`. Es decir: hay que **tratar cada nombre como un generador de
pleno derecho** y reescribir antes de partir. Eso es lo que queda por implementar, y es un cambio
en `opciones_de`/`intentar`, no en la codificación de la cota.

Consecuencias, todas aplicadas:

| antes | ahora |
|---|---|
| `estado == "optimo"` | `estado == "optimo_del_encoding"` |
| «aplanar mejor es IMPOSIBLE» (test [4]) | «esta cifra es la mejor **construida**, no un mínimo» |
| (46, 5) | **(44, 5)** |

Y una limitación que hay que decir al lado de la cifra siempre: el objetivo del optimizador
minimiza **nombres**, con las 25 incógnitas originales **congeladas**. No puede ni representar
«eliminar una incógnita» —no hay término del objetivo que lo premie—, que es exactamente la jugada
que quita dos. El espacio de búsqueda son 453 subexpresiones con recortes heurísticos codificados a
mano. «20 es óptimo» significa: *mínimo número de nombres que esta codificación sabe certificar,
dentro de ese catálogo, con las originales intactas*. Tres restricciones, ninguna de ellas
mencionada antes al lado de la cifra.

### 3.2h Investigación cerrada: qué existe CONSTRUIDO y qué solo está anunciado

**Construido y exhibible** (escrito o verificado por máquina):

| Polinomio | Variables | Grado | Estado |
|---|---|---|---|
| Jones–Sato–Wada–Wiens 1976 | 26 | 25 | escrito en el paper; reproducido en Wikipedia; **transcrito y verificado aquí** |
| Pąk–Kaliszyk 2022 (Mizar) | 10 | > 6000 | formalizado; *«we present only the non-expanded version»* |
| **Este trabajo** | **46** | **5** | materializado, equivalencia con JSWW **verificada simbólicamente** |

**Anunciado pero sin construcción publicada que hayamos podido encontrar:**

| Cifra | Origen | Qué falta |
|---|---|---|
| (42, 5) | una frase de JSWW 1976, p. 450 | ninguna construcción; el método que citan (Davis p. 263) da **≥ 51** por cota demostrada |
| (58, 4) para primos | par universal de Jones 1982 | la ecuación universal sí es explícita; su **instanciación para primos** no aparece escrita |
| (12, enorme) | JSWW Teorema 2 | *«reportedly known to Matiyasevich in 1973, although no literature is available»* — palabras del propio paper |

**Y hay precedente reconocido en el campo.** Bayer–David, *A Formal Proof of Complexity Bounds on
Diophantine Equations* (ITP 2025), al elegir de qué resultados depender:

> *«the second pair depends on Jones' universal pair (32, 12)ℕ **of which there is no published
> proof in the literature**.»*

En 2025, investigadores del área señalan que **algunos pares anunciados carecen de prueba
publicada** y toman la molestia de no apoyarse en ellos. Que el (42, 5) sea otro caso así no es
una hipótesis excéntrica: es el patrón documentado de esta literatura.

#### ⚠️ Corrección: la afirmación anterior era un EMPATE vendido como récord

Este apartado decía: *«entre los polinomios **representadores** de primos efectivamente
construidos y exhibibles, éste es el de menor grado»*. Una revisión adversarial la **refutó**, y
con razón. Tres errores, todos comprobables con el código de este repo en segundos:

1. **El grado 5 es una MESETA, no un récord.** Aplicar la sustitución de Davis (1973, p. 263) al
   sistema publicado de JSWW da un generador de grado 5 en **3 segundos**. Medido aquí mismo:

   | ruta desde el (1) publicado | generador |
   |---|---|
   | Davis/Skolem textual | (134, 5) |
   | voraz | (56, 5) |
   | árbol | (52, 5) |
   | óptimo del encoding + post-eliminación | **(44, 5)** |

   Los cuatro están «construidos y exhibidos» exactamente en el mismo sentido. Cualquier lector de
   JSWW podía obtener un generador explícito de grado 5 en una tarde desde 1976; que nadie gastara
   páginas del *Monthly* en imprimir 2.000 monomios es un hecho tipográfico, no matemático.

2. **El filtro «solo lo construido» no discrimina nada en el eje del grado.** Ordenados por grado,
   los generadores conocidos son: 5 (42 vars, anunciado), 25 (26, exhibido), 29 (19, anunciado),
   >6000 (10, exhibido), … El filtro elimina **un** elemento, el (42,5), que **empata**. No hay
   nada por debajo de 5, ni construido ni anunciado. Aplicar ahí la distinción
   construido/anunciado —legítima, con precedente en Bayer–David— es retórica: convierte un empate
   en un récord aparente. Donde esa distinción **sí** discrimina es en el eje de variables.

3. **La palabra «representadores» la hundía sola.** Como *representación* —una sola ecuación
   `ΣPᵢ² = 0`— el grado es **4**, no 5, y se obtiene aquí en 2 segundos (45 incógnitas). Y la
   ecuación universal de Jones (1982) también es de grado 4. La frase solo se sostenía leyendo
   «representador» como «generador», que es justo el intercambio de unidades contra el que este
   documento advierte.

**La afirmación que sí se sostiene**, y es sobre el eje de VARIABLES dentro de la meseta de grado:

> *Éste es el generador de primos de grado 5 con **menos variables** que consta construido y
> verificado: **46**, y **47** si no se admite ninguna demostración auxiliar. El grado 5 no es
> nuestro — es el suelo publicado por JSWW en 1976, alcanzable mecánicamente en segundos.*

Con tres salvedades que van siempre pegadas:

1. **JSWW anunciaron 42 < 46.** Si alguien lo construyó alguna vez, somos segundos. La evidencia a
   favor es que el método que citan (Davis, p. 263) da un mínimo demostrado de **51**, así que su
   42 no sale de lo que citan. Pero no haberlo encontrado no prueba que no exista.
2. **Descansa en que el sistema (1) de JSWW represente los primos** — resultado de 1976 con
   cincuenta años de citas y linaje de formalización. No lo hemos verificado nosotros ni hace falta.
3. **Nadie con criterio lo ha revisado.** Sigue siendo la salvedad que más pesa, y la única que no
   podemos levantar por nuestra cuenta.

**Y lo que NO se sostiene:** que sea el de menor grado *y* menos variables. Es una frontera de
Pareto y nuestro punto **no domina** al de JSWW (26, 25): ellos tienen menos variables, nosotros
menos grado. Ninguno es mejor en ambos ejes. Decir las dos cosas sería repetir el error de agosto.

### 3.2f Cierre del ataque al récord: MESETA EN 46, por tres caminos independientes

| Base de partida | Mejor generador | Cómo |
|---|---|---|
| JSWW (1), 26 variables | **46** | aplanado óptimo, cota alcanzada |
| JSWW Teorema 3.9, sustituyendo B, C, S | **46** | 28 base + 17 nombres |
| JSWW Teorema 3.9, búsqueda voraz de sustituciones | **46** | sustituye B y S |
| Teorema 3.9 sin sustituir nada | 49 | nombrar los 14 intermedios sale caro |
| Teorema 3.9 sustituyendo además M y A | 56 | aparecen al cuadrado: ruinoso |
| (1) con eliminación lineal (16 subconjuntos) | 50–65 | siempre peor |

**Tres construcciones independientes convergen a 46.** Eso es más informativo que cualquiera por
separado: sugiere que 46 no es un accidente de una base concreta sino el suelo de esta familia
bajo aplanado óptimo.

**La regla que emergió, y vale más que el número:** *sustituir lo poco profundo, nombrar lo
profundo.* Sustituir `S` —que aparece una vez y tiene definición lineal— gana 2 variables;
sustituir `M` y `A` —que aparecen elevados al cuadrado— cuesta 10. Todo-o-nada era la decisión
equivocada: es una elección **por variable**, y el optimizador la toma mejor que cualquier regla
fija. Es la misma lección que la cota de Pell y el aplanado por árbol, ya en su forma general.

**Lo que haría falta para bajar de 46.** No optimizar mejor (demostrado imposible) ni cambiar a
otra base publicada (probadas las dos de JSWW). Haría falta **una construcción con menos
profundidad algebraica**: el coste no está en las incógnitas de partida —el Teorema 3.9 parte de
10 y acaba igual— sino en cuántos productos anidados hay que desmontar.

### 3.2c Cotejo del récord: **hecho, con fuente primaria**

Con el egreso a arXiv abierto, el (42, 5) queda cotejado. **Jones–Sato–Wada–Wiens,
«Diophantine representation of the set of prime numbers», *Amer. Math. Monthly* 83:6 (1976)
449–464, p. 450**, textual:

> *"Our construction here yields a polynomial in 19 variables and degree 29. **It also yields a
> polynomial in 42 variables and degree 5.** [...] All that is necessary to reduce the degree to 5
> is **the Skolem substitution method**. However, this procedure increases the number of variables
> (**to 42 when applied to (1)**). **We do not know whether there is a prime representing
> polynomial of degree < 5.**"*

Tres consecuencias, y ninguna es cómoda:

1. **El (42, 5) es real y está bien citado.** No era un recuerdo mal transcrito de un resumen.
2. **No es una construcción aparte: es su propio polinomio (1) —26 variables, grado 25— pasado
   por la sustitución de Skolem.** Es decir, exactamente la operación que hace nuestro aplanado.
   Nadie lo optimizó: es «lo que sale al aplicárselo a (1)». Bajar de 42 es, por tanto, menos
   sorprendente de lo que la palabra *récord* sugiere.
3. **Grado < 5 sigue abierto según los propios autores.** Nuestro argumento estructural
   (`deg Q = 1 + 2·max deg Pᵢ`, y un sistema lineal daría un conjunto semilineal) acota **esta**
   construcción, no todas. No contradice a JSWW: dice menos.

Y una cuarta, la que más duele. Su sistema está escrito explícitamente, así que se transcribe
entero (`src/analysis/dioph_jsww.py`) y **se comprueba que reproduce (26, 25)**. Eso da un patrón
de medida externo que **no depende de que nuestra cadena de Wilson sea correcta**: aplicar
nuestro aplanado a *su* sistema y comparar con su 42.

| Aplanado a grado 2 sobre el sistema de JSWW | Incógnitas añadidas | Generador |
|---|---|---|
| voraz, sobre la forma expandida | +30 | (56, 5) |
| Skolem por árbol, sobre la forma expandida | +41 | (67, 5) |
| Skolem por árbol, **sobre la forma factorizada** | **+27** | (53, 5) |
| **JSWW 1976, a mano** | **+16** | **(42, 5)** |

**Vamos 11 incógnitas por detrás de lo que ellos hicieron a mano en 1976.** El aplanado era
entonces la pieza floja, y la brecha pasó a ser un número medido en un test en vez de una
impresión. *(Esa brecha se cerró después: el aplanado óptimo de §3.2d llega a **+20** sobre el
sistema de JSWW, y su +16 resultó no ser comparable — ver §3.2e.)*

> **Aviso sobre una cifra retirada.** Esta sección decía además que nuestro generador «queda por
> debajo de 42 por partir de una representación mucho más barata (31 incógnitas)». Aquella
> representación tenía el índice anclado por congruencia y **admitía valores espurios**: no
> representaba los primos, así que no había nada por debajo de 42. Reconstruida sobre `L_psi`
> (§3.2c-bis) la representación propia cuesta **49** incógnitas y su generador es **(68, 5)**.
> El mejor punto del proyecto, **(44, 5)**, viene de aplanar el sistema *publicado* de JSWW, no
> de nuestra cadena.

*Detalle que cambia el resultado:* expandir destruye el árbol. `flatten_tree` sobre la forma
factorizada gasta 27; sobre la misma expresión expandida, 41. Como `dioph_lemmas` construye
todo con `sympy.expand`, hoy el voraz gana en nuestros sistemas y el de árbol en los de fuera.

**Otras cifras del mismo paper**, ya cotejadas: (19, 29), y el Teorema 2, un polinomio en **12
variables** cuyo grado **sí está publicado: 13.697** (Pąk–Kaliszyk, arXiv:2204.12311, «the rank of
the polynomial is 13,697»; y `13697 = 1+2·6848` confirma que se lee como generador). El de
**10 variables** es de Matiyasevich 1977, y Pąk–Kaliszyk
(ITP 2022, formalización en Mizar) lo llaman *"today the smallest known"* — confirmado en fuente
primaria; su propio polinomio formalizado tiene **grado > 6000**.

**Consistencia interna que sí se puede comprobar.** (42, 5) equivale a una *representación* de
grado 2 en 41 incógnitas, porque el generador es `1 + 2·2 = 5` y `41 + 1 = 42`. Del mismo modo,
JSWW (26, 25) equivale a una representación de grado 12 en 25 incógnitas: `1 + 2·12 = 25`.
Las dos cifras encajan con la construcción estándar, lo que las hace creíbles aunque no cotejadas.

**Por qué el grado 5 es la esquina correcta y no hay que buscar más abajo.** El generador es
`Q = n·(1 − ΣPᵢ²)`, de grado `1 + 2·max deg(Pᵢ)`. Un sistema de grado 1 (lineal) define un
conjunto semilineal, y los primos no lo son; luego `deg Pᵢ ≥ 2` y `deg Q ≥ 5` para esta
construcción. **Aplanar a grado 2 siempre es posible**, así que en esta esquina el único eje
que queda es el número de variables: la partida entera se juega ahí.

### 3.3 Arsenal de Pell verificado (14.752 casos, 0 fallos)

- **P1**: `y_k | y_l ⟺ k | l` y `gcd(y_k,y_l) = y_gcd(k,l)` → convierte índices en divisibilidades
- **P2** (*lema de Matiyasevich*, el más importante): `y_k² | y_l ⟺ k·y_k | l` → hace la sucesión definible
- **P3**: `y_k ≡ k (mod a−1)` → **recupera el índice sin gastar incógnita** (por qué Pell < β)
- **P4**: periodicidad mod x_k → evita espurios
- **P5**: `a ≡ b (mod c) ⟹ y_k(a) ≡ y_k(b) (mod c)`
- **JR**: `(2a−1)^(k−1) ≤ y_k ≤ (2a)^(k−1)` → crecimiento exponencial

---

## 4. Los dos mecanismos duales (y por qué importan)

| | Mecanismo | Efecto | Implementado en |
|---|---|---|---|
| ↓ incógnitas | **Compartición**: relaciones con el mismo exponente comparten (a,x,y,t) | 38 → 29 | `PellContext` |
| ↓ incógnitas | **Eliminación**: sustituir variables definidas (R = E+1) | −1 | `L_prime_shared` |
| ↓ grado | **Aplanado**: nombrar productos v₁·v₂ con incógnitas nuevas | grado 8 → 4, +13 incógnitas | `flatten_to_degree` |
| ↓ grado | **Aplanado voraz**: nombrar primero el producto más frecuente | grado 8 → 4, +11 incógnitas | `flatten_greedy` |

**Principio común:** las sustituciones se **comparten** entre ecuaciones; si un producto aparece
varias veces, una sola incógnita sirve a todas.

---

## 5. Garantías metodológicas (lo que NO se debe relajar)

1. **Verificar la matemática ANTES de implementar.** Cada identidad se comprueba numéricamente en
   cientos o miles de casos antes de escribir el lema. Así se cazaron todos los errores.
2. **Testigo constructivo, no búsqueda.** La completitud se prueba *construyendo* el testigo y
   *evaluando* el sistema.
3. **La soundness se DEMUESTRA, no se declara.** Construir el testigo verifica la completitud
   y nada más. Para la dirección inversa hay que probar que **no existe solución**, y eso ninguna
   búsqueda lo hace: las incógnitas viven en rangos astronómicos. Se usa un demostrador SMT
   (`dioph_soundness.solve`), que devuelve tres estados y los tres se reportan tal cual:
   `unsat` (demostrado), `sat` (**defecto**, con modelo) y `unknown` (**no es evidencia de nada**).
   Un `unsat` con cota solo vale dentro de la caja, y el informe lo dice (`unsat<=200`).
   *Ninguna cifra de coste vale sin su veredicto.*
4. **Ambas direcciones o declararlo.** `DiophProblem.soundness` vale `'exhaustivo'` (la dirección
   inversa se comprueba por búsqueda) o `'teorema'` (el constructor cortocircuita con el oráculo,
   luego comprobarla sería **circular**; descansa en la referencia). **Nunca presentar 'teorema'
   como si fuera 'exhaustivo'.**
5. **`sys.exit(1)` en fallo.** El proyecto ya tuvo tests que fallaban y salían con 0.

---

## 5.bis LA ESQUINA DE VARIABLES — arranque

Dual exacto del aplanado: aplanar baja el grado introduciendo nombres; **eliminar quita incógnitas
a costa de subirlo**. Sobre el sistema (1) de JSWW, cuatro incógnitas están linealmente determinadas
con miembro derecho de **coeficientes todos positivos** —luego ≥ 0 sobre ℕ automáticamente, y la
equisatisfacibilidad vale en las dos direcciones sin ninguna suposición—:

```
e = 2n + p + q + z          (α₂)        y = l + n + v            (α₈)
q = h + j + w·z             (α₀)        z = (gk+2g+k+1)(h+j) + h  (α₁)
```

| Eliminaciones | Incógnitas | Grado ec. | **Generador** | Literatura |
|---|---|---|---|---|
| `e, q, y` | 22 | 12 | **(23, 25)** | JSWW **publican** (26, 25) — 3 variables menos, mismo grado |
| `+ z` | 21 | 18 | **(22, 37)** | Matiyasevich 1971 **anuncia** (24, 37) — 2 menos |

**Lo llamativo es lo barato que es.** Son sustituciones lineales: no hay optimización, ni SMT, ni
nada de la maquinaria que costó esta sesión. Que no estuvieran escritas encaja con el patrón ya
documentado —estas cifras se anunciaban, no se exhibían—, pero conviene no deducir de ahí más de lo
que hay: **es una operación elemental**, y si algo dice es que el terreno está menos peinado de lo
que parece.

**Lo que NO mejora:** el (19, 29) que JSWW también anuncian. Por esta vía se llega a (24, 29), cinco
por encima. Esa es la cifra a batir en esta esquina.

**Dónde se agota y dónde sigue.** Tras eliminar las cuatro no quedan más eliminaciones gratis. Las
que quedan —`l`, `m`, `p`, `x`— tienen coeficientes negativos en su miembro derecho, así que
exigirían **demostrar su no-negatividad**, exactamente el mismo patrón que en la esquina de grado
(§3.2n), donde una de esas demostraciones resultó ser un corolario de una línea y bajó la cifra.

**Actualización: `l` queda desbloqueada.** Se demostró `a ≥ 2` (§3.2o) y, reparametrizando
`a = A+2`, el miembro derecho de α₁₁ pasa a `k+1+i(A+1)`, todo positivo. Eso añade dos puntos:

| Eliminaciones | **Generador** | Literatura |
|---|---|---|
| `l, q, y, z` | **(22, 29)** | **dominado** por el (19, 29) que JSWW anuncian |
| `+ e` | **(21, 37)** | **dominado** por el mismo (19, 29) |

Se anotan porque medirlos costó lo mismo, pero **no son récord**: el (19, 29) los supera en los dos
ejes. Presentarlos como mejora sería quedarse con la comparación que favorece —«a igual grado»—
ignorando que existe un par mejor en ambas coordenadas. La `l` sí paga, y mucho, en la **otra**
esquina: es parte de lo que llevaba el grado 5 de (38,5) a (33,5) — dos cifras **retiradas** (§2.bis),
así que lo que sigue vale como registro del razonamiento, no como cifra.

**Intento de desbloquear las cuatro restantes: FALLIDO, con la frontera medida.** Eliminar `m` o
`x` exigiría demostrar `a > n` y `a > p` —las mismas condiciones que bloquean la esquina de grado—,
así que se atacó con SMT sobre subsistemas, que es lo tratable:

| Hipótesis | `a > n` | `a > p` |
|---|---|---|
| 6 ecuaciones (α₅,α₈,α₉,α₁₀,α₁₁,α₁₂) | contraejemplo `a=0` | contraejemplo `a=0` |
| las mismas + `a ≥ 2` | contraejemplo `a=2, n=2, p=3` | contraejemplo `a=2, n=0, p=1` |
| **+ α₃ (7 ecuaciones)** | **Z3 no concluye** | **Z3 no concluye** |

Lectura correcta, que no es «es falso»: los contraejemplos son soluciones **del subsistema**, no del
sistema completo —el primero viola α₃ de inmediato—. Lo que dicen es que esas seis ecuaciones **no
bastan** para forzarlo. Y en cuanto se añade la séptima, Z3 deja de concluir en ninguna dirección.

La frontera es nítida: **con 6 ecuaciones hay contraejemplo, con 7 no hay respuesta**. La vía queda
**bloqueada por herramienta, no refutada**. Si se quiere abrir, hay que derivar `a > n` a mano de las
ecuaciones del sistema completo, igual que se hizo con `a + u²(u²−a) ≥ 1`.

**Y el marco general, que no cambia:** el récord de esta esquina es **9 incógnitas / 10 variables**
(Matiyasevich 1977), y a diferencia del (42,5) **está construido y formalizado en Mizar**. Lleva 48
años sin moverse. Nuestra cadena propia está en 49 incógnitas. El objetivo realista no es batir 9
sino bajar sustancialmente de ahí, y la palanca identificada sigue siendo el **Teorema de
Combinación de Relaciones** (§6.1), aún sin implementar.

## 6. Frontera abierta (dónde retomar)

### 6.1 Hacia pocas incógnitas (esquina de 9)
- **Punto de partida real: 49 incógnitas** en la representación propia (la anclada por `L_psi`;
  el esqueleto de 29 no representa los primos y no cuenta como punto de partida).
- **Bloqueante:** la compartición por exponente común está **agotada**. Bajar de ahí exige
  reestructurar la construcción, no encadenar Wilson→factorial→binomial.
- **El motor real, aún NO implementado:** *Teorema de Combinación de Relaciones*
  (Matiyasevich–Robinson): para todo q>0 existe M_q tal que
  `S|T ∧ R>0 ∧ A₁…A_q cuadrados ⟺ ∃n: M_q(A₁…A_q,S,T,R,n)=0`.
  Convierte q condiciones en **una ecuación al coste de UNA incógnita**. Es la única pieza que
  reduce el conteo.
- **Aviso:** debe implementarse como constructor **simbólico** (straight-line program), nunca
  expandiendo monomios: el grado resultante es ~10⁴⁵.
- **Observación nueva, y prometedora para esta esquina.** `L_psi` cuesta 11 incógnitas por
  exponente distinto, y la cadena usa dos exponentes. Si la reestructuración logra **un solo
  exponente**, no ahorra un contexto de Pell (3) sino **13**. El anclaje del índice, que en la
  esquina de grado bajo es un gasto molesto, en la esquina de pocas incógnitas es la palanca
  principal: el coste está concentrado, no repartido.

### 6.2 Hacia grado bajo — el grado está cerrado; el **número de variables no**
- El grado ya está en la esquina mínima (5 como generador) y **ahí se queda**: aplanar a grado 2
  siempre es posible, y por debajo de 2 el conjunto sería semilineal. Toda la partida en esta
  esquina es **número de variables**.
- Y esa partida **sigue abierta**, con evidencia directa: el «óptimo» del optimizador ha caído
  tres veces —46 → 17 → 15 nombres— y las tres por **ampliar el catálogo**, nunca por buscar mejor.
  No hay motivo para creer que el catálogo esté completo ahora. Lo que queda por probar:
  candidatos que aún no están (¿productos de subsumas? ¿reescrituras encadenadas?). Las
  no-negatividades que bloqueaban las tres eliminaciones restantes ya **no** son el cuello de
  botella: se siguen de `a ≥ e+1` (§2.ter), y Pell está demostrado, no citado.
- **Dos puntos, y no son el mismo:**

  | ruta | punto | estado |
  |---|---|---|
  | eliminar sobre el sistema **publicado** de JSWW 1976 | **(23, 25)** | 3 variables menos que el (26,25) publicado; **formalizado en Lean** (§2.ter). No es un mínimo |
  | lo mismo, usando además `a ≥ e+1` | **(21, 25)** | 5 menos, **también formalizado**: los tres teoremas de Pell que sostienen la cota se demuestran en `Pell.lean` (§2.ter) |
  | cadena **propia** anclada por `L_psi` | **(68, 5)** | óptimo del *encoding* del aplanado (18 nombres, cota 18) |

  La primera es el mejor punto del proyecto y la que se compara con la literatura (§3.2f–h). La
  segunda mide otra cosa: **lo que cuesta la representación que el cálculo obtiene por su cuenta**.
  Mezclarlas sería el error de agosto en otra forma.
- **De dónde vienen las 68.** 49 de la representación + 18 nombres del aplanado + 1 del parámetro.
  De las 49, **22 son los dos `L_psi`** (11 por exponente): casi la mitad del gasto está en anclar
  el índice. Eso no es un defecto de la implementación, es el precio del teorema; pero señala
  dónde mirar.
- **Palancas que quedan, en orden de rendimiento esperado:**
  1. **Menos exponentes distintos.** No menos exponenciaciones —compartir por exponente común ya
     está hecho— sino menos *exponentes*: cada uno cuesta un `L_psi` entero. Ya se ganó uno al
     tomar `E = n^(n-1)` y `R = n·E+1` en vez de `E = n^n`. Queda uno.
  2. **Una ruta al factorial que no pase por el binomial de Robinson**, que es quien introduce el
     segundo exponente (`r`, con `T = 2^r` y `W = (u+1)^r`).
  3. **Un anclaje del índice más barato que `L_psi`.** La construcción clásica de Davis (1973)
     ronda las mismas 11–12 incógnitas, así que no hay ganancia evidente — y `L_psi` tiene a su
     favor estar **formalizado en Mizar**, que en un resultado así vale más que una incógnita.
- **Regla no negociable:** ninguna cifra vale sin su veredicto de `dioph_soundness`. La (41,5)
  de agosto venía de un sistema que Z3 refuta, y la (40,5) que la siguió venía de un lema
  exponencial que admitía valores espurios.

### 6.3 Puente entre las dos islas del repo
El proyecto tiene dos subsistemas maduros **sin un solo import entre ellos**: el colapso de
trazas (β, dominancia de dígitos) y el cálculo diofántico. La técnica es la misma matemática,
pero `check_beta_trajectory` **ejecuta** un bucle `for i in range(T)` — el cuantificador acotado
se evalúa en vez de eliminarse. Construir ese puente es trabajo pendiente.

---

## 7. Lo que NO se puede afirmar (para no repetir la historia de la "Ecuación Suprema")

- **No se ha batido ningún récord, y ahora sabemos que ni siquiera se medía lo que parecía.**
  El lema exponencial admite valores espurios (§3.2b): la cadena de primos no es sound y las
  cifras del generador quedan retiradas. Para que eso fuera un récord harían falta tres
  cosas que NO tenemos: (a) ~~el (42, 5) cotejado contra fuente primaria~~ **hecho** (§3.2c); (b) la corrección de la cadena verificada más allá de n=3, donde el testigo deja de ser
  computable; (c) revisión experta. Mientras falte cualquiera de las tres, es **un punto medido
  en nuestra curva**, no un resultado.
- **Y un aviso concreto:** en agosto este documento decía (41, 5) y era un sistema **insound**
  que habría emitido compuestos. El número de ahora es distinto porque el sistema es distinto,
  no porque se haya afinado la cuenta.
- **La lección, otra vez:** el error no se detectó con más tests de testigos, sino cambiando de
  pregunta. La completitud se verifica construyendo; la soundness exige **demostrar ausencia**,
  y eso solo lo da un demostrador. Cualquier cifra futura debe venir acompañada del veredicto
  SMT correspondiente.
- Los números famosos de primos (**JSWW: 26 variables, grado 25**; y la versión de 10 variables)
  son **GENERADORES** (sus valores positivos son los primos). Lo nuestro es una **REPRESENTACIÓN**
  (∃ testigo ⟺ n primo). **Son objetos distintos**; convertir uno en otro cambia el grado. Comparar
  las cifras directamente sería un error.
- Cotejar si algún punto de nuestra curva es notable exige **fuentes primarias** (bloqueadas en
  este entorno por la política de egreso) y **revisión experta**.
- La corrección de la cadena de primos descansa en teoremas citados (Wilson, Robinson,
  Matiyasevich), no en el cómputo: **el testigo explota** (n=6 exigiría ~2×10¹¹ dígitos), así que
  solo se verifica hasta n=3.

---

## 8. Cómo ejecutar

```bash
# dependencias
pip install sympy mpmath z3-solver libclang
ln -sf /usr/lib/llvm-18/lib/libclang-18.so.1 /usr/lib/x86_64-linux-gnu/libclang.so

# suite completa
python src/tests/verification/run_verification_suite.py

# solo el cálculo diofántico
python src/tests/verification/test_dioph_pell.py       # arsenal de Pell
python src/tests/verification/test_dioph_calculus.py   # lemas y coste
python src/tests/verification/test_dioph_problems.py   # catálogo universal
python src/tests/verification/test_dioph_degree.py     # reducción de grado
```

Estado de la suite al cerrar: **47 PASS · 0 SKIP · 1 FAIL** (el FAIL es el bug preexistente de
fusión de tail-calls en `collatz_trajectory`, ajeno a este trabajo).

---

## 9. Cómo añadir un conjunto nuevo al catálogo

```python
# en src/analysis/dioph_problems.py
def _p_mi_conjunto():
    n = sympy.Symbol('n', integer=True)
    r = fresh("x")
    sysm = Dioph([n], [r], [sympy.expand(<ecuacion>)],
                 witness=lambda v: {r: <valor calculado>} or None,
                 name="mi conjunto")
    return DiophProblem("mi conjunto", n, sysm,
                        oracle=<criterio independiente>,   # NO derivado del sistema
                        referencia="<fuente>", search_bound=<cota>)
# y anadirlo a build_catalog()
```

El verificador único y la reducción de grado funcionan sobre él **sin tocar nada más**.
