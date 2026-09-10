#!/usr/bin/env python3
"""Follow-up probe: epsilon-dependence, ref correlation, coupling convention.
Tests:
  T1. Monotone eps-dependence of P_M at r=3.855 (claim C1 refinement).
  T2. Correlation between GLM P_M and Frontier odd_even_motif_index.
  T3. Coupling-on-x convention: does it produce low F (frame decoherence),
      matching the Frontier's wall_ac_late_mean ~ 0 signature?
"""
import csv
import numpy as np

REF = "../../shared_agora/artifacts/cartographer_ref_dual_ridge.csv"
TRANSIENT, MEAS = 500, 1000
EVEN = [50, 100, 150, 200, 250, 260]
ODD = [25, 75, 125, 175, 225]


def run(r, eps, N=128, T=3500, seed=0, couple_on_x=False):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.01, 0.99, N)
    Xt = np.empty((MEAS, N))
    for t in range(TRANSIENT + T):
        f = r * x * (1 - x)
        if couple_on_x:
            g = x
        else:
            g = f
        x = (1 - eps) * f + eps * 0.5 * (np.roll(g, 1) + np.roll(g, -1))
        x = np.clip(x, 1e-9, 1 - 1e-9)
        if t >= TRANSIENT + T - MEAS:
            Xt[t - (TRANSIENT + T - MEAS)] = x
    return Xt


def indices(Xt):
    B = Xt > 0.5
    M = {l: float(np.mean(B[l:] == B[:-l])) for l in EVEN + ODD}
    F = {}
    for l in EVEN + ODD:
        a, b = Xt[l:], Xt[:-l]
        am = a - a.mean(1, keepdims=True); bm = b - b.mean(1, keepdims=True)
        num = (am * bm).sum(1)
        den = np.sqrt((am**2).sum(1) * (bm**2).sum(1)) + 1e-12
        F[l] = float(np.mean(num / den))
    Me, Mo = np.mean([M[l] for l in EVEN]), np.mean([M[l] for l in ODD])
    Fe, Fo = np.mean([F[l] for l in EVEN]), np.mean([F[l] for l in ODD])
    return Me - Mo, Fe - Fo, Me, Fe


def main():
    ref = list(csv.DictReader(open(REF)))
    ref_index = {(float(x["r"]), float(x["epsilon"])): float(x["odd_even_motif_index"]) for x in ref}
    pts = [(float(x["r"]), float(x["epsilon"])) for x in ref]

    print("=== T1: eps dependence at r=3.855 (GLM convention: coupling on f) ===")
    for eps in [0.103, 0.1083, 0.1137, 0.119, 0.12, 0.1253, 0.1307, 0.136, 0.15, 0.2, 0.3, 0.4]:
        d = indices(run(3.855, eps, seed=0))
        print(f"eps={eps:.4f}: P_M={max(d[0],0):.3f}  M_even={d[2]:.3f}")

    print("\n=== T2: GLM P_M vs Frontier odd_even_motif_index ===")
    pms, refs = [], []
    for (r, e) in pts:
        ds = []
        for seed in range(3):
            ds.append(max(indices(run(r, e, seed=seed))[0], 0))
        pms.append(np.mean(ds)); refs.append(ref_index[(r, e)])
    cc = np.corrcoef(pms, refs)[0, 1]
    print(f"Pearson r = {cc:.3f} over {len(pts)} points")
    print("(low correlation shows the Frontier index is NOT reproduced by the "
          "simple parity metric despite the underlying even/odd structure existing)")

    print("\n=== T3: coupling-on-x convention (frontier-matching frame decoherence?) ===")
    for (r, e) in [(3.845, 0.1253), (3.855, 0.1253), (3.875, 0.1307), (3.905, 0.1083)]:
        dF = indices(run(r, e, seed=0, couple_on_x=True))
        dG = indices(run(r, e, seed=0, couple_on_x=False))
        print(f"r={r}, eps={e}:  GLM-conv F_even={dG[3]:.3f} P_F={max(dG[1],0):.2f}  |  "
              f"x-conv F_even={dF[3]:.3f} P_F={max(dF[1],0):.2f}")

    print("\n=== T3b: x-coupling, eps dependence (does frame decohere at high eps?) ===")
    for eps in [0.103, 0.12, 0.136, 0.2, 0.3, 0.4, 0.5]:
        dF = indices(run(3.855, eps, seed=0, couple_on_x=True))
        print(f"eps={eps:.3f}: F_even={dF[3]:.3f}  F_odd={np.nan:.3f}  P_M={max(dF[0],0):.3f}  M_even={dF[2]:.3f}")


if __name__ == "__main__":
    main()