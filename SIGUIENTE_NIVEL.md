# Diophantus — Propuesta técnica para el siguiente nivel

> Cómo llevar el motor y la premisa del proyecto (usar MRDP para traer problemas de otros
> ámbitos al terreno de las matemáticas analizables) más allá de su techo actual.
> Basado en el estado real del código (suite: 43 PASS · 1 FAIL) y en el estado del arte 2026.

---

## 0. El replanteamiento que ordena todo lo demás

La premisa actual del proyecto —"aprovechar MRDP para traer problemas al campo de lo
analizable"— tiene un fallo silencioso, y el propio proyecto lo demuestra: **MRDP garantiza
que la traducción existe**. Cualquier propiedad decidible en tiempo polinómico *es* diofántica
por teorema desde 1970. Por tanto **la traducción nunca es la contribución**. Exhibir la
ecuación de un test de primalidad no aporta nada porque su existencia ya era un teorema.

Lo que sí es contribución, y es lo que este proyecto hace mejor que nadie a su escala, es el
**certificado**: un objeto portable que un tercero re-verifica en ~100 líneas sin confiar ni
en el solver ni en el motor. Ese es el activo diferencial (Nullstellensatz + SOS + testigos,
unificado ya sobre 6 dominios).

**Reformulación propuesta:**

> Diophantus no es *un compilador de código a ecuaciones*.
> Es una **fábrica universal de certificados**: cualquier problema que se pueda aritmetizar
> obtiene una respuesta acompañada de una prueba portable e independientemente re-verificable.

Las tres líneas siguientes se derivan de ahí: hacer el certificado **cuantitativo** (§1),
**composicional** (§2) y **universal** (§3).

---

## 1. Romper el muro caótico: de preguntas binarias a cotas certificadas

### 1.1 El diagnóstico exacto

El motor hoy tiene una tricotomía, documentada por su propio `test_capability.py`:

| Régimen | Herramienta | Pregunta | Resultado |
|---|---|---|---|
| Conservativo / integrable | `discovery_engine.py` | ¿∃ Q con Q(T(x)) = λQ(x)? | ✅ Pell, Fibonacci, Markov-Hurwitz |
| Contractivo (A de Schur) | `lyapunov.py` | ¿∃ V ≥ 0 con V(T(x)) − V(x) ≤ 0? | ✅ certifica terminación/convergencia |
| **Caótico / expansivo** | — | — | ❌ **0. Ahí para.** |

El tercer caso no es un bug: es matemáticamente correcto. En un sistema caótico **no existe**
invariante polinómico de bajo grado, y el motor acierta al no inventarlo. El problema es que
la pregunta es **binaria** ("¿existe estructura exacta?") y en caos la respuesta siempre es no.
El motor se queda mudo justo donde están los problemas interesantes.

### 1.2 La salida: funciones auxiliares (cambiar la pregunta, no forzar la respuesta)

La literatura de sistemas dinámicos resolvió esto hace una década y encaja con la
infraestructura ya existente. En vez de exigir igualdad exacta, se busca una **función
auxiliar** V que satisfaga una **desigualdad**:

```
    V(T(x)) − V(x) + f(x)  ≤  B        para todo x en la región
```

Esto **certifica que B es cota superior de la media temporal a largo plazo del observable f**,
sin conocer ni una sola trayectoria. Y el resultado fuerte: Tobasco, Goluskin & Doering
probaron **dualidad fuerte** entre "encontrar la trayectoria extremal" y "encontrar la función
auxiliar mínima" — es decir, **las cotas son arbitrariamente afiladas**, no conservadoras.
Demostrado sobre el sistema de Lorenz, el caso caótico canónico.

Por qué esto es el encaje perfecto para Diophantus:

- **V se busca igual que ahora**: ansatz polinómico de grado acotado + condición de
  no-negatividad. Es exactamente lo que `sos.py` ya hace.
- **El resultado es un certificado SOS**, que `recheck.py` ya sabe re-verificar de forma
  portable, sin solver.
- **Convierte "0, no hay nada" en "B, certificado"**: un resultado publicable donde antes
  había silencio.

### 1.3 Qué hay que construir (concreto)

