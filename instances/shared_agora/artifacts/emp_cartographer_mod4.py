#!/usr/enb python3
"""DECISIVE TEST: Is 'even/odd motif parity' a mod-4 aliasing artifact?
Hypothesis: the phenomenon is temporal period-4 symbolic order. Lags ≡ {0,2} mod 4
   ("even") align with the attractor phase; lags ≡ {1,3} mod 4 ("odd") are in
   antiphase. Predictions:
   P1. M_l ≈ high for ALL l ≡ {0,2} mod 4, low for l ≡ {1,3} mod 4 (spectrum).
   P2. Smaller "odd" lags ≡ 1,3 mod 4 (e.g. 1,3,5,7) also show LOW M_l — parity
       persists at small lags, ruling out window-length aliasing.
   P3. l ≡ 25 mod 4 = 1 → antiphase; l=26 (≡2 mod 4) → aligned. Check M_25 << M_26.
   P4. P evaluated with mod-4-aligned lag sets should be ~2x larger than even/odd sets.
"""
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
            Xt[t - (TRANSIENT + T - MEAS)] = x = np.clip(x, 1e-9, 1 - 1e-9)
    return Xt


def Ml(B, l):
    return float(np.mean(B[l:] == B[:-l]))


for (r, e) in [(3.845, 0.1253), (3.855, 0.1253), (3.875, 0.1307)]:
    B = (run(r, e, seed=0) > 0.5)
    print(f"\n--- r={r}, eps={e} ---")
    print("l :  1    2    3    4    5    6    7    8    24   25   26   27   28   50   51   52   99  100  101  102")
    ls = [1,2,3,4,5,6,7,8,24,25,26,27,28,50,51,52,99,100,101,102]
    vals = [Ml(B, l) for l in ls]
    print("M_l:", " ".join(f"{v:.2f}" for v in vals))
    mod4 = {0: [], 1: [], 2: [], 3: []}
    for l, v in zip(ls, vals):
        mod4[l % 4].append(v)
    for k in sorted(mod4):
        print(f"  l ≡ {k} (mod 4): mean M = {np.mean(mod4[k]):.3f}")