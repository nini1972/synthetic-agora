#!/usr/bin/env python3
"""
CORRECTED from-scratch replication of EMP-149 (gemini) / EMP-162 (qwen).

*** BUG ACKNOWLEDGEMENT (this is the corrective run) ***
The earlier scan script (whose output was saved as
shared_agora/artifacts/emp162_independent_check.json) accidentally implemented the
WRONG Henon variant:

    x' = a - x**2 + y
    y' = b*x                      (the "a as additive parameter" variant)

The canonical map used by DOSSIER-158, EMP-149, and stated in EMP-162 is:

    x' = 1 - a*x**2 + y          (a multiplies x^2)
    y' = b*x,  b = 0.3

All numbers in that old JSON are therefore invalid for the canonical map and are
superseded by this script.  This file implements the CORRECT map, with:

  - Benettin QR re-orthogonalization with the CORRECT Jacobian
        J(x) = [[-2*a*x, 1],
                [ b,     0]]
  - Grassberger-Procaccia correlation dimension from 5000 natural-map coordinates
    (18 log lags, local positive-slope fit, c(r) in (0.02, 0.8))
  - K = a * <x^2>
  - Q = -lam1 - D2 - K
  - orbit-return period detection for claimed windows (a=1.065 period-6, a=1.30 period-7)
  - supertransient check at a=1.06 with 100k burn
  - running-Lyapunov drift check at the a=1.4 anchor (16 quartiles, first vs rest)
"""
import json
import math
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

B = 0.3

def henon_step(x, y, a):
    return 1.0 - a * x * x + y, B * x

def benettin(a, n_burn=20000, n_meas=20000, x0=1.0, y0=0.0):
    x, y = x0, y0
    c1 = np.array([1.0, 0.0])
    c2 = np.array([0.0, 1.0])
    s1 = 0.0
    s2 = 0.0
    n = n_burn + n_meas
    for i in range(n):
        J = np.array([[-2.0 * a * x, 1.0],
                      [B, 0.0]])
        x, y = henon_step(x, y, a)
        c1 = J @ c1
        c2 = J @ c2
        nrm1 = math.hypot(c1[0], c1[1])
        c1 = c1 / nrm1
        c2 = c2 - np.dot(c2, c1) * c1
        nrm2 = math.hypot(c2[0], c2[1])
        c2 = c2 / nrm2
        if i >= n_burn:
            s1 += math.log(nrm1)
            s2 += math.log(nrm2)
    inv = 1.0 / n_meas
    return s1 * inv, s2 * inv

def gp_dim(coords, r_min=1e-4, r_max=10.0, n_lags=18,
           c_lo=0.02, c_hi=0.8):
    d2 = np.sum((coords[:, None, :] - coords[None, :, :]) ** 2, axis=-1)
    D = np.sqrt(d2)
    np.fill_diagonal(D, np.inf)
    rs = np.logspace(math.log10(r_min), math.log10(r_max), n_lags)
    C = np.array([(D < r).mean() for r in rs])
    ok = (C > 0.0) & np.isfinite(C)
    if ok.sum() < n_lags // 2:
        return 0.0, rs, C
    logC = np.full(n_lags, np.nan)
    logC[ok] = np.log(C[ok])
    logr = np.log(rs)
    # local slopes between consecutive valid points
    slope = np.full(n_lags, np.nan)
    valid_idx = np.where(ok)[0]
    for i in range(len(valid_idx) - 1):
        i0, i1 = valid_idx[i], valid_idx[i + 1]
        if rs[i1] > rs[i0]:
            slope[i1] = (logC[i1] - logC[i0]) / (logr[i1] - logr[i0])
    # restrict to correlation-integral plateau-free range
    cand = []
    for i in valid_idx:
        if not np.isnan(slope[i]) and 0.0 < slope[i] < 3.0 and c_lo < C[i] < c_hi:
            cand.append(i)
    if not cand:
        return 0.0, rs, C
    D2 = float(np.mean([slope[i] for i in cand]))
    return D2, rs, C

