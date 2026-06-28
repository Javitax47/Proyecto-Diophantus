# Catálogo de ejemplos (corpus `src/examples/`)

> 27 programas en C "Diophantine-Compliant" que el compilador convierte en sistemas
> diofánticos genuinos. Organizados por nivel. Los marcados **(nuevo)** se añadieron
> en la última ronda de enriquecimiento. Todos los de las tablas Básico/Avanzado/
> Primalidad compilan a sistemas polinómicos (verificado con `diophantus.py` y por el
> test E2E `test_corpus_e2e.py`).
>
> Compilar cualquiera:  `python diophantus.py src/examples/<archivo>.c`
> El sistema PURE queda en `output/<archivo>_pure_poly_system.txt`.

---

## 🟢 Nivel BÁSICO — recurrencias simples (verifican el núcleo de arithmetización)

| Ejemplo | Qué computa | Qué demuestra |
|---|---|---|
| `countdown.c` | k + (k−1) + … + 1 (acumulador) | tail-recursión → sistema acoplado |
| `gcd.c` **(nuevo)** | MCD por Euclides `gcd(a,b)=gcd(b,a%b)` | módulo + recursión no estructural |
| `factorial.c` **(nuevo)** | k! con acumulador | producto acumulado |
| `sum_squares.c` **(nuevo)** | 1²+2²+…+k² | acumulador no lineal; forma cerrada k(k+1)(2k+1)/6 contrastable |
| `linrec.c` | x → 2x+1 | recurrencia lineal de 1 variable |
| `fib.c` | Fibonacci (a,b)→(b,a+b) | recurrencia lineal acoplada (el motor halla su forma cuadrática) |

## 🔵 Nivel AVANZADO — estructura algebraica rica

| Ejemplo | Qué computa | Qué demuestra |
|---|---|---|
| `pell.c` | (x,y)→(3x+4y,2x+3y) | el motor **descubre** el invariante `x²−2y²` (no inyectado) |
| `tribonacci.c` **(nuevo)** | (a,b,c)→(b,c,a+b+c) | recurrencia lineal de 3 términos (companion 3×3) |
| `lucas_seq.c` **(nuevo)** | Lucas Vₙ = 3Vₙ₋₁ − Vₙ₋₂ | base del test de Lucas; conecta con Baillie-PSW |
| `markov_triple.c` **(nuevo)** | (x,y,z)→(y,z,3yz−x) | el motor **descubre y certifica** `x²+y²+z²−3xyz` (ecuación de Markov) |
| `collatz.c` | trayectoria de Collatz (3n+1)/2 | transición no afín polinómica; colapso de traza |
| `collatz_cycle.c` | sistema de ciclos de Collatz | no-existencia certificada de ciclos cortos (Z3 UNSAT) |
| `massive_loop.c` | bucle lineal gigantesco | estrés del runtime de pila / colapso lineal |
| `avalanche.c` | carga pesada (PDA) | estrés del compilador y la VM |

## 🟣 Nivel PRIMALIDAD — tests de primalidad (correctos y heredados auditados)

| Ejemplo | Qué computa | Estado |
|---|---|---|
| `trial_division.c` **(nuevo)** | división de prueba hasta √n | ✅ **correcto y exacto** |
| `wilson.c` **(nuevo)** | teorema de Wilson (n−1)!≡−1 (mod n) | ✅ correcto (criterio exacto) |
| `fermat.c` | Fermat base 2: 2ⁿ⁻¹≡1 | ⚠️ acepta pseudoprimos de Fermat (didáctico) |
| `primes_lucas.c` | estructura del test de Lucas | simbólico (placeholder para el optimizador) |
| `primes_solovay_64.c` | Solovay-Strassen (símbolo de Jacobi) | test probabilístico |
| `primes_innovative.c` | "ecuación logarítmica" | 🏛️ heredado, **auditado como defectuoso** (ver `test_primality_audit.py`) |
| `primes_ecpp_final.c` | "ECPP determinista" | 🏛️ heredado, **auditado: no es prueba** (compuestos la pasan) |

> La implementación de primalidad **correcta y de referencia** del proyecto NO es un
> ejemplo en C sino `src/analysis/primality.py` (Baillie-PSW determinista < 3.3·10²⁴).

## 🟠 Nivel INNOVADOR / APLICACIONES — seguridad, contratos, cripto, simulación

| Ejemplo | Dominio | Qué demuestra |
|---|---|---|
| `crackme_license.c` | seguridad / reversing | validación de licencia como sistema diofántico (¿clave válida?) |
| `vault_attack.c` | seguridad | condición de apertura de una "bóveda" → ¿alcanzable? |
| `token_sale.c` | smart contract | lógica de venta de tokens (el ángulo Certora/verificación) |
| `mini_sha_mining.c` | cripto | minería SHA simplificada (preimagen acotada) |
| `arb_kernel_tax.c` | DeFi / aritmética | kernel aritmético de impuestos/arbitraje |
| `pong.c` | simulación | juego completo en la VM de pila infinita (runtime) |

---

## Cómo los ejemplos alimentan al resto del proyecto

- **Arithmetización fiel** (Fase 0-1): cada ejemplo → sistema PURE polinómico, validado por `test_corpus_e2e.py`.
- **Descubrimiento** (Fase 4): `pell.c`, `fib.c`, `markov_triple.c`, `tribonacci.c`, `lucas_seq.c` → el motor halla y **certifica** sus invariantes sin que se le inyecten.
- **Certificados portables** (producto): los ejemplos de aplicación (`token_sale.c`, `vault_attack.c`, `crackme_license.c`) son los casos de uso del verificador `src/product/` — "este contrato NO puede alcanzar este estado" con certificado re-verificable.
- **Primalidad**: `trial_division.c`/`wilson.c` (correctos) contrastan con los heredados auditados, documentando honestamente qué es y qué no es una prueba.
