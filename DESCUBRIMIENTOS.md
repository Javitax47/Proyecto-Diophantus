# Descubrimientos matemáticos: qué puede encontrar el proyecto, además de pruebas de irracionalidad

> Octubre 2026. Complemento de `AUDITORIA.md` y `PROPUESTAS.md`, centrado en descubrimiento
> matemático: crear criterios o ecuaciones propias "tipo Wilson", cosas curiosas y pedagógicas, e
> información nueva. Las dos primeras herramientas ya existen y funcionan
> (`descubrimientos/criterios_clasicos.py` y `descubrimientos/criterios_perrin.py`).

---

## 0. Respuesta corta

No, la irracionalidad no es la única vía. Por orden de lo que creo que vale:

| Vía | Qué saldría | Valor científico | Valor pedagógico | Estado |
|---|---|---|---|---|
| **1. Criterios de primalidad propios ("tu Wilson")** | Criterios nuevos, sus falsos positivos, récords | Medio: conjeturas nuevas y secuencias para OEIS | **Muy alto** | **Funcionando** |
| **2. Polinomios que generan conjuntos famosos** | Fibonacci, potencias de 2, primos de Mersenne, números perfectos… exhibidos y verificados | Medio: exhibir lo que sólo está anunciado | **Muy alto** | Maquinaria del paper lista |
| 3. Fórmulas cerradas aritméticas | Fórmulas para funciones aritméticas (como el n-ésimo primo) | Medio, línea de investigación activa | Alto | Por hacer |
| 4. Identidades y fracciones continuas | Conjeturas tipo Ramanujan Machine | Medio, campo competido | Alto | Conjeturador validado |
| 5. Secuencias nuevas para OEIS | Pseudoprimos de criterios nuevos, invariantes | Bajo-medio, pero publicable y citable | Medio | Sale de 1 y 6 |
| 6. Mapas integrables nuevos | Sistemas dinámicos discretos con cantidad conservada | Medio, nicho | Medio | Motor de invariantes validado |
| 7. Irracionalidad (Catalan, ζ(5)) | Una prueba nueva | Altísimo si sale | Medio | Validado; probabilidad baja |

---

## 1. Tu propio Wilson: criterios de primalidad

### 1.1 El tipo de problema que hay que buscar

El teorema de Wilson dice: **n es primo si y sólo si (n−1)! ≡ −1 (mod n)**. Lo valioso de un
criterio así es el "si y sólo si". La mayoría de los criterios conocidos sólo funcionan en una
dirección: todo primo los cumple, pero también algunos compuestos (los *pseudoprimos*).

Y hay un tipo intermedio, que es exactamente "un Wilson nuevo que nadie ha conseguido demostrar":
criterios en los que **"primo ⇒ se cumple" es un teorema, y "se cumple ⇒ primo" es una conjetura
abierta**, porque nadie ha encontrado ningún compuesto que lo cumpla:

| Criterio | Desde | Estado |
|---|---|---|
| **Giuga:** Σ_{k=1}^{n−1} k^(n−1) ≡ −1 (mod n) | 1950 | Abierto. Un contraejemplo tendría al menos ~13.900 cifras |
| **Lehmer:** φ(n) divide a n − 1 | 1932 | Abierto. Un contraejemplo tendría que ser número de Carmichael |
| **Recíproco de Wolstenholme:** C(2n−1, n−1) ≡ 1 (mod n³), n > 3 | — | Abierto. Comprobado hasta 10⁹ |

Encontrar un criterio **nuevo** de este tipo —con un "si y sólo si" que resista hasta números
enormes y no sea un disfraz de uno conocido— sería una conjetura nueva, publicable. Demostrarlo
sería "un Wilson propio".

### 1.2 El cazador, parte 1: el catálogo

`descubrimientos/criterios_clasicos.py` comprueba los criterios conocidos para todo n ≤ 3.000:

