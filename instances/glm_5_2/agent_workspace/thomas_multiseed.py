# Multi-seed lambda_1 audit at the contested dissipation values.
# Usage: python thomas_multiseed.py 0.19 0.208
# Purpose: separate parametric trend from basin-of-attraction lottery.
import sys
import numpy as np

def thomas_rk4(s, b, dt):
    x, y, z = s
    k1x, k1y, k1z = np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z
    y2, z2, x2 = y + 0.5*dt*k1y, z + 0.5*dt*k1z, x + 0.5*dt*k1x
    k2x, k2y, k2z = np.sin(z2) - b*y2, np.sin(x2) - b*z2, np.sin(y2) - b*x2
    y3, z3, x3 = y + 0.5*dt*k2y, z + 0.5*dt*k2z, x + 0.5*dt*k2x
    k3x, k3y, k3z = np.sin(z3) - b*y3, np.sin(x3) - b*z3, np.sin(y3) - b*x3
    y4, z4, x4 = y + dt*k3y, z + dt*k3z, x + dt*k3x
    k4x, k4y, k4z = np.sin(z4) - b*y4, np.sin(x4) - b*z4, np.sin(y4) - b*x4
    return (x + dt/6*(k1x + 2*k2x + 2*k3x + k4x),
            y + dt/6*(k1y + 2*k2y + 2*k3y + k4y),
            z + dt/6*(k1z + 2*k2z + 2*k3z + k4z))

def largest_lyapunov(b, seed, dt=0.05, t_trans=100.0, t_meas=400.0, d0=1e-8):
    n_trans = int(t_trans/dt); n_meas = int(t_meas/dt)
    rng = np.random.default_rng(70000 + seed)
    x, y, z = rng.uniform(-3, 3, 3)   # wider IC box to sample different basins
    for _ in range(n_trans):
        x, y, z = thomas_rk4((x, y, z), b, dt)
    x2, y2, z2 = x + d0, y, z
    accum, n_renorm, renorm_every = 0.0, 0, 10
    for i in range(n_meas):
        x, y, z = thomas_rk4((x, y, z), b, dt)
        x2, y2, z2 = thomas_rk4((x2, y2, z2), b, dt)
        if (i+1) % renorm_every == 0:
            d = np.sqrt((x2-x)**2 + (y2-y)**2 + (z2-z)**2)
            if d == 0.0: d = d0
            accum += np.log(d/d0); n_renorm += 1
            sc = d0/d
            x2, y2, z2 = x + (x2-x)*sc, y + (y2-y)*sc, z + (z2-z)*sc
    return accum / (n_renorm * renorm_every * dt)

for b in [float(a) for a in sys.argv[1:]]:
    vals = [largest_lyapunov(b, s) for s in range(6)]
    print(f"b={b:.3f}: " + "  ".join(f"{v:+.4f}" for v in vals) +
          f"  | mean={np.mean(vals):+.4f} std={np.std(vals):.4f} min={min(vals):+.4f} max={max(vals):+.4f}", flush=True)
