# Formalización en Lean 4

## Qué hay aquí

`CotaA.lean` — demostración **verificada por el núcleo de Lean 4** de que toda
solución sobre ℕ del sistema (1) de Jones–Sato–Wada–Wiens cumple **`n ≥ 2`** y
**`a ≥ 2`**.

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
`a = A + 2`, y con ella la cifra **(33, 5)**.

## Garantías, y sus límites

| qué | estado |
|---|---|
| compila con Lean 4.33.1 | ✅ |
| `sorry` / `admit` / `axiom` / `native_decide` | ninguno |
| axiomas de los que depende | `propext`, `Classical.choice`, `Quot.sound` — los tres estándar |
| dependencias externas | **ninguna**; no usa Mathlib |
| el enunciado es el que se cree | comprobado por `test_lean_cota_a.py` |

Esa última fila es la que suele faltar. Que un fichero compile garantiza que la
**demostración** es correcta, no que el **enunciado** sea el que uno quería: un
teorema formal de un enunciado equivocado parece más fuerte y vale menos. El test
extrae las cinco hipótesis del `.lean` y comprueba con sympy que cada una es
equivalente a su ecuación en `dioph_jsww.ECUACIONES`, y que aparecen
literalmente en el fichero.

**Lo que este teorema NO dice:** nada sobre que el sistema (1) represente los
primos. Eso es de JSWW (1976) y aquí se cita.

## Detalles técnicos

* **Sobre ℕ y sin restas.** Las ecuaciones de JSWW están sobre ℤ con variables en
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