| Criterio | Resultado hasta 3.000 | Lo que se sabe |
|---|---|---|
| Wilson | caracteriza | Teorema |
| Fermat, base 2 | **falla en 341** | Primer pseudoprimo de Fermat |
| Lucas-Fibonacci | **falla en 323** | Primer pseudoprimo de Fibonacci |
| Giuga | caracteriza | Conjetura abierta |
| Lehmer | caracteriza | Conjetura abierta |
| Babbage (módulo n²) | caracteriza | **Falla en 16.843² = 283.686.649**, mucho más allá de 3.000 |
| Recíproco de Wolstenholme | caracteriza | Conjetura abierta |

La fila de Babbage es la lección: **comprobar hasta N no es demostrar**. Un criterio puede parecer
perfecto durante cientos de millones de números.

### 1.3 La trampa de Perrin

La sucesión de Perrin (3, 0, 2, 3, 2, 5, 5, 7, 10, …, en la que cada término es la suma de los que
están dos y tres posiciones antes) cumple que **si n es primo, n divide a P(n)**. Durante casi un siglo pareció que el
recíproco también era cierto. Hasta 1982: el primer compuesto que lo cumple es **271.441 = 521²**.
El cazador lo reproduce en 1,8 segundos: hasta 300.000, el único compuesto que pasa el test es ése.

Es el ejemplo perfecto para enseñar por qué en matemáticas no basta con comprobar muchos casos.

### 1.4 El cazador, parte 2: la familia de Perrin

Perrin es sólo un caso de una familia entera. Cada polinomio cúbico x³ − ax² − bx − c con
coeficientes enteros da una sucesión (la suma de las potencias n-ésimas de sus raíces) que cumple
"n primo ⇒ s(n) ≡ a (mod n)". Cada polinomio es un criterio candidato, y hay una pregunta medible:
**¿cuál tarda más en fallar?**

`descubrimientos/criterios_perrin.py` lo calcula para todos los n a la vez con numpy. Barrido de los
**100 cúbicos con coeficientes entre −2 y 2**, hasta 300.000:

| Polinomio | Primer falso positivo | Falsos positivos ≤ 300.000 |
|---|---:|---:|
| x³ − x − 1 (**Perrin**) | **271.441** | 1 |
| x³ − x + 1 (su espejo) | **271.441** | 1 |
| x³ + x² + 2x − 2 | 43.707 | 3 |
| x³ + x − 2 | 3.745 | 5 |
| x³ + x + 2 | 3.745 | 5 |
| x³ − x² − x + 2 | 1.085 | 7 |
| … | … | … |
| x³ + x² − 2 | 561 (el primer número de Carmichael) | 62 |

Conclusión medida: **entre los 100 cúbicos más pequeños, Perrin es el campeón**, y por mucho: el
segundo falla seis veces antes. Todos los primos cumplen todos los criterios, como dice el teorema,
lo que comprueba que el cálculo es correcto.

**Barrido ampliado a los 648 cúbicos con coeficientes entre −4 y 4** (848 s), hasta 300.000:

| Polinomio | Primer falso positivo | Falsos positivos ≤ 300.000 |
|---|---:|---:|
| x³ − x − 1 (**Perrin**) y su espejo | **271.441** = 521² | 1 |
| **x³ − x² + 3x − 4** | **269.011** = 367 × 733 | 1 |
| x³ + x² + 2x − 2 | 43.707 | 3 |
| x³ + 2x² + 2x − 3 | 42.559 | 2 |
| x³ + x² − 2x − 3 | 9.996 | 3 |

Perrin sigue siendo el campeón, pero **aparece un segundo polinomio prácticamente empatado**,
x³ − x² + 3x − 4 (irreducible, discriminante −331; el de Perrin es −23), muy por delante del resto.
Y si se mira más lejos, **falla menos que Perrin**: hasta 2.000.000, Perrin tiene dos falsos
positivos (271.441 y 904.631, que es el segundo pseudoprimo de Perrin conocido, así que el cálculo
cuadra) y este polinomio **sólo uno** (269.011).

Curiosidad sin relación aparente: 269.011 también es un pseudoprimo fuerte en base 61 (está en la
OEIS, A020287).