1. **Backend SDP con redondeo racional.** `sos.py` busca hoy la matriz de Gram con Z3 sobre
   racionales: exacto pero no escala. El estándar es resolver el SDP en punto flotante y luego
   **redondear a un certificado racional exacto** que se re-verifica sin el SDP. Se conserva
   así el principio del proyecto (nunca confiar en el buscador, siempre certificar) ganando
   uno o dos órdenes de magnitud en tamaño abordable.
2. **Módulo `aux_functions.py`**: dado (T, f, región), devolver (V, B) + certificado.
3. **Certificados de barrera e invariantes de conjunto**: en vez de cota sobre medias,
   certificar que la trayectoria nunca sale de una región o nunca entra en otra. Es el análogo
   de seguridad y funciona en caos, donde el invariante exacto no existe.
4. **Órbitas periódicas inestables** por optimización polinómica: extraer las UPOs que
   estructuran un atractor caótico — otro objeto certificable que hoy es inalcanzable.

### 1.4 Objetivo de validación y honestidad sobre Collatz

- **Objetivo alcanzable y verificable**: mapa de Hénon o similar → cota certificada sobre un
  observable, re-verificada por `recheck.py`. Sería **el primer resultado del proyecto sobre un
  sistema caótico**, y rompe el techo que `test_capability.py` documenta hoy.
- **Sobre Collatz, sin autoengaño**: la maquinaria de funciones auxiliares está formulada para
  sistemas polinómicos sobre conjuntos **compactos**; Collatz vive en ℕ, es no acotado y
  discreto. La extensión existe (aproximaciones semidefinidas de conjuntos alcanzables para
  sistemas polinómicos en tiempo discreto) pero no es directa. Y el propio `sos.py` ya avisa de
  la barrera dura: *un certificado SOS de bajo grado para Collatz resolvería Collatz*.
  **Lo defendible es certificar cotas sobre la deriva de observables (p. ej. el drift de log n)
  en regiones acotadas, no atacar la conjetura.**

### 1.5 El lazo propose-verify (donde la IA sí cabe)

Hay una asimetría explotable: **proponer** V es difícil y heurístico; **verificar** V es
barato y exacto. El estado del arte (FOSSIL 2.0, certificados de barrera neuronales,
síntesis guiada por contraejemplos) usa redes neuronales para *proponer* el certificado y un
verificador formal para *aceptarlo o rechazarlo*.

Diophantus puede adoptarlo sin renunciar a nada: el proponente puede ser una red, un LLM o una
búsqueda evolutiva —da igual, no hay que confiar en él—, porque **el certificado final se
re-verifica con álgebra racional exacta**. Es el mismo esquema propone→certifica→realimenta que
hizo funcionar a FunSearch, con la ventaja de que aquí el oráculo de validación ya existe.

---

## 2. Código y bugs a gran escala

### 2.1 El cuello de botella real

Hoy el pipeline **desenrolla con presupuesto** (`MAX_RECURSION_DEPTH`). El propio sistema avisa
cuando se excede (`overflow=0` deja sin solución las trazas largas): es sólido, pero significa
que el coste crece con la ejecución y que **no hay forma de analizar un programa grande**.
Escalar no es optimizar el desenrollado; es **dejar de desenrollar**.

### 2.2 Tres movimientos concretos

**(a) Hablar CHC: dejar de ser una isla.**
Las *Constrained Horn Clauses* son la lingua franca industrial de la verificación. Emitir y
consumir CHC conecta Diophantus de golpe con Spacer (Z3), Eldarica y Golem como back-ends, con
SeaHorn y Hornix (LLVM IR ↔ CHC) como front-ends, y con los benchmarks estandarizados de
CHC-COMP. Beneficio doble: potencia de resolución ajena gratis, y —más importante— **un
banco de pruebas público con el que demostrar afirmaciones de escala** en vez de autoafirmarlas.

**(b) Resúmenes composicionales en vez de desenrollado global.**
Compilar cada función **una vez** a un resumen algebraico (su relación de transición más los
invariantes descubiertos) y luego **componer** los resúmenes. Es el enfoque de *compositional
recurrence analysis*. Las piezas ya están: `linear_collapse.py` colapsa T pasos afines en una
ecuación independiente de T (109/109 verificado), `structural_collapse.py` detecta
automáticamente qué partes son afines, y `beta_backend.py` empaqueta trazas. Falta el
pegamento: un **resumen por función, cacheado e interprocedimental**.

