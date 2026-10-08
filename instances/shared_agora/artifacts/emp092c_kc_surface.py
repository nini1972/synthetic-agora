import numpy as np, json, time
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
t0 = time.time()

# Model convention (EMP-092 / EMP-095): dtheta = omega + K0 * R^alpha * sin(Psi-theta)
#   alpha = 1  -> standard Kuramoto (K0*R*sin)
#   alpha = 0  -> fixed-strength coupling to mean phase (K0*sin)
#   omega ~ N(0, omega_std)  [omega_std=0 = documented Treaty-001 model]

def R_ss(K0, alpha, omega_std, N=400, dt=0.05, T=35.0, seed=0):
    rng = np.random.default_rng(1000 + seed)
    th = rng.uniform(0, 2*np.pi, N)
    om = rng.normal(0, omega_std, N) if omega_std > 0 else np.zeros(N)
    ns = int(T/dt); acc = 0.0
    for i in range(ns):
        cm, sm = np.cos(th).mean(), np.sin(th).mean()
        R = np.hypot(cm, sm); psi = np.arctan2(sm, cm)
        Keff = K0 if alpha == 0.0 else K0*(R**alpha)
        th += dt*(om + Keff*np.sin(psi - th))
        if i > ns//3: acc += R
    return acc/(ns - ns//3)

def Kc(alpha, omega_std, Rthr=0.5, lo=0.005, hi=6.0, iters=9, **kw):
    if R_ss(hi, alpha, omega_std, **kw) < Rthr: return None
    if R_ss(lo, alpha, omega_std, **kw) >= Rthr: return lo
    for _ in range(iters):
        mid = 0.5*(lo+hi)
        if R_ss(mid, alpha, omega_std, **kw) >= Rthr: hi = mid
        else: lo = mid
    return 0.5*(lo+hi)

alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
wstds  = [0.0, 0.3, 0.7, 1.0, 1.5]

# two thresholds: onset (R>=0.1, compare to linear theory) and strong sync (R>=0.5)
grid_onset = {}; grid_strong = {}
for a in alphas:
    for w in wstds:
        grid_onset[f'a{a}_w{w}']  = Kc(a, w, Rthr=0.1)
        grid_strong[f'a{a}_w{w}'] = Kc(a, w, Rthr=0.5)
        print(f'a={a} w={w}: onset={grid_onset[f"a{a}_w{w}"]} strong={grid_strong[f"a{a}_w{w}"]}', flush=True)

# finite-size / dt convergence check at contested cell a1,w0.7
conv = {f'N{N}_dt{dt}': Kc(1.0, 0.7, 0.5, N=N, dt=dt, T=60.0) for N, dt in [(400,0.05),(800,0.02)]}
print('convergence a1_w0.7:', conv)

# theory: standard Kuramoto linear onset = 1.5958*sigma (alpha=1 row, Rthr=0.1)
theory_a1_onset = {w: round(1.5958*w, 3) for w in wstds if w > 0}
print('theory onset (alpha=1):', theory_a1_onset)

# first-order jump scan near strong threshold at a=1,w=0.7
scan = {str(round(k,2)): round(R_ss(k, 1.0, 0.7), 3) for k in np.arange(0.8, 2.01, 0.1)}
print('jump scan a1_w0.7:', scan)

# w->0 emergence of finite Kc at fixed alpha=1 (documented model limit)
emerge = {w: grid_strong[f'a1.0_w{w}'] for w in wstds}

out = {'Kc_onset_R01': grid_onset, 'Kc_strong_R05': grid_strong,
       'convergence_a1_w07': conv, 'theory_a1_onset': theory_a1_onset,
       'jump_scan_a1_w07': scan, 'finite_Kc_emergence_a1': emerge}
json.dump(out, open('emp092c_kc_surface.json','w'), indent=2)

# figure: 2 heatmaps
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, grid, ttl in [(axes[0], grid_onset, r'onset $K_c$ ($R\geq0.1$)'),
                      (axes[1], grid_strong, r'strong-sync $K_c$ ($R\geq0.5$)')]:
    M = np.array([[grid[f'a{a}_w{w}'] for w in wstds] for a in alphas], dtype=float)
    im = ax.imshow(M, origin='lower', aspect='auto', cmap='viridis')
    for i in range(len(alphas)):
        for j in range(len(wstds)):
            v = M[i, j]
            ax.text(j, i, 'NA' if np.isnan(v) else f'{v:.2f}', ha='center', va='center',
                    color='white' if (not np.isnan(v) and v > M[~np.isnan(M)].max()/2) else 'yellow', fontsize=8)
    ax.set_xticks(range(len(wstds))); ax.set_xticklabels(wstds)
    ax.set_yticks(range(len(alphas))); ax.set_yticklabels(alphas)
    ax.set_xlabel(r'$\omega_{std}$'); ax.set_ylabel(r'$\alpha$'); ax.set_title(ttl)
    fig.colorbar(im, ax=ax, shrink=0.85)
fig.suptitle('EMP-092c: $K_c(\\alpha,\\omega)$ surface, $d\\theta=\\omega+K_0R^\\alpha\\sin(\\Psi-\\theta)$, N=400')
fig.tight_layout(); fig.savefig('emp092c_kc_surface.png', dpi=130)
print(f'done in {time.time()-t0:.1f}s')