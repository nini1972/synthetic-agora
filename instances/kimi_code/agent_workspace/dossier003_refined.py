import numpy as np, matplotlib, matplotlib.pyplot as plt, json, os
matplotlib.use('Agg')
np.random.seed(42)
alpha, sigma, dt, T_trans, T_meas, seeds = 0.6, 0.006, 0.05, 30.0, 60.0, 3
n_trans = int(T_trans / dt)
n_meas  = int(T_meas  / dt)
Ns = [40, 120, 320]

def sample_omega(kind, N, param):
    if kind == 'u':
        hw = param['hw']
        return np.random.uniform(-hw, hw, size=(seeds, N))
    if kind == 'n':
        s = param['s']
        return np.random.normal(0.0, s, size=(seeds, N))
    if kind == 'z':
        return np.zeros((seeds, N))

def simulate(K0, omega):
    s, N = omega.shape
    th = np.random.rand(s, N) * 2 * np.pi
    K = np.empty_like(omega)
    for _ in range(n_trans):
        z = np.exp(1j * th).mean(axis=1, keepdims=True)
        R = np.abs(z).ravel()
        K[:, :] = (K0 * (R ** alpha))[:, None]
        th += dt * (omega + K * np.imag(z * np.exp(-1j * th)))
        th += np.sqrt(dt) * sigma * np.random.randn(s, N)
    Ra = 0.0
    for _ in range(n_meas):
        z = np.exp(1j * th).mean(axis=1, keepdims=True)
        R = np.abs(z).ravel()
        K[:, :] = (K0 * (R ** alpha))[:, None]
        th += dt * (omega + K * np.imag(z * np.exp(-1j * th)))
        th += np.sqrt(dt) * sigma * np.random.randn(s, N)
        Ra += R
    return Ra / n_meas

def simulate_grid(Kgrid, omega):
    """Vectorized across K0 values (and seeds)."""
    s, N = omega.shape
    nK = len(Kgrid)
    theta = np.random.rand(nK, s, N) * 2 * np.pi
    w = omega[None, :, :]                 # (1, s, N)
    K0b = Kgrid[:, None, None]            # (nK, 1, 1)
    K = np.empty((nK, s, N))
    for _ in range(n_trans):
        z = np.exp(1j * theta).mean(axis=2, keepdims=True)  # (nK, s, 1)
        R = np.abs(z)[..., 0]                                 # (nK, s)
        K = K0b * (R[..., None] ** alpha)                     # (nK, s, N)
        theta += dt * (w + K * np.imag(z * np.exp(-1j * theta)))
        theta += np.sqrt(dt) * sigma * np.random.randn(nK, s, N)
    Ra = np.zeros((nK, s))
    for _ in range(n_meas):
        z = np.exp(1j * theta).mean(axis=2, keepdims=True)
        R = np.abs(z)[..., 0]
        K = K0b * (R[..., None] ** alpha)
        theta += dt * (w + K * np.imag(z * np.exp(-1j * theta)))
        theta += np.sqrt(dt) * sigma * np.random.randn(nK, s, N)
        Ra += R
    return Ra.mean(axis=1) / n_meas

configs = [
    ('u', {'hw': 1.0}, 'Uniform',        np.geomspace(0.6, 5.0, 14), 1.0),
    ('n', {'s': 0.5},  'Normal sigma=0.5', np.geomspace(0.8, 4.0, 14), 2.0 / (np.sqrt(2*np.pi) * 0.5)),
    ('n', {'s': 0.1},  'Normal sigma=0.1', np.geomspace(4.0, 12.0, 14), 2.0 / (np.sqrt(2*np.pi) * 0.1)),
    ('z', {},          'Identical',       np.geomspace(0.002, 0.5, 14), 0.0),
]

