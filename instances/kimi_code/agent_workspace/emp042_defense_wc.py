#!/usr/bin/env python3
"""Deterministic hysteresis replication/refinement of EMP-042 (state-dependent feedback Kuramoto).
Parameters: N=200, Gaussian frequencies sigma=1.0, Heun integration dt=0.02.
Runs on World C / local; writes to ../../shared_agora/artifacts.
"""
import os, json, time, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import quad

np.random.seed(2024)
N = 200
sigma_omega = 1.0
omega = np.random.normal(0.0, sigma_omega, N)
dt = 0.02
T_trans = 30.0
T_per = 80.0
trans = int(T_trans/dt)
per = int(T_per/dt)
K_grid = np.arange(0.5, 4.55, 0.2)
alpha_vals = [1.0, 2.0]

# Mean-field locked-branch threshold via Ott-Antonsen self-consistency
def h_scalar(x):
    if x <= 0.0: return 0.0
    val, _ = quad(lambda u: np.exp(-u*u/2)/np.sqrt(2*np.pi)*np.sqrt(max(0.0, 1-(u/x)**2)), -x, x, limit=80)
    return val

def mf_threshold(alpha, sigma):
    xs = np.linspace(0.05, 8.0, 1600)
    hs = np.array([h_scalar(x) for x in xs])
    K0 = sigma * xs / (hs**(alpha+1))
    imin = np.argmin(K0)
    return xs[imin], K0[imin], hs[imin]

mf = {}
for a in alpha_vals:
    xv, kc, rc = mf_threshold(a, sigma_omega)
    mf[a] = {'K0_c': float(kc), 'x_c': float(xv), 'R_c': float(rc)}
print('Mean-field thresholds:', mf)

# Heun helpers
def rhs(theta, K0, alpha):
    z = np.mean(np.exp(1j*theta), axis=-1, keepdims=True)
    R = np.abs(z); psi = np.angle(z)
    K = K0 * (R**alpha)
    return omega + K * np.sin(psi - theta)

def heun_step(theta, K0, alpha):
    k1 = rhs(theta, K0, alpha)
    k2 = rhs(theta + dt*k1, K0, alpha)
    return theta + 0.5*dt*(k1 + k2)

def order(theta):
    return np.abs(np.mean(np.exp(1j*theta), axis=-1))

# Backward coherent sweep
results = {a: {'K0': K_grid.tolist()} for a in alpha_vals}
t0 = time.time()
for alpha in alpha_vals:
    theta = np.zeros(N)
    Rb = []
    for K0 in K_grid[::-1]:
        for _ in range(trans): theta = heun_step(theta, K0, alpha)
        Rs = []
        for s in range(per):
            theta = heun_step(theta, K0, alpha)
            if s % 10 == 0: Rs.append(order(theta))
        Rb.append(float(np.mean(Rs[-20:])))
    results[alpha]['R_back'] = Rb[::-1]
print('Backward sweep time', time.time()-t0)

# Forward random-IC sweep (vectorized seeds)
n_seeds = 20
t0 = time.time()
for alpha in alpha_vals:
    Rf_mean, Rf_std, lock_frac = [], [], []
    for K0 in K_grid:
        theta = np.random.uniform(0.0, 2*np.pi, size=(n_seeds, N))
        for _ in range(trans): theta = heun_step(theta, K0, alpha)
        Rs = []
        for s in range(per):
            theta = heun_step(theta, K0, alpha)
            if s % 5 == 0: Rs.append(order(theta))
        Rs = np.array(Rs)  # (snap, seeds)
        Rlast = Rs[-20:].mean(axis=0)
        Rf_mean.append(float(Rlast.mean()))
        Rf_std.append(float(Rlast.std()))
        lock_frac.append(float(np.mean(Rlast > 0.5)))
    results[alpha]['R_forward_mean'] = Rf_mean
    results[alpha]['R_forward_std'] = Rf_std
    results[alpha]['lock_fraction'] = lock_frac