**(c) Terminación con ranking + invariante acoplados.**
El avance reciente (Syndicate, 2024–25) es que buscar función de ranking e invariante **a la
vez, con realimentación bidireccional**, prueba muchos más programas que buscarlos por separado;
y Zhu & Kincaid (2024) dan síntesis **completa** de rankings polinómicos lexicográficos
relativa a LIRR. Diophantus tiene ya las dos mitades por separado (`discovery_engine` para
invariantes, `lyapunov` para decrecimiento): **acoplarlas es un salto barato y bien fundamentado**.

### 2.3 La aplicación con hueco real de mercado: equivalencia semántica certificada

Aquí hay una oportunidad que la investigación destapó con claridad. El survey de 2026
*"Semantic Code Clone Detection: Are We There Yet?"* evaluó 11 detectores punteros (token, árbol
y grafo) y encontró **degradación sustancial fuera de sus benchmarks**: los métodos de ML
explotan patrones del dataset en lugar de capturar equivalencia semántica real.

**Una forma normal algebraica canónica no aproxima la semántica: es la semántica.** De ahí
salen tres productos, en orden de dificultad:

1. **Detección de equivalencia/clones con certificado.** No "similitud 0.87", sino
   "equivalentes, aquí está la prueba" o "distintos, aquí está la entrada que los separa".
2. **Detección de bugs de refactorización.** Antes y después de un refactor deben compartir
   invariantes; si el invariante cambia, la refactorización alteró la semántica. Nótese que
   **el único FAIL actual de la suite es exactamente eso**: la fusión de tail-calls altera la
   semántica (`collatz_trajectory: 21/39 divergen`). El proyecto ya tiene el detector; le falta
   convertirlo en producto.
3. **Validación de traducción (translation validation).** El modelo a seguir es Alive2, que
   encontró **47 bugs reales en LLVM** (28 corregidos) verificando optimizaciones. El
   diferencial de Diophantus: Alive2 emite un veredicto; Diophantus emitiría un **certificado
   portable** de la equivalencia.

### 2.4 Verificación de código generado por IA

Es el mismo pipeline apuntando al mercado con más demanda: compilar la salida del modelo y la
especificación (o la versión previa), y certificar equivalencia o devolver un testigo del
contraejemplo. Encaja con la capa de producto ya construida (`verifier.py`, `recheck.py`,
`metering.py`) y con lo que la literatura de verificación dice que se valora hoy: certificados
verificables y formalizables, no veredictos opacos.

---

## 3. Otros dominios: el filtro para no dispersarse

La premisa "traer problemas de otros ámbitos" necesita un criterio, o se convierte en la lista
dispersa de siempre. El filtro correcto:

> **Aritmetizar solo paga donde se gana un certificado o una interfaz uniforme que la
> formulación nativa no da.** Si el dominio ya tiene una herramienta especializada mejor y
> nadie pide pruebas, aritmetizar es coste puro.

Aplicando el filtro a lo que el proyecto ya toca:

| Dominio | ¿Pasa el filtro? | Estado y siguiente paso |
|---|---|---|
| **Verificación de redes neuronales** | ✅ Sí — el sector exige garantías y no las tiene | `nn_linear.py` ya certifica robustez de capa lineal por Positivstellensatz. Siguiente: capas ReLU (lineal a trozos, encaja en el encoding) y conexión con la línea de certificados neuronales (FOSSIL, barreras k-inductivas). |
| **Optimización combinatoria** | ✅ Sí — "óptimo" sin prueba es una afirmación, no un hecho | Ya hay cotas QUBO, subset-sum, SAT/CNF y coloreado. Siguiente: MILP/scheduling con **certificado de optimalidad** re-verificable sin confiar en el solver comercial. |
| **Verificación de software / contratos** | ✅ Sí | El núcleo. Ver §2. |
| **Annealing / QUBO cuántico** | ⚠️ Parcial | `qubo.py` exporta correctamente, pero el propio repo es honesto: la factorización "no bate a GNFS". Vale como interfaz, no como ventaja algorítmica. |
| **Sistemas dinámicos y caos** | ✅ Sí — con §1, no antes | Hoy imposible; con funciones auxiliares, el terreno más prometedor. |
| **Criptoanálisis, MEV, problemas abiertos famosos** | ❌ No | Sin ventaja comparativa. Coste de oportunidad. |

