# Auditoría independiente de Diophantus — qué es, qué puede llegar a ser y qué no

> Octubre 2026. Auditoría hecha midiendo sobre el código, no leyendo la documentación. Cada cifra
> de este documento sale de una ejecución reproducible; los scripts están en `auditoria/` y §8.
>
> Pregunta que responde: el proyecto quería analizar el "espacio matemático" de un algoritmo para
> encontrar olores de bugs, llevar el polinomio al plano complejo y estudiar sus fractales, y en
> última instancia atacar Collatz, los primos y Riemann, ofuscar código, hacer código a prueba de
> bugs, convertir repositorios enteros, ejecutar más rápido que un lenguaje secuencial, usar chips
> analógicos, IA y bots de bolsa o criptomonedas. ¿Qué de eso es alcanzable, y cómo?

---

## 0. Veredicto en una página

**Lo que el proyecto es de verdad.** Un traductor de un subconjunto muy pequeño de C (funciones
enteras recursivas de cola, sin arreglos ni punteros) a un sistema de ecuaciones polinómicas, que
**desenrolla el programa un número fijo de pasos** y convierte cada `if` en un selector algebraico.
Técnicamente es *bounded model checking* (comprobación de modelos acotada) escrito con polinomios
sobre los enteros. Alrededor hay varios módulos independientes de buena calidad: un sintetizador de
invariantes para sistemas integrables, una capa de certificados verificables por terceros, un
conjeturador de fracciones continuas que redescubre a Apéry, y el cálculo diofántico del paper.

**Lo que no es.** No es una representación diofántica en el sentido del teorema de Matiyasevich
(ésa no tiene límite de pasos); no modela el C real (ignora el desbordamiento de 32 bits); no
ejecuta nada más rápido salvo en un caso de libro (recurrencias lineales); y no contiene ni una
línea sobre fractales, plano complejo, Riemann, ofuscación, chips analógicos ni trading.

**Lo que decide el techo.** Tres teoremas, no la falta de esfuerzo (§2):

1. **MRDP funciona en los dos sentidos.** "El programa termina ⟺ la ecuación tiene solución"
   significa que decidir la ecuación es *exactamente tan difícil* como decidir el programa. La
   traducción conserva la dificultad; no la reduce.
2. **Pasar a ℂ borra justo la información que importa.** Si un sistema tiene solución en los
   complejos es *decidible*; si la tiene en los enteros, *no lo es*. Ningún método que mire sólo la
   geometría compleja puede decidir lo que pasa en los enteros. Sobre el sistema del factorial que
   compila el propio proyecto, construimos una solución compleja en la que **factorial(7) = 7**
   (§2.2).
3. **Los fractales viven en la dinámica (iterar un mapa), no en el polinomio estático.** El enfoque
   fractal de Collatz existe desde 1999 y no ha producido una demostración.

**Lo que sí tiene futuro**, por orden de lo que apostaría (§5): un **detector de cambios semánticos
con certificado** (el proyecto ya cazó con él un bug real de su propio optimizador), el bucle
**"la IA propone, el verificador comprueba"**, un **acelerador de bucles** para recurrencias lineales
en Python, y certificados que **sí entienden de enteros**. Ninguno resuelve Collatz ni hace dinero
en bolsa; los dos últimos objetivos no tienen ruta técnica (§3).

---

## 1. Lo que medí

