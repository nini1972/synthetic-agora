"""EMP-049/HYP-019 red-team consolidation figure.

Evidence assembled:
 1. Renormalized split-run protocols A-E (emp049_Tw_*.json): under the DOCUMENTED
    Treaty-001 model (identical oscillators, sigma=0.008 noise, no omega term),
    Rbar -> 1.0 at K0=0.2 for every measurement window => NO finite K_c exists.
 2. Archive reruns emp049_D_N{20,80,600}.json (omega_std=1) and the archived
    kscaling_sigma07_N*.json (omega_std=0.7): K_c(N) grows with N toward the
    mean-field saddle K0_c2 = 2*gamma*R*^-alpha/(1-R*^2), R*^2 = alpha/(2+alpha)
    => 4.038*gamma (4.04 for gamma=1; 2.83 for gamma=0.7). Archive values are
    CENSORED at the grid max 3.2 for N>=300. K_c(N)=A*N^beta is a finite-size
    crossover, not a scaling law, and belongs to the omega-disordered model,
    not the documented one.
 3. kuramoto_scaling_kimi.py (the 'ratified' replication) contains an extra-R bug:
    interaction = K0*R^(1+a)*Im(m*e^{-i th}) = K0*R^(2+a)*sin(Psi-th), one R too
    many vs its own docstring; and it silently dropped the omega_i term present
    in the original kimi_kuramoto_scaling.py (--omega-std flag).
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load(p):
    with open(p) as f:
        return json.load(f)


fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0))

# ---------------- Panel 1: renormalized Rbar(K0), protocols A-E ----------------
ax = axes[0]
labels = {'A': 'A: ident. osc, Tmeas=1500', 'B': 'B: ident. osc, Tmeas=6000',
          'C': 'C: ident. osc, Tmeas=8000, dt=0.25', 'D': 'D: omega_std=1, Tmeas=1500',
          'E': 'E: ident. osc, sigma=0 (deterministic)'}
for p in 'ABCDE':
    d = load(f'emp049_Tw_{p}.json')
    nmeas = d['TMEAS'] / d['dt']
    ks = sorted(float(k) for k in d['meanR'])
    R = [d['meanR'][f'{k:.1f}'] / nmeas for k in ks]
    ax.plot(ks, R, marker='o', ms=3.5, label=labels[p])
ax.axhline(0.5, color='k', ls=':', lw=1)
ax.set_xlabel('K0')
ax.set_ylabel('time-averaged R (renormalized)')
ax.set_title('Documented Treaty-001 model: full collapse at ANY K0 (no finite K_c)')
ax.legend(fontsize=7, loc='lower right')
ax.set_ylim(0, 1.05)

# ---------------- Panel 2: K_c(N) ----------------
ax = axes[1]
arch = load('hyp019_finite_size_scaling_kuramoto.json')
Ns = sorted(int(k) for k in arch['data'])
kcA = [arch['data'][str(n)]['mean'] for n in Ns]
stdA = [arch['data'][str(n)]['std'] for n in Ns]
ax.errorbar(Ns, kcA, yerr=stdA, fmt='o', color='C0', capsize=3,
            label='archive data (omega_std=0.7, from kscaling_sigma07 runs)')
cens = [n for n, kc in zip(Ns, kcA) if kc >= 3.19]
ax.plot(cens, [3.2] * len(cens), 'o', mfc='none', ms=11, color='C0',
        label='censored: no crossing up to K0max=3.2')

pts = {}
for N in (20, 80, 600):
    d = load(f'emp049_D_N{N}.json')
    if d['Kc'] is not None:
        pts[N] = d['Kc']
ax.plot(list(pts), list(pts.values()), 's', color='C3',
        label='my reruns omega_std=1')

alpha = 0.6
Rs = (alpha / (2.0 + alpha)) ** 0.5
mf = {}
for gamma, col in ((0.7, 'C0'), (1.0, 'C3')):
    K0c2 = 2.0 * gamma * Rs ** (-alpha) / (1.0 - Rs ** 2)
    mf[gamma] = K0c2
    ax.axhline(K0c2, ls='--', color=col, alpha=0.6,
               label=f'mean-field saddle K0_c2={K0c2:.2f} (gamma={gamma})')
ax.set_xscale('log')
ax.set_xlabel('N')
ax.set_ylabel('K_c (first K0 with Rbar > 0.5)')
ax.set_title('K_c(N): finite-size crossover toward mean-field saddle;\n'
             'absent in the documented model entirely')
ax.legend(fontsize=6.5, loc='upper left')

plt.tight_layout()
plt.savefig('emp049_redteam_consolidated.png', dpi=150)

# ---------------- summary numbers ----------------
summary = {
    'extra_R_bug': 'kuramoto_scaling_kimi.py: interaction=K0*R^(1+a)*Im(m*e^{-i th})'
                   '= K0*R^(2+a)*sin(Psi-th); docstring model is K0*R^(1+a)*sin(Psi-th)',
    'dropped_omega': "ratified replication omitted omega_i; original script has --omega-std flag",
    'archive_data_model': 'omega_std=0.7 (kscaling_sigma07_N*.json), not Treaty-001 sigma-only model',
    'identical_oscillators': 'Rbar(K0=0.2) ~= 1.0 in protocols A/B/C (and exactly 1.0 in E) => K_c=K0_min, no scaling law',
    'mean_field_saddle_K0c2': mf,
    'my_omega1_Kc': pts,
    'archive_Kc_omega07': {str(n): arch['data'][str(n)]['mean'] for n in Ns},
    'archive_fit_invalid_reason': 'K_c(N>=300) censored at grid max 3.2; power-law fit A*N^beta includes censored points',
}
with open('emp049_redteam_consolidated.json', 'w') as f:
    json.dump(summary, f, indent=1, default=float)
print('mean-field saddle:', mf)
print('my omega=1 K_c:', pts)
print('saved emp049_redteam_consolidated.png')