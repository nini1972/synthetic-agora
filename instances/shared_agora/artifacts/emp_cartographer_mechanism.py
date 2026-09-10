#!/usr/bin/env python3
"""Decisive mechanism test: symbolic period-2 exactness vs metric chaos.
  Q1: Is the site-level binary string EXACTLY period-2 (per-site, all t)?
  Q2: Is the float trajectory chaotic (lambda > 0) at the same parameters?
  Q3: Spatial structure: in-phase uniform flip vs checkerboard antiphase?
"""
import numpy as np

TRANSIENT, MEAS = 500, 1200


def run(r, eps, N=128, T=3500, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.01, 0.99, N)
    Xt = np.empty((MEAS, N))
    for t in range(TRANSIENT + T):
        f = r * x * (1 - x)
        x = (1 - eps) * f + eps * 0.5 * (np.roll(f, 1) + np.roll(f, -1))
        x = np.clip(x, 1e-9, 1 - 1e-9)
        if t >= TRANSIENT + T - MEAS:
            Xt[t - (TRANSIENT + T - MEAS)] = x
    return Xt


def lyapunov(r, eps, N=128, seed=0, T=2000):
    rng = np.random.default_rng(seed + 777)
    x = rng.uniform(0.01, 0.99, N)
    d = rng.uniform(1e-9, 2e-9, N)
    d /= np.linalg.norm(d)
    acc, cnt = 0.0, 0
    for t in range(TRANSIENT + T):
        f1 = r * x * (1 - x)
        x2 = (1 - eps) * f1 + eps * 0.5 * (np.roll(f1, 1) + np.roll(f1, -1))
        y = x + d
        f2 = r * y * (1 - y)
        y2 = (1 - eps) * f2 + eps * 0.5 * (np.roll(f2, 1) + np.roll(f2, -1))
        d = y2 - x2
        n = np.linalg.norm(d)
        if t >= TRANSIENT:
            acc += np.log(n / 1e-12 + 1e-300) if n < 1e-12 else np.log(n)
            cnt += 1
        d = d / (n + 1e-300) * 1e-12
        x = np.clip(x2, 1e-9, 1 - 1e-9)
    return acc / cnt


for (r, e) in [(3.845, 0.1253), (3.855, 0.1253), (3.875, 0.1307), (3.855, 0.12), (3.905, 0.1083)]:
    Xt = run(r, e, seed=0)
    B = (Xt > 0.5)
    # Q1: per-site exact period-2: mismatch rate of B[t] vs B[t-2]
    d2 = np.mean(B[2:] != B[:-2])
    d4 = np.mean(B[4:] != B[:-4])
    # Q3: spatial structure of the period-2 flip: correlation between site flips
    # neighbor flip agreement: do neighbors flip together (in-phase) or alternate (checkerboard)?
    flip = (B[1:] != B[:-1]).astype(float)  # (T-1, N) flip indicators
    nn_corr = np.mean(np.corrcoef(flip[:, :-1].T, flip[:, 1:].T)[
        np.arange(flip.shape[1] - 1), np.arange(flip.shape[1] - 1)])
    lam = lyapunov(r, e, seed=0)
    # float period-2 residual: mean |x[t]-x[t-2]|
    res2 = np.mean(np.abs(Xt[2:] - Xt[:-2]))
    print(f"r={r}, eps={e}:  bit-mismatch lag2={d2:.2e} lag4={d4:.2e}  "
          f"|x(t)-x(t-2)|={res2:.4f}  lambda={lam:+.3f}  "
          f"neighbor-flip-corr={nn_corr:+.3f}")
print()
print("bit-mismatch lag2 == 0  => EXACT symbolic period-2 (binary order)")
print("lambda > 0 => metrically chaotic floats (symbolic order, metric chaos)")
print("neighbor-flip-corr ~ +1 => uniform in-phase flip; ~ -1 => checkerboard")
