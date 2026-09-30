"""Peer verification of EMP-094 (deepseek, noisy Adler).
Model: dtheta/dt = dw - 2K*sin(theta) + sigma*xi, K=1.65.
Checks (metric-agnostic, physics-level):
 P1: R(dw, sigma=0.05) at dw=4,5,6 vs claims 0.229/0.570/0.388.
 P2: no collapse at sigma=0.05 for dw in [2,6].
 P3: mean R over dw in [2,6] non-decreasing in sigma.
Euler-Maruyama, walkers x dw-grid vectorized in one array.
Shortened T for turn limits; tau_relax << T so results remain valid.
"""
import numpy as np
import json

K = 1.65
NW = 4000          # walkers per dw
DT = 0.005
T = 120.0
NSTEPS = int(T / DT)
DW_GRID = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
BURN_FRAC = 0.25


def run_sigma(dw_grid, sigma, seed):
    rng = np.random.default_rng(seed)
    ndw = len(dw_grid)
    n = ndw * NW
    ph = 0.5 * rng.uniform(0.0, 2.0 * np.pi, n)  # phase = theta/2
    dw_tile = np.repeat(dw_grid, NW)
    sqdt = np.sqrt(DT)
    burn = int(NSTEPS * BURN_FRAC)
    csum = np.zeros(ndw)
    cnum = 0
    for step in range(NSTEPS):
        eta = rng.standard_normal(n)
        ph += (dw_tile - 2.0 * K * np.sin(ph)) * 0.5 * DT + 0.5 * sigma * sqdt * eta
        if step >= burn:
            sums = np.cos(ph).reshape(ndw, NW).sum(axis=1)
            csum += np.abs(sums) / NW
            cnum += 1
    return csum / cnum


results = {}
acc = np.zeros(len(DW_GRID))
for seed in (11, 22, 33):
    acc += run_sigma(DW_GRID, 0.05, seed)
R05 = acc / 3.0
results["R_sigma0.05"] = {str(d): round(float(r), 4) for d, r in zip(DW_GRID, R05)}

p3 = {}
for sig in (0.05, 0.3, 0.5, 0.8):
    r = run_sigma(DW_GRID, sig, 77)
    p3[str(sig)] = round(float(r.mean()), 4)
results["P3_meanR_vs_sigma"] = p3

with open("emp094_verify_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))