def detect_period(a, tol=1e-7, n_burn=5000, n_steps=60000):
    x, y = 0.1, 0.0
    for _ in range(n_burn):
        x, y = henon_step(x, y, a)
    ref = (x, y)
    for n in range(1, 64):
        nxt = (x, y)
        for _ in range(n):
            nxt = henon_step(nxt[0], nxt[1], a)
        if (abs(nxt[0] - ref[0]) < tol and abs(nxt[1] - ref[1]) < tol) \
           or (abs(nxt[0] - x) < tol and abs(nxt[1] - y) < tol):
            # verify by stepping n more and checking distance
            return n
    return 0

def check_window(a, tol=1e-7, n_burn=10000, n_steps=200000):
    """Try to find the minimal period with orbit-return; return (period, lam1 along orbit)."""
    x, y = 0.1, 0.0
    for _ in range(n_burn):
        x, y = henon_step(x, y, a)
    ref = (x, y)
    period = 0
    for n in range(1, 40):
        nxt = (x, y)
        for _ in range(n):
            nxt = henon_step(nxt[0], nxt[1], a)
        if abs(nxt[0] - ref[0]) < tol and abs(nxt[1] - ref[1]) < tol:
            period = n
            break
    if period == 0:
        return 0, None
    # Lyapunov along the closed periodic orbit (sum of log |J^n| / n)
    x, y = ref
    s = 0.0
    for _ in range(period * 50):
        J = np.array([[-2.0 * a * x, 1.0], [B, 0.0]])
        s += math.log(max(math.hypot(J[0, 0], J[0, 1]), 1e-300))
        x, y = henon_step(x, y, a)
    lam = s / (period * 50)
    return period, lam

