"""Robustness/stress test for Kuramoto escape-time prefactor u.

Tests sensitivity of u = a*K0*R0**a*t_esc/2 to:
  (1) locking threshold R_thr,
  (2) numerical integration (Euler vs RK4, multiple dt),
  (3) system size N at fixed K0 (K/N convention).

Saves a JSON summary and PNG figures.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

np.random.seed(0)


def simulate_many(seeds, N, a, K0, kappa, R_thr, dt, t_max, method='euler', normalize=True):
    """Vectorized over seeds. Returns dict with arrays R0, t_esc, u, locked."""
    n_steps = int(t_max / dt)
    R0 = np.empty(seeds)
    t_esc = np.full(seeds, np.nan)
    locked = np.zeros(seeds, dtype=bool)

    omega = np.random.standard_cauchy(size=(seeds, N)) * kappa  # Lorentzian spread
    theta = np.random.uniform(0, 2*np.pi, size=(seeds, N))

    z0 = np.mean(np.exp(1j*theta), axis=1)
    R0[:] = np.abs(z0)

    def f(th, z):
        R = np.abs(z)
        psi = np.angle(z)
        K = (K0 / N) if normalize else K0
        return omega + K * (R**a) * np.sin(psi - th)

    if method == 'euler':
        for step in range(n_steps):
            z = np.mean(np.exp(1j*theta), axis=1)
            hit = (~locked) & (np.abs(z) >= R_thr)
            locked[hit] = True
            t_esc[hit] = step * dt
            if locked.all():
                break
            theta += dt * f(theta, z[:, None])
    elif method == 'rk4':
        for step in range(n_steps):
            z0s = np.mean(np.exp(1j*theta), axis=1)
            hit = (~locked) & (np.abs(z0s) >= R_thr)
            locked[hit] = True
            t_esc[hit] = step * dt
            if locked.all():
                break
            k1 = f(theta, z0s[:, None])
            th1 = theta + 0.5*dt*k1
            z1 = np.mean(np.exp(1j*th1), axis=1)
            k2 = f(th1, z1[:, None])
            th2 = theta + 0.5*dt*k2
            z2 = np.mean(np.exp(1j*th2), axis=1)
            k3 = f(th2, z2[:, None])
            th3 = theta + dt*k3
            z3 = np.mean(np.exp(1j*th3), axis=1)
            k4 = f(th3, z3[:, None])
            theta += (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
    else:
        raise ValueError(method)

    u = (a * K0 * (R0**a) * t_esc) / 2.0
    return {'R0': R0, 't_esc': t_esc, 'u': u, 'locked': locked}


def summarize(arr):
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return {'mean': np.nan, 'median': np.nan, 'std': np.nan,
                'min': np.nan, 'max': np.nan, 'n': 0}
    return {'mean': float(np.mean(arr)), 'median': float(np.median(arr)),
            'std': float(np.std(arr)), 'min': float(np.min(arr)),
            'max': float(np.max(arr)), 'n': len(arr)}


outdir = 'world_c_results' if os.path.isdir('world_c_results') else '../../shared_agora/artifacts'
os.makedirs(outdir, exist_ok=True)

results = {}
base = {'N': 100, 'a': 1, 'K0': 5.0, 'kappa': 1.0, 'dt': 0.01, 't_max': 40.0, 'seeds': 20}

# (1) Threshold dependence
thr_sweep = np.arange(0.1, 0.85, 0.1)
rows_thr = []
for R_thr in thr_sweep:
    res = simulate_many(seeds=base['seeds'], N=base['N'], a=base['a'], K0=base['K0'],
                        kappa=base['kappa'], R_thr=R_thr, dt=base['dt'], t_max=base['t_max'],
                        method='euler')
    lock_rate = float(np.mean(res['locked']))
    s = summarize(res['u'])
    rows_thr.append({'R_thr': round(R_thr, 2), 'lock_rate': lock_rate, **s})
    print(f"R_thr={R_thr:.2f} lock={lock_rate:.2f} u_median={s['median']:.4f}")
results['threshold_dependence'] = rows_thr

# (2) dt / integrator convergence
dt_vals = [0.02, 0.01, 0.005]
rows_dt = []
for method in ['euler', 'rk4']:
    for dt in dt_vals:
        res = simulate_many(seeds=12, N=80, a=base['a'], K0=base['K0'],
                            kappa=base['kappa'], R_thr=0.5, dt=dt, t_max=15.0,
                            method=method)
        lock_rate = float(np.mean(res['locked']))
        s = summarize(res['u'])
        rows_dt.append({'method': method, 'dt': dt, 'lock_rate': lock_rate, **s})
        print(f"method={method} dt={dt:.3f} lock={lock_rate:.2f} u_median={s['median']:.4f}")
results['dt_integrator_convergence'] = rows_dt

# (3) N dependence
N_vals = [50, 100, 200, 400]
rows_N = []
for N in N_vals:
    res = simulate_many(seeds=base['seeds'], N=N, a=base['a'], K0=base['K0'],
                        kappa=base['kappa'], R_thr=0.5, dt=base['dt'], t_max=base['t_max'],
                        method='euler')
    lock_rate = float(np.mean(res['locked']))
    s = summarize(res['u'])
    rows_N.append({'N': N, 'lock_rate': lock_rate, **s})
    print(f"N={N} lock={lock_rate:.2f} u_median={s['median']:.4f}")
results['N_dependence'] = rows_N

# (4) a=2 quick check
print("\na=2 check...")
res_a2 = simulate_many(seeds=24, N=300, a=2, K0=5.0, kappa=1.0, R_thr=0.5,
                       dt=0.01, t_max=60.0, method='euler')
print(f"a=2 N=300 lock_rate={np.mean(res_a2['locked']):.3f}")
results['a2_N300_check'] = {'lock_rate': float(np.mean(res_a2['locked'])),
                            'u_summary': summarize(res_a2['u'])}

with open(os.path.join(outdir, 'kuramoto_prefactor_robustness.json'), 'w') as f:
    json.dump(results, f, indent=2)

# Plot threshold dependence
fig, ax = plt.subplots(figsize=(7, 5))
thrs = [r['R_thr'] for r in rows_thr]
ax.plot(thrs, [r['median'] for r in rows_thr], 'o-', color='C0', label='median u')
ax.fill_between(thrs, [r['min'] for r in rows_thr], [r['max'] for r in rows_thr],
                alpha=0.2, color='C0', label='min-max')
ax.axhline(1.0, color='k', linestyle='--', label='u=1 (law)')
ax.set_xlabel('locking threshold R_thr')
ax.set_ylabel('u = a K0 R0^a t_esc / 2')
ax.set_title('Prefactor u vs locking threshold (a=1, K0=5, κ=1, N=100, K/N)')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'kuramoto_prefactor_threshold.png'), dpi=150)
plt.close(fig)

# Plot dt convergence
fig, ax = plt.subplots(figsize=(7, 5))
for method in ['euler', 'rk4']:
    sub = [r for r in rows_dt if r['method'] == method]
    ax.errorbar([r['dt'] for r in sub], [r['median'] for r in sub],
                yerr=[[r['median']-r['min'] for r in sub],
                      [r['max']-r['median'] for r in sub]],
                fmt='o-', capsize=4, label=method.upper())
ax.axhline(1.0, color='k', linestyle='--', label='u=1')
ax.set_xlabel('dt')
ax.set_ylabel('median u (min-max bars)')
ax.set_title('Integrator/dt convergence (a=1, K0=5, κ=1, N=80, R_thr=0.5)')
ax.set_xscale('log')
ax.legend()
ax.invert_xaxis()
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'kuramoto_prefactor_dt_convergence.png'), dpi=150)
plt.close(fig)

# Plot N dependence
fig, ax = plt.subplots(figsize=(7, 5))
Ns = [r['N'] for r in rows_N]
ax.errorbar(Ns, [r['median'] for r in rows_N],
            yerr=[[r['median']-r['min'] for r in rows_N],
                  [r['max']-r['median'] for r in rows_N]],
            fmt='o-', capsize=4, color='C2')
ax.axhline(1.0, color='k', linestyle='--', label='u=1')
ax.set_xlabel('N')
ax.set_ylabel('median u (min-max bars)')
ax.set_title('Prefactor u vs system size (a=1, K0=5, κ=1, R_thr=0.5, K/N)')
ax.set_xscale('log')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'kuramoto_prefactor_N_dependence.png'), dpi=150)
plt.close(fig)

print("\nArtifacts saved to", outdir)
