#!/usr/bin/env python3
"""Final control + summary figure.
  CONTROL: r=3.90, eps=0.05 (the 'frame persistence' class from EMP-047/HYP-018).
           Prediction under the mod-4 theory: frozen/period-dynamics, parity ~0
           under BOTH lag conventions (no period-4 alignment -> no spurious P).
  FIGURE: lag spectra M_l for candidate points showing exact period-4 structure,
           plus even/odd vs mod4-convention parity bars.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

TRANSIENT, MEAS = 500, 1200


def run(r, eps, N=128, T=3500, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.2, 0.8, N)
    Xt = np.empty((MEAS, N))
    for t in range(TRANSIENT + T):
        f = r * x * (1 - x)
        x = (1 - eps) * f + eps * 0.5 * (np.roll(f, 1) + np.roll(f, -1))
        x = np.clip(x, 1e-9, 1 - 1e-9)
        if t >= TRANSIENT + T - MEAS:
            Xt[t - (TRANSIENT + T - MEAS)] = x
    return Xt


def Ml(B, l):
    return float(np.mean(B[l:] == B[:-l]))


def parity_stats(B):
    even = [50, 100, 150, 200, 250, 260]
    odd = [25, 75, 125, 175, 225]
    me, mo = np.mean([Ml(B, l) for l in even]), np.mean([Ml(B, l) for l in odd])
    # mod-4 convention on the same 1000-step window: residues {0,2} vs {1,3}
    r02 = np.mean([Ml(B, l) for l in even + [24, 26, 48, 52] if l % 4 in (0, 2)])
    r13 = np.mean([Ml(B, l) for l in odd + [1, 3, 5, 7] if l % 4 in (1, 3)])
    # exact period check
    d4 = np.mean(B[4:] != B[:-4])
    return me, mo, me - mo, r02, r13, r02 - r13, d4


fig, axes = plt.subplots(2, 2, figsize=(13, 9))
pts = [(3.845, 0.1253), (3.855, 0.1253), (3.875, 0.1307), (3.90, 0.05)]
rows = []
for ax, (r, e) in zip(axes.flat, pts):
    B = run(r, e, seed=0) > 0.5
    ls = np.arange(1, 41)
    vals = [Ml(B, l) for l in ls]
    ax.plot(ls, vals, 'o-', ms=4)
    ax.axhline(0.5, color='gray', lw=0.5)
    for l in range(1, 41, 4):
        ax.axvline(l, color='green', alpha=0.15)
    ax.set_title(f"r={r}, eps={e}   (green bands: l≡0 mod 4)")
    ax.set_xlabel("lag l"); ax.set_ylabel("M_l")
    ax.set_ylim(-0.05, 1.05)
    me, mo, p_eo, r02, r13, p_m4, d4 = parity_stats(B)
    rows.append((r, e, me, mo, p_eo, r02, r13, p_m4, d4))
plt.tight_layout()
plt.savefig("emp_cartographer_mod4_summary.png", dpi=120)
print("saved emp_cartographer_mod4_summary.png")

print("\n=== CONTROL + SUMMARY TABLE ===")
print(f"{'r':>6} {'eps':>6} | {'M_even':>7} {'M_odd':>6} {'P_eo':>6} | "
      f"{'M_r02':>6} {'M_r13':>6} {'P_m4':>6} | {'bitmismatch4':>12}")
for (r, e, me, mo, peo, r02, r13, pm4, d4) in rows:
    print(f"{r:>6.3f} {e:>6.4f} | {me:>7.3f} {mo:>6.3f} {peo:>6.3f} | "
          f"{r02:>6.3f} {r13:>6.3f} {pm4:>6.3f} | {d4:>12.2e}")
print("\nPrediction check: control (3.90, 0.05) should show P_eo ~ 0 AND P_m4 ~ 0")
print("(no period-4 alignment -> no spurious parity under either convention),")
print("while candidate points show P_m4 >> 0 with exact period-4 bit order.")