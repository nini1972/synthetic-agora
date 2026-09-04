"""ADLER GAMMA UNIFICATION: all disputed resonance-gap exponents as
finite-window local slopes of the exact Adler curve R = delta - sqrt(delta^2-1).
Two-cluster Kuramoto -> relative phase obeys phi' = Dw - 2 K_eff sin(phi).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

K0 = 2.0
dd = np.linspace(1.000001, 60, 400000)
x = 2*K0*dd           # = Dw
y = dd - np.sqrt(dd**2 - 1)   # exact |<e^{i phi}>| period-avg
lx, ly = np.log(x), np.log(y)

# (lineage, reported gamma, window [xlo, xhi])
claims = [
    ("EMP-030 peak (~2.2)",        2.2,  (4.0, 5.0)),
    ("CRT-004 steep (1.58-2.09)",  1.90, (4.0, 6.0)),
    ("EMP-020 (1.58-1.60)",        1.59, (4.5, 7.0)),
    ("DOSSIER_003 / EMP-015 (1.38 / 1.34-1.44)", 1.38, (4.0, 10.0)),
    ("CRT-004 tail (0.86-1.08)",   1.01, (15.0, 60.0)),
]
fig, ax = plt.subplots(figsize=(9, 6.5))
ax.loglog(x, y, 'k-', lw=2, label=r"Exact Adler: $R=\delta-\sqrt{\delta^2-1}$, $\delta=\Delta\omega/2K_{eff}$")
colors = plt.cm.tab10(np.linspace(0, 1, len(claims)))
for (name, g_rep, (a, b)), c in zip(claims, colors):
    m = (x >= a) & (x <= b)
    g, c0 = np.polyfit(lx[m], ly[m], 1)
    yfit = np.exp(c0) * x[m]**g
    ax.loglog(x[m], yfit, '-', color=c, lw=3, alpha=0.85)
    ax.annotate(f"{name}\nfit γ={-g:.3f}", xy=(x[m][len(x[m])//2], yfit[len(yfit)//2]),
                fontsize=7.5, color=c, xytext=(6, 6), textcoords='offset points')
ax.axhline(1.0, color='gray', ls=':', lw=0.8)
ax.set_xlabel(r'$\Delta\omega$'); ax.set_ylabel(r'$R_{cross}(\Delta\omega)$')
ax.set_title("One curve, many exponents: the γ-controversy as windowed slopes of the Adler law\n(asymptotic invariant: γ=1; near-threshold windows yield 1.3–2.5)")
ax.legend(loc='lower left', fontsize=9); fig.tight_layout()
out = "../../shared_agora/artifacts"
os.makedirs(out, exist_ok=True)
fig.savefig(f"{out}/adler_gamma_unification.png", dpi=130)
# dump numeric table
with open(f"{out}/adler_gamma_unification.txt", "w") as f:
    f.write("lineage_claim\treported\twindow\tfitted_local_gamma\n")
    for name, g_rep, (a, b) in claims:
        m = (x >= a) & (x <= b)
        g, _ = np.polyfit(lx[m], ly[m], 1)
        f.write(f"{name}\t{g_rep}\t[{a},{b}]\t{-g:.3f}\n")
print("saved", f"{out}/adler_gamma_unification.png")
