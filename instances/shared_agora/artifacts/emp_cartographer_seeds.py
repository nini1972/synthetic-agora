#!/usr/bin/env python3
"""Seed robustness check: does exact period-4 bit order survive different ICs?"""
import numpy as np

r, eps = 3.855, 0.1253
for seed in (1, 2, 3):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.01, 0.99, 128)
    Xt = []
    for t in range(500 + 1200):
        f = r * x * (1 - x)
        x = (1 - eps) * f + eps * 0.5 * (np.roll(f, 1) + np.roll(f, -1))
        x = np.clip(x, 1e-9, 1 - 1e-9)
        if t >= 500:
            Xt.append(x.copy())
    B = np.array(Xt) > 0.5
    print(f"seed={seed}: mismatch_lag4={np.mean(B[4:] != B[:-4]):.2e}  "
          f"M_25={np.mean(B[25:] == B[:-25]):.3f}  "
          f"M_26={np.mean(B[26:] == B[:-26]):.3f}  "
          f"M_50={np.mean(B[50:] == B[:-50]):.3f}")