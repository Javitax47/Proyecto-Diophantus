# Formalización en Lean 4

## Qué hay aquí

Cinco ficheros, todos verificados por el núcleo de Lean 4 y **sin Mathlib**.

`Aplanado.lean` — **generado** por `dioph_lean.py`, no escrito a mano: el
aplanado a grado 2 del sistema (1), o sea el **(44, 5)**. Llevaba tiempo en el
repo sin compilar y sin auditar; era el artefacto del noveno defecto. Al
arreglarlo aparecieron **tres** defectos de enunciado en el generador, dos de
ellos capaces de producir un fichero que compila diciendo otra cosa (ver el
registro). Ahora compila, está en `verificar.sh` y `test_lean_aplanado.py`
comprueba su enunciado **posicionalmente** — que es lo único que caza un
argumento de menos.

`Pell.lean` — la ecuación `x² − (A²−1)y² = 1` desde cero: **completitud** (toda
solución está en la sucesión, por descenso), **congruencia** (`Y j ≡ j mod A−1`)
y **crecimiento**. Con ellas, `a ≥ e+1` en el sistema (1), a partir de sólo tres
de sus catorce ecuaciones. Existe porque esos tres hechos se estaban *citando*.

`Eliminacion21.lean` — usando esas cotas, **25 incógnitas ⟶ 20**: generador
**(21, 25)**, cinco variables por debajo del (26, 25) publicado.

`Eliminacion.lean` — **el resultado del proyecto**: el sistema (1) de
Jones–Sato–Wada–Wiens, que ellos publican con 25 incógnitas más el parámetro
(generador de **26 variables y grado 25**), es **equisatisfacible** con uno de
22 incógnitas del mismo grado — generador de **(23, 25)**, tres variables por
debajo del suyo.

```
theorem equisatisfacible (k : Int) (hk : 0 ≤ k) :
    (∃ a b c d e f g h i j l m n o p q r s t u v w x y z : Int,
        (0 ≤ a ∧ … ∧ 0 ≤ z) ∧ completo k a … z)
  ↔ (∃ a b c d e f g h i j l m n o p     r s t u v w x     : Int,
        (0 ≤ a ∧ … ∧ 0 ≤ x) ∧ reducido k a … x)
```

Es formalizable justamente porque **no hay aplanado, ni optimizador, ni
reescritura**: son tres sustituciones lineales. Las ecuaciones (1), (2) y (9)
determinan `q`, `z` e `y`, y sus definiciones tienen todos los coeficientes **no
negativos** — que es lo que hace válida la vuelta sobre ℕ, y aquí deja de ser un
criterio implementado en Python para ser tres lemas (`defZ_nonneg`, `defQ_nonneg`,
`defY_nonneg`).

`CotaA.lean` — demostración de que toda solución sobre ℕ del sistema (1) cumple
**`n ≥ 2`** y **`a ≥ 2`**.

```
theorem a_ge_two {a e f k l n o p q v x y z : Nat}
    (h3 : 2 * n + p + q + z = e)
    (h4 : ec4 k n f)                                  -- 16(k+1)³(k+2)(n+1)²+1 = f²
    (h5 : ec5 e a o)                                  -- e³(e+2)(a+1)²+1 = o²
    (h6 : a ^ 2 * y ^ 2 + 1 = y ^ 2 + x ^ 2)          -- (a²−1)y²+1 = x²
    (h9 : n + l + v = y) : 2 ≤ a
```

## Por qué este teorema y no otro

Es **el único resultado propio del proyecto que no depende de que el sistema (1)
represente los primos**. Es un enunciado sobre las soluciones del sistema, sea
cual sea el conjunto que represente. Todo lo demás que hace el proyecto se apoya
en el teorema de JSWW, que se **cita**; esto no. Por tanto es lo único que se
puede verificar de arriba abajo sin importar nada de fuera.

Y no es un teorema decorativo: es lo que justifica la reparametrización
`a = A + 2`, que da los puntos altos de la frontera. (Aquí ponía «y con ella la
cifra (33, 5)»; esa cifra está **retirada** — venía de la ruta de reescritura del
aplanado, que certificaba conjuntos no materializables.)

