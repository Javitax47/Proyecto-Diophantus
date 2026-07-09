#!/usr/bin/env python3
"""
Portfolio asset #5 -- Convergencia de Apery para zeta(3), estilo publicacion.

Fondo blanco, serif (STIX), monocromo, reglas finas, caption de figura.
Reproduce la tesis de scripts/accelerate.py: la fraccion continua polinomica que
el motor RECUPERA para zeta(3),

    a(n) = -n^6 ,   b(n) = (2n+1)(17 n^2 + 17 n + 5)   ->   6 / zeta(3),

converge geometricamente (~3 digitos por termino) frente a la serie sum 1/n^3.

Genera frames y los ensambla con ffmpeg en:
    portfolio_assets/apery_convergence.mp4
    portfolio_assets/apery_convergence.gif
"""
import os
import math
import shutil
import subprocess
import mpmath as mp
import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter

mp.mp.dps = 55

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 12,
    "axes.edgecolor": "black",
    "axes.linewidth": 0.8,
    "text.color": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

INK  = "#000000"
GRAY = "#606060"

N = 12
SCRATCH = os.environ.get("CLAUDE_SCRATCH",
    r"C:\Users\Javier\AppData\Local\Temp\claude\C--Users-Javier-Desktop-Proyecto-Diophantus\ba169c17-9c05-414a-b88d-15c9bee4e36b\scratchpad")
FRAMES = os.path.join(SCRATCH, "apery_frames")
OUT = "portfolio_assets"


def compute():
    z3 = mp.zeta(3)
    z3s = mp.nstr(z3, 22)

    def b(n): return (2 * n + 1) * (17 * n * n + 17 * n + 5)
    def a(n): return -n**6

    hm1, h0 = mp.mpf(1), mp.mpf(b(0))
    km1, k0 = mp.mpf(0), mp.mpf(1)
    naive = mp.mpf(0)

    ap_err, nv_err, ap_val = [], [], []
    for n in range(1, N + 1):
        h = b(n) * h0 + a(n) * hm1
        k = b(n) * k0 + a(n) * km1
        hm1, h0 = h0, h
        km1, k0 = k0, k
        est = 6 * k / h
        naive += mp.mpf(1) / n**3
        ap_err.append(float(abs(est - z3)))
        nv_err.append(float(abs(naive - z3)))
        ap_val.append(mp.nstr(est, 22))
    return z3s, ap_err, nv_err, ap_val


def correct_digits(est, z3s):
    k = 0
    for ca, cb in zip(est, z3s):
        if ca != cb:
            break
        k += 1
    return max(0, k - 2)  # descontar "1."