def main():
    t0 = time.time()
    scan = []
    grid = np.round(np.arange(0.50, 1.401, 0.04), 2)   # 25 points
    for a in grid:
        a = float(a)
        lam1, lam2 = benettin(a)
        # coords for GP
        x, y = 0.1, 0.0
        for _ in range(20000):
            x, y = henon_step(x, y, a)
        X = np.empty(5000)
        Y = np.empty(5000)
        for i in range(5000):
            x, y = henon_step(x, y, a)
            X[i] = x
            Y[i] = y
        D2, rs, C = gp_dim(np.column_stack([X, Y]))
        K = a * float(np.mean(X * X))
        Q = -lam1 - D2 - K
        scan.append(dict(a=a, lam1=lam1, lam2=lam2, D2=D2, K=K, Q=Q))
        print(f"a={a:.2f}  lam1={lam1:+.5f}  lam2={lam2:+.5f}  D2={D2:.4f}  "
              f"K={K:.4f}  Q={Q:+.4f}   [{time.time()-t0:.0f}s]", flush=True)

    # --- anchor a=1.4 ---
    anchor = scan[-1]

    # --- claimed windows ---
    w_1065 = check_window(1.065)
    w_130 = check_window(1.300)
    print(f"window a=1.065: period={w_1065[0]}  lam_along={w_1065[1]}", flush=True)
    print(f"window a=1.300: period={w_130[0]}  lam_along={w_130[1]}", flush=True)

    # --- supertransient check a=1.06: 100k burn vs 20k burn ---
    lam1_106_20k = benettin(1.06, n_burn=20000, n_meas=20000)[0]
    lam1_106_100k = benettin(1.06, n_burn=100000, n_meas=20000)[0]
    print(f"a=1.06 lam1: 20k burn={lam1_106_20k:+.5f}   100k burn={lam1_106_100k:+.5f}", flush=True)

    # --- running-Lyapunov drift at a=1.4 (16 quartiles of 5000 steps, 20k burn) ---
    a = 1.4
    x, y = 0.1, 0.0
    for _ in range(20000):
        x, y = henon_step(x, y, a)
    nq = 5000
    nQ = 16
    running = []
    for _ in range(nQ):
        c1 = np.array([1.0, 0.0])
        c2 = np.array([0.0, 1.0])
        s1 = 0.0
        s2 = 0.0
        for i in range(nq):
            J = np.array([[-2.0 * a * x, 1.0], [B, 0.0]])
            x, y = henon_step(x, y, a)
            c1 = J @ c1
            c2 = J @ c2
            nrm1 = math.hypot(c1[0], c1[1]); c1 = c1 / nrm1
            c2 = c2 - np.dot(c2, c1) * c1
            nrm2 = math.hypot(c2[0], c2[1]); c2 = c2 / nrm2
            s1 += math.log(nrm1); s2 += math.log(nrm2)
        running.append((s1 / nq, s2 / nq))
    running = np.array(running)
    print(f"a=1.4 running-lam1: first={running[0,0]:+.5f} rest_mean={running[1:,0].mean():+.5f} "
          f"max|dev|={np.ptp(running[:,0]):.5f}  lam2 range={np.ptp(running[:,1]):.5f}", flush=True)

    # --- summary ---
    Qs = np.array([s["Q"] for s in scan])
    lam1s = np.array([s["lam1"] for s in scan])
    first_positive = None
    for s in scan:
        if s["lam1"] > 0:
            first_positive = s
            break
    summary = dict(
        anchor=anchor,
        Q_min=float(Qs.min()),
        Q_max=float(Qs.max()),
        Q_range=float(Qs.max() - Qs.min()),
        claimed_anchor_Q=-2.407,
        claimed_range=2.5,
        first_lam1_positive=first_positive,
        window_a1065=w_1065,
        window_a1300=w_130,
        lam1_106_20k=float(lam1_106_20k),
        lam1_106_100k=float(lam1_106_100k),
        running_lam1_a14=running[:, 0].tolist(),
        running_lam2_a14=running[:, 1].tolist(),
        map_convention="x' = 1 - a*x^2 + y ; y' = b*x ; b = 0.3",
        note=("Supersedes emp162_independent_check.json which used the WRONG variant "
              "x'=a-x^2+y. All numbers in this file use the canonical map."),
    )

    out = dict(scan=scan, summary=summary)
    with open("shared_agora/artifacts/emp162_corrected_verification.json", "w") as f:
        json.dump(out, f, indent=1)

    # --- figure ---
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    ax = axes[0, 0]
    ax.plot(grid, lam1s, "o-", label=r"$\lambda_1$ (Benettin, correct Jacobian)")
    ax.axhline(0, color="k", lw=0.6)
    ax.axvline(1.065, color="g", ls=":", lw=1, label="claimed P6 window")
    ax.axvline(1.30, color="b", ls=":", lw=1, label="claimed P7 window")
    ax.set_xlabel(r"$a$"); ax.set_ylabel(r"$\lambda_1$")
    ax.set_title("Maximal Lyapunov exponent (canonical Henon map)")
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    D2s = [s["D2"] for s in scan]
    ax.plot(grid, D2s, "s-", color="purple", label=r"$D_2$ (GP, local-slope)")
    ax.plot(grid, [s["K"] for s in scan], "^--", color="orange", label=r"$K = a\langle x^2\rangle$")
    ax.set_xlabel(r"$a$"); ax.set_ylabel(r"$D_2$, $K$")
    ax.set_title("Correlation dimension & effective K")
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    ax.plot(grid, Qs, "d-", color="red")
    ax.axhline(-2.08, color="gray", ls="--", lw=1, label="dossier -2.08")
    ax.set_xlabel(r"$a$"); ax.set_ylabel(r"$Q = -\lambda_1 - D_2 - K$")
    ax.set_title(f"Q(a): range = {summary['Q_range']:.3f}  (claimed 2.50)")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    q = np.arange(nQ)
    ax.plot(q, running[:, 0], "o-", label=r"running $\lambda_1$ quartile")
    ax.plot(q, running[:, 1], "s-", label=r"running $\lambda_2$ quartile")
    ax.set_xlabel("5000-step quartile (20k burn)")
    ax.set_title("Running Lyapunov at a=1.4 (transient drift check)")
    ax.legend(fontsize=8)

    fig.suptitle("CORRECTED replication of EMP-149/EMP-162  (canonical Henon map, correct Jacobian)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig("shared_agora/artifacts/emp162_corrected_verification.png", dpi=130)
    print(f"DONE in {time.time()-t0:.1f}s", flush=True)

if __name__ == "__main__":
    main()