Lo mismo vale, y más, para `Eliminacion.lean`: tampoco depende de que (1)
represente los primos. Dice que las dos formulaciones tienen **las mismas
soluciones**, que es exactamente donde este proyecto se ha equivocado nueve veces
con la maquinaria de aplanado. Por eso se formaliza justo esto: es el único punto
que mejora a la literatura y el único lo bastante simple para verificarlo entero.

## Garantías, y sus límites

| qué | estado |
|---|---|
| compila con Lean 4.33.1 | ✅ |
| `sorry` / `admit` / `axiom` / `native_decide` | ninguno |
| axiomas de los que depende | `propext`, `Classical.choice`, `Quot.sound` — los tres estándar |
| dependencias externas | **ninguna**; no usa Mathlib |
| el enunciado es el que se cree | comprobado por `test_lean_cota_a.py` y `test_lean_eliminacion.py` |

Esa última fila es la que suele faltar. Que un fichero compile garantiza que la
**demostración** es correcta, no que el **enunciado** sea el que uno quería: un
teorema formal de un enunciado equivocado parece más fuerte y vale menos. El test
extrae las cinco hipótesis del `.lean` y comprueba con sympy que cada una es
equivalente a su ecuación en `dioph_jsww.ECUACIONES`, y que aparecen
literalmente en el fichero.

**Lo que estos teoremas NO dicen:** nada sobre que el sistema (1) represente los
primos. Eso es de JSWW (1976) y aquí se cita. `Eliminacion.lean` tampoco dice
nada sobre el **grado**: que el sistema reducido siga en grado 12 —y por tanto el
generador en 25— se mide en `dioph_degree`, no se demuestra aquí. Lo que se
verifica es la parte donde estaba el riesgo: que las soluciones sean las mismas.

### Cómo se comprueba el enunciado de `Eliminacion.lean`

Es más largo que en `CotaA.lean` porque hay más superficie donde equivocarse —
catorce ecuaciones escritas a mano más once. `test_lean_eliminacion.py` extrae del
`.lean`:

1. las **14** ecuaciones de `completo`, y las empareja **1 a 1** con
   `ECUACIONES` (que «exista alguna que case» taparía una repetida y una ausente);
2. las tres definiciones, contra las que produce `eliminar_lineales`;
3. las **11** ecuaciones de `reducido`, también 1 a 1;
4. las **listas de variables cuantificadas**: 25 y 22, y que la diferencia sea
   exactamente `{q, y, z}`. Sin esta cuarta comprobación el teorema podría estar
   cuantificando de menos y ser cierto por vacío.

## Detalles técnicos

* **`Eliminacion.lean` va sobre ℤ con `0 ≤ ·` explícito**, al revés que
  `CotaA.lean`. Las ecuaciones de JSWW tienen restas (`a²−1`, `a−n−1`, `u²−a`)
  que sobre `Nat` se truncarían; modelarlas en ℤ con la no negatividad como
  hipótesis es equivalente y deja las ecuaciones **literalmente** como están
  publicadas, que es lo que permite cotejar la transcripción a ojo.
* **En `CotaA.lean`, sobre ℕ y sin restas.** Las ecuaciones de JSWW están sobre ℤ con variables en
  ℕ. Aquí los términos negativos pasan al otro lado: `(a²−1)y² + 1 − x² = 0` se
  escribe `a²y² + 1 = y² + x²`. La resta truncada de ℕ convierte un error de signo
  en un teorema que sigue compilando y ya no dice lo mismo; de ahí el test.
* **Cinco hipótesis de catorce.** El teorema usa solo las ecuaciones (3), (4),
  (5), (6) y (9). Menos hipótesis ⇒ teorema más fuerte.
* **Sin Mathlib.** El núcleo de Lean 4.33 trae `grind`, que normaliza anillos y
  cierra las identidades polinómicas de grado 4 que necesita el encaje. `ring` sí
  es de Mathlib y no hace falta.
* **La única ayuda manual** es la monotonía del cuadrado en el paso `a = 0`:
  `grind` no la aplica sola y sin ella `2 ≤ y` no contradice `y² + x² = 1`.

## Reproducir

```bash
./verificar.sh          # descarga Lean si hace falta, compila, audita axiomas y enunciado
```
