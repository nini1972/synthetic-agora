import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, brentq
import json, os

N = 100
DT = 0.03
OUT_DIR = '../../shared_agora/artifacts'

def frequencies(delta_w, dispersion='gaussian', disp_scale=0.2, seed=0):
    rng = np.random.default_rng(seed)
    N1 = N // 2
    N2 = N - N1
    if dispersion == 'gaussian':
        d1 = rng.normal(0.0, disp_scale, N1)
        d2 = rng.normal(0.0, disp_scale, N2)
    elif dispersion == 'cauchy':
        u1 = rng.uniform(0.05, 0.95, N1)
        u2 = rng.uniform(0.05, 0.95, N2)
        d1 = disp_scale * np.tan(np.pi * (u1 - 0.5))
        d2 = disp_scale * np.tan(np.pi * (u2 - 0.5))
    elif dispersion == 'uniform':
        d1 = rng.uniform(-disp_scale, disp_scale, N1)
        d2 = rng.uniform(-disp_scale, disp_scale, N2)
    else:
        d1 = np.zeros(N1)
        d2 = np.zeros(N2)
    return np.concatenate([-0.5 * delta_w + d1, 0.5 * delta_w + d2])

def simulate(omega, K, T_settle=30.0, T_measure=15.0, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(-np.pi, np.pi, len(omega))
    n_settle = int(T_settle / DT)
    n_meas = int(T_measure / DT)
    N1 = len(omega) // 2
    for _ in range(n_settle):
        z = np.mean(np.exp(1j * theta))
        k1 = omega + K * np.abs(z) * np.sin(np.angle(z) - theta)
        th_tmp = theta + k1 * DT
        z2 = np.mean(np.exp(1j * th_tmp))
        k2 = omega + K * np.abs(z2) * np.sin(np.angle(z2) - th_tmp)
        theta = theta + 0.5 * (k1 + k2) * DT
    cross_coh = []
    for _ in range(n_meas):
        z = np.mean(np.exp(1j * theta))
        k1 = omega + K * np.abs(z) * np.sin(np.angle(z) - theta)
        th_tmp = theta + k1 * DT
        z2 = np.mean(np.exp(1j * th_tmp))
        k2 = omega + K * np.abs(z2) * np.sin(np.angle(z2) - th_tmp)
        theta = theta + 0.5 * (k1 + k2) * DT
        z1 = np.mean(np.exp(1j * theta[:N1]))
        z2 = np.mean(np.exp(1j * theta[N1:]))
        if abs(z1) > 1e-4 and abs(z2) > 1e-4:
            cross_coh.append(np.exp(1j * (np.angle(z1) - np.angle(z2))))
    return abs(np.mean(cross_coh)) if cross_coh else 0.0

def sim_cross(delta_w, K=2.0, dispersion='gaussian', disp_scale=0.2,
              T_settle=30.0, T_measure=15.0, seed=0):
    omega = frequencies(delta_w, dispersion, disp_scale, seed)
    return simulate(omega, K, T_settle, T_measure, seed)

def power_law(x, a, gamma):
    return a * np.maximum(x, 1e-9) ** (-gamma)

def fit_gamma(dw, r, lo=1.5):
    m = (dw >= lo) & (r > 1e-3) & np.isfinite(r)
    if np.sum(m) < 4:
        return np.nan, np.nan
    popt, _ = curve_fit(power_law, dw[m], r[m], p0=[1.0, 1.4], maxfev=20000)
    return popt[1], popt[0]

def critical_coupling(delta_w, target=0.5, seed=0):
    def f(K):
        return sim_cross(delta_w, K=K, dispersion='zero', disp_scale=0.0,
                         T_settle=40.0, T_measure=20.0, seed=seed) - target
    try:
        lo = max(0.05, 0.3 * delta_w)
        hi = max(0.5, 2.0 * delta_w)
        for _ in range(12):
            if f(hi) > 0:
                break
            hi *= 1.5
        else:
            return np.nan
        return brentq(f, lo, hi, xtol=0.05, maxiter=20)
    except Exception:
        return np.nan

def main():
    dw = np.geomspace(0.7, 12.0, 16)
    print('Fixed K=2.0 distribution comparison...')
    configs = [
        ('gaussian', 0.2, 'Gaussian s=0.2'),
        ('cauchy', 0.2, 'Cauchy s=0.2'),
        ('gaussian', 0.4, 'Gaussian s=0.4'),
        ('cauchy', 0.4, 'Cauchy s=0.4'),
    ]
    fixed_results = {}
    for disp, scale, label in configs:
        r = np.array([sim_cross(w, K=2.0, dispersion=disp, disp_scale=scale,
                                T_settle=30.0, T_measure=15.0, seed=42)
                      for w in dw])
        g, a = fit_gamma(dw, r, lo=1.5)
        fixed_results[label] = {'dw': dw.tolist(), 'r': r.tolist(),
                                'gamma': float(g), 'amplitude': float(a)}
        print(f'  {label}: gamma = {g:.3f}')

    print('Measurement-window sensitivity...')
    T_measures = [10.0, 25.0, 60.0, 120.0]
    gamma_by_T = {}
    r_by_T = {}
    for T in T_measures:
        r = np.array([sim_cross(w, K=2.0, dispersion='gaussian', disp_scale=0.2,
                                T_settle=30.0, T_measure=T, seed=42)
                      for w in dw])
        g, _ = fit_gamma(dw, r, lo=1.5)
        gamma_by_T[T] = float(g)
        r_by_T[T] = r.tolist()
        print(f'  T_meas={T:6.1f} -> gamma={g:.3f}')

    print('Fit-cutoff sensitivity...')
    r0 = np.array([sim_cross(w, K=2.0, dispersion='gaussian', disp_scale=0.2,
                             T_settle=30.0, T_measure=15.0, seed=42)
                   for w in dw])
    cutoffs = [0.9, 1.3, 1.7, 2.2, 2.8, 3.5]
    gamma_by_cut = {}
    for lo in cutoffs:
        g, _ = fit_gamma(dw, r0, lo=lo)
        gamma_by_cut[lo] = float(g)
        print(f'  lo={lo:.2f} -> gamma={g:.3f}')

    print('Critical coupling scaling (zero dispersion)...')
    dw_crit = np.geomspace(0.6, 8.0, 12)
    Kc = []
    for w in dw_crit:
        kc = critical_coupling(w, target=0.5, seed=42)
        Kc.append(kc)
        print(f'  Delta_w={w:.3f} -> Kc={kc:.3f}')
    Kc = np.array(Kc)
    valid = ~np.isnan(Kc)
    p_Kc = [np.nan, np.nan]
    if np.sum(valid) >= 4:
        popt, _ = curve_fit(lambda x, a, p: a * x ** p,
                            dw_crit[valid], Kc[valid], p0=[1.0, 1.0])
        p_Kc = [float(popt[0]), float(popt[1])]
        print(f'  Kc ~ Delta_w^{popt[1]:.3f}')

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']

    ax = axes[0, 0]
    for (disp, scale, label), col in zip(configs, colors):
        r = np.array(fixed_results[label]['r'])
        g = fixed_results[label]['gamma']
        ax.loglog(dw, r, 'o', color=col, label=f'{label} (gamma={g:.2f})', ms=4)
        if not np.isnan(g):
            xfit = np.geomspace(1.5, 12.0, 50)
            ax.loglog(xfit, fixed_results[label]['amplitude'] * xfit ** (-g),
                      '--', color=col, alpha=0.7)
    ax.set_xlabel(r'Delta omega')
    ax.set_ylabel(r'R_cross')
    ax.set_title('Fixed K=2.0: distribution topology dependence')
    ax.grid(True, which='both', ls='--', alpha=0.5)
    ax.legend(loc='lower left', fontsize=8)

    ax = axes[0, 1]
    cmap = plt.cm.viridis(np.linspace(0, 1, len(T_measures)))
    for T, col in zip(T_measures, cmap):
        r = np.array(r_by_T[T])
        ax.loglog(dw, r, 'o-', color=col, label=f'T={T:.0f}, gamma={gamma_by_T[T]:.2f}')
    ax.set_xlabel(r'Delta omega')
    ax.set_ylabel(r'R_cross')
    ax.set_title('Measurement-window sensitivity (Gaussian s=0.2)')
    ax.grid(True, which='both', ls='--', alpha=0.5)
    ax.legend(loc='lower left', fontsize=8)

    ax = axes[1, 0]
    ax.plot(cutoffs, [gamma_by_cut[c] for c in cutoffs], 's-', color='#e67e22')
    ax.set_xlabel('Power-law fit lower cutoff')
    ax.set_ylabel('Fitted gamma')
    ax.set_title('Fit-cutoff sensitivity')
    ax.grid(True, ls='--', alpha=0.5)

    ax = axes[1, 1]
    ax.loglog(dw_crit[valid], Kc[valid], 'o', color='#8e44ad',
              label='K_c(R_cross=0.5)')
    if not np.isnan(p_Kc[1]):
        xfit = np.geomspace(dw_crit[valid].min(), dw_crit[valid].max(), 50)
        ax.loglog(xfit, p_Kc[0] * xfit ** p_Kc[1], '--', color='k',
                  label=f'fit Kc ~ Delta omega^{p_Kc[1]:.2f}')
    ax.set_xlabel(r'Delta omega')
    ax.set_ylabel(r'K_c')
    ax.set_title('Critical coupling scaling (pure bimodal)')
    ax.grid(True, which='both', ls='--', alpha=0.5)
    ax.legend()

    plt.suptitle('Dossier #003 Red-Team Stress Test', fontsize=14, fontweight='bold')
    plt.tight_layout()
    out_png = os.path.join(OUT_DIR, 'dossier_003_redteam_stress_test.png')
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved {out_png}')

    out_json = os.path.join(OUT_DIR, 'dossier_003_redteam_stress_test.json')
    with open(out_json, 'w') as f:
        json.dump({'fixed_K_results': fixed_results,
                   'gamma_by_T': gamma_by_T,
                   'gamma_by_cutoff': gamma_by_cut,
                   'critical_coupling': {'dw': dw_crit.tolist(),
                                         'Kc': Kc.tolist(),
                                         'exponent': p_Kc[1],
                                         'amplitude': p_Kc[0]}}, f, indent=2)
    print(f'Saved {out_json}')

if __name__ == '__main__':
    main()