| # | Qué | Resultado | Gravedad |
|---|---|---|---|
| 1 | Subconjunto de C | `if`, `while`/`for`, llamadas, asignación y aritmética entera. **Sin arreglos, punteros, memoria dinámica, cadenas, E/S ni biblioteca estándar** (se parsea con `-nostdinc`) | Bloquea "repositorios enteros" |
| 2 | Qué produce | El programa **desenrollado**: un SSA con un selector `e(1−e)=0` por `if` y cada comparación codificada con el teorema de los cuatro cuadrados; un ancla `overflow = 0` corta las trazas largas | Es BMC, no MRDP |
| 3 | Profundidad de desenrollado | **Tope fijo de 15** para cualquier función, cableado en `generator.py:424` (salvo `power_mod`, sin tope, y `jacobi_logic`, 12). Pedir 20 o 40 da 15. El ejemplo de Collatz pide 300 | Bug: el aviso dice que subas `DIOPHANTUS_MAX_RECURSION`, que por encima de 15 no hace nada |
| 4 | Escalado | Factorial: 30 ecuaciones a profundidad 5, 60 a 10, 90 a 15 — lineal, ~6 ecuaciones por nivel | Correcto pero acotado |
| 5 | **Desbordamiento de enteros** | `BIT_WIDTH` se lee y **nadie lo usa**. El polinomio compilado da `factorial(13) = 6.227.020.800`; el C real da `1.932.053.504` (con `-fwrapv`; sin él es comportamiento indefinido) | **Grave**: el polinomio no es el programa justo donde viven muchos bugs de C |
| 6 | Problema inverso con Z3 | Directo (`k = 10`): resuelto en 1,2 s. Inverso (`out = 10!`, ¿qué entrada?): **sin respuesta en 10 minutos**, y Z3 no respetó el límite de 60 s; con límite externo de 100 s, `unknown`. Ejecutar el programa resuelve el inverso en microsegundos | La representación algebraica es **más lenta** que el programa justo donde debería aportar |
| 7 | "Ejecución más eficiente" | Potencia de matrices para recurrencias lineales: **0,23 ms** frente a **1,5 s** del bucle con T = 10⁶ — real, pero es una técnica de libro y sólo vale para lo lineal. El "colapso lineal" (toda la traza en un entero): **2,1 s** frente a **2,3 ms** del bucle con T = 1.000, **~900 veces más lento** | La promesa general es falsa |
| 8 | Certificados | El verificador independiente cabe en 121 líneas y sólo importa sympy. Pero un certificado de Nullstellensatz (`Σ cofᵢ·pᵢ = 1`) prueba que no hay solución **ni siquiera en ℂ**: no puede certificar lo que es imposible en ℤ pero posible en ℂ | Activo real, con un límite de diseño |
| 9 | Suite del motor | **42 de 43** pasan. Falla `test_tail_merge`: la fusión de llamadas de cola **altera la semántica** (21 de 39 casos de Collatz divergen). Señalado el 19 de agosto, sin arreglar | El fallo es a la vez el mejor resultado del proyecto (§5.1) |
| 10 | Portabilidad | El parser busca `libclang` en rutas fijas (`llvm-14`); en un sistema con LLVM 18 los tests del compilador **fallan o se saltan en silencio**. Las dependencias no están fijadas y no hay CI | Los resultados no son reproducibles fuera de la máquina original |
| 11 | Promesas sin código | Ninguna línea sobre fractales, plano complejo, Riemann, ofuscación, chips analógicos ni trading | — |
| 12 | Ejemplo de "minado SHA" | Un hash de juguete de 4 rondas; su `ROTR` no reduce módulo 2³², así que ni siquiera es una rotación de 32 bits | Etiquetar como juguete |
| 13 | Factorización | El módulo dice honestamente que no bate a Pollard-rho ni a GNFS | Bien |
| 14 | Apéry | Redescubre la fracción continua de ζ(3) y mide δ = 0,156 > 0 (13/13 tests). Sobre Catalan: ninguna ejecución guardada; una muestra de 151 s con coeficientes ±8 dio **0 hallazgos** | Validado, sin explotar |
| 15 | Documentación | El README remite a `OVERVIEW.md` para "resultados y validación"; **ese fichero no ha existido nunca** en el historial | Corregir |
| 16 | Dónde fue el esfuerzo | 106 commits. 6 construyeron el motor. De los 99 posteriores a la propuesta del 19 de agosto, 65 tocan el cálculo diofántico y 13 Lean; **0** tocan el compilador, los certificados, el verificador o el conjeturador | El plan no se ejecutó |

---

## 2. Tres teoremas que fijan el alcance

### 2.1 MRDP es una reducción, y las reducciones conservan la dificultad