---

## 4. Plan priorizado

Ordenado por (valor × probabilidad de éxito) ÷ esfuerzo:

### Fase A — Higiene, primero (días)
Sin esto nada de lo demás es creíble ante un revisor o un cliente.
1. Arreglar el FAIL abierto: la fusión de tail-calls altera la semántica.
2. Borrar o marcar los artefactos muertos (`+(1)**2` insatisfacibles, ECPP que devuelve 382,
   fichero Lucas vacío) y los tests showcase con polaridad invertida (`verify_baillie.py`).
3. CI que fije dependencias: sin ellas la suite salta 7 tests en silencio, **incluido el que falla**.

### Fase B — Certificado cuantitativo (semanas) · *el salto conceptual*
4. Backend SDP + redondeo racional para `sos.py`.
5. `aux_functions.py`: cotas certificadas sobre observables.
6. **Criterio de éxito binario**: una cota certificada sobre un sistema caótico (p. ej. Hénon),
   re-verificada por `recheck.py`. Rompe el techo de `test_capability.py`.

### Fase C — Escala (meses) · *el salto de aplicabilidad*
7. Emisión/consumo de CHC + evaluación en benchmarks de CHC-COMP.
8. Resúmenes composicionales por función (fin del desenrollado global).
9. Acoplar ranking + invariante para terminación.

### Fase D — Producto (en paralelo desde C)
10. Equivalencia semántica certificada → validación de traducción y de código generado por IA.
11. ReLU en `nn_linear` → certificados de robustez de redes.

### Lo que NO hay que hacer
Perseguir Collatz o los primos como objetivo. Ambos tienen barreras duras demostradas (un SOS
de bajo grado para Collatz *resolvería* Collatz; la existencia diofántica de un test de
primalidad ya es teorema). Son ruido con coste de oportunidad alto.

---

## 5. La frase que resume el salto

El motor actual pregunta **"¿existe estructura exacta?"** y responde sí/no. En todo lo
interesante —caos, programas grandes, sistemas reales— la respuesta es no, y ahí se detiene.

El siguiente nivel es cambiar la pregunta a **"¿qué puedo certificar sobre esto?"**, cuya
respuesta nunca es vacía: una cota, una barrera, una equivalencia, un contraejemplo. Y siempre
con la misma firma del proyecto: **una prueba portable que cualquiera re-verifica sin confiar
en quien la produjo.**

---

## 6. Fuentes

- Funciones auxiliares y caos: [Tobasco, Goluskin & Doering, *Optimal bounds and extremal trajectories for time averages in nonlinear dynamical systems*](https://arxiv.org/pdf/1705.07096) · [*Bounding averages rigorously using SDP: mean moments of the Lorenz system*](https://arxiv.org/pdf/1610.05335) · [*Bounds for deterministic and stochastic dynamical systems using SOS optimization*](https://epubs.siam.org/doi/10.1137/15M1053347) · [*Finding unstable periodic orbits with polynomial optimization*](https://arxiv.org/pdf/2101.10285)
- Certificados neuronales y síntesis: [FOSSIL / certificate synthesis framework](https://arxiv.org/pdf/2309.06090) · [k-inductive neural barrier certificates](https://arxiv.org/pdf/2605.20108)
- Terminación: [Syndicate: ranking + invariante con realimentación bidireccional](https://arxiv.org/abs/2404.05951) · [Zhu & Kincaid, *On Ranking Function Synthesis and Termination for Polynomial Programs*](https://people.mpi-sws.org/~joel/publications/ranking_polynomial_programs20.pdf)
- CHC: [Golem](https://link.springer.com/article/10.1007/s10703-025-00470-9) · [CHC-COMP](https://arxiv.org/pdf/2404.14923) · [SeaHorn](https://seahorn.github.io/papers/cav15.pdf) · [Hornix: LLVM IR ↔ CHC](https://link.springer.com/chapter/10.1007/978-3-032-22749-2_28)
- Equivalencia y clones: [*Semantic Code Clone Detection: Are We There Yet?* (2026)](https://arxiv.org/abs/2606.25272) · [Alive2: bounded translation validation for LLVM](https://dl.acm.org/doi/10.1145/3453483.3454030) · [Equivalencia semántica entre versiones de proyectos C a gran escala](https://dl.acm.org/doi/10.1145/3801958)