print('Forward sweep time', time.time()-t0)

# Projected finite-difference Lyapunov exponent (benchmark on constant K, then feedback)
def le_finite_diff(K0, alpha, T=250.0, warm=40.0, renorm=25, eps0=1e-8):
    nwarm = int(warm/dt)
    nsteps = int(T/dt)
    theta = np.zeros(N)
    for _ in range(nwarm): theta = heun_step(theta, K0, alpha)
    theta2 = theta.copy() + eps0*np.random.randn(N)
    theta2 -= theta2.mean(); theta -= theta.mean()  # remove global rotation
    lam_sum = 0.0
    nren = 0
    for s in range(nsteps):
        theta = heun_step(theta, K0, alpha)
        theta2 = heun_step(theta2, K0, alpha)
        if s % renorm == 0 and s > 0:
            d = theta2 - theta
            d -= d.mean()  # project out rotation
            norm = np.linalg.norm(d)
            lam_sum += np.log(norm / eps0)
            theta2 = theta + eps0 * (d / norm)
            nren += 1
    return lam_sum / (nren * renorm * dt)

le_records = []
for ctrl_K in [1.0, 2.5, 4.0]:
    le_records.append({'case': f'constant_K={ctrl_K}', 'alpha': 0.0, 'K0': ctrl_K,
                       'LE': float(le_finite_diff(ctrl_K, 0.0))})
for alpha in alpha_vals:
    for K0 in [1.5, 2.5, 3.5]:
        le_records.append({'case': f'feedback_a{alpha}_K{K0}', 'alpha': alpha, 'K0': K0,
                           'LE': float(le_finite_diff(K0, alpha))})
print('LE:', le_records)

# Save artifacts
outdir = '../../shared_agora/artifacts'
os.makedirs(outdir, exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for idx, alpha in enumerate(alpha_vals):
    ax = axes[idx]
    ax.plot(K_grid, results[alpha]['R_back'], 'o-', color='C0', label='backward coherent')
    ax.errorbar(K_grid, results[alpha]['R_forward_mean'], yerr=results[alpha]['R_forward_std'],
                fmt='s', color='C1', alpha=0.7, label='forward random (mean±std)')
    ax.plot(K_grid, results[alpha]['lock_fraction'], '^--', color='C2', alpha=0.6, label='forward lock frac')
    ax.axvline(mf[alpha]['K0_c'], color='k', ls='--', lw=1.5, label=f"OA saddle-node K0={mf[alpha]['K0_c']:.2f}")
    ax.set_xlabel('K0')
    ax.set_ylabel('R / lock fraction')
    ax.set_title(f'alpha={int(alpha)}, sigma={sigma_omega}, N={N}')
    ax.set_ylim(-0.05, 1.05); ax.grid(True, alpha=0.3); ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'emp042_defense_hysteresis.png'), dpi=150)

fig, ax = plt.subplots(figsize=(8, 4))
names = [r['case'] for r in le_records]
vals = [r['LE'] for r in le_records]
ax.bar(range(len(names)), vals, color=['C0' if 'constant' in n else 'C1' for n in names])
ax.set_xticks(range(len(names))); ax.set_xticklabels(names, rotation=45, ha='right', fontsize=7)
ax.axhline(0, color='k', lw=0.8); ax.set_ylabel('max nontrivial LE')
ax.set_title('Projected finite-difference LE (deterministic)')
ax.grid(True, axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'emp042_defense_lyapunov.png'), dpi=150)

with open(os.path.join(outdir, 'emp042_defense.json'), 'w') as f:
    json.dump({'parameters': {'N':N,'sigma_omega':sigma_omega,'dt':dt,'T_trans':T_trans,'T_per':T_per,'seeds':n_seeds},
               'mean_field': mf, 'hysteresis': results, 'lyapunov': le_records}, f, indent=2)
print('Saved to', outdir)
