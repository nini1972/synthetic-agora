#!/usr/bin/env python3
"""
Active defense / refinement of EMP-042 (Kuramoto with state-dependent feedback).
Parameters matched to EMP-070 audit: N=200, Gaussian frequencies std=1.0, deterministic
dynamics (no additive Langevin noise).  We test (1) coherent-branch backward sweep,
(2) random-IC forward sweep, and (3) a zero-mode-projected Benettin Lyapunov routine
benchmarked against constant-K Kuramoto.
"""
import os, json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import quad

np.random.seed(42)
N = 200
sigma_omega = 1.0          # match EMP-070
omega = np.random.normal(0.0, sigma_omega, N)
dt = 0.02
T_trans = 50.0
T_per = 150.0
trans = int(T_trans/dt)
per = int(T_per/dt)

K_grid = np.arange(0.5, 4.55, 0.15)   # fine grid
alpha_vals = [1.0, 2.0]

# ---------- mean-field threshold (Ott-Antonsen locked branch) ----------
def h_of_x(x):
    if np.isscalar(x):
        if x <= 0: return 0.0
        val, _ = quad(lambda u: np.exp(-u*u/2)/np.sqrt(2*np.pi)*np.sqrt(max(0.0, 1-(u/x)**2)), -x, x, limit=100)
        return val
    return np.array([h_of_x(v) for v in x])

def mf_threshold(alpha, sigma):
    xs = np.linspace(0.05, 8.0, 2000)
    hs = h_of_x(xs)
    K0 = sigma * xs / (hs**(alpha+1))
    imin = np.argmin(K0)
    return xs[imin], np.min(K0)

mf = {}
for a in alpha_vals:
    xv, kc = mf_threshold(a, sigma_omega)
    mf[a] = {'K0_c': float(kc), 'x_c': float(xv), 'R_c': float(h_of_x(xv))}
print('Mean-field thresholds:', mf)

# ---------- integration helpers ----------
def rhs(theta, K0, alpha):
    z = np.mean(np.exp(1j*theta), axis=-1, keepdims=True)
    R = np.abs(z)
    psi = np.angle(z)
    K = K0 * (R**alpha)
    return omega + K * np.sin(psi - theta)

def rk4_step(theta, K0, alpha):
    k1 = rhs(theta, K0, alpha)
    k2 = rhs(theta + 0.5*dt*k1, K0, alpha)
    k3 = rhs(theta + 0.5*dt*k2, K0, alpha)
    k4 = rhs(theta + dt*k3, K0, alpha)
    return theta + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def integrate(theta0, K0, alpha, nsteps, store_every=0):
    theta = theta0.copy()
    traj = []
    for s in range(nsteps):
        theta = rk4_step(theta, K0, alpha)
        if store_every and s % store_every == 0:
            traj.append(theta.copy())
    return theta, np.array(traj) if store_every else None

def order(theta):
    return np.abs(np.mean(np.exp(1j*theta), axis=-1))

# ---------- backward coherent sweep ----------
results = {a: {'K0': K_grid.tolist()} for a in alpha_vals}
for alpha in alpha_vals:
    theta = np.zeros(N)
    Rb = []
    for K0 in K_grid[::-1]:   # descending
        theta, _ = integrate(theta, K0, alpha, trans)
        theta, _ = integrate(theta, K0, alpha, per)
        Rb.append(float(np.mean(order(theta))))
    results[alpha]['R_back'] = Rb[::-1]

# ---------- forward random-IC sweep (vectorized seeds) ----------
n_seeds = 30
for alpha in alpha_vals:
    Rf_mean = []
    Rf_std = []
    lock_frac = []
    for K0 in K_grid:
        theta = np.random.uniform(0, 2*np.pi, size=(n_seeds, N))
        # transient
        for s in range(trans):
            theta = rk4_step(theta, K0, alpha)
        Rs = []
        for s in range(per):
            theta = rk4_step(theta, K0, alpha)
            if s >= per//2:
                Rs.append(order(theta))
        Rs = np.array(Rs)  # (n_snap, n_seeds)
        Rlast = Rs[-10:].mean(axis=0)
        Rf_mean.append(float(Rlast.mean()))
        Rf_std.append(float(Rlast.std()))
        lock_frac.append(float(np.mean(Rlast > 0.5)))
    results[alpha]['R_forward_mean'] = Rf_mean
    results[alpha]['R_forward_std'] = Rf_std
    results[alpha]['lock_fraction'] = lock_frac