El teorema de Matiyasevich dice que todo conjunto computablemente enumerable es diofántico. Leído
en la dirección que interesa al proyecto: *para cada programa hay un polinomio que tiene raíces
enteras si y sólo si el programa termina*. Eso implica que **no existe** un método general para
decidir si un polinomio tiene raíces enteras (por eso el décimo problema de Hilbert es indecidible).

Consecuencia directa: cualquier pregunta sobre programas que sea indecidible (¿termina?, ¿tiene
este bug?, Rice) **sigue siendo indecidible** sobre su polinomio. Traducir mueve el problema de
sitio; no lo abarata. Lo que sí da la traducción es una **forma uniforme** de expresar problemas y
de **comprobar** soluciones y certificados — y ahí está el valor real (§4).

Lo mismo vale para los grandes problemas abiertos. **La hipótesis de Riemann ya se escribió como
"cierta ecuación diofántica no tiene soluciones" en 1976** (Davis, Matiyasevich y Robinson); Davis
la llamó "una ecuación que sólo su madre podría querer". Tenerla escrita no ha acercado la
demostración ni un milímetro. Para Collatz, Conway demostró en 1972 que la **generalización**
natural del problema es indecidible, así que no existe un método general que funcione para toda la
familia (el 3n+1 concreto sigue abierto).

### 2.2 El plano complejo es decidible; los enteros no

Si un sistema polinómico tiene solución en **ℂ** se decide algorítmicamente (Nullstellensatz de
Hilbert, bases de Gröbner); en **ℝ** también (Tarski–Seidenberg). En **ℤ** es indecidible. Por
tanto **ninguna información que dependa sólo de la variedad compleja (o real) puede decidir en
general si hay soluciones enteras**: si pudiera, el décimo problema de Hilbert sería decidible.

**Lo comprobamos sobre el sistema del factorial que compila el propio proyecto.** El compilador
codifica cada comparación `x ≤ y` como "`y − x` es suma de cuatro cuadrados" (Lagrange). En ℤ eso
es exactamente el orden. En ℂ **no significa nada**, porque todo número complejo es un cuadrado:
cada `if` puede tomar la rama que se quiera. Construimos una asignación compleja explícita de las
**91 ecuaciones** del sistema con entrada `in_k = 7`, en la que el primer `if` va por la rama
"k > 1" y el segundo por el caso base; el residuo máximo es **2·10⁻¹⁶** y la salida es
**`out = 7`**. El programa calcula 7! = 5040. En la variedad compleja del factorial, "factorial(7)
= 7" es un punto tan legítimo como el correcto.

Esa es la razón exacta por la que mirar el polinomio en el plano complejo no da pistas sobre el
programa: **el plano complejo no tiene orden, y sin orden no hay `if`**.

Sobre **ℝ** el resultado salió distinto de lo que esperábamos, y conviene contarlo. Fijando la
entrada a 10,000000001 o a 10,001, el sistema es **insatisfacible** en los reales. La causa es una
decisión de la codificación: la rama `else` de `k ≤ 1` exige `k ≥ 2`, que es "k > 1" **sólo para
enteros**; un real entre 1 y 2 no cumple ninguna de las dos ramas. La codificación mete la
integralidad dentro de las desigualdades estrictas, así que su relajación real no es una simple
sobreaproximación. Es una buena propiedad, pero no cambia el teorema: ℝ sigue siendo decidible y ℤ
no.

### 2.3 Los fractales salen de iterar, no del polinomio

El conjunto de ceros complejos de un polinomio es una variedad algebraica: no es fractal. Los
fractales (conjuntos de Julia) aparecen al **iterar** un mapa. Para Collatz eso ya se hizo:
Letherman, Schleicher y Wood construyeron en 1999 funciones holomorfas enteras que coinciden con el
mapa 3n+1 en los enteros y reformularon la conjetura en términos de componentes de Fatou. Es un
trabajo valioso y bonito, y en 27 años no ha dado una demostración. Repetirlo con más potencia de
cálculo no cambia la situación.

---

## 3. Aspiración por aspiración

