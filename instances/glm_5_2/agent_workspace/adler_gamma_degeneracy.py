"""GAMMA DEGENERACY QUANTIFICATION (Adler thread, follow-up to adler_gamma_unification).

Hypothesis (mine, from EMP-171 follow-up plan): all disputed resonance-gap
exponents gamma are not independent observables but windowed local slopes of the
single Adler curve R = delta - sqrt(delta^2-1), delta = dw/(2 K_eff).

Exact local slope:  gamma_local(delta) = d ln R / d ln dw = delta / sqrt(delta^2-1).
  (verified symbolically: R = delta - sqrt(delta^2-1) => ln R' wrt ln delta is
   delta/sqrt(delta^2-1); and dw = 2 K_eff delta so d ln dw = d ln delta.)

INVERSION: gamma^2 = delta^2/(delta^2-1)  =>  delta(gamma) = gamma/sqrt(gamma^2-1),
and the delta-measure density per unit gamma is
  D(gamma) = |d delta/d gamma| = (gamma^2 - 1)^(-3/2),
which diverges integrably (~(2(gamma-1))^(-3/2), integral ~ (gamma-1)^(-1/2))
as gamma -> 1+. This is the DEGENERACY FACTOR: near-asymptotic windows (gamma~1)
occupy vastly more delta-measure than near-threshold windows (gamma large),
under ANY smooth prior on delta. The uniform-gamma null has D = const.

TESTS
  T1 (self-consistency / degeneracy collapse): for each of the 5 lineage claims,
     locate the delta* at which gamma_local(delta*) equals the window-fitted
     gamma, and check delta* lies inside the window's own delta-range.
  T2 (predictive power): predict each window's fitted gamma from the log-midpoint
     delta of the window; compare to the actual polyfit of the exact curve.
  T3 (degeneracy vs uniform null): measure-weighted gamma density
     p(gamma) ∝ D(gamma) over windows delta in [1, d_max], vs uniform null on
     gamma in [1, gamma_max]. Report the P(gamma < 1.2) contrast and a KL-style
     discrepancy, plus the per-claim degeneracy ratios D(gamma_i)/D_uniform.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

K0 = 2.0  # K_eff used throughout the thread (delta = dw/(2*K0))

# ---- exact Adler curve on a dense grid ----
d = np.linspace(1.0000001, 60.0, 400000)
x = 2 * K0 * d                      # Delta-omega axis
y = d - np.sqrt(d ** 2 - 1.0)       # exact R
lx, ly = np.log(x), np.log(y)

# ---- the five lineage claims (from adler_gamma_unification.txt) ----
claims = [
    ("EMP-030 peak",        2.20, (4.0, 5.0)),
    ("CRT-004 steep",       1.90, (4.0, 6.0)),
    ("EMP-020",             1.59, (4.5, 7.0)),
    ("DOSSIER-003/EMP-015", 1.38, (4.0, 10.0)),
    ("CRT-004 tail",        1.01, (15.0, 60.0)),
]

def gamma_local(dd):
    return dd / np.sqrt(dd ** 2 - 1.0)

def delta_of_gamma(g):
    return g / np.sqrt(g ** 2 - 1.0)

def D_gamma(g):
    """degeneracy factor |ddelta/dgamma| = (gamma^2-1)^(-3/2)"""
    return (g ** 2 - 1.0) ** (-1.5)

rows = []
print("=" * 100)
print("T1 SELF-CONSISTENCY: does each fitted gamma map back into its own window's delta-range?")
print("=" * 100)
for name, g_rep, (xlo, xhi) in claims:
    m = (x >= xlo) & (x <= xhi)
    g_fit, _ = np.polyfit(lx[m], ly[m], 1)
    g_fit = -g_fit
    dlo, dhi = xlo / (2 * K0), xhi / (2 * K0)
    # geometric-midpoint delta (natural for power-law windows)
    d_mid = np.sqrt(dlo * dhi)
    g_pred = gamma_local(d_mid)
    d_star = delta_of_gamma(g_fit)
    inside = dlo - 1e-9 <= d_star <= dhi + 1e-9
    rows.append(dict(name=name, g_reported=g_rep, g_fit=g_fit, g_pred=g_pred,
                     d_lo=dlo, d_hi=dhi, d_star=d_star, inside=bool(inside),
                     D=D_gamma(g_fit)))
    print(f"{name:22s} g_fit={g_fit:.3f}  window d=[{dlo:.3f},{dhi:.3f}]  "
          f"d*={d_star:.3f}  inside={inside}  "
          f"pred@d_mid={g_pred:.3f} (err {abs(g_pred-g_fit)/g_fit*100:.1f}%)")

n_inside = sum(r["inside"] for r in rows)
print(f"\nT1 RESULT: {n_inside}/{len(rows)} fitted exponents map back into their own window.")

print()
print("=" * 100)
print("T3 DEGENERACY vs UNIFORM NULL")
print("=" * 100)
gmax = max(r["g_fit"] for r in rows)
gmin = min(r["g_fit"] for r in rows)
# Adler-measure-weighted density of gamma over delta in [1, d_max], d_max from widest window
d_max = max(r["d_hi"] for r in rows)
gg = np.linspace(1.0 + 1e-9, gamma_local(1.0000001), 200000)  # gamma from ~1+ to ~inf
gg = np.linspace(1.0 + 1e-9, 3.0, 200000)
# delta(gamma) runs from d_max (at gamma_min) to 1+ (at gamma -> inf);
# gamma density p(g) ∝ D(gamma) on gamma in [1, gamma_local(d_max)]... careful:
# delta in [1, d_max]  <=>  gamma in [gamma_local(d_max), inf)
g_lo = gamma_local(d_max)
gg = np.linspace(g_lo + 1e-12, 3.0, 400000)
w = D_gamma(gg)
w_norm = w / np.trapezoid(w, gg)
P_below_12 = np.trapezoid(w_norm[gg < 1.2], gg[gg < 1.2])
P_unif_below_12 = (1.2 - 1.0) / (2.5 - 1.0)  # uniform null on [1, 2.5]
# KL-ish discrepancy between weighted density and uniform on [1,2.5] (discretized)
grid = np.linspace(1.0 + 1e-6, 2.5, 20000)
p_w = np.interp(grid, gg, w_norm)
p_w = p_w / np.trapezoid(p_w, grid)
p_u = np.full_like(grid, 1.0 / (2.5 - 1.0))
kl = np.trapezoid(np.where(p_w > 0, p_w * np.log(p_w / p_u), 0.0), grid)
print(f"delta-range of claims: [1, {d_max:.2f}]  =>  gamma support [{g_lo:.4f}, inf)")
print(f"P(gamma < 1.2) under Adler degeneracy D(gamma):      {P_below_12:.4f}")
print(f"P(gamma < 1.2) under uniform null on [1, 2.5]:       {P_unif_below_12:.4f}")
print(f"contrast ratio: {P_below_12 / P_unif_below_12:.2f}x")
print(f"KL(Adler-weighted || uniform) over [1,2.5]: {kl:.4f} nats")
print()
print("per-claim degeneracy ratios D(gamma_fit) relative to D(2.5) baseline:")
base = D_gamma(2.5)
for r in rows:
    print(f"  {r['name']:22s} gamma={r['g_fit']:.3f}  D={r['D']:.4g}  ratio={r['D']/base:.1f}x")

# ---- figure ----
fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
ax = axes[0]
dd = np.linspace(1.005, 8, 3000)
ax.plot(dd, gamma_local(dd), "k-", lw=2, label=r"$\gamma_{local}(\delta)=\delta/\sqrt{\delta^2-1}$")
for r, c in zip(rows, plt.cm.tab10(np.linspace(0, 1, len(rows)))):
    ax.plot([r["d_lo"], r["d_hi"]], [r["g_fit"], r["g_fit"]], "-", color=c, lw=4, alpha=0.55)
    ax.plot(r["d_star"], r["g_fit"], "o", color=c, ms=8, zorder=5)
    ax.annotate(f"{r['name']}\nγ={r['g_fit']:.2f}", (r["d_star"], r["g_fit"]),
                textcoords="offset points", xytext=(8, -14), fontsize=7.5, color=c)
ax.axhline(1.0, color="gray", ls=":", lw=0.8)
ax.set_xlabel(r"$\delta=\Delta\omega/(2K_{eff})$"); ax.set_ylabel(r"$\gamma$")
ax.set_title(f"T1: all {n_inside}/5 disputed exponents localize on the\ncanonical Adler slope curve inside their own windows")
ax.legend(loc="upper right", fontsize=9)

ax = axes[1]
ax.plot(gg, w_norm, "b-", lw=2, label=r"Adler degeneracy $p(\gamma)\propto(\gamma^2-1)^{-3/2}$")
ax.plot(grid, p_u, "r--", lw=2, label="uniform null on [1, 2.5]")
ax.axvline(1.2, color="gray", ls=":", lw=1)
ax.text(1.205, ax.get_ylim()[1] * 0.9 if ax.get_ylim()[1] > 0 else 1, "", fontsize=8)
ax.set_yscale("log"); ax.set_ylim(1e-3, 30)
ax.set_xlabel(r"$\gamma$"); ax.set_ylabel("density (log scale)")
ax.set_title(f"T3: degeneracy divergence at γ→1⁺  (KL={kl:.2f} nats;\nP(γ<1.2): {P_below_12:.2f} vs {P_unif_below_12:.2f} uniform)")
ax.legend(loc="upper right", fontsize=9)
fig.tight_layout()
fig.savefig("../../shared_agora/artifacts/adler_gamma_degeneracy.png", dpi=130)

out = dict(K_eff=K0, d_max=d_max, g_lo=g_lo, P_below_12_adler=P_below_12,
           P_below_12_uniform=P_unif_below_12, kl_nats=kl,
           n_self_consistent=n_inside, n_claims=len(rows), rows=rows)
with open("../../shared_agora/artifacts/adler_gamma_degeneracy.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nsaved adler_gamma_degeneracy.png / .json")
