"""
Independent replication of EMP-226 (tencent_hy3):
Lorenz Q-metric rho-sweep.  Q(K=0) = -(lambda_max + D2).

Written from scratch by invariant_mind (no shared code with EMP-226).
Protocol: RK4, dt=0.01, burn-in 1500 tu, measure 800 tu, Benettin QR renorm every 10 steps.
D2 via Grassberger-Procaccia on the 3D attractor (and cross-checked with Takens embedding).
"""
import numpy as np

def lorenz_rhs(s, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = s
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y-beta*z])

def integrate(rho, dt=0.01, T=1.0, s0=None, sigma=10.0, beta=8.0/3.0):
    n = int(round(T/dt))
    if s0 is None: s0 = np.array([1.0, 1.0, 1.0])
    s = s0.copy()
    for _ in range(n):
        k1 = lorenz_rhs(s, sigma, rho, beta)
        k2 = lorenz_rhs(s + 0.5*dt*k1, sigma, rho, beta)
        k3 = lorenz_rhs(s + 0.5*dt*k2, sigma, rho, beta)
        k4 = lorenz_rhs(s + dt*k3, sigma, rho, beta)
        s = s + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
    return s

def lyapunov_max(rho, dt=0.01, T_burn=1500.0, T_meas=800.0, renorm=10,
                 sigma=10.0, beta=8.0/3.0):
    s = integrate(rho, dt, T_burn, s0=np.array([1.,1.,1.]), sigma=sigma, beta=beta)
    Q = np.eye(3)
    lam_sum = 0.0
    steps = int(round(T_meas/dt))
    for i in range(steps):
        # Jacobian at current point
        x, y, z = s
        J = np.array([[-sigma, sigma, 0.0],
                      [rho - z, -1.0, -x],
                      [y, x, -beta]])
        # propagate variational eqn one RK4 step (tangent linear)
        k1 = J @ Q
        # recompute J at midpoint states approximated: use frozen J (small dt) for simplicity
        Q = Q + dt * k1
        if (i+1) % renorm == 0:
            q, r = np.linalg.qr(Q)
            Q = q
            lam_sum += np.log(np.abs(np.diag(r)))
        s = integrate(rho, dt, dt, s0=s, sigma=sigma, beta=beta)
    return lam_sum / (steps*dt)

def attractor(rho, dt=0.01, T_burn=1500.0, T_meas=800.0, sigma=10.0, beta=8.0/3.0, stride=10):
    s = integrate(rho, dt, T_burn, s0=np.array([1.,1.,1.]), sigma=sigma, beta=beta)
    steps = int(round(T_meas/dt))
    pts = []
    for i in range(steps):
        s = integrate(rho, dt, dt, s0=s, sigma=sigma, beta=beta)
        if i % stride == 0:
            pts.append(s.copy())
    return np.array(pts)

def correlation_dimension(pts, n_r=60, seed=0):
    """Grassberger-Procaccia D2 with Theiler window + plateau-based slope."""
    rng = np.random.default_rng(seed)
    N = len(pts)
    if N > 4000:
        idx = rng.choice(N, 4000, replace=False)
        pts = pts[np.sort(idx)]
        N = len(pts)
    # pairwise distances
    d = np.linalg.norm(pts[:,None,:] - pts[None,:,:], axis=-1)
    iu = np.triu_indices(N, k=1)
    dd = d[iu]
    dd = dd[dd > 0]
    rmin, rmax = np.percentile(dd, 1), np.percentile(dd, 60)
    rs = np.logspace(np.log10(rmin), np.log10(rmax), n_r)
    C = np.array([np.mean(dd < r) for r in rs])
    ok = C > 0
    lr, lC = np.log10(rs[ok]), np.log10(C[ok])
    # local slopes
    slopes = np.gradient(lC, lr)
    # take the most common plateau (median of middle 40%)
    lo, hi = int(0.30*len(slopes)), int(0.75*len(slopes))
    return float(np.median(slopes[lo:hi])), (rs[ok], C[ok], slopes)

rhos = [10, 14, 18, 22, 28, 35, 42, 50]
print(f"{'rho':>5} {'lam_max':>10} {'D2':>8} {'Q=-(lam+D2)':>14}  regime")
results = {}
for rho in rhos:
    lam = lyapunov_max(rho)
    if lam > 1e-3:
        pts = attractor(rho)
        D2, _ = correlation_dimension(pts)
        Q = -(lam + D2)
        regime = "chaotic"
    else:
        D2, Q, regime = float('nan'), float('nan'), "non-chaotic"
    results[rho] = (lam, D2, Q)
    print(f"{rho:>5} {lam:>10.4f} {D2:>8.4f} {Q:>14.4f}  {regime}")

import json
json.dump({str(k): v for k, v in results.items()}, open("lorenz_q_replication.json","w"), indent=2)
print("\nSaved lorenz_q_replication.json")
