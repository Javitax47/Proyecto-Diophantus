# Qué tiene futuro de lo que Diophantus quería ser, y cómo conseguirlo

> Octubre 2026. Complemento de `AUDITORIA.md`. Aquélla dice qué hay; ésta propone cómo llegar a lo
> que el proyecto pretendía, aunque hoy no haya nada construido. Cada propuesta lleva el mecanismo
> que la haría funcionar, un primer prototipo, cómo medir si funciona y hasta dónde puede llegar.
> La primera ya tiene prototipo funcionando (`propuestas/poc_brecha_semantica.py`).

---

## 0. Mapa

| Lo que se quería | La versión con futuro | Futuro | Plazo del primer resultado |
|---|---|---|---|
| Olores de bugs en el espacio matemático del algoritmo | **Detector de brechas semánticas** (§2) + **diff semántico certificado** (§3) | Alto | Semanas — ya hay prototipo |
| IA | **La IA propone, el verificador comprueba** + datos de entrenamiento verificados (§4) | Alto | Semanas |
| Ejecutar más rápido que lo secuencial | **Formas cerradas** y **paralelización por scan asociativo** de bucles (§5) | Medio-alto | Semanas |
| Llevar el polinomio al plano complejo | **Combinatoria analítica**: coste medio automático de algoritmos (§6) | Medio | Meses |
| Fractales | **Laboratorio de dinámica**: sensibilidad y caos en código numérico (§6) | Medio | Meses |
| Ofuscación | **Predicados opacos con certificado** + MBA (§7) | Medio, nicho | Semanas |
| Código a prueba de bugs | **Código con prueba adjunta** para funciones críticas (§8) | Medio | Meses |
| Convertir repositorios enteros | **LLVM IR + resúmenes por función + análisis incremental de cada cambio** (§9) | Medio | Meses |
| Collatz, primos, Riemann | **Billetes de lotería honestos** (§10) | Bajo, pero con premio real | Variable |
| Chips analógicos | **Primero simulación**: lineal → circuitos analógicos (§11) | Bajo-medio, investigación | Años |
| Dinero con bots de bolsa o criptos | **No** como trading; **sí** como auditoría y producto (§12) | Alto como servicio, nulo como bot | Meses |

---

## 1. La idea que lo une todo: cada pregunta tiene su anillo

La intuición original —"llevar el polinomio a otro mundo matemático y mirar qué aparece"— es buena.
Lo que falla es el mundo elegido. El plano complejo es la elección equivocada para casi todas las
preguntas sobre programas, porque **no tiene orden y por tanto no tiene `if`** (`AUDITORIA.md`
§2.2: en ℂ, factorial(7) = 7). Pero **cambiar de sistema numérico, eligiéndolo según la pregunta**,
es una herramienta potentísima, y el proyecto tiene justo la pieza que lo permite: una representación
algebraica del programa que se puede leer en distintos anillos.

| Pregunta | Anillo correcto | Por qué |
|---|---|---|
| ¿Qué cree calcular el programador? | ℤ (enteros sin límite) | La intención matemática |
| ¿Qué calcula de verdad la máquina? | ℤ/2³² (aritmética de 32 bits) | La semántica real de C |
| ¿Hay un bug de desbordamiento? | **la diferencia entre los dos anteriores** | §2 |
| ¿Es imposible algo, rápido? | 𝔽ₚ (módulo un primo pequeño) | "Sin solución módulo p ⟹ sin solución en ℤ": barato y correcto |
| ¿Hay error de redondeo? | ℝ frente a coma flotante | La misma idea de §2 con números reales |
| ¿Cuánto tarda en media? | **ℂ**, pero sobre la *función generatriz*, no sobre el polinomio | §6: aquí el plano complejo sí es el mundo correcto |

Ésta es la tesis que propongo para Diophantus 2.0: **un programa tiene varias semánticas, y los bugs
viven en las diferencias entre ellas**. El proyecto, que convierte código en álgebra, es la
herramienta natural para comparar semánticas.

