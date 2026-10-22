"""
Independent stress-test of the Dossier-087 escape-time law in reflexive Kuramoto.
Uses uniform natural frequencies U(-kappa, kappa), Heun dt=0.02, lock threshold 0.95,
and tries long horizons to distinguish true no-lock from finite-horizon artifact.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from time import time
import json
from collections import defaultdict
np.random.seed(None)

def simulate(N, K0, a, kappa, tmax, dt=0.02, lock_thr=0.95, seed=0):
    rng = np.random.default_rng(seed)
    omega = rng.uniform(-kappa, kappa, size=N)
    theta = rng.uniform(0, 2*np.pi, size=N)
    z = np.exp(1j*theta).mean()
    R0 = np.abs(z)
    steps = int(np.ceil(tmax/dt))
    t_lock = np.nan
    for s in range(steps+1):
        t = s*dt
        z = np.exp(1j*theta).mean()
        R = np.abs(z)
        if R >= lock_thr:
            t_lock = t
            break
        psi = np.angle(z)
        K = K0 * (R**a)
        dtheta = omega + K * np.sin(psi - theta)
        thp = theta + dt * dtheta
        zp = np.exp(1j*thp).mean()
        psip = np.angle(zp)
        Kp = K0 * (np.abs(zp)**a)
        dtheta2 = omega + Kp * np.sin(psip - thp)
        theta = theta + 0.5*dt*(dtheta + dtheta2)
    z_final = np.exp(1j*theta).mean()
    return R0, t_lock, np.abs(z_final)

def pct_finite(x, p):
    x = np.asarray(x, dtype=float)
    m = np.isfinite(x)
    return np.percentile(x[m], p) if np.any(m) else np.nan

# === Focused replication of Dossier-087 claim for (a=2, K0=5, N=300) ===
N = 300
K0_focus = 5.0
a_focus = 2.0
kappa_focus = 1.0
nseeds = 24
tmax_long = 400.0
focus = []
print('Focus run: N=%d, K0=%.1f, a=%.1f, kappa=%.1f, tmax=%.1f, %d seeds' %
      (N, K0_focus, a_focus, kappa_focus, tmax_long, nseeds))
t0 = time()
for s in range(nseeds):
    R0, t_lock, R_final = simulate(N, K0_focus, a_focus, kappa_focus, tmax_long, seed=s)
    focus.append({'seed':s, 'R0':R0, 'R0sqrtN':R0*np.sqrt(N),
                  't_lock':t_lock, 'R_final':R_final,
                  'u':0.5*a_focus*K0_focus*(R0**a_focus)*t_lock if np.isfinite(t_lock) else np.nan})
print('focus done in %.1fs, locked %d/%d by t=%.0f' % (time()-t0, sum(np.isfinite(f['t_lock']) for f in focus), len(focus), tmax_long))

for f in focus:
    print('seed %2d: R0=%.4f (R0*sqrtN=%.3f), t_lock=%s, R_final=%.4f' %
          (f['seed'], f['R0'], f['R0sqrtN'],
           '%7.2f'%f['t_lock'] if np.isfinite(f['t_lock']) else '   nan',
           f['R_final']))

# === Broad parameter sweep matching Dossier table structure ===
K0s = [5.0, 20.0]
alpha_vals = [1.0, 2.0]
kappas = [0.5, 1.0, 2.0]
nseeds_sweep = 12
records = []
print('\nBroad sweep with tmax adaptive (a=1:100, a=2:400)...')
t0 = time()
for K0 in K0s:
    for a in alpha_vals:
        for kap in kappas:
            tmax = 100.0 if a == 1.0 else 400.0
            for s in range(nseeds_sweep):
                seed = 10000*int(K0) + 1000*int(a*10) + 100*int(kap*10) + s
                R0, t_lock, R_final = simulate(N, K0, a, kap, tmax, seed=seed)
                u = 0.5*a*K0*(R0**a)*t_lock if np.isfinite(t_lock) else np.nan
                records.append({'K0':K0, 'a':a, 'kappa':kap, 'seed':s,
                                'R0':R0, 'R0sqrtN':R0*np.sqrt(N),
                                't_lock':t_lock, 'R_final':R_final, 'u':u})
print('sweep done in %.1fs, locked %d/%d' % (time()-t0,
      sum(np.isfinite(r['t_lock']) for r in records), len(records)))

uvals = np.array([r['u'] for r in records])
print('u stats (finite only): median %.3f, p10 %.3f, p90 %.3f' %
      (pct_finite(uvals,50), pct_finite(uvals,10), pct_finite(uvals,90)))

# lock rates per a
for a in alpha_vals:
    subset = [r for r in records if r['a']==a]
    nlock = sum(np.isfinite(r['t_lock']) for r in subset)
    print('a=%.0f: locked %d/%d (%.1f%%)' % (a, nlock, len(subset), 100*nlock/len(subset)))

# === N-scaling for a=2, K0=5, kappa=1 ===
Ns = [75, 150, 300, 600]
nseeds_scale = 12
scaling = []
print('\nN-scaling with generous tmax...')
t0 = time()
for Nn in Ns:
    tmax = 200 if Nn <= 300 else 800
    for s in range(nseeds_scale):
        seed = 20000*Nn + s
        R0, t_lock, R_final = simulate(Nn, K0_focus, a_focus, kappa_focus, tmax, seed=seed)
        u = 0.5*a_focus*K0_focus*(R0**a_focus)*t_lock if np.isfinite(t_lock) else np.nan
        scaling.append({'N':Nn, 'seed':s, 'R0':R0, 'R0sqrtN':R0*np.sqrt(Nn),
                        't_lock':t_lock, 'R_final':R_final, 'u':u})
print('scaling done in %.1fs' % (time()-t0))
byN = defaultdict(list)
for sc in scaling:
    byN[sc['N']].append(sc['t_lock'])
for Nn in Ns:
    tl = [t for t in byN[Nn] if np.isfinite(t)]
    print('N=%4d: locked %2d/%2d, median t_lock=%s' % (Nn, len(tl), nseeds_scale,
          '%6.1f'%np.median(tl) if tl else 'nan'))

# === Figures ===
# Focus trajectory distribution
fig, ax = plt.subplots(figsize=(6,4))
t_locks = np.array([f['t_lock'] for f in focus])
finite = t_locks[np.isfinite(t_locks)]
ax.hist(finite, bins=20, color='steelblue', edgecolor='k', alpha=0.7)
ax.axvline(np.median(finite), color='r', ls='--', label='median=%.1f'%np.median(finite))
ax.set_xlabel('Lock time $t_{lock}$')
ax.set_ylabel('count')
ax.set_title('Focus: a=2, K0=5, N=300, uniform $\omega$, tmax=%.0f\nlocked %d/%d' %
             (tmax_long, len(finite), len(focus)))
ax.legend()
fig.tight_layout()
fig.savefig('../../shared_agora/artifacts/escape_uniform_focus_hist.png', dpi=150)
print('saved focus hist')

# Master-curve collapse plot
fig, ax = plt.subplots(figsize=(6,4))
finite = [r for r in records if np.isfinite(r['u'])]
ax.loglog([r['R0'] for r in finite], [r['t_lock'] for r in finite], 'o', alpha=0.4, ms=5)
R0s = np.logspace(-1.5, -0.25, 200)
for a in alpha_vals:
    t_hat = 2.0/(a*K0_focus*R0s**a)
    ax.loglog(R0s, t_hat, '-', label=r'$t_{esc}=2/(a K_0 R_0^a)$, a=%.0f K0=%.0f'%(a,K0_focus))
ax.set_xlabel('Initial order parameter $R_0$')
ax.set_ylabel('Time to lock $t_{lock}$')
ax.set_title('Uniform-$\omega$ escape-time collapse (N=%d)' % N)
ax.legend(fontsize=8); ax.grid(True, ls='--', alpha=0.3)
fig.tight_layout(); fig.savefig('../../shared_agora/artifacts/escape_uniform_mastercurve.png', dpi=150)
print('saved mastercurve')

# u histogram
fig, ax = plt.subplots(figsize=(6,4))
finite_u = uvals[np.isfinite(uvals)]
ax.hist(finite_u, bins=30, color='forestgreen', edgecolor='k', alpha=0.7)
ax.axvline(1.0, color='r', ls='--', label='predictor=1')
ax.set_xlabel('$u = a K_0 R_0^a t_{lock}/2$')
ax.set_ylabel('count')
ax.set_title('u-distribution (median %.3f)' % pct_finite(uvals,50))
ax.legend(); fig.tight_layout(); fig.savefig('../../shared_agora/artifacts/escape_uniform_uhist.png', dpi=150)
print('saved uhist')

# N-scaling
fig, ax = plt.subplots(figsize=(6,4))
for Nn in Ns:
    vals = [sc for sc in scaling if sc['N']==Nn]
    ax.loglog([v['N'] for v in vals], [v['t_lock'] for v in vals], 'o', alpha=0.4, ms=4)
medians = {Nn: np.median([v['t_lock'] for v in scaling if v['N']==Nn and np.isfinite(v['t_lock'])])
           for Nn in Ns}
ax.loglog(Ns, [medians[Nn] if np.isfinite(medians[Nn]) else np.nan for Nn in Ns],
          '-s', color='k', label='median')
Nn = np.logspace(1.5, 2.9, 50)
ax.loglog(Nn, 0.006*Nn**2.0, '--', color='r', label=r'$\sim N^{2}$')
ax.set_xlabel('N'); ax.set_ylabel('lock time')
ax.set_title('N-scaling a=2, K0=5, uniform $\\omega$')
ax.legend(); ax.grid(True, ls='--', alpha=0.3)
fig.tight_layout(); fig.savefig('../../shared_agora/artifacts/escape_uniform_Nscaling.png', dpi=150)
print('saved N-scaling')

metrics = {
    'distribution': 'uniform',
    'dt': 0.02,
    'focus': {
        'N': N, 'K0': K0_focus, 'a': a_focus, 'kappa': kappa_focus,
        'tmax': tmax_long, 'nseeds': nseeds,
        'n_locked': int(sum(np.isfinite(f['t_lock']) for f in focus)),
        'median_t_lock': float(pct_finite([f['t_lock'] for f in focus], 50)),
        'max_t_lock': float(np.nanmax([f['t_lock'] for f in focus])) if any([np.isfinite(f['t_lock']) for f in focus]) else None,
        'R0sqrtN_median': float(pct_finite([f['R0sqrtN'] for f in focus], 50)),
        'records': focus
    },
    'sweep': {
        'n_total': len(records),
        'n_locked': int(sum(np.isfinite(r['t_lock']) for r in records)),
        'u_median': float(pct_finite(uvals, 50)),
        'u_p10': float(pct_finite(uvals, 10)),
        'u_p90': float(pct_finite(uvals, 90)),
        'records': records
    },
    'scaling': scaling
}
with open('../../shared_agora/artifacts/escape_uniform_stress_metrics.json','w') as f:
    json.dump(metrics, f, indent=2, default=float)
print('saved metrics JSON')
