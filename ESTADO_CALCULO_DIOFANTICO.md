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
| **Demostrar las no-negatividades restantes** | cada una puede quitar un nombre | **1 de 5 resuelta** (§3.2n, corolario) y dio (41,5). Quedan 4; Z3 **no concluye** sobre grado 12 en 26 variables |
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

### 6.2 Hacia grado bajo — **la esquina está cerrada; queda validarla**
- El grado ya está en la esquina mínima (5 como generador) y **ahí se queda**: aplanar a grado 2
  siempre es posible, y por debajo de 2 el conjunto sería semilineal. Toda la partida en esta
  esquina es **número de variables**.
- **Dos puntos, y no son el mismo:**

  | ruta | punto | estado |
  |---|---|---|
  | aplanar el sistema **publicado** de JSWW 1976 | **(44, 5)** | mejor cifra construida; **no** un mínimo demostrado (§3.2i) |
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
