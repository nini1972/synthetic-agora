"""Micro-debug: step-by-step dynamics, N=50 and N=800, K0=0.8, sigma=0.
Print R, Keff, spread half-width h, and angle-resolved density to find the
mechanism of fast ignition despite tiny Keff at small R."""
import numpy as np

ALPHA = 0.6
r = np.random.default_rng(7)

def run(N, DT, K0, T, nprint=14):
    th = r.uniform(0, 2*np.pi, N)
    nsteps = int(T / DT)
    every = max(1, nsteps // nprint)
    for t in range(nsteps):
        c, s_ = np.cos(th), np.sin(th)
        C, S = c.mean(), s_.mean()
        R = np.hypot(C, S)
        psi = np.arctan2(S, C) if R > 1e-12 else 0.0
        Keff = K0 * R**ALPHA * R
        force = Keff * np.sin(psi - th)
        th = th + DT * force
        if t % every == 0 or t == nsteps - 1:
            d = (th - psi + np.pi) % (2*np.pi) - np.pi
            frac90 = np.mean(np.abs(d) < np.pi/2)
            h95 = np.percentile(np.abs(d), 95)
            print(f"  t={DT*t:6.1f} R={R:.4f} Keff={Keff:.3e} frac(|d|<pi/2)={frac90:.2f} h95={h95:.2f}")

print("=== N=50, K0=0.8, dt=0.1, sigma=0, T=60 ===")
run(50, 0.1, 0.8, 60.0)
print("=== N=800, K0=0.8, dt=0.1, sigma=0, T=90 ===")
run(800, 0.1, 0.8, 90.0)