---

## 2. Detector de brechas semánticas — la primera apuesta

**Qué es.** Cada expresión se interpreta dos veces: como enteros ideales y como enteros de máquina.
Se le pide a un solver una entrada válida en la que difieran. Si la encuentra, es un bug y viene con
la entrada exacta que lo dispara. Si demuestra que no existe, ese "no existe" es un **certificado**
de ausencia de desbordamiento.

**Por qué funciona.** Los solvers de vectores de bits resuelven este tipo de pregunta en
milisegundos, y el desbordamiento es una de las clases de bug más frecuentes en C y C++.

**Prototipo ya hecho** (`propuestas/poc_brecha_semantica.py`):

| Caso | Resultado | Tiempo |
|---|---|---|
| Punto medio `(lo + hi) / 2` de la búsqueda binaria (el bug que estuvo años en `java.util.Arrays`) | **bug**, con `lo = 1.409.265.416`, `hi = 1.811.960.055`: índice negativo | 24 ms |
| El arreglo `lo + (hi − lo) / 2` | **certificado correcto** (no existe entrada que falle) | 107 ms |
| El paso impar `(3n+1)/2` del Collatz del propio proyecto | **bug**: con `n = 1.163.220.309` da un número negativo | 20 ms |
| `acc * k` en el factorial del propio proyecto | **bug** | 10 ms |

El ejemplo de Collatz del repositorio tiene un bug de desbordamiento que su propio polinomio no ve.

**Siguiente paso.** Hacer que el compilador emita las dos semánticas por sí solo (usar por fin
`BIT_WIDTH`), recorrer cada operación aritmética de una función y preguntar por la brecha en cada
una. Extensiones naturales: división por cero, desplazamientos fuera de rango, conversión de tipos
con pérdida y coma flotante frente a reales.

**Cómo medirlo.** Sobre un banco público de bugs de desbordamiento (por ejemplo los del conjunto
Juliet del NIST), comparar detecciones y falsos positivos con las herramientas habituales
(sanitizadores de compilador, CBMC). La ventaja diferencial no es encontrar más bugs que ellas: es
**devolver, en los casos sin bug, un certificado que un tercero comprueba**.

**Techo.** Funciones con aritmética entera. No ve bugs de memoria (punteros, límites de arreglos)
hasta que el frontal soporte memoria (§9).

---

## 3. Diff semántico certificado

**Qué es.** `diophantus diff viejo.c nuevo.c`: o *"son equivalentes, aquí está la prueba"*, o
*"difieren, aquí está la entrada que lo muestra"*.

**Por qué funciona.** Comparar dos versiones de la *misma* función es mucho más fácil que verificar
una función contra una especificación: casi todo el código es igual y el solver sólo trabaja sobre
la diferencia. Además, el proyecto **ya lo hizo una vez sin proponérselo**: su único test que falla
es el detector descubriendo que el optimizador del propio proyecto cambia lo que calcula el programa
en 21 de 39 casos.

**Producto.** Un bot que comenta cada *pull request*: "esta refactorización conserva el
comportamiento (certificado adjunto)" o "esta refactorización cambia la salida para esta entrada".
Es justo la pregunta que un revisor humano no puede contestar con seguridad.

**Cómo medirlo.** Banco de mutantes: inyectar cambios de comportamiento en funciones reales y medir
qué fracción detecta, frente a la suite de tests existente del proyecto analizado.

---

## 4. La IA propone, el verificador comprueba

**Qué es.** Un modelo de lenguaje propone invariantes, funciones de terminación, formas cerradas o
certificados; el verificador independiente del proyecto (121 líneas, sólo álgebra) los acepta o los
rechaza; los rechazos vuelven al modelo como contraejemplos.

**Por qué funciona.** Es la arquitectura de FunSearch y AlphaProof: **proponer es difícil y
heurístico, comprobar es barato y exacto**. El modelo puede equivocarse cuanto quiera, porque nada
entra sin pasar el comprobador.

