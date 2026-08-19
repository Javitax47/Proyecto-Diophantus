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
| `L_nonneg_N` (sobre ℕ) | **0 ⚠️** | **0** si es variable suelta o constante; **1** si es expresión | — |
| `L_exponential` (Pell) | 5 | **7** | 1368 casos |
| `L_binomial` | 21 | **27** | 209 casos |
| `L_factorial` | 36 | **46** | n=1..7 |
| `L_prime` (Wilson, aditivo) | 38 | **50** | Wilson en [2,250) |
| `L_prime_shared` (compartido + pool) | 29 | **36** | ídem |

La fila crítica es `L_nonneg_N`: declarar coste 0 para una expresión compuesta era el defecto.
El resto de la tabla es su propagación por la cadena.

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

**La corrección, y su precio.** Las condiciones que faltaban se imponen ahora. Casi todas son
**cotas inferiores sobre la propia incógnita compartida `a`**, así que en vez de gastar una
holgura por condición se **reparametriza**:

```
a := a' + k + 2 + Σᵢ(bᵢ + cᵢ)      con a' ≥ 0 fresca
y := y' + 1
```

y entonces `a−1 > k`, `a > cᵢ`, `a ≥ bᵢ`, `cᵢ < Mᵢ` e `y ≥ 1` se cumplen **por construcción,
a coste cero**. Solo quedan `k ≥ 1` y `bᵢ ≥ 2`, que no son cotas sobre incógnitas propias
(en la cadena `k` y `bᵢ` son expresiones), y cuestan una holgura cada una.

| | Incógnitas | ¿Sound? |
|---|---|---|
| Antes (lo que se publicó) | 29 | **No** — Z3 halla testigo para 4, 9, 15, 25 |
| Corrección ingenua (1 holgura por condición) | 53 | Sí |
| Corrección por reparametrización | 39 | Sí |
| **+ pool de desigualdades (deduplicación)** | **36** | Sí |

### 3.2b El marcador REAL, después de la corrección

| Conjunto | Representación (incógnitas, grado combinado) | **Generador (variables, grado)** |
|---|---|---|
| cuadrado, triangular, Pell D=2, Pell D=3 | (1, 4) | (2, 5) |
| compuesto, suma de 2 cuadrados | (2, 4) | (3, 5) |
| Fibonacci | (2, 16) | (12, 5) |
| potencia de 2 | (7, 8) | (14, 5) |
| **primo** | **(36, 8)** | **(62, 5)** |

Frente a los récords publicados de generadores de primos:

| | Variables | Grado |
|---|---|---|
| **Nuestro generador (sound)** | **62** | **5** |
| Récord de menor grado *(citado, sin cotejar)* | **42** | 5 |
| Jones–Sato–Wada–Wiens 1976 | 26 | 25 |
| Matiyasevich (menos variables) | 10 | ~1,6×10⁴⁵ |

**Estamos 20 variables por detrás**, no una por delante. La versión anterior de este documento
decía lo contrario porque medía un sistema que no era sound.

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

### 6.2 Hacia grado bajo (donde estamos)
- El grado ya está en la esquina mínima (5 como generador) y **ahí se queda**: aplanar a grado 2
  siempre es posible, y por debajo de 2 el conjunto sería semilineal. Toda la partida en esta
  esquina es **número de variables**.
- **Punto actual: 62 variables. Récord citado: 42.** El salto es grande y no se cierra afinando
  el voraz; exige que la *representación* tenga menos incógnitas antes de aplanar (36 hoy).
- **Dónde está el gasto** (36 incógnitas de la representación de primos): la cadena
  Wilson → factorial → binomial → 5 exponenciaciones. Cada exponenciación cuesta 5 incógnitas
  del núcleo de Pell más las holguras de `k ≥ 1` y `b ≥ 2`; `PellContext` ya comparte (a,x,y,t)
  entre relaciones con el mismo exponente.
- **Tres palancas concretas, en orden de rendimiento esperado:**
  1. **Eliminar las holguras restantes por reparametrización.** `k ≥ 1` y `bᵢ ≥ 2` cuestan 1
     cada una solo porque `k` y `bᵢ` son *expresiones* de la cadena (ya hecho para las que son
     variables sueltas o constantes; queda `n ≥ 2`, `E ≥ 1`, `T ≥ 1`). Si la cadena introdujera
     esas magnitudes ya desplazadas (`k = k'+1`, `b = b'+2`) el coste sería 0.
  2. **Compartir el contexto de Pell entre exponentes distintos**, no solo iguales. Hoy hay 3
     contextos; las propiedades P1/P2 permiten relacionar índices distintos sobre la misma `a`.
  3. **Teorema de Combinación de Relaciones** (§6.1): la única pieza que reduce el conteo de
     verdad, y sigue sin implementar.
- **Regla nueva y no negociable:** ninguna cifra de esta sección vale sin su veredicto de
  `dioph_soundness`. La cifra (41, 5) que estuvo aquí venía de un sistema que Z3 refuta.

### 6.3 Puente entre las dos islas del repo
El proyecto tiene dos subsistemas maduros **sin un solo import entre ellos**: el colapso de
trazas (β, dominancia de dígitos) y el cálculo diofántico. La técnica es la misma matemática,
pero `check_beta_trajectory` **ejecuta** un bucle `for i in range(T)` — el cuantificador acotado
se evalúa en vez de eliminarse. Construir ese puente es trabajo pendiente.

---

## 7. Lo que NO se puede afirmar (para no repetir la historia de la "Ecuación Suprema")

- **No hemos batido ningún récord.** Estamos en (62, 5) frente a (42, 5): **20 variables por
  detrás**. La cifra (41, 5) que figuró aquí era de un sistema **insound** y no medía nada.
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