| Aspiración | ¿Alcanzable? | Por qué | La versión real que sí se puede hacer |
|---|---|---|---|
| Olores de bugs en el "espacio matemático" del algoritmo | **Sí, acotado** | Comparar invariantes y comportamiento antes/después de un cambio es decidible en casos acotados | **Diff semántico con certificado** (§5.1) |
| Polinomio en el plano complejo y fractales | **No como método de prueba** (§2.2–2.3) | ℂ es decidible y olvida la integralidad | Laboratorio de dinámica: Julia del mapa iterado, codificación 2-ádica, cotas de deriva certificadas — explica, no demuestra |
| Resolver Collatz | **No** | Problema abierto; la familia generalizada es indecidible | Resultados parciales certificados; redescubrir automáticamente la conjugación 2-ádica de Lagarias |
| Primos | **Hecho lo posible** | Ver el paper: puntos exhibidos y verificados, sin récord | — |
| Riemann | **No** | La ecuación existe desde 1976 y no ayuda | A lo sumo un artefacto expositivo verificado |
| Ofuscación de código | **Nicho real, muy competido** | La aritmetización de operaciones booleanas es exactamente la ofuscación MBA (*Mixed Boolean-Arithmetic*), técnica industrial desde 2006–2007. Ya hay desofuscadores eficientes (MBA-Blast 2021, SiMBA 2022). La ofuscación general de "caja negra" es imposible (Barak et al., 2001). Además, un sistema diofántico **no se ejecuta**: no es un programa ofuscado sino su especificación | Generador y simplificador de MBA, medidos contra los conjuntos de pruebas de SiMBA |
| Código a prueba de bugs | **En general no** (Rice) | Pero para funciones pequeñas y críticas sí, con certificado | Código con prueba adjunta: certificado SMT/Lean de una especificación, re-verificable |
| Convertir repositorios enteros | **No con este diseño** | Desenrollado monolítico, 15 niveles, subconjunto mínimo de C | Enchufarse a frontales que ya existen (cláusulas de Horn, LLVM) y aportar sólo la capa de certificados |
| Ejecutar más rápido que lo secuencial | **Sólo en casos especiales** | Resolver la ecuación cuesta al menos lo que ejecutar: el testigo *es* la traza. La única aceleración real son las formas cerradas, que los compiladores ya aplican en parte | Acelerador de bucles lineales para Python (§5.3) |
| Chips analógicos | **Interfaz sí, ventaja no demostrada** | El sistema se puede convertir en una función de energía (QUBO/Ising); el propio módulo de factorización admite que no bate a los algoritmos clásicos | Exportador + banco de pruebas honesto antes de afirmar nada |
| IA | **Sí, la mejor apuesta** | Proponer certificados es difícil; comprobarlos es barato y exacto | Bucle "el modelo propone, el verificador de 121 líneas comprueba" (§5.2) |
| Bots de bolsa o criptomonedas | **No** | Los mercados no son programas cerrados; un polinomio no predice precios. Explotar fallos de contratos para lucrarse tiene riesgo penal (ha habido procesos) | Auditoría de contratos inteligentes y programas de recompensa por bugs, que son el uso legítimo y pagado |

---

## 4. Lo que sí vale del proyecto

1. **La capa de certificados.** Un tercero comprueba el resultado con 121 líneas de álgebra sin
   fiarse del motor. Es el único activo que el propio plan del 19 de agosto consideraba diferencial,
   y tenía razón.
2. **La cultura de verificación.** Tests de enunciado, tests de soundness, retractaciones escritas,
   formalización en Lean. Es rara y vale más que cualquier cifra.
3. **El sintetizador de invariantes.** Encuentra `x²−2y²` en Pell o la ecuación de Markov sin que se
   la inyecten. Es generación de invariantes polinómicos para bucles, un problema clásico de
   verificación.
4. **El conjeturador estilo Ramanujan Machine.** Validado contra Apéry; útil como herramienta de
   exploración.
5. **El paper.** Dos generadores exhibidos y verificados formalmente y tres correcciones a la
   literatura.

---

## 5. Propuestas, por orden de apuesta

### 5.1 Diff semántico con certificado (la que más me convence)

