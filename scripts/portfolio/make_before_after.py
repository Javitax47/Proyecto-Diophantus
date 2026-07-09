#!/usr/bin/env python3
"""
Portfolio asset #2 -- "Antes / Despues", estilo publicacion (paper).

Fondo blanco, tipografia serif (STIX / Computer-Modern-like), monocromo, reglas
finas y caption de figura. Sin cajas redondeadas ni colores de "IDE".

Izquierda: extracto real de src/examples/fermat.c.
Derecha:   el sistema diofantico equivalente que emite el compilador
           (formula operacional + primeros terminos del certificado suma-de-
           cuadrados, tal cual output/fermat_mathematical_formula.txt).

Salida: portfolio_assets/before_after_fermat.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

# ---- Estilo paper ----------------------------------------------------------
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 11,
    "text.color": "black",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

INK   = "#000000"
GRAY  = "#555555"
LIGHT = "#f5f5f5"

# ---- Extracto real de src/examples/fermat.c --------------------------------
CODE = """// src/examples/fermat.c  (extracto)
int n = 0;          // entrada
int is_prime = 0;   // salida: 1=primo, 0=compuesto

// Exponenciacion modular recursiva  O(log exp)
int power_mod(int base, int exp, int mod){
    if (exp == 0) return 1;
    if (exp == 1) return base % mod;
    int half    = power_mod(base, exp/2, mod);
    int half_sq = (half * half) % mod;
    if (exp % 2 == 0) return half_sq;
    return (half_sq * base) % mod;
}

// Test de Fermat base 2:  2^(n-1) == 1 (mod n)
int fermat_test(int c){
    if (c % 2 == 0) return c == 2;
    return power_mod(2, c-1, c) == 1;
}"""


def frame_axes(ax, facecolor="white"):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_facecolor(facecolor)
    for s in ax.spines.values():
        s.set_edgecolor(INK); s.set_linewidth(0.8)


def draw_code(ax):
    frame_axes(ax, LIGHT)
    lines = CODE.split("\n")
    y = 0.965
    dy = 0.93 / len(lines)
    for ln in lines:
        stripped = ln.lstrip()
        if stripped.startswith("//"):
            color, style = GRAY, "italic"
        else:
            color, style = INK, "normal"
        ax.text(0.04, y, ln, color=color, family="monospace", fontsize=10.5,
                va="top", ha="left", transform=ax.transAxes, style=style)
        y -= dy


def draw_equation(ax):
    frame_axes(ax, "white")

    def T(x, y, s, fs=12, color=INK, ha="left"):
        ax.text(x, y, s, color=color, fontsize=fs, va="top", ha=ha,
                transform=ax.transAxes)

    T(0.05, 0.95, r"$P(x_1,\ \ldots\ ,\ x_{180}) \;=\; 0$", fs=17)
    T(0.05, 0.875, r"solución entera existe $\Leftrightarrow$ el programa termina", fs=10.5, color=GRAY)
    ax.plot([0.05, 0.95], [0.845, 0.845], color=INK, lw=0.6,
            transform=ax.transAxes)

    # Forma operacional (real, del .txt)
    T(0.05, 0.78,
      r"$f(N)=\sum_{R=0}^{\infty} R\left\lfloor \dfrac{1}{1+\mathcal{D}(N,R,\mathbf{x})} \right\rfloor$",
      fs=15)

    T(0.05, 0.63,
      r"$\mathcal{D}(N,R,\mathbf{x})=\sum_{\mathbf{x}\in\mathbb{N}^{180}}\left(\ \cdots\ \right)^2 = 0$",
      fs=13)

    terms = [
        r"$\left(exp-(2\,\epsilon_2+\epsilon_1)\right)^2$",
        r"$+\ \left(\epsilon_4-(2-1)\right)^2$",
        r"$+\ \left(\epsilon_3\,(1-\epsilon_3)\right)^2$",
        r"$+\ \left(\epsilon_3(\epsilon_4-\epsilon_1-(\epsilon_5^2+\epsilon_6^2+\epsilon_7^2+\epsilon_8^2))\right)^2$",
        r"$+\ \left((1-\epsilon_3)(\epsilon_1-\epsilon_4-1-(\epsilon_9^2+\epsilon_{10}^2+\epsilon_{11}^2+\epsilon_{12}^2))\right)^2$",
        r"$\vdots$",
    ]
    y = 0.52
    for t in terms:
        T(0.08, y, t, fs=11.5)
        y -= 0.066
    T(0.08, y - 0.005, r"$+\ \ (147\ \mathrm{t\acute{e}rminos\ restantes})$", fs=11.5, color=GRAY)


def main():
    fig = plt.figure(figsize=(13, 7.3), dpi=170)

    fig.text(0.5, 0.955,
             "Compilación de un algoritmo a una ecuación diofántica",
             fontsize=15, ha="center", va="center")
    fig.text(0.5, 0.912,
             r"Teorema de Matiyasevich (MRDP, 1970)",
             fontsize=11, ha="center", va="center", color=GRAY, style="italic")

    ax_code = fig.add_axes([0.045, 0.06, 0.42, 0.775])
    ax_eq   = fig.add_axes([0.535, 0.06, 0.42, 0.775])

    # Encabezados de panel
    fig.text(0.045, 0.845, r"(a)  Entrada: algoritmo en C", fontsize=11.5,
             ha="left", va="bottom", style="italic")
    fig.text(0.535, 0.845, r"(b)  Salida: sistema diofántico", fontsize=11.5,
             ha="left", va="bottom", style="italic")

    draw_code(ax_code)
    draw_equation(ax_eq)

    ar = FancyArrowPatch((0.468, 0.485), (0.532, 0.485),
                         transform=fig.transFigure, mutation_scale=18,
                         lw=1.1, color=INK, arrowstyle="-|>")
    fig.patches.append(ar)
    fig.text(0.5, 0.515, "compila", fontsize=10.5, ha="center", va="bottom",
             style="italic", color=GRAY)
    fig.text(0.5, 0.455, "MRDP", fontsize=9, ha="center", va="top", color=GRAY)

    out = os.path.join("portfolio_assets", "before_after_fermat.png")
    fig.savefig(out, dpi=170)
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