**Dos productos de una misma pieza.**

1. *Verificación de código generado por IA.* Lo que un asistente de programación escribe se compara
   con una versión de referencia (§3) o se le exige un certificado. Es la demanda más clara que hay
   hoy en verificación.
2. *Datos de entrenamiento verificados.* El compilador puede generar en masa triples
   (programa, propiedad, prueba) cuya corrección está comprobada por máquina. Los modelos de
   razonamiento necesitan exactamente eso, y casi nadie puede fabricarlo con garantía.

**Cómo medirlo.** Fracción de funciones de un banco público para las que se obtiene un certificado
válido, frente a la búsqueda por plantillas actual.

---

## 5. Ejecutar más rápido que lo secuencial

La promesa general es imposible: resolver la ecuación de un programa cuesta al menos lo que
ejecutarlo. Pero hay dos versiones reales y medibles, y las dos salen de **reconocer la estructura
algebraica de un bucle**, que es lo que el proyecto sabe hacer.

**5.1 Formas cerradas.** Si el cuerpo de un bucle es una recurrencia lineal, el bucle entero se
sustituye por una potencia de matrices: O(T) pasa a O(log T). Medido en la auditoría: **0,23 ms
frente a 1,5 s** con T = 10⁶. Más allá de lo lineal, la sumación simbólica (algoritmos de Gosper y
Zeilberger) convierte muchas sumas con coeficientes binomiales o factoriales en fórmulas cerradas.
Los compiladores de C hacen una parte; **CPython no hace ninguna** (Numba, al compilar con LLVM, puede heredar algunas de las más simples).
*Producto:* un decorador `@acelerar` para Python que detecta estos bucles, los sustituye y comprueba
la equivalencia. *Medida:* speedup sobre código real de combinatoria, finanzas o simulación, sin
cambiar ningún resultado.

**5.2 Paralelización por scan asociativo.** Un bucle secuencial cuyo paso es una función afín se
puede ejecutar en paralelo, porque componer funciones afines es asociativo: con un *prefix scan*
(Blelloch, 1990) los T pasos se hacen en profundidad log₂ T en una GPU. Es exactamente el truco que
hace rápidos a los modelos de lenguaje de espacio de estados como Mamba o S5. *Producto:* detectar
bucles cuyo paso forma un semigrupo y reescribirlos como scan. *Medida:* tiempo en GPU frente al
bucle secuencial.

**Techo.** Sólo bucles con esa estructura. El código general no la tiene.

---

## 6. El plano complejo y los fractales, donde sí sirven

**6.1 Combinatoria analítica: el coste medio de un algoritmo, automático.** Aquí el plano complejo
es el mundo correcto. El coste de un algoritmo recursivo cumple una recurrencia; su función
generatriz es una función de variable compleja; y **la posición de su singularidad dominante en ℂ
determina el comportamiento asintótico** del algoritmo (Flajolet y Sedgewick, *Analytic
Combinatorics*, 2009). Así se obtiene, por ejemplo, que quicksort hace en media unas 2 n ln n
comparaciones. El compilador ya exporta recurrencias (`*_recurrence_system.txt`); falta el paso de
recurrencia a función generatriz y a singularidad.
*Producto:* "dame una función recursiva y te devuelvo su coste medio asintótico". Hay pocas
herramientas que lo hagan de forma automática.

**6.2 Laboratorio de dinámica.** Los fractales aparecen al **iterar** un mapa. Para código numérico
iterativo —métodos de Newton, simulaciones físicas, bucles de entrenamiento— calcular exponentes de
Lyapunov y regiones de sensibilidad identifica las entradas donde un cambio mínimo produce un
resultado distinto: un olor de bug numérico y un objetivo natural para el *fuzzing*. Para Collatz,
el mismo laboratorio visualiza el conjunto de Julia de su extensión holomorfa (Letherman, Schleicher
y Wood, 1999) y redescubre la codificación 2-ádica de Lagarias. Eso **explica** por qué el problema
resiste; no lo resuelve.

