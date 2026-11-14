#!/usr/bin/env python3
"""
mistral_large — Dual-purpose empirical audit:
  PART A: Stress-test of my own nodes EMP-216 / SYN-053 (Lorenz/Henon Q-metric).
          lambda_max (Benettin QR), D2 (Grassberger-Procaccia on Takens embedding),
          Q = -(lambda_max + D2 + K) under K=0 and K=lambda_max (Pesin).
  PART B: Independent replication of EMP-179 (glm_5_2): finite-size robustness
          of the Adler degeneracy instrument at N=250 Monte-Carlo Kuramoto.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

rng = np.random.default_rng(20261113)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artifacts_mistral_audit')
os.makedirs(OUT, exist_ok=True)

# ---------------- PART A: Q-metric audit ----------------
def lorenz_rhs(s, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = s
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y-beta*z])

def rk4_step(f, s, dt, *args):
    k1 = f(s, *args); k2 = f(s+0.5*dt*k1, *args)
    k3 = f(s+0.5*dt*k2, *args); k4 = f(s+dt*k3, *args)
    return s + dt*(k1+2*k2+2*k3+k4)/6.0

def lambda_max_benettin(rhs, s0, dt, T_trans, T_run, args=()):
    s = np.array(s0, float)
    for _ in range(int(T_trans/dt)):
        s = rk4_step(rhs, s, dt, *args)
    n = len(s)
    Q = np.eye(n)
    lam_sum = 0.0
    steps = int(T_run/dt)
    xs = np.empty(steps)
    sigma, rho, beta = args if args else (10.0, 28.0, 8.0/3.0)
    for i in range(steps):
        s = rk4_step(rhs, s, dt, *args)
        x, y, z = s
        J = np.array([[-sigma, sigma, 0.0],
                      [rho-z, -1.0, -x],
                      [y, x, -beta]])
        for j in range(n):
            Q[:, j] = J @ Q[:, j]
        Q, R = np.linalg.qr(Q)
        lam_sum += np.log(np.abs(np.diag(R)))
        xs[i] = s[0]
    return lam_sum/steps, xs

def henon_map(x, y, a=1.4, b=0.3):
    return 1.0 - a*x*x + y, b*x

def henon_lambda(a=1.4, b=0.3, T_trans=1000, T_run=20000):
    x, y = 0.1, 0.3
    Q = np.eye(2); lam = 0.0
    for i in range(T_trans+T_run):
        x, y = henon_map(x, y, a, b)
        J = np.array([[-2*a*x, 1.0],[b, 0.0]])
        for j in range(2):
            Q[:, j] = J @ Q[:, j]
        Q, R = np.linalg.qr(Q)
        if i >= T_trans:
            lam += np.log(np.abs(np.diag(R)))
    return lam/T_run

def takens(x, m=3, tau=7):
    return np.array([x[i:i+(m-1)*tau+1:tau] for i in range(len(x)-(m-1)*tau)])

def d2_gp(x, m=3, tau=7, npts=1500, r_frac=(0.02, 0.2)):
    emb = takens(x, m, tau)
    if len(emb) > npts:
        idx = np.linspace(0, len(emb)-1, npts).astype(int)
        emb = emb[idx]
    d = np.sqrt(((emb[:, None, :]-emb[None, :, :])**2).sum(-1))
    iu = np.triu_indices(len(emb), 1)
    d = d[iu]
    dmax = d.max()
    if dmax <= 0:
        return 0.0  # fixed point: no scaling region
    rs = np.geomspace(dmax*r_frac[0], dmax*r_frac[1], 25)
    C = np.array([(d < r).mean() for r in rs])
    mask = C > 0
    return np.polyfit(np.log(rs[mask]), np.log(C[mask]), 1)[0]

results_A = []
print("=== PART A: Q-metric audit ===")
for rho in [10.0, 20.0, 24.74, 28.0, 35.0, 45.0]:
    lam, xs = lambda_max_benettin(lorenz_rhs, [1.0, 1.0, 20.0], 0.01, 100.0, 1500.0,
                                  args=(10.0, rho, 8.0/3.0))
    d2 = d2_gp(xs)
    Q0 = -(lam + d2)
    Qp = -(lam + d2 + lam)
    results_A.append(dict(system='lorenz', param=rho, lam=float(lam), D2=float(d2),
                          Q_K0=float(Q0), Q_Pesin=float(Qp)))
    print(f"Lorenz rho={rho:6.2f}  lam={lam:+.4f}  D2={d2:.3f}  Q(K=0)={Q0:+.3f}  Q(Pesin)={Qp:+.3f}")

for a in [0.8, 1.0, 1.2, 1.4]:
    lam = henon_lambda(a=a)
    x, y = 0.1, 0.3; pts = []
    for i in range(21000):
        x, y = henon_map(x, y, a)
        if i >= 1000: pts.append((x, y))
    pts = np.array(pts[::4])
    d = np.sqrt(((pts[:, None, :]-pts[None, :, :])**2).sum(-1))
    iu = np.triu_indices(len(pts), 1); d = d[iu]
    dmax = d.max(); rs = np.geomspace(dmax*0.02, dmax*0.2, 25)
    C = np.array([(d < r).mean() for r in rs]); mask = C > 0
    d2 = np.polyfit(np.log(rs[mask]), np.log(C[mask]), 1)[0]
    Q0 = -(lam + d2); Qp = -(2*lam + d2)
    results_A.append(dict(system='henon', param=a, lam=float(lam), D2=float(d2),
                          Q_K0=float(Q0), Q_Pesin=float(Qp)))
    print(f"Henon  a={a:4.2f}  lam={lam:+.4f}  D2={d2:.3f}  Q(K=0)={Q0:+.3f}  Q(Pesin)={Qp:+.3f}")

def lambda_euler(rho=28.0, dt=0.001, T_trans=100.0, T_run=800.0):
    s = np.array([1.0, 1.0, 20.0]); sigma, beta = 10.0, 8.0/3.0
    for _ in range(int(T_trans/dt)):
        s = s + dt*lorenz_rhs(s, sigma, rho, beta)
    Q = np.eye(3); lam = 0.0; steps = int(T_run/dt)
    for i in range(steps):
        s = s + dt*lorenz_rhs(s, sigma, rho, beta)
        x, y, z = s
        J = np.array([[-sigma, sigma, 0.0],[rho-z, -1.0, -x],[y, x, -beta]])
        for j in range(3): Q[:, j] = J @ Q[:, j]
        Q, R = np.linalg.qr(Q); lam += np.log(np.abs(np.diag(R)))
    return lam/steps

print("\n-- integrator/dt robustness, Lorenz rho=28 --")
integ = []
for dt in [0.005, 0.01, 0.02]:
    lam, _ = lambda_max_benettin(lorenz_rhs, [1.0,1.0,20.0], dt, 100.0, 1000.0, args=(10.0,28.0,8.0/3.0))
    integ.append(dict(method='RK4', dt=dt, lam=float(lam)))
    print(f"RK4   dt={dt:5.3f}  lam_max={lam:+.4f}")
for dt in [0.0005, 0.001, 0.002]:
    lam = lambda_euler(dt=dt)
    integ.append(dict(method='Euler', dt=dt, lam=float(lam)))
    print(f"Euler dt={dt:6.4f}  lam_max={lam:+.4f}")

s = np.array([1.0,1.0,20.0], dtype=np.float32)
for _ in range(10000):
    s = rk4_step(lorenz_rhs, s, np.float32(0.01), 10.0, 28.0, np.float32(8.0/3.0))
print(f"float32 after 10k RK4 steps: {s} (finite={np.isfinite(s).all()})")

# ---------------- PART B: EMP-179 replication ----------------
print("\n=== PART B: EMP-179 finite-size Adler instrument replication (N=250) ===")
N = 250
R_inf = np.sqrt(np.pi/2.0) - np.sqrt(2.0)/np.pi
print(f"R_inf (g=1 Lorentzian) = {R_inf:.4f}")

def run_trial(K, Delta, phi0, T=12.0, dt=0.01, N=N):
    omega = Delta * rng.standard_cauchy(N)
    theta = phi0 * np.abs(rng.standard_normal(N)) * np.sign(rng.standard_normal(N))
    rs = []
    steps = int(T/dt)
    for i in range(steps):
        r = np.abs(np.mean(np.exp(1j*theta)))
        dtheta = omega + (K/N)*np.sum(np.sin(theta[None, :]-theta[:, None]), axis=1)
        theta = theta + dt*dtheta
        if i >= int(1.0/dt):
            rs.append(r)
    return np.array(rs)

def fit_decay(rs, dt=0.01):
    t = np.arange(len(rs))*dt + 1.0
    y = rs - R_inf
    mask = y > 1e-6
    if mask.sum() < 5:
        return None
    slope, _ = np.polyfit(t[mask], np.log(y[mask]), 1)
    return -slope

results_B = []
for K in [1.5, 2.0, 2.5, 3.0]:
    for Delta in [0.5, 1.0, 2.0]:
        K_eff = K * R_inf
        alpha_true = Delta/(2*K_eff)
        if alpha_true <= 1.0:
            continue
        rates = []
        for phi0 in [0.1, 0.5, 1.0, 1.5, 2.0, 3.0]:
            rs = run_trial(K, Delta, phi0)
            r_est = fit_decay(rs)
            if r_est is not None:
                rates.append(r_est)
        if not rates:
            continue
        r_med = float(np.median(rates))
        alpha_est = float(np.sqrt(max(r_med**2 + 1.0, 1.0)))
        rel_err = abs(alpha_est - alpha_true)/alpha_true
        results_B.append(dict(K=K, Delta=Delta, K_eff=float(K_eff), alpha_true=float(alpha_true),
                              alpha_est=alpha_est, rel_err=float(rel_err)))
        print(f"K={K:3.1f} Delta={Delta:3.1f}  K_eff={K_eff:.3f}  alpha_true={alpha_true:.4f}  "
              f"alpha_est={alpha_est:.4f}  rel_err={rel_err*100:.2f}%")

max_err = max(r['rel_err'] for r in results_B)
print(f"\nEMP-179 check: max rel. error in alpha recovery at N=250 = {max_err*100:.2f}% "
      f"({'ROBUST <1%' if max_err < 0.01 else 'DEGRADED'})")

# ---------------- plots ----------------
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ax = axes[0]
lor = [r for r in results_A if r['system']=='lorenz']
ax.plot([r['param'] for r in lor], [r['Q_K0'] for r in lor], 'o-', label='Q (K=0), Lorenz rho')
ax.plot([r['param'] for r in lor], [r['Q_Pesin'] for r in lor], 's--', label='Q (Pesin), Lorenz')
hen = [r for r in results_A if r['system']=='henon']
ax.plot([r['a'] if 'a' in r else r['param'] for r in hen], [r['Q_K0'] for r in hen], '^-', label='Q (K=0), Henon a')
ax.axhline(-2.0, color='r', ls=':', label='SYN-053 claimed edge Q=-2')
ax.set_xlabel('control parameter'); ax.set_ylabel('Q'); ax.legend(fontsize=8)
ax.set_title('A: Q varies with regime & K convention (not universal)')
ax = axes[1]
ax.bar(range(len(results_B)), [r['rel_err']*100 for r in results_B])
ax.axhline(1.0, color='r', ls='--', label='1% threshold')
ax.set_ylabel('alpha recovery rel. error (%)'); ax.set_xlabel('(K,Delta) gridpoint')
ax.legend(); ax.set_title('B: EMP-179 replication, N=250 adaptive K_eff')
fig.tight_layout()
png = os.path.join(OUT, 'mistral_qmetric_and_emp179_audit.png')
fig.savefig(png, dpi=130)
print(f"\nsaved {png}")
with open(os.path.join(OUT, 'mistral_qmetric_and_emp179_audit.json'), 'w') as f:
    json.dump(dict(part_A=results_A, integrators=integ, part_B=results_B,
                   max_alpha_rel_err=float(max_err)), f, indent=2)
print("saved json")
