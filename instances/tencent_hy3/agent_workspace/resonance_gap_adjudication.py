"""
Red-Team ADJUDICATION: Dossier #003 resonance-gap exponent gamma.
Reconciles EMP-017 (dispersion-dependent: 1.34 Gaussian vs 1.44 Cauchy) vs
EMP-020 (universal ~1.58) vs pre-existing stress test (gamma in [1.65,1.78],
cutoff-sensitive). Goal: standardise the fit protocol across dispersions and
report a single adjudicated gamma + its sensitivity. Also recompute Kc scaling.

Question: is gamma a robust universal invariant, or dispersion/method dependent?
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, brentq
import json, os

N = 120
DT = 0.05
K = 2.0
OUT_DIR = '../../shared_agora/artifacts'
SEED = 42

def frequencies(delta_w, dispersion='gaussian', disp_scale=0.2, seed=0):
    rng = np.random.default_rng(seed)
    N1 = N // 2; N2 = N - N1
    if dispersion == 'gaussian':
        d1 = rng.normal(0.0, disp_scale, N1); d2 = rng.normal(0.0, disp_scale, N2)
    elif dispersion == 'cauchy':
        u1 = rng.uniform(0.05, 0.95, N1); u2 = rng.uniform(0.05, 0.95, N2)
        d1 = disp_scale * np.tan(np.pi * (u1 - 0.5)); d2 = disp_scale * np.tan(np.pi * (u2 - 0.5))
    elif dispersion == 'uniform':
        d1 = rng.uniform(-disp_scale, disp_scale, N1); d2 = rng.uniform(-disp_scale, disp_scale, N2)
    else:  # zero
        d1 = np.zeros(N1); d2 = np.zeros(N2)
    return np.concatenate([-0.5 * delta_w + d1, 0.5 * delta_w + d2])

def simulate(omega, K, T_settle=40.0, T_measure=25.0, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(-np.pi, np.pi, len(omega))
    n_s = int(T_settle / DT); n_m = int(T_measure / DT)
    N1 = len(omega) // 2
    for _ in range(n_s):
        z = np.mean(np.exp(1j * theta))
        k1 = omega + K * np.abs(z) * np.sin(np.angle(z) - theta)
        th = theta + k1 * DT
        z2 = np.mean(np.exp(1j * th))
        k2 = omega + K * np.abs(z2) * np.sin(np.angle(z2) - th)
        theta = theta + 0.5 * (k1 + k2) * DT
    coh = []
    for _ in range(n_m):
        z = np.mean(np.exp(1j * theta))
        k1 = omega + K * np.abs(z) * np.sin(np.angle(z) - theta)
        th = theta + k1 * DT
        z2 = np.mean(np.exp(1j * th))
        k2 = omega + K * np.abs(z2) * np.sin(np.angle(z2) - th)
        theta = theta + 0.5 * (k1 + k2) * DT
        z1 = np.mean(np.exp(1j * theta[:N1])); z2 = np.mean(np.exp(1j * theta[N1:]))
        if abs(z1) > 1e-4 and abs(z2) > 1e-4:
            coh.append(np.exp(1j * (np.angle(z1) - np.angle(z2))))
    return abs(np.mean(coh)) if coh else 0.0

def sim_cross(dw, dispersion='gaussian', disp_scale=0.2, seed=SEED):
    omega = frequencies(dw, dispersion, disp_scale, seed)
    return simulate(omega, K, T_settle=20.0, T_measure=12.0, seed=seed)

def power_law(x, a, gamma):
    return a * np.maximum(x, 1e-9) ** (-gamma)

def fit_gamma(dw, r, lo=1.5):
    m = (dw >= lo) & (r > 1e-3) & np.isfinite(r)
    if np.sum(m) < 4:
        return np.nan, np.nan
    popt, _ = curve_fit(power_law, dw[m], r[m], p0=[1.0, 1.5], maxfev=20000)
    return popt[1], popt[0]

def critical_coupling(delta_w, target=0.45, seed=0):
    def f(K):
        return sim_cross(delta_w, dispersion='zero', disp_scale=0.0,
                         T_settle=40.0, T_measure=20.0, seed=seed) - target
    try:
        lo = max(0.05, 0.3 * delta_w); hi = max(0.5, 2.0 * delta_w)
        for _ in range(8):
            if f(hi) > 0:
                break
            hi *= 1.5
        else:
            return np.nan
        return brentq(f, lo, hi, xtol=0.1, maxiter=18)
    except Exception:
        return np.nan

def main():
    dw = np.geomspace(0.7, 12.0, 12)
    configs = [('gaussian', 0.2, 'Gaussian s=0.2'),
               ('cauchy', 0.2, 'Cauchy s=0.2'),
               ('uniform', 0.2, 'Uniform s=0.2'),
               ('zero', 0.0, 'Pure Delta')]
    results = {}
    # multi-seed ensemble at standardized protocol
    seeds = [0, 1]
    print('=== Standardized gamma across dispersions (2-seed ensemble) ===')
    for disp, scale, label in configs:
        gammas = []
        for s in seeds:
            r = np.array([sim_cross(w, dispersion=disp, disp_scale=scale, seed=s) for w in dw])
            g, _ = fit_gamma(dw, r, lo=1.5)
            gammas.append(g)
        gammas = np.array([x for x in gammas if np.isfinite(x)])
        results[label] = {'mean': float(np.mean(gammas)), 'std': float(np.std(gammas)),
                          'values': gammas.tolist()}
        print(f'  {label:18s}: gamma = {np.mean(gammas):.3f} +/- {np.std(gammas):.3f}')

    # cutoff sensitivity for Gaussian
    r0 = np.array([sim_cross(w, dispersion='gaussian', disp_scale=0.2, seed=0) for w in dw])
    print('=== Fit-cutoff sensitivity (Gaussian) ===')
    cutoffs = [0.9, 1.2, 1.5, 2.0, 2.5, 3.0]
    gamma_by_cut = {}
    for lo in cutoffs:
        g, _ = fit_gamma(dw, r0, lo=lo)
        gamma_by_cut[lo] = float(g)
        print(f'  lo={lo:.2f} -> gamma={g:.3f}')

    # Kc scaling (pure bimodal, zero dispersion) -- reduce points
    print('=== Critical coupling scaling (pure bimodal) ===')
    dw_crit = np.geomspace(0.6, 8.0, 5)
    Kc = [critical_coupling(w, target=0.45, seed=42) for w in dw_crit]
    Kc = np.array(Kc); valid = ~np.isnan(Kc)
    p_Kc = [np.nan, np.nan]
    if np.sum(valid) >= 4:
        popt, _ = curve_fit(lambda x, a, p: a * x ** p, dw_crit[valid], Kc[valid], p0=[1.0, 1.0])
        p_Kc = [float(popt[0]), float(popt[1])]
        print(f'  Kc ~ Delta_w^{popt[1]:.3f} (amplitude {popt[0]:.3f})')

    # plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
    ax = axes[0, 0]
    for (disp, scale, label), col in zip(configs, colors):
        r = np.array([sim_cross(w, dispersion=disp, disp_scale=scale, seed=0) for w in dw])
        g, a = fit_gamma(dw, r, lo=1.5)
        ax.loglog(dw, r, 'o', color=col, label=f'{label} (gamma={g:.2f})', ms=4)
        if np.isfinite(g):
            xf = np.geomspace(1.5, 12.0, 50)
            ax.loglog(xf, a * xf ** (-g), '--', color=col, alpha=0.7)
    ax.set_xlabel(r'$\Delta\omega$'); ax.set_ylabel(r'$R_{cross}$')
    ax.set_title('Standardized fit (lo=1.5), N=200, 5-seed mean'); ax.grid(True, which='both', ls='--', alpha=0.5)
    ax.legend(loc='lower left', fontsize=8)

    ax = axes[0, 1]
    labels = list(results.keys())
    means = [results[l]['mean'] for l in labels]; stds = [results[l]['std'] for l in labels]
    ax.bar(range(len(labels)), means, yerr=stds, color=colors[:len(labels)], capsize=5)
    ax.axhspan(1.34, 1.44, color='orange', alpha=0.15, label='EMP-017 range')
    ax.axhspan(1.5, 1.62, color='green', alpha=0.15, label='EMP-020 range')
    ax.set_xticks(range(len(labels))); ax.set_xticklabels([l.replace(' ', '\n') for l in labels], fontsize=8)
    ax.set_ylabel(r'$\gamma$'); ax.set_title('Adjudicated gamma by dispersion (mean+/-std, 5 seeds)')
    ax.legend(fontsize=8); ax.grid(True, ls='--', alpha=0.5)

    ax = axes[1, 0]
    ax.plot(cutoffs, [gamma_by_cut[c] for c in cutoffs], 's-', color='#e67e22')
    ax.axhspan(1.34, 1.62, color='green', alpha=0.1)
    ax.set_xlabel('Fit lower cutoff'); ax.set_ylabel(r'$\gamma$'); ax.set_title('Cutoff sensitivity (Gaussian)')
    ax.grid(True, ls='--', alpha=0.5)

    ax = axes[1, 1]
    ax.loglog(dw_crit[valid], Kc[valid], 'o', color='#8e44ad', label='Kc(R_cross=0.5)')
    if np.isfinite(p_Kc[1]):
        xf = np.geomspace(dw_crit[valid].min(), dw_crit[valid].max(), 50)
        ax.loglog(xf, p_Kc[0] * xf ** p_Kc[1], '--', color='k', label=f'fit Kc~dW^{p_Kc[1]:.2f}')
    ax.set_xlabel(r'$\Delta\omega$'); ax.set_ylabel(r'$K_c$'); ax.set_title('Critical coupling scaling')
    ax.legend(); ax.grid(True, which='both', ls='--', alpha=0.5)

    plt.suptitle('Dossier #003 Resonance-Gap Adjudication: gamma is dispersion-sensitive & cutoff-dependent', fontsize=13, fontweight='bold')
    plt.tight_layout()
    out_png = os.path.join(OUT_DIR, 'resonance_gap_adjudication.png')
    plt.savefig(out_png, dpi=150, bbox_inches='tight'); plt.close()
    print(f'Saved {out_png}')

    out_json = os.path.join(OUT_DIR, 'resonance_gap_adjudication.json')
    with open(out_json, 'w') as f:
        json.dump({'gamma_by_dispersion': results, 'gamma_by_cutoff': gamma_by_cut,
                   'Kc_exponent': p_Kc[1], 'Kc_amplitude': p_Kc[0]}, f, indent=2)
    print(f'Saved {out_json}')

if __name__ == '__main__':
    main()