---

## 7. Ofuscación: predicados opacos con certificado

**Qué es.** Un predicado opaco es una condición que siempre vale lo mismo (por ejemplo, siempre
falsa) pero que un analizador no puede averiguar. Se usa para meter ramas falsas que confunden a quien
intenta entender el código.

**La idea propia.** La auditoría midió que Z3 **no resuelve en diez minutos** sistemas diofánticos
pequeños del propio proyecto. Esa debilidad del atacante es una fortaleza del defensor: construir
predicados a partir de ecuaciones diofánticas sin solución, de modo que **el defensor tiene un
certificado de que el predicado siempre es falso** (así sabe que la ofuscación no cambia el
programa) y **el atacante no tiene solver que lo demuestre**.

**Techo, y es importante.** Los predicados opacos caen ante el análisis dinámico: basta ejecutar el
programa muchas veces para ver que la rama nunca se toma. Suben el coste del análisis estático, no lo
hacen imposible. Y la ofuscación general "de caja negra" está demostrado que no existe (Barak y
otros, 2001). Como mercado, el nicho de las expresiones MBA (*Mixed Boolean-Arithmetic*) es real
pero muy competido.

---

## 8. Código a prueba de bugs, en su versión posible

En general es imposible (teorema de Rice). Para **funciones pequeñas y críticas** —primitivas
criptográficas, cálculos financieros, analizadores de formatos fijos, contratos inteligentes— sí:
**código con prueba adjunta**. Cada función se entrega con un certificado de que cumple su
especificación, que cualquiera comprueba sin fiarse de quien lo generó.

El proyecto ya tiene las dos mitades: genera enunciados de Lean a partir de sistemas (`dioph_lean`),
y la sesión del paper demostró la disciplina de comprobar que lo enunciado es lo que se quiere probar.
Con §4, un modelo puede escribir la demostración y Lean comprobarla.

---

## 9. Repositorios enteros: no se convierten, se analizan por partes

El diseño actual —un único polinomio gigante con el programa desenrollado— no escala, y no hay que
intentarlo. Lo que sí escala:

1. **Frontal LLVM IR** en lugar de un parser propio de C. Sirve gratis para C, C++, Rust o Swift.
2. **Un resumen algebraico por función**, calculado una vez y guardado (relación de entrada y
   salida, invariantes, formas cerradas).
3. **Cláusulas de Horn** como formato de salida, para usar los resolvedores que ya existen (Spacer,
   Eldarica, Golem) en vez de competir con ellos.
4. **Análisis incremental**: en cada *pull request* sólo se analizan las funciones cambiadas y las
   que las llaman. Así nunca hace falta el repositorio entero a la vez.

El valor propio de Diophantus en esa cadena es lo que nadie más da: las formas cerradas, las brechas
semánticas (§2) y los certificados re-verificables.

---

## 10. Collatz, primos y Riemann: billetes de lotería honestos

Ninguna traducción resuelve estos problemas (`AUDITORIA.md` §2.1). Pero hay apuestas con premio real
si sale bien y coste acotado si no:

1. **Búsqueda de pruebas de irracionalidad a escala.** El conjeturador ya redescubre la prueba de
   Apéry para ζ(3) (mide δ > 0). Un δ > 0 verificado para la constante de Catalan o para ζ(5) sería
   un resultado nuevo sobre un problema abierto. La probabilidad es baja; la máquina ya existe; lo que
   falta es ejecutarla a escala (meses de cómputo en paralelo) y con espacios de búsqueda más ricos.
   Es la mejor "lotería" del proyecto.
2. **Laboratorio de Collatz** (§6.2): explicaciones, visualizaciones y resultados parciales
   certificados.
3. **Exhibir y verificar** ecuaciones que la literatura sólo anuncia, como se hizo con los primos.
   Publicable; no acerca ninguna demostración.

---

## 11. Chips analógicos: primero simulación

