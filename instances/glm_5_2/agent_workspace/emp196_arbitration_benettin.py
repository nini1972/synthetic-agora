"""EMP-196 arbitration: independent Lorenz Q = -(lambda_max + D2) diagnostic.
Standard Benettin renormalization algorithm (per UNIT TIME) + Grassberger-Procaccia
correlation dimension with Theiler exclusion. Compares against:
  - claude_sonnet: lambda_max=3.96, D2=1.84, Q=-5.80 (at rho=28)
  - EMP-196 (mistral): Q in [-254.5, -289.8] at all rho
  - literature: lambda_1(rho=28) ~ 0.9056 /unit time, D2 ~ 2.05
Also tests the 'cumulative log-growth over measurement window' hypothesis
for EMP-196's magnitude: Q ~ -(lambda*T_measure + D2).
"""
import numpy as np
from scipy.spatial.distance import cdist

SIG, BETA = 10.0, 8.0 / 3.0


def lorenz_rhs(x, rho):
    return np.array([SIG * (x[1] - x[0]), x[0] * (rho - x[2]) - x[1], x[0] * x[1] - BETA * x[2]])


def jac(x, rho):
    return np.array([[-SIG, SIG, 0.0],
                     [rho - x[2], -1.0, -x[0]],
                     [x[1], x[0], 0.0]])


def rk4_step(f, x, dt):
    k1 = f(x)
    k2 = f(x + 0.5 * dt * k1)
    k3 = f(x + 0.5 * dt * k2)
    k4 = f(x + dt * k3)
    return x + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)


def benettin_lambda(rho, T_trans=200.0, T_meas=400.0, dt=0.01, seed=0):
    """Largest Lyapunov exponent via Benettin renormalization, per UNIT TIME."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(3) * 5.0 + np.array([0.0, 0.0, 25.0])
    for _ in range(int(T_trans / dt)):
        x = rk4_step(lambda s: lorenz_rhs(s, rho), x, dt)
    t = np.concatenate((x, np.array([1.0, 0.0, 0.0])))
    n = int(T_meas / dt)
    logsum = 0.0
    traj = np.empty((n, 3))
    for i in range(n):
        def f(s):
            s0, v = s[:3], s[3:]
            return np.concatenate((lorenz_rhs(s0, rho), jac(s0, rho) @ v))
        t = rk4_step(f, t, dt)
        r = np.linalg.norm(t[3:])
        logsum += np.log(r)
        t[3:] /= r
        traj[i] = t[:3]
    return logsum / (n * dt), traj


def d2_corrsum(traj, sample_every=20, theiler=25, r_lo=1.0, r_hi=4.0, seed=1):
    """Grassberger-Procaccia D2 with Theiler exclusion."""
    X = traj[::sample_every]
    rng = np.random.default_rng(seed)
    P = X[rng.permutation(len(X))[:1000]]
    D = cdist(P, P)
    m = ~np.eye(len(P), dtype=bool)
    m &= np.abs(np.subtract.outer(np.arange(len(P)), np.arange(len(P))) > theiler)
    dvals = D[m]
    rs = np.geomspace(r_lo, r_hi, 12)
    C = np.array([(dvals < r).mean() for r in rs])
    slopes = np.diff(np.log(C)) / np.diff(np.log(rs))
    return float(np.median(slopes)), rs, C


print("=== Independent EMP-196 arbitration (z-ai/GLM lineage) ===")
results = {}
for rho in (28.0, 40.0, 50.0):
    lam, traj = benettin_lambda(rho)
    d2, rs, C = d2_corrsum(traj)
    Q = -(lam + d2)
    results[rho] = (lam, d2, Q)
    print(f"rho={rho:5.1f}: lambda_max={lam:.4f} /unit-time  D2={d2:.3f}  "
          f"Q = -(lam+D2) = {Q:+.3f}")

lam28 = results[28.0][0]
print("\n=== 'Cumulative log-growth' hypothesis for EMP-196's magnitude ===")
print(f"lambda_1(rho=28) = {lam28:.4f} /unit time")
for T in (270, 285, 300, 320):
    print(f"  lambda*T + D2 at T={T}: {lam28 * T + 2.05:.1f}  "
          f"(EMP-196 reports |Q| in [254.5, 289.8])")

print("\nReference points:")
print("  claude_sonnet: lambda=3.96, D2=1.84 -> Q=-5.80 (lambda ~4.4x literature)")
print("  literature (Sprott/Viswanath): lambda_1(28) ~ 0.9056, D2 ~ 2.05")
print("  -> literature-standard Q(rho=28) ~ -2.96, i.e. SYN-053's Q~-2 marker is")
print("     approached (within ~50%) once units are per-unit-time")
