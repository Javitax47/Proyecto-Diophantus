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

Tests correspondientes en `src/tests/verification/test_dioph_*.py`, todos registrados en
`run_verification_suite.py`.

---

## 3. Números medidos (el marcador)

### 3.1 Coste de los lemas (sobre ℕ)

| Lema | Incógnitas | Verificación previa |
|---|---|---|
| `L_divides`, `L_congruent`, `L_square` | 1 | elemental |
| `L_composite` | 2 | elemental |
| `L_nonneg` (Lagrange) | 4 sobre ℤ, **0 sobre ℕ** | 200 enteros |
| `L_exponential` (Pell) | **5** sobre ℕ, 17 sobre ℤ | 1368 casos |
| `L_binomial` | 21 | 209 casos |
| `L_factorial` | 36 | n=1..7 |
| `L_prime` (Wilson, aditivo) | 38 | Wilson en [2,250) |
| `L_prime_shared` (compartido) | **29** | ídem |

### 3.2 Curva de Pareto del catálogo — (incógnitas, grado combinado)

| Conjunto | Original | Aplanado a grado 4 |
|---|---|---|
| cuadrado, triangular, Pell D=2, Pell D=3 | (1, 4) | — |
| compuesto, suma de 2 cuadrados | (2, 4) | — |
| Fibonacci | (2, 16) | (39, 4) |
| potencia de 2 | (6, 8) | (8, 4) |
| **primo** | **(29, 8)** | **(42, 4)** |

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

**Principio común:** las sustituciones se **comparten** entre ecuaciones; si un producto aparece
varias veces, una sola incógnita sirve a todas.

---

## 5. Garantías metodológicas (lo que NO se debe relajar)

1. **Verificar la matemática ANTES de implementar.** Cada identidad se comprueba numéricamente en
   cientos o miles de casos antes de escribir el lema. Así se cazaron todos los errores.
2. **Testigo constructivo, no búsqueda.** La completitud se prueba *construyendo* el testigo y
   *evaluando* el sistema.
3. **Ambas direcciones o declararlo.** `DiophProblem.soundness` vale `'exhaustivo'` (la dirección
   inversa se comprueba por búsqueda) o `'teorema'` (el constructor cortocircuita con el oráculo,
   luego comprobarla sería **circular**; descansa en la referencia). **Nunca presentar 'teorema'
   como si fuera 'exhaustivo'.**
4. **`sys.exit(1)` en fallo.** El proyecto ya tuvo tests que fallaban y salían con 0.

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
- Ya alcanzamos grado 4 por aplanado, la esquina mínima conocida.
- **Pendiente:** reducir el número de incógnitas *a grado fijo 4*. Hoy 42 para los primos; la
  pregunta abierta es cuánto se puede bajar sin subir el grado.

### 6.3 Puente entre las dos islas del repo
El proyecto tiene dos subsistemas maduros **sin un solo import entre ellos**: el colapso de
trazas (β, dominancia de dígitos) y el cálculo diofántico. La técnica es la misma matemática,
pero `check_beta_trajectory` **ejecuta** un bucle `for i in range(T)` — el cuantificador acotado
se evalúa en vez de eliminarse. Construir ese puente es trabajo pendiente.

---

## 7. Lo que NO se puede afirmar (para no repetir la historia de la "Ecuación Suprema")

- **No hemos batido ningún récord**, ni lo hemos intentado con éxito.
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