**La prueba de que funciona ya existe:** el test que falla, `test_tail_merge`, es el proyecto
detectando que **su propio optimizador cambia lo que calcula el programa** en 21 de 39 casos. Eso es
exactamente un detector de bugs de refactorización.

- **Producto:** `diophantus diff viejo.c nuevo.c` devuelve *equivalentes, con certificado* o
  *distintos, con la entrada que los separa*.
- **Primer paso:** arreglar la fusión de llamadas de cola y convertir el test en la herramienta.
- **Criterio de éxito:** sobre un banco de mutantes (bugs inyectados en funciones pequeñas), tasa de
  detección comparada con CBMC, y certificados re-verificados por el verificador independiente.
- **Requisito previo:** modelar el desbordamiento de 32 bits (§1, fila 5). Sin eso, el diff no ve
  los bugs más comunes de C.

### 5.2 La IA propone, el verificador comprueba

La asimetría que hace funcionar a FunSearch o AlphaProof: **proponer** un invariante, una función de
Lyapunov o un certificado es difícil y heurístico; **comprobarlo** es barato y exacto. Aquí el
comprobador ya existe.

- **Producto:** un modelo de lenguaje propone invariantes o certificados para funciones y bucles; el
  verificador los acepta o rechaza; los rechazos se le devuelven como contraejemplos.
- **Criterio de éxito:** porcentaje de funciones de un banco público para las que se obtiene un
  certificado válido, comparado con la búsqueda actual por plantillas.

### 5.3 Acelerador de bucles lineales para Python

Es la única forma honesta de cumplir la promesa de "ejecutar más rápido". Python no tiene el análisis
de evolución escalar que tienen los compiladores de C, y Numba acelera la ejecución pero no cambia
O(T) por O(log T).

- **Producto:** un decorador que detecta bucles que calculan recurrencias lineales y los sustituye por
  potencia de matrices, con una comprobación de equivalencia.
- **Criterio de éxito:** speedup medido sobre código real (combinatoria, finanzas, simulación), sin
  cambios de resultado.

### 5.4 Certificados que entienden de enteros

Arreglar el límite de §1, fila 8: hoy un certificado sólo puede probar imposibilidad en ℂ.

- **Producto:** descomponer en bits (que es además la semántica real de C, módulo 2³²) y emitir
  certificados booleanos de Nullstellensatz/Positivstellensatz; añadir **obstrucciones modulares**
  ("no hay solución módulo m, luego no la hay en ℤ"), que son baratas y correctas.
- **Criterio de éxito:** certificar inalcanzabilidades que hoy no se pueden certificar.

### 5.5 Laboratorio de dinámica (la versión honesta de los fractales)

Si se quiere explorar Collatz, hacerlo donde vive la estructura: el mapa iterado, no el polinomio.

- Visualizar el conjunto de Julia de la extensión holomorfa del mapa.
- Redescubrir automáticamente la conjugación 2-ádica de Lagarias (el vector de paridad determina n
  módulo 2^k).
- Cotas certificadas de la deriva media de log n sobre residuos.

Da **explicaciones** de por qué el problema resiste. No da una demostración, y no debe anunciarse
como camino hacia ella.

### 5.6 Ofuscación MBA, si interesa el nicho de seguridad

Generar y simplificar expresiones MBA con la aritmetización del proyecto, medido contra SiMBA. Es un
mercado real (análisis de malware, protección de software) y muy competido.

---

## 6. Plan

**Fase 0 — higiene (días).** Sin esto nada de lo demás es creíble.

1. Arreglar la fusión de llamadas de cola (`test_tail_merge`).
2. Quitar el tope fijo de 15 niveles o hacer que el aviso diga la verdad.
3. Modelar el desbordamiento de 32 bits (usar `BIT_WIDTH`).
4. Localizar `libclang` sin rutas fijas; fijar dependencias; añadir CI.
5. Corregir el README (`OVERVIEW.md` no existe) y etiquetar el ejemplo de SHA como juguete.

**Fase 1 — semanas.** Diff semántico con certificado (5.1) y bucle IA-verificador (5.2).