def draw_frame(idx, head, tprog, xs, ap_err, nv_err, ap_val, z3s):
    fig = plt.figure(figsize=(8.2, 5.4), dpi=170)
    ax = fig.add_axes([0.115, 0.125, 0.845, 0.66])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_yscale("log")
    ax.set_xlim(0.5, N + 0.5)
    ax.set_ylim(1e-41, 1e1)
    ax.set_xticks(range(1, N + 1))
    ax.tick_params(labelsize=11)
    ax.set_yticks([10.0 ** e for e in range(0, -41, -5)])
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=(1.0,), numticks=40))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="y", color="0.88", lw=0.6, zorder=0)
    ax.set_xlabel("número de términos  $n$", fontsize=13)
    ax.set_ylabel(r"error absoluto  $|\,\hat\zeta(3)-\zeta(3)\,|$", fontsize=13)

    def partial(err):
        xr = list(xs[:head]); yr = list(err[:head])
        if head >= 1 and 0 < tprog and head < N:
            x0, x1 = xs[head - 1], xs[head]
            ly0, ly1 = math.log10(err[head - 1]), math.log10(err[head])
            xr.append(x0 + (x1 - x0) * tprog)
            yr.append(10 ** (ly0 + (ly1 - ly0) * tprog))
        return xr, yr

    # Serie ingenua: linea discontinua gris, marcador cuadrado hueco
    xr, yr = partial(nv_err)
    ax.plot(xr, yr, "--", color=GRAY, lw=1.3, zorder=2)
    ax.plot(xs[:head], nv_err[:head], "s", mfc="white", mec=GRAY, mew=1.1,
            ms=6, zorder=3, label=r"serie ingenua  $\sum_{n\geq1} n^{-3}$")

    # Apery PCF: linea continua negra, marcador circular relleno
    xr, yr = partial(ap_err)
    ax.plot(xr, yr, "-", color=INK, lw=1.6, zorder=4)
    ax.plot(xs[:head], ap_err[:head], "o", mfc=INK, mec=INK, ms=5, zorder=5,
            label="fracción continua de Apéry")
    if xr:
        ax.plot([xr[-1]], [yr[-1]], "o", mfc=INK, mec="white", mew=1.0,
                ms=7, zorder=6)

    leg = ax.legend(loc="lower left", frameon=True, fontsize=11,
                    handlelength=2.4, borderpad=0.6)
    leg.get_frame().set_edgecolor("0.6")
    leg.get_frame().set_linewidth(0.7)

    # Estado (sobrio, sin color): n y digitos correctos
    est = ap_val[head - 1] if head >= 1 else "1."
    kd = correct_digits(est, z3s)
    ax.text(0.97, 0.62, f"$n = {head}$\n{kd} dígitos correctos",
            transform=ax.transAxes, ha="right", va="top", fontsize=12,
            linespacing=1.6,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.7", lw=0.7))

    # Titulo + forma recuperada
    fig.text(0.5, 0.955, "Convergencia de la fracción continua de Apéry para  $\\zeta(3)$",
             ha="center", va="center", fontsize=15)
    fig.text(0.5, 0.905,
             r"forma recuperada:  $a_n=-n^6,\quad b_n=(2n+1)(17n^2+17n+5)\ \longrightarrow\ 6/\zeta(3)$",
             ha="center", va="center", fontsize=11.5, color=GRAY)

    path = os.path.join(FRAMES, f"f{idx:04d}.png")
    fig.savefig(path)
    plt.close(fig)


def render():
    z3s, ap_err, nv_err, ap_val = compute()
    xs = list(range(1, N + 1))
    if os.path.isdir(FRAMES):
        shutil.rmtree(FRAMES)
    os.makedirs(FRAMES)

    K = 5
    idx = 0
    for _ in range(6):
        draw_frame(idx, 1, 0.0, xs, ap_err, nv_err, ap_val, z3s); idx += 1
    for head in range(1, N):
        for s in range(1, K + 1):
            draw_frame(idx, head, s / K, xs, ap_err, nv_err, ap_val, z3s); idx += 1
        draw_frame(idx, head + 1, 0.0, xs, ap_err, nv_err, ap_val, z3s); idx += 1
    for _ in range(22):
        draw_frame(idx, N, 0.0, xs, ap_err, nv_err, ap_val, z3s); idx += 1
    print(f"[OK] {idx} frames -> {FRAMES}")
    return idx


def encode():
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(FRAMES, "f%04d.png").replace("\\", "/")
    mp4 = os.path.join(OUT, "apery_convergence.mp4").replace("\\", "/")
    gif = os.path.join(OUT, "apery_convergence.gif").replace("\\", "/")
    pal = os.path.join(FRAMES, "palette.png").replace("\\", "/")
    fps = "15"
    even = "scale=trunc(iw/2)*2:trunc(ih/2)*2"

    subprocess.run(["ffmpeg", "-y", "-framerate", fps, "-i", src,
                    "-vf", even, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-framerate", fps, "-i", src,
                    "-vf", "scale=1100:-1:flags=lanczos,palettegen", pal], check=True)
    subprocess.run(["ffmpeg", "-y", "-framerate", fps, "-i", src, "-i", pal,
                    "-filter_complex",
                    "scale=1100:-1:flags=lanczos[x];[x][1:v]paletteuse", gif], check=True)
    print(f"[OK] {mp4}")
    print(f"[OK] {gif}")


if __name__ == "__main__":
    render()
    encode()