**Lo que esto es y lo que no.** Es un dato curioso y medido. **No puedo afirmar que sea nuevo**: no
encontré ninguna fuente sobre este polinomio concreto, pero el marco está muy estudiado (Adams y
Shanks, 1982; Adams, 1987; Gurak, 1990) y hay un trabajo reciente dedicado justo a fabricar tests
tipo Perrin (Dougherty-Bliss y Zeilberger, 2023). Antes de publicarlo como hallazgo hay que cotejarlo
con ese trabajo. Si no estuviera, la secuencia de falsos positivos de este polinomio sería una
entrada candidata para la OEIS.

La tabla, en esta forma exacta, no la he encontrado publicada; pero el problema está estudiado (ver
arriba), así que es probable que buena parte se conozca.

### 1.5 Qué haría falta para que fuera un descubrimiento

1. **Ampliar el espacio**: cuárticos y quínticos, coeficientes mayores, y otras familias (sumas de
   potencias tipo Giuga con exponentes distintos, combinaciones de binomiales y factoriales).
2. **Ampliar N** a 10⁸ o 10⁹ para los supervivientes, con la misma vectorización por bloques.
3. **Filtrar los disfraces.** Hay infinitas formas de escribir Wilson: ((n−1)!)² ≡ 1, (n−2)! ≡ 1… El
   cazador debe detectar automáticamente cuándo un candidato es equivalente a uno conocido.
4. **Cotejar con la literatura y la OEIS** antes de afirmar nada.

Lo que podría salir, de más a menos probable:

- **Secuencias nuevas para OEIS**: los falsos positivos de cada criterio forman una secuencia. Si no
  está, es una contribución pequeña pero real y citable.
- **Un criterio que aguante más que Perrin**: un dato curioso y posiblemente nuevo. Ya hay un
  candidato que falla *menos* que Perrin hasta dos millones (arriba), aunque falla un poco antes.
- **Una conjetura nueva** tipo Giuga: un criterio sin contraejemplos hasta números enormes.
- **Demostrarla**: sería un Wilson propio. Muy improbable si no es equivalente a algo conocido.

---

## 2. Polinomios que generan conjuntos famosos

Es la línea del paper, aplicada a otros conjuntos. La pregunta de fondo es preciosa: **¿qué
polinomio tiene como valores positivos exactamente los números de Fibonacci, o las potencias de 2,
o los números perfectos?**

- **Fibonacci** (Jones, 1975): los valores positivos de **y·(2 − (y² − yx − x²)²)**, con x, y ≥ 0,
  son exactamente los números de Fibonacci. Sólo **2 variables y grado 5**. Comprobado aquí: con
  x, y < 400 salen 1, 2, 3, 5, 8, 13, …, 377 y ningún otro valor. Es una joya para enseñar.
- **Primos de Mersenne y de Fermat**: Jones, 1979. Existen.
- **Números perfectos pares**: son 2^(p−1)·(2^p − 1) con 2^p − 1 primo, así que salen de los de
  Mersenne. En una búsqueda rápida no encontré un polinomio escrito; si no existe, exhibirlo y
  verificarlo en Lean sería un resultado del mismo tipo que el paper.
- **Potencias de 2, cuadrados, triangulares**: el catálogo del proyecto (`dioph_problems`) ya los
  tiene; falta medir su frontera de Pareto (variables frente a grado) como se hizo con los primos.

**Producto pedagógico:** un atlas de polinomios generadores verificados, con un explorador
interactivo: eliges x e y y ves salir números de Fibonacci, primos o perfectos.

---

## 3. Fórmulas cerradas aritméticas

Hay una línea de investigación activa sobre **términos aritméticos cerrados**: fórmulas construidas
sólo con suma, resta, producto, división entera y potencias, que calculan funciones como el
factorial o cuentan los primos de Mersenne, de Fermat y los primos gemelos (Prunescu, 2025). Es
"una fórmula propia" en sentido literal, y el puente entre representaciones diofánticas y fórmulas
cerradas es justo la especialidad de este proyecto.