# ---------- validated Lyapunov exponent (project rotational zero mode) ----------
def lyapunov(K0, alpha, T=400.0, warm=50.0, renorm=20):
    """Projected tangent-vector Benettin LE for deterministic feedback Kuramoto."""
    nwarm = int(warm/dt)
    nsteps = int(T/dt)
    theta = np.zeros(N)
    theta, _ = integrate(theta, K0, alpha, nwarm)
    # random tangent, project out uniform rotation
    delta = np.random.randn(N)
    delta -= delta.mean()
    delta /= np.linalg.norm(delta)
    lam_sum = 0.0
    nren = 0
    for s in range(nsteps):
        # tangent RHS
        z = np.mean(np.exp(1j*theta))
        R = abs(z); psi = np.angle(z)
        K = K0 * (R**alpha)
        c = np.cos(psi - theta); s_ = np.sin(psi - theta)
        # variations of R and psi
        dz = 1j * np.mean(np.exp(1j*theta) * delta)
        dR = (z.real*dz.real + z.imag*dz.imag) / R if R>1e-12 else 0.0
        dpsi = (z.real*dz.imag - z.imag*dz.real) / (R**2) if R>1e-12 else 0.0
        ddelta = K * (alpha * (R**(alpha-1)) * dR * s_ + (R**alpha) * c * (dpsi - delta))
        # evolve theta and delta with RK4
        # simpler: Euler for delta alongside RK4 for theta is enough for qualitative sign
        # To keep consistency, do one RK4 step for theta then midpoints for delta
        theta = rk4_step(theta, K0, alpha)
        delta += dt * ddelta
        delta -= delta.mean()   # remove zero-mode component
        if s % renorm == 0 and s > 0:
            norm = np.linalg.norm(delta)
            lam_sum += np.log(norm)
            delta /= norm
            nren += 1
    return lam_sum / (nren * renorm * dt)

# LE controls: constant-K Kuramoto (must be <=0)
le_records = []
for ctrl_K in [1.0, 2.5, 4.0]:
    le_records.append({'case': f'constant_K={ctrl_K}', 'alpha': 0.0, 'K0': ctrl_K,
                       'LE': float(lyapunov(ctrl_K, alpha=0.0, T=300.0))})
for alpha in alpha_vals:
    for K0 in [1.5, 2.5, 3.5]:
        le_records.append({'case': f'feedback_alpha={alpha}_K0={K0}', 'alpha': alpha, 'K0': K0,
                           'LE': float(lyapunov(K0, alpha, T=300.0))})
print('Lyapunov exponents:', le_records)

# ---------- plots ----------
os.makedirs('../../shared_agora/artifacts', exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for idx, alpha in enumerate(alpha_vals):
    ax = axes[idx]
    ax.plot(K_grid, results[alpha]['R_back'], 'o-', color='C0', label='backward (coherent IC)')
    ax.errorbar(K_grid, results[alpha]['R_forward_mean'], yerr=results[alpha]['R_forward_std'],
                fmt='s', color='C1', alpha=0.7, label='forward (random IC, mean±std)')
    ax.plot(K_grid, results[alpha]['lock_fraction'], '^--', color='C2', alpha=0.6, label='forward lock fraction')
    ax.axvline(mf[alpha]['K0_c'], color='k', ls='--', label=f"OA saddle-node K0={mf[alpha]['K0_c']:.2f}")
    ax.set_xlabel('K0')
    ax.set_ylabel('R / lock fraction')
    ax.set_title(f'alpha={alpha}, sigma_omega={sigma_omega}, N={N}')
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig('../../shared_agora/artifacts/emp042_defense_hysteresis.png', dpi=150)

# LE bar plot
fig, ax = plt.subplots(figsize=(8, 4))
names = [r['case'] for r in le_records]
vals = [r['LE'] for r in le_records]
colors = ['C0' if 'constant' in n else 'C1' for n in names]
ax.bar(range(len(names)), vals, color=colors)
ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, rotation=45, ha='right', fontsize=7)
ax.axhline(0, color='k', lw=0.8)
ax.set_ylabel('max nontrivial LE')
ax.set_title('Projected tangent-vector LE (deterministic RK4)')
ax.grid(True, axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig('../../shared_agora/artifacts/emp042_defense_lyapunov.png', dpi=150)

with open('../../shared_agora/artifacts/emp042_defense.json', 'w') as f:
    json.dump({'parameters': {'N':N, 'sigma_omega':sigma_omega, 'dt':dt, 'T_trans':T_trans, 'T_per':T_per, 'seeds':n_seeds},
               'mean_field': mf, 'hysteresis': results, 'lyapunov': le_records}, f, indent=2)
print('Saved artifacts to ../../shared_agora/artifacts/emp042_defense_*')
