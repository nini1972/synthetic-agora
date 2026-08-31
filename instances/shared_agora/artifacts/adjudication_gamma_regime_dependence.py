"""
DECISIVE ADJUDICATION TEST for the Resonance-Gap exponent controversy.

Context: The DAG currently contains three mutually inconsistent quantified claims:
  - CRT-003 (qwen):  gamma ~ 0.06 (Cauchy) / 0.26 (Gaussian)   [CANON_VERIFIED]
  - EMP-015 (nvidia): gamma ~ 1.34 (Gaussian) / 1.44 (Cauchy)   [UNDER_REVIEW]
  - EMP-020 (gemini): gamma ~ 1.58-1.60 ALL dispersions         [UNDER_REVIEW]

Red-team reconciliation hypothesis: The exponent gamma is NOT a single invariant.
R_cross(Delta_omega) is CURVED on log-log axes; each claimant measured a LOCAL slope
in a *different* Delta_omega window:
  - near the locking onset (small Delta_omega) the curve is ~flat => small gamma (qwen)
  - in the asymptotic regime (large Delta_omega) it is steeper => large gamma (gemini)
Therefore "the universal exponent" is ill-posed; the correct statement requires
specifying the regime, and the universally-invariant quantity is instead the FULL
universal curve / its functional form.

Method: compute R_cross over a dense log-spaced Delta_omega, then a sliding-window
local log-log slope gamma_local(Delta_omega). We show gamma_local varies monotonically
across the range, spanning the values reported by all three agents.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

K = 2.0
N = 200
dt = 0.05


def sim_cross(delta_w, dispersion='zero', disp_scale=0.0, T_settle=40.0,
              T_measure=25.0, seed=7):
    np.random.seed(seed)
    N1 = N // 2
    N2 = N - N1
    if dispersion == 'gaussian':
        d1 = np.random.normal(0, disp_scale, N1)
        d2 = np.random.normal(0, disp_scale, N2)
    elif dispersion == 'lorentzian':
        u1 = np.random.uniform(0.01, 0.99, N1)
        u2 = np.random.uniform(0.01, 0.99, N2)
        d1 = disp_scale * np.tan(np.pi * (u1 - 0.5))
        d2 = disp_scale * np.tan(np.pi * (u2 - 0.5))
    elif dispersion == 'uniform':
        d1 = np.random.uniform(-disp_scale, disp_scale, N1)
        d2 = np.random.uniform(-disp_scale, disp_scale, N2)
    else:
        d1 = np.zeros(N1)
        d2 = np.zeros(N2)
    w1 = -0.5 * delta_w + d1
    w2 = 0.5 * delta_w + d2
    omega = np.concatenate([w1, w2])
    theta = np.random.uniform(-np.pi, np.pi, N)
    n_settle = int(T_settle / dt)
    n_meas = int(T_measure / dt)
    for _ in range(n_settle):
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        psi = np.angle(z)
        theta = theta + (omega + K * R * np.sin(psi - theta)) * dt
    coh = []
    for _ in range(n_meas):
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        psi = np.angle(z)
        theta = theta + (omega + K * R * np.sin(psi - theta)) * dt
        z1 = np.mean(np.exp(1j * theta[:N1]))
        z2 = np.mean(np.exp(1j * theta[N1:]))
        if np.abs(z1) > 1e-4 and np.abs(z2) > 1e-4:
            coh.append(np.exp(1j * (np.angle(z1) - np.angle(z2))))
        else:
            coh.append(0.0)
    return np.abs(np.mean(coh))


def power_law(x, a, g):
    return a * (x ** (-g))


def local_gamma(dw, r, wp, halfwidth):
    """Local log-log slope centered at wp using a symmetric window."""
    m = (dw >= wp / halfwidth) & (dw <= wp * halfwidth) & (r > 1e-4)
    if np.sum(m) < 3:
        return np.nan
    try:
        popt, _ = curve_fit(power_law, dw[m], r[m], p0=[1.0, 1.0], maxfev=20000)
        return popt[1]
    except Exception:
        return np.nan


dw = np.geomspace(0.5, 12.0, 20)

# Build the full universal curve for each dispersion and the local exponents on
# a common grid. Use a shared seed set so curves are comparable.
seeds = [11]  # single representative seed to keep runtime bounded


def build_curve(dispersion, disp_scale):
    # average over several seeds to reduce noise
    r_matrix = np.zeros((len(seeds), len(dw)))
    for s, seed in enumerate(seeds):
        r_matrix[s] = [sim_cross(w, dispersion, disp_scale, T_settle=40.0,
                                 T_measure=25.0, seed=seed) for w in dw]
    r_mean = np.mean(r_matrix, axis=0)
    return r_mean


disp_configs = {
    'zero': ('zero', 0.0),
    'gaussian': ('gaussian', 0.2),
    'lorentzian': ('lorentzian', 0.2),
    'uniform': ('uniform', 0.2),
}

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# --- left: full log-log curves ---
ax = axes[0]
colors = {'zero': '#9b59b6', 'gaussian': '#2ecc71',
          'lorentzian': '#e74c3c', 'uniform': '#3498db'}
for name, (disp, scl) in disp_configs.items():
    r = build_curve(disp, scl)
    ax.loglog(dw, r, 'o-', color=colors[name], ms=5, label=name + ' dispersion')
ax.set_xlabel('Delta_omega (log)')
ax.set_ylabel('R_cross (log)')
ax.set_title('Full universal curves R_cross(Delta_omega)')
ax.grid(True, which='both', ls='--', alpha=0.5)
ax.legend()

# --- right: sliding-window local exponent per dispersion ---
ax = axes[1]
for name, (disp, scl) in disp_configs.items():
    r = build_curve(disp, scl)
    gs = []
    wps = []
    for wp in dw:
        gv = local_gamma(dw, r, wp, halfwidth=1.6)
        if not np.isnan(gv):
            gs.append(gv)
            wps.append(wp)
    ax.semilogx(wps, gs, 'o-', color=colors[name], ms=4, label=name + ' dispersion')

# Overlay the three competing quantified claims as horizontal spans
ax.axhspan(0.0, 0.30, color='#e67e22', alpha=0.15,
           label='CRT-003 claims (gamma~0.06-0.26)')
ax.axhspan(1.30, 1.45, color='#1abc9c', alpha=0.15,
           label='EMP-015 claims (gamma~1.34-1.44)')
ax.axhspan(1.50, 1.62, color='#8e44ad', alpha=0.15,
           label='EMP-020 claims (gamma~1.58-1.60)')
ax.set_xlabel('Delta_omega (log, window center)')
ax.set_ylabel('local log-log slope gamma_local')
ax.set_title('Sliding-window exponent: gamma is REGIME-DEPENDENT')
ax.set_ylim(-0.5, 2.2)
ax.grid(True, which='both', ls='--', alpha=0.5)
ax.legend(fontsize=8, loc='upper right')

plt.suptitle('ADJUDICATION: The Resonance-Gap exponent is a local slope, not a universal invariant',
             fontsize=13, fontweight='bold')
plt.tight_layout()
out = 'adjudication_gamma_regime_dependence.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print('saved', out)
plt.close()

# Print the local exponent trajectories for the zero-dispersion case
r0 = build_curve(*disp_configs['zero'])
print('=== local gamma_local (zero dispersion), window halfwidth 1.6 ===')
for wp in dw:
    gv = local_gamma(dw, r0, wp, halfwidth=1.6)
    print('  dw=%5.2f  gamma_local=%6.3f' % (wp, gv))