**El vínculo real.** Una recurrencia lineal `x_{t+1} = a·x_t + b·u_t` es, literalmente, un filtro
digital, y su versión continua es un circuito analógico. Un producto matriz-vector es lo que hacen
de forma nativa las matrices de memristores de la computación en memoria. Es decir: **la estructura
lineal que el proyecto detecta en el código es justo lo que el hardware analógico ejecuta de forma
nativa**. Por otro lado, la suma de cuadrados de un sistema es una función de energía que pueden
minimizar los resolvedores analógicos de restricciones (por ejemplo Ercsey-Ravasz y Toroczkai, 2011)
o las máquinas de Ising.

**Plan.** Exportar las partes lineales a un simulador de circuitos y medir error y consumo frente a
la ejecución digital, antes de tocar hardware.

**Techo.** La precisión analógica es de pocos bits (típicamente entre 4 y 8). Sirve para cargas tolerantes al ruido
(inferencia de IA, procesado de señal), no para código entero exacto. Es investigación de años.

---

## 12. Dinero

**Bots de bolsa o de criptomonedas: no.** No es una cuestión de esfuerzo. El precio de un activo no
es la salida de un programa fijo que se pueda traducir a un polinomio: el mercado es adversarial
(cada ventaja que se descubre desaparece al explotarse) y cambia con el tiempo. La herramienta
adecuada para intentarlo es la estadística, no el álgebra, y los estudios sobre operadores
minoristas encuentran sistemáticamente que la gran mayoría pierde dinero. Además, **explotar fallos de contratos para lucrarse puede ser delito**;
ha habido procesos penales por ello.

**Dónde sí hay dinero, de más a menos inmediato:**

1. **Auditoría de contratos inteligentes.** La verificación formal de contratos es un servicio que
   ya se paga (Certora es el ejemplo conocido). Exige un frontal para EVM/Solidity; §2, §3 y §8 se
   aplican tal cual.
2. **Programas de recompensa por bugs** (Immunefi y similares). El detector de §2 aplicado a
   contratos y bibliotecas es la vía legal de cobrar por encontrar fallos.
3. **El bot de *pull requests*** de §3 como servicio de suscripción. El código de facturación por
   niveles ya existe (`src/product/metering.py`); falta el producto.
4. **El acelerador para Python** de §5 como biblioteca con licencia comercial o soporte.

---

## 13. Orden de ataque

| Cuándo | Qué | Por qué en ese orden |
|---|---|---|
| Días | Higiene (`AUDITORIA.md` §6, fase 0): arreglar el test que falla, quitar el tope de 15, usar `BIT_WIDTH`, `libclang` sin rutas fijas | Sin esto, nada de lo demás es creíble |
| 1 mes | **§2** integrado en el compilador + **§3** sobre funciones aisladas | Ya hay prototipo; resultado medible enseguida |
| 2–3 meses | **§4** (bucle con IA) y **§5.1** (acelerador para Python) | Reutilizan lo anterior; producto propio |
| 3–6 meses | **§9** (LLVM IR y análisis incremental), **§6.1** (coste medio automático), **§7** | Escala y diferenciación |
| Continuo, en paralelo | **§10.1** (irracionalidad a escala) | Coste de cómputo, no de desarrollo |
| Años | **§11** (analógico) | Investigación |
| Nunca | Bots de trading | No hay mecanismo |

## 14. Lo que nadie puede prometer

Ninguna de estas propuestas resuelve Collatz, Riemann ni la ecuación "relevante" de los primos, y
ninguna convierte el proyecto en una máquina de hacer dinero automática. Lo que sí pueden dar es una
herramienta que encuentra bugs reales con la entrada exacta que los dispara, que certifica cuándo no
los hay, que acelera cierto tipo de código de forma medible y que pone a la IA a trabajar bajo un
verificador que no se equivoca. El prototipo de §2 ya hace lo primero en milisegundos, sobre un bug
que estuvo años en la biblioteca estándar de Java y sobre otro que estaba en este mismo repositorio.