---

## 4. Identidades y fracciones continuas

El conjeturador, al estilo de la Ramanujan Machine, encuentra fracciones continuas que coinciden con
constantes (π, e, ζ(3), Catalan) a cientos de cifras. La irracionalidad es sólo un subproducto. Lo
principal son **conjeturas de identidades nuevas**. El campo está competido: antes de afirmar
novedad hay que cotejar con la base de datos de la Ramanujan Machine.

---

## 5. Mapas integrables

El motor de invariantes encuentra cantidades conservadas en mapas polinómicos (`x² − 2y²` en Pell,
la ecuación de Markov). Recorrer familias de mapas buscando nuevos integrables es investigación real
en sistemas dinámicos discretos, de nicho, y con un verificador que certifica cada hallazgo.

---

## 6. Piezas curiosas y pedagógicas que ya existen

1. **"factorial(7) = 7 en los complejos"**: una solución exacta del polinomio del factorial con un
   número imaginario (`auditoria/complejo.py`). Explica por qué el plano complejo engaña.
2. **La trampa de Perrin**: 271.441 (`descubrimientos/criterios_perrin.py`).
3. **Un polinomio de grado 5 cuyos valores positivos son exactamente los primos**: el (44, 5) del
   paper, escrito entero y verificado en Lean.
4. **Fibonacci en 2 variables**: el de Jones, verificado.
5. **El bug que estuvo años en Java**, encontrado en 24 ms (`propuestas/poc_brecha_semantica.py`).

Juntas darían una exposición o una charla divulgativa con un hilo conductor: lo que pasa cuando
conviertes números y programas en ecuaciones.

---

## 7. Orden que propongo

1. **Ampliar el cazador de criterios** (1.5): es lo más divertido, lo más pedagógico y lo que antes
   puede dar información nueva (secuencias para OEIS). Semanas.
2. **Atlas de polinomios generadores** (§2), empezando por números perfectos. Reutiliza todo lo del
   paper. Semanas a meses.
3. **Exposición pedagógica** (§6) como página web interactiva. Días, cuando lo anterior esté listo.
4. En paralelo y sin prisa, **la búsqueda de irracionalidad a escala**.

## Fuentes

- Giuga y Lehmer: [Pomerance y otros, *A remark on Giuga's conjecture and Lehmer's totient problem*](https://math.dartmouth.edu/~carlp/Carmichael_giuga.pdf);
  [*Generalizing Giuga's conjecture*](https://ar5iv.arxiv.org/html/1103.3483).
- Recíproco de Wolstenholme: [Meštrović, *Wolstenholme's theorem: its generalizations and extensions*](https://arxiv.org/pdf/1111.3057);
  [OEIS A088164](https://oeis.org/A088164).
- Fibonacci: [Jones, *Diophantine representation of the Fibonacci numbers*, Fibonacci Quarterly 13 (1975)](https://www.mathstat.dal.ca/FQ/Scanned/13-1/jones.pdf).
- Mersenne y Fermat: [Jones, Acta Arithmetica 35 (1979) 209–221](https://impan.pl/en/publishing-house/journals-and-series/acta-arithmetica/all/35/3/102229/diophantine-representation-of-mersenne-and-fermat-primes).
- Fórmulas cerradas: [Prunescu, *Arithmetic closed forms count the Mersenne primes, the Fermat primes and the twin-prime pairs*](https://arxiv.org/pdf/2512.01680).
- Tests tipo Perrin: [Adams, *Characterizing pseudoprimes for third-order linear recurrences*, Math. Comp. 48 (1987)](https://www.ams.org/journals/mcom/1987-48-177/S0025-5718-1987-0866094-6);
  [Dougherty-Bliss y Zeilberger (2023)](https://arxiv.org/pdf/2307.16069);
  [Lucas and Perrin pseudoprimes, MathPages](https://mathpages.com/home/kmath127/kmath127.htm).
- 269.011 como pseudoprimo fuerte en base 61: [OEIS A020287](https://oeis.org/A020287).