**Fase 2 — meses.** Certificados con enteros (5.4), acelerador de bucles (5.3) y, si se quiere
escala, emisión de cláusulas de Horn para enchufarse a los resolvedores existentes.

## 7. Lo que no hay que hacer

- **Bots de bolsa o criptomonedas basados en el motor.** No hay ningún mecanismo por el que un
  polinomio dé ventaja en un mercado.
- **Anunciar ataques a Collatz o Riemann.** La traducción conserva la dificultad (§2.1).
- **Estudiar los fractales del polinomio estático.** En el plano complejo factorial(7) = 7 (§2.2).
- **Afirmar velocidad sin medirla.** El "colapso lineal" es 900 veces más lento que el bucle.

---

## 8. Reproducibilidad

Entorno: Python 3.11, sympy 1.14, z3, mpmath 1.3, libclang 18 (con un enlace
`libclang.so → libclang-18.so.1`, necesario por la fila 10).

- **Escalado del compilador:** `diophantus.py` sobre `factorial.c` con `DIOPHANTUS_MAX_RECURSION`
  igual a 5, 10, 20 y 40.
- **Desbordamiento:** `factorial(13)` compilado con `gcc -fwrapv` frente al sistema compilado
  resuelto con Z3 (`in_k = 13`).
- **Velocidad:** `encodings.unroll_affine` frente a `encodings.closed_form_affine`, y
  `linear_collapse.pack_and_collapse`.
- **Banco del problema inverso y de ℤ frente a ℝ:** el sistema compilado de `factorial.c` cargado
  en Z3, con `QF_NIA` sobre ℤ y `QF_NRA` sobre ℝ, 60 s por caso:

| Caso | Dominio | Resultado |
|---|---|---|
| Directo: `in_k = 10` | ℤ | `sat` en 1,2 s, `out = 10!` |
| Inverso: `out = 10!`, ¿qué entrada? | ℤ | sin respuesta en ~10 min (límite de 60 s no respetado); `unknown` a 100 s con límite externo |
| Sin solución: `out = 10! + 1` | ℤ | `unknown` a 100 s |
| Sin solución: `out = 10! + 1` | ℝ | `unknown` a 100 s |
| Entrada fija `10 + 10⁻⁹` y `10,001` | ℝ | `unsat` (la rama `else` exige `k ≥ 2`) |
| Asignación explícita, `in_k = 7` | ℂ | las 91 ecuaciones con residuo ≤ 2,2·10⁻¹⁶, **`out = 7`** |
| Ejecutar el programa para el inverso | — | microsegundos |

El sistema medido es `auditoria/factorial_15_niveles.txt`: `factorial.c` compilado pidiendo
profundidad 20, que el tope fijo deja en 15. Los scripts están en `auditoria/`: `banco.py` (carga el sistema en Z3 sobre ℤ o ℝ), `caso.py` (un
caso aislado con límite externo), `continuidad.py` (las dos entradas reales fijas) y `complejo.py`
(construye y comprueba la solución compleja).

## Fuentes

- Davis, Matiyasevich y Robinson (1976), la hipótesis de Riemann como ecuación diofántica sin
  soluciones: [Martin Davis, in memoriam](https://logicprogramming.org/2023/01/in-memoriam-martin-davis/),
  [On the Riemann Hypothesis and Hilbert's Tenth Problem](https://arxiv.org/pdf/2311.09464).
- Conway (1972), indecidibilidad del Collatz generalizado: [On the Collatz general problem qn+1](https://arxiv.org/pdf/2005.00346).
- Letherman, Schleicher y Wood, *The 3n+1-problem and holomorphic dynamics*, Experimental
  Mathematics 8(3) (1999) 241–251: [Project Euclid](https://www.projecteuclid.org/euclid.em/1047262405).
- Ofuscación MBA y desofuscadores: [MBA-Blast, USENIX Security 2021](https://www.usenix.org/conference/usenixsecurity21/presentation/liu-binbin),
  [SiMBA (2022)](https://arxiv.org/pdf/2209.06335), [MBA semi-lineales (2024)](https://arxiv.org/pdf/2406.10016).
