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
| `L_prime_shared` (compartido) | 29 | **30** | ídem |

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
| **Diseño final** | **30** | Sí |

### 3.2b El marcador, después de corregir **y** de cerrar la esquina

| Conjunto | Representación (incógnitas, grado combinado) | **Generador (variables, grado)** |
|---|---|---|
| cuadrado, triangular, Pell D=2, Pell D=3 | (1, 4) | (2, 5) |
| compuesto, suma de 2 cuadrados | (2, 4) | (3, 5) |
| Fibonacci | (2, 16) | (12, 5) |
| potencia de 2 | (7, 8) | (14, 5) |
| **primo** | **(30, 8)** | **(40, 5)** |

Frente a los récords publicados de generadores de primos:

| | Variables | Grado |
|---|---|---|
| **Nuestro generador (sound)** | **40** | **5** |
| Récord de menor grado *(citado, sin cotejar)* | 42 | 5 |
| Jones–Sato–Wada–Wiens 1976 | 26 | 25 |
| Matiyasevich (menos variables) | 10 | ~1,6×10⁴⁵ |

**Trayectoria completa de esta esquina.** Todas las cifras posteriores a la corrección salen de
sistemas cuya **completitud** está verificada con testigo real y valores no negativos. El
**veredicto SMT del sistema final para los primos estaba en curso al cerrar esta sesión**: el
catálogo entero pasa, y los pasos intermedios pasaron, pero la comprobación del punto (30, 8)
sobre ocho compuestos no había terminado. *Hasta que termine, la cifra (40, 5) es provisional.*

| Paso | Repr. | Generador | Qué cambió |
|---|---|---|---|
| «(41,5)» de agosto | 29 | (41, 5) | **insound**: no medía nada |
| corrección ingenua | 53 | — | una holgura por condición |
| reparametrización `a := a' + cota` | 39 | (65, 5) | coste 0 en la repr., **carísimo al aplanar** |
| pool de desigualdades | 36 | (62, 5) | deduplicación universal |
| **cota por ecuación lineal** | 39 | **(51, 5)** | `a` vuelve a ser un símbolo: −11 |
| **base de Pell compartida** | 35 | **(44, 5)** | una sola `a` para los tres exponentes |
| desplazamiento de origen + implicación | 32 | (41, 5) | `E=Ev+1`, `T=Tv+1`: 3 holguras menos |
| `a` = suma de cotas (igualdad) | 31 | (40, 5) | la holgura de la base sobra |
| eliminación de `Q` por sustitución | **30** | **(40, 5)** | la congruencia va dentro de `Q = B + u·c` |

**La lección de ingeniería, que vale para cualquier problema:** la reparametrización
`a := a' + cota` es óptima en la representación y **pésima en el generador**. `a` aparece al
cuadrado en la ecuación de Pell, y elevar al cuadrado una suma de seis símbolos genera decenas
de monomios de grado 4 que luego hay que nombrar uno a uno. Imponer la misma cota con una
**ecuación lineal aparte** cuesta una incógnita y ahorra once. *Dónde se paga el coste importa
tanto como cuánto se paga.*

### 3.2c Estado del cotejo del récord (paso 1, parcialmente bloqueado)

| Dato | Fuente alcanzada | Estado |
|---|---|---|
| Generador de primos de menor grado: **(42 variables, grado 5)** | resúmenes de búsqueda que citan el *Prime Glossary* (t5k.org) | **corroborado a nivel secundario**; PDF no accesible |
| Generador con menos variables: **(10, ~1,6×10⁴⁵)** | ídem | ídem |
| **JSWW 1976: (26, 25)** | citado en varias fuentes independientes | consistente |
| **Par universal de Jones 1982: (58, 4) sobre ℕ**, y **(9, 1,638×10⁴⁵)** | Jones, *Universal Diophantine Equation*, JSL 47 (1982) 549–571 | referencia bibliográfica confirmada |
| Sigue siendo el **menor grado conocido** en 2025 | Bayer–David, *A Formal Proof of Complexity Bounds on Diophantine Equations* (ITP 2025) y *Diophantine Equations over ℤ* (arXiv 2506.20909): dan el **primer par universal no trivial sobre ℤ**, 11 incógnitas, y una nueva pareja (32, 12); (58, 4) sigue en pie sobre ℕ | corroborado |

**Lo que NO se pudo hacer:** abrir ninguna fuente primaria. La política de egreso del entorno
bloquea `arxiv.org`, `drops.dagstuhl.de`, `t5k.org`, `mathworld.wolfram.com` e `isa-afp.org`;
solo la búsqueda web (que devuelve resúmenes) atraviesa. La cifra (42, 5) sigue, por tanto,
**sin cotejar contra el papel**.

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
- **Qué queda del gasto** (30 incógnitas de la representación): 8 valores de la cadena
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

- **No se ha batido ningún récord, y decir lo contrario sería repetir la historia.** El punto
  medido es (40, 5) frente al (42, 5) *citado*. Para que eso fuera un récord harían falta tres
  cosas que NO tenemos: (a) el (42, 5) cotejado contra fuente primaria — el entorno bloquea el
  acceso; (b) la corrección de la cadena verificada más allá de n=3, donde el testigo deja de ser
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
