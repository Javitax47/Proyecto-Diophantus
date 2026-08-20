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

| Lema | Antes (insound) | **Ahora (sound)** | Verificación previa |
|---|---|---|---|
| `L_divides`, `L_congruent`, `L_square` | 1 | 1 | elemental |
| `L_composite` | 2 | 2 | elemental |
| `L_nonneg` (Lagrange, sobre ℤ) | 4 | 4 | 200 enteros |
| `L_nonneg_N` (sobre ℕ) | **0 ⚠️ siempre** | **0** si todos los coeficientes son ≥ 0; **1** en otro caso | — |
| `L_exponential` (Pell) | 5 | **7** (13 sobre ℤ) | 1368 casos |
| `L_binomial` | 21 | **27** | 209 casos |
| `L_factorial` | 36 | **46** | n=1..7 |
| `L_prime` (Wilson, aditivo) | 38 | **50** | Wilson en [2,250) |
| `L_prime_shared` (compartido) | 29 | **31** | ídem |

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

**Siguiente paso concreto.** Para bajar de 47 hace falta algo con MEMORIA, no más muestreo ciego:
búsqueda por haz sobre la secuencia de nombres, o —lo que encaja con la maquinaria que ya hay—
**codificar el aplanado mínimo como problema de optimización y pasárselo a Z3 o al exportador
QUBO**. «Elegir el conjunto mínimo de productos que reduce todos los monomios a grado ≤ 2» es un
problema tipo cobertura, y el proyecto ya tiene ambos backends.

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

**Vamos 11 incógnitas por detrás de lo que ellos hicieron a mano en 1976.** Nuestro generador de
primos queda por debajo de 42 **por partir de una representación mucho más barata** (31 incógnitas
y grado 4, frente a sus 25 y grado 12), **no por aplanar mejor**. El aplanado es hoy la pieza
floja, y ahora la brecha es un número medido en un test, no una impresión.

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
- **Bloqueante:** la compartición por exponente común está **agotada**. Bajar de 29 exige
  reestructurar la construcción, no encadenar Wilson→factorial→binomial.
- **El motor real, aún NO implementado:** *Teorema de Combinación de Relaciones*
  (Matiyasevich–Robinson): para todo q>0 existe M_q tal que
  `S|T ∧ R>0 ∧ A₁…A_q cuadrados ⟺ ∃n: M_q(A₁…A_q,S,T,R,n)=0`.
  Convierte q condiciones en **una ecuación al coste de UNA incógnita**. Es la única pieza que
  reduce el conteo.
- **Aviso:** debe implementarse como constructor **simbólico** (straight-line program), nunca
  expandiendo monomios: el grado resultante es ~10⁴⁵.

### 6.2 Hacia grado bajo — **la esquina está cerrada; queda validarla**
- El grado ya está en la esquina mínima (5 como generador) y **ahí se queda**: aplanar a grado 2
  siempre es posible, y por debajo de 2 el conjunto sería semilineal. Toda la partida en esta
  esquina es **número de variables**.
- **Punto actual: (40, 5). Récord citado: (42, 5).** Dos variables por debajo. Con las salvedades
  de §3.2c y §7 — que son las que impiden llamarlo récord.
- **Qué queda del gasto** (31 incógnitas de la representación): 8 valores de la cadena
  (m, Eᵥ, A, Tᵥ, W, P, B) + 1 base de Pell + 9 por exponente (x, y, t × 3) + 5 multiplicadores
  de relación + 3 holguras de desigualdad + 2 restos de división + 1 multiplicador. El aplanado
  añade 9: tres ecuaciones de Pell (grado 4) y cuatro congruencias de Davis (grado 3).
- **Palancas que quedan, en orden de rendimiento esperado:**
  1. **Aplanado óptimo en vez de voraz.** Elegir qué productos nombrar es optimización
     combinatoria (como *common subexpression elimination*); el mínimo teórico son ~7 y el voraz
     gasta 9.
  2. **Menos exponenciaciones.** Son cinco (Eᵥ, A, Tᵥ, W, P) y cada una cuesta x,y,t o un
     multiplicador. Una ruta al factorial que no pase por el binomial de Robinson las reduciría.
  3. **Teorema de Combinación de Relaciones** (§6.1): la pieza que reduce el conteo de verdad,
     y sigue sin implementar. Es la vía a la OTRA esquina (pocas incógnitas), no a esta.
- **Regla no negociable:** ninguna cifra vale sin su veredicto de `dioph_soundness`. La (41,5)
  de agosto venía de un sistema que Z3 refuta.

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
