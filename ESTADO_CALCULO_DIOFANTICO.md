# Estado del Cálculo Diofántico — documento de reanudación

> **Propósito:** que cualquiera (incluido tu yo futuro) pueda retomar este trabajo sin releer
> la conversación. Contiene qué existe, qué está verificado, con qué números, qué se aprendió
> y cuál es el siguiente paso.
> Última actualización: agosto 2026.

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

## 3. Números medidos (el marcador)

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
| El aplanado es el mínimo | `z3.Optimize` alcanza su **cota inferior**: 20 nombres. No es «lo mejor que encontré» |
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

- **No hemos batido el récord publicado.** El récord citado es (42, 5) y estamos en (46, 5).
  Lo que sí tenemos es que **el (42, 5) no aparece construido en ningún sitio** y que el método
  que sus autores citan da, como mínimo demostrado, **51**.
- **Nadie con criterio lo ha revisado.** Sigue siendo la salvedad que más pesa.

**La afirmación honesta, entonces**, no es «tenemos un récord» sino: *este es un polinomio de
grado 5 representador de primos, explícitamente construido, con 46 variables, cuya reducción es
demostrablemente mínima, cuya equivalencia con el sistema de JSWW está verificada simbólicamente y
en el que **cada incógnita añadida es demostrablemente no negativa**.* Si el (42, 5) nunca se
construyó, sería el mejor construido. Eso es exhibible y comprobable por cualquiera; una frase de
1976 no lo es.

**Y conviene decir qué NO es un récord aquí: el grado 5 no lo es.** El grado 5 lo anunciaron JSWW
en 1976. No hemos bajado de 5 ni podríamos con esta construcción —el argumento de §3.2c lo cierra
para la familia `n·(1−ΣP²)`—. Lo único que puede reclamarse es la **exhibición**: tener escrito un
polinomio de grado 5 que genera los primos, cosa que hasta donde alcanza la búsqueda nadie había
publicado.

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
   | óptimo demostrado | **(46, 5)** |

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
> El mejor punto del proyecto, **(46, 5)**, viene de aplanar el sistema *publicado* de JSWW, no
> de nuestra cadena.

*Detalle que cambia el resultado:* expandir destruye el árbol. `flatten_tree` sobre la forma
factorizada gasta 27; sobre la misma expresión expandida, 41. Como `dioph_lemmas` construye
todo con `sympy.expand`, hoy el voraz gana en nuestros sistemas y el de árbol en los de fuera.

**Otras cifras del mismo paper**, ya cotejadas: (19, 29), y el Teorema 2, un polinomio en **12
variables** de grado enorme. El de **10 variables** es de Matiyasevich 1977, y Pąk–Kaliszyk
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

### 6.2 Hacia grado bajo — **la esquina está cerrada; queda validarla**
- El grado ya está en la esquina mínima (5 como generador) y **ahí se queda**: aplanar a grado 2
  siempre es posible, y por debajo de 2 el conjunto sería semilineal. Toda la partida en esta
  esquina es **número de variables**.
- **Dos puntos, y no son el mismo:**

  | ruta | punto | estado |
  |---|---|---|
  | aplanar el sistema **publicado** de JSWW 1976 | **(46, 5)** | óptimo demostrado; meseta por tres caminos independientes |
  | cadena **propia** anclada por `L_psi` | **(68, 5)** | óptimo demostrado del aplanado (18 nombres, cota 18) |

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