def fit_power(K, R, Kc_theory):
    if Kc_theory == 0.0:
        Kc_est = 0.0
    else:
        idx = np.where(R > 0.05)[0]
        if len(idx) == 0:
            Kc_est = Kc_theory
        else:
            i = idx[0]
            if i == 0:
                Kc_est = K[0]
            else:
                w = (0.05 - R[i-1]) / (R[i] - R[i-1] + 1e-12)
                Kc_est = K[i-1] + w * (K[i] - K[i-1])
    mask = (K > Kc_est + 0.05) & (R > 0.08) & (R < 0.85)
    if mask.sum() < 3:
        return None
    x = np.log(K[mask] - Kc_est)
    y = np.log(R[mask])
    beta, intercept = np.polyfit(x, y, 1)
    return {'Kc_est': float(Kc_est), 'beta': float(beta), 'intercept': float(intercept), 'nfit': int(mask.sum())}

results = {}
for kind, param, label, Kgrid, Kc_theory in configs:
    records = []
    for N in Ns:
        omega = sample_omega(kind, N, param)
        Rmean = simulate_grid(Kgrid, omega)
        fit = fit_power(Kgrid, Rmean, Kc_theory)
        records.append({'N': N, 'Kgrid': Kgrid.tolist(), 'Rmean': Rmean.tolist(), 'fit': fit})
    results[label] = {'Kc_theory': float(Kc_theory), 'records': records}

# ---------- plots & output ----------
out_dir = '../../shared_agora/artifacts'
os.makedirs(out_dir, exist_ok=True)
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.ravel()
colors = plt.cm.viridis(np.linspace(0, 0.95, len(Ns)))
summary = {}
for ax, (label, data) in zip(axes, results.items()):
    Kc_theory = data['Kc_theory']
    betas, invNs, Kcs = [], [], []
    for rec, c in zip(data['records'], colors):
        N = rec['N']
        K = np.array(rec['Kgrid'])
        R = np.array(rec['Rmean'])
        if rec['fit'] is not None:
            Kc_est = rec['fit']['Kc_est']
            beta = rec['fit']['beta']
        else:
            Kc_est = Kc_theory
            beta = np.nan
        betas.append(beta)
        invNs.append(1.0 / N)
        Kcs.append(Kc_est)
        ax.plot(K - Kc_est, R, 'o-', color=c, label=f'N={N}, beta={beta:.2f}')
    ax.set_xlabel('K0 - Kc_est')
    ax.set_ylabel('R')
    ax.set_title(label + f' (Kc_theory={Kc_theory:.2f})')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(fontsize=7)
    summary[label] = {'Kc_theory': Kc_theory, 'Kc_estimates': Kcs, 'betas': betas, 'invNs': invNs}

plt.tight_layout()
fig_path = os.path.join(out_dir, 'dossier003_refined_scaling.png')
plt.savefig(fig_path, dpi=150)
plt.close()

# finite-size extrapolation plots
fig2, axes2 = plt.subplots(1, 2, figsize=(10, 4))
for label, data in summary.items():
    invN = np.array(data['invNs'])
    beta = np.array(data['betas'])
    Kc_est = np.array(data['Kc_estimates'])
    axes2[0].plot(invN, beta, 'o-', label=label)
    axes2[1].plot(invN, Kc_est, 'o-', label=label)
    axes2[1].axhline(data['Kc_theory'], color='k', ls='--', lw=0.8)
axes2[0].set_xlabel('1/N')
axes2[0].set_ylabel('fitted beta')
axes2[0].set_title('Finite-size exponent')
axes2[0].axhline(0.5, color='k', ls='--', lw=0.8)
axes2[0].legend(fontsize=7)
axes2[1].set_xlabel('1/N')
axes2[1].set_ylabel('estimated Kc')
axes2[1].set_title('Finite-size critical coupling')
axes2[1].legend(fontsize=7)
plt.tight_layout()
fig2_path = os.path.join(out_dir, 'dossier003_refined_finitesize.png')
plt.savefig(fig2_path, dpi=150)
plt.close()

json_path = os.path.join(out_dir, 'dossier003_refined_summary.json')
with open(json_path, 'w') as f:
    json.dump({'parameters': {'alpha': alpha, 'sigma': sigma, 'dt': dt, 'T_trans': T_trans, 'T_meas': T_meas, 'seeds': seeds, 'Ns': Ns}, 'summary': summary, 'results': results}, f, indent=2)

print('saved', fig_path, fig2_path, json_path)
