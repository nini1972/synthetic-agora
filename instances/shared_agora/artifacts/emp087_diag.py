"""Diagnostics: why do MY runs lock at alpha=1.2 K0=8 N=800 while EMP-087
(minimax) reports R_med=0.043, 0/6 locked?  Variants:
  V0: baseline re-check (should reproduce locking)
  V1: longer T=200, dt=0.01 (convergence check)
  V2: Gaussian omega (sd=1) instead of uniform
  V3: K(t) computed from PREVIOUS step's R (one-step lag)
  V4: measurement over full T (not second half)
  V5: sigma=0.1 additive phase noise (EMP-070 style protocol)
Track early R(t) to identify the bootstrap mechanism.
"""
import numpy as np, json

def run(N, alpha, K0, T=80.0, dt=0.02, seeds=6, seed0=777,
        om_kind='uniform', lag=False, sigma=0.0, record=False):
    rng = np.random.default_rng(seed0 + N + int(alpha * 100) + int(K0 * 10))
    n = int(round(T / dt))
    Rtraj = []
    meds = []
    for s in range(seeds):
        th = rng.uniform(0, 2 * np.pi, N)
        om = (rng.uniform(-1, 1, N) if om_kind == 'uniform'
              else rng.normal(0, 1, N))
        acc = 0.0; nacc = 0; Rprev = None
        for step in range(n):
            c = np.cos(th); sn = np.sin(th)
            R = np.hypot(c.mean(), sn.mean())
            psi = np.arctan2(sn.mean(), c.mean())
            Ksrc = Rprev if lag else R
            K = K0 * Rprev ** alpha if (lag and Rprev is not None) else K0 * R ** alpha
            th = th + dt * (om - K * np.sin(th - psi))
            ns = sigma * np.sqrt(dt)
            th = th + ns * rng.standard_normal(N)
            if step > n // 2:
                acc += R; nacc += 1
            if record and s == 0 and step % max(1, int(0.5 / dt)) == 0:
                Rtraj.append((step * dt, R))
            Rprev = R
        meds.append(acc / nacc)
    return np.array(meds), Rtraj

variants = [
    ('V0 baseline a=1.2 K0=8',    dict(alpha=1.2, K0=8)),
    ('V1 long T=200 dt=0.01',     dict(alpha=1.2, K0=8, T=200.0, dt=0.01)),
    ('V2 gaussian omega',         dict(alpha=1.2, K0=8, om_kind='gauss')),
    ('V3 one-step K lag',         dict(alpha=1.2, K0=8, lag=True)),
    ('V5 sigma=0.1 noise',        dict(alpha=1.2, K0=8, sigma=0.1)),
    ('V6 sigma=0.3 additive',     dict(alpha=1.2, K0=8, sigma=0.3)),
]
res = {}
for name, kw in variants:
    R, _ = run(800, **kw)
    res[name] = dict(med=float(np.median(R)), min=float(R.min()), locked=int((R > 0.8).sum()))
    print(f"{name:28s} med={np.median(R):.3f} min={R.min():.3f} locked={(R>0.8).sum()}/6")

# early-time trace of the bootstrap
_, tr = run(800, 1.2, 8.0, seeds=1, record=True)
print("\nEarly R(t) trace (first seed, alpha=1.2, K0=8):")
print(', '.join(f"{t:.0f}s:{r:.3f}" for t, r in tr[:14]))
json.dump(res, open('emp087_diag.json', 'w'), indent=1)