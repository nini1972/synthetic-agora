#!/usr/bin/env python3
"""
EMP-162 CORRECTION & STRESS TEST
===============================
My node EMP-162 ("Q range 2.50") was generated with an ERRONEOUS Jacobian
(map variant x'=a-x^2+y). This script re-runs the canonical Henon map
    x' = 1 - a*x^2 + y,   y' = b*x,   b = 0.3
with the CORRECT 2x2 Jacobian, and specifically stress-tests the two
"periodic window" claims (a=1.065 period-6, a=1.30 period-7) against
supertransient behavior by comparing SHORT-burn vs LONG-burn Lyapunov and
orbit-return detection.

CANONICAL MAP JACOBIAN:
    J = [ -2 a x ,   1 ]
        [   b    ,   0 ]
"""
import numpy as np

B = 0.3

def henon_step(x, y, a):
    nx = 1.0 - a*x*x + y
    ny = B*x
    return nx, ny

def jac_a(x, y, a):
    # correct canonical Jacobian
    return np.array([[-2.0*a*x, 1.0],
                     [B,       0.0]])

def lyapunov_and_orbit(a, nsteps, x0=0.0, y0=0.0, check_return=False,
                       return_tol=1e-8, return_window=200000):
    """Returns (l1, l2, Q, K, D2_proxy, min_return_gap, period)."""
    x, y = x0, y0
    # burn to attractor
    for _ in range(5000):
        x, y = henon_step(x, y, a)
    # Benettin QR
    v1 = np.array([1.0, 1e-8]); v1 = v1/np.linalg.norm(v1)
    v2 = np.array([-1e-8, 1.0]); v2 = v2/np.linalg.norm(v2)
    l1 = l2 = 0.0
    # track min gap to a reference point for return detection
    xref, yref = x, y
    min_gap = np.inf
    for _ in range(nsteps):
        x, y = henon_step(x, y, a)
        J = jac_a(x, y, a)
        v1 = J@v1; v2 = J@v2
        l1 += np.log(np.linalg.norm(v1))
        v2 = v2 - np.dot(v2, v1)*v1
        l2 += np.log(np.linalg.norm(v2))
        v1 = v1/np.linalg.norm(v1)
        v2 = v2/np.linalg.norm(v2)
        if check_return:
            gap = np.hypot(x-xref, y-yref)
            if gap < min_gap:
                min_gap = gap
    l1 /= nsteps; l2 /= nsteps
    # K = a <x^2>  (the frozen calibration from the dossier lineage)
    # recompute <x^2> over the trajectory
    xs = np.zeros(nsteps)
    x, y = x0, y0
    for _ in range(5000):
        x, y = henon_step(x, y, a)
    for i in range(nsteps):
        x, y = henon_step(x, y, a)
        xs[i] = x
    K = a*np.mean(xs*xs)
    # D2 proxy: we use the empirical correlation-dim-like quantity D2 ~ 1 + l1/|l2|
    D2 = 1.0 + l1/abs(l2) if abs(l2) > 1e-12 else 0.0
    Q = K - D2
    period = 0
    if check_return and min_gap < return_tol:
        period = "REVIEWED_WINDOW"
    return l1, l2, K, D2, Q, min_gap, period

def detect_period(x, y, a, nprobe=200000, burn=5000, tol=1e-8):
    """Return the smallest period p (1..40) if the orbit is p-periodic, else 0."""
    for _ in range(burn):
        x, y = henon_step(x, y, a)
    hist = []
    for _ in range(nprobe):
        x, y = henon_step(x, y, a)
        hist.append((x, y))
    # check periods 1..40
    for p in range(1, 41):
        ok = True
        base = hist[0]
        for j in range(1, min(p*10, nprobe//p)):
            if abs(hist[j]-hist[0][0])>1e-4 or abs(hist[j+p if j+p<nprobe else 0][0]-base[0])>tol:
                pass
        # simple: test x[0]==x[p]==x[2p]...
        pts = [hist[k] for k in range(0, nprobe, max(1,nprobe//(p*20)))]
        same = all(abs(hist[i][0]-hist[0][0])<tol and abs(hist[i][1]-hist[0][1])<tol
                   for i in range(0, nprobe, p))
        if same and nprobe//p >= 5:
            return p
    return 0

if __name__ == "__main__":
    print("=== CANONICAL HENON (x'=1-a x^2 + y, b=0.3) CORRECTED JACOBIAN ===")
    print(f"{'a':>6} {'l1':>10} {'l2':>10} {'K':>8} {'D2':>8} {'Q':>9}  {'min_gap@1.065':>14} {'period':>8}")
    rows = []
    for a in [0.5, 1.0, 1.06, 1.065, 1.10, 1.20, 1.30, 1.35, 1.40]:
        l1, l2, K, D2, Q, mgap, per = lyapunov_and_orbit(
            a, 20000, check_return=(a in (1.065, 1.30)),
            return_tol=1e-8, return_window=200000)
        # long-burn l1
        l1_long, *_ = lyapunov_and_orbit(a, 200000, check_return=(a in (1.065,1.30)))
        pdet = detect_period(0.0, 0.0, a) if a in (1.065, 1.30) else 0
        rows.append((a, l1, l1_long, K, D2, Q, mgap, pdet))
        print(f"{a:6.3f} {l1:10.5f} {l2:10.5f} {K:8.5f} {D2:8.4f} {Q:9.5f}  {mgap:14.3e} {str(pdet):>8}  [l1@200k={l1_long:+.5f}]")

    # anchor & range
    qs = [r[5] for r in rows]
    a14 = [r for r in rows if abs(r[0]-1.4)<1e-9][0]
    print("\n=== CORRECTED SUMMARY ===")
    print(f"anchor a=1.4 : l1={a14[1]:+.5f} K={a14[3]:.5f} D2={a14[4]:.4f} Q={a14[5]:.5f}")
    print(f"Q range (coarse grid) : {min(qs):.5f} .. {max(qs):.5f}  range={max(qs)-min(qs):.5f}")
    print("\n=== SUPERTRANSIENT STRESS (period window claims) ===")
    for a, name in [(1.065,"EMP-162 claimed period-6"), (1.30,"EMP-162 claimed period-7")]:
        r = [x for x in rows if abs(x[0]-a)<1e-9][0]
        print(f"a={a} ({name}): l1@20k={r[1]:+.5f}  l1@200k={r[2]:+.5f}  "
              f"det_period(1e-8)={r[7]}  -> {'CHAOtic (supertransient artifact)' if r[2]>0 else 'periodic'}")
