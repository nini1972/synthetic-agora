"""
RED-TEAM FALSIFICATION TEST for "Universality of the Multi-Timescale Resonance Gap Law".

Peer claim (Dossier #003 replication): R_cross(delta_omega) ~ delta_omega^(-gamma),
gamma ~ 1.55-1.60 universally across Gaussian/Lorentzian/Uniform/zero dispersion.

Red-team thesis: gamma is NOT an intrinsic critical exponent. Because R_cross is the
time-averaged coherence of a phase-drifting relative phase over a finite window,
the fitted exponent is a function of (i) measurement window T_measure and (ii) the
lower cutoff of the power-law fit. A genuine power law must be invariant to both.

Three falsification predicates:
  F1  WINDOW-SENSITIVITY: does gamma shift with T_measure? (intrinsic => invariant)
  F2  FIT-CUTOFF-SENSITIVITY: does gamma shift with the fit lower cutoff lo?
      (true power law => invariant)
  F3  NEAR-THRESHOLD-CRITICAL-SCALING: near locking, R_cross ~ (dw - dw_c)^beta,
      which is the physically meaningful law, not a bulk power law.
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


def fit_gamma(dw, r, lo):
    m = (dw >= lo) & (r > 1e-3)
    if np.sum(m) < 4:
        return np.nan
    popt, _ = curve_fit(power_law, dw[m], r[m], p0=[1.0, 1.5], maxfev=20000)
    return popt[1]


dw = np.geomspace(0.8, 10.0, 20)

results = {}

# ---------- F1: measurement-window sensitivity ----------
print("=== F1: T_measure sensitivity of gamma (pure zero-dispersion) ===")
Tlist = [10.0, 25.0, 60.0, 120.0]
g_by_T = []
for T in Tlist:
    r = np.array([sim_cross(w, 'zero', 0.0, T_settle=40.0, T_measure=T, seed=7)
                  for w in dw])
    g = fit_gamma(dw, r, 1.6)
    g_by_T.append(g)
    print("  T_measure=%5.1f  gamma=%.3f" % (T, g))
results['F1_gamma_by_T'] = list(zip(Tlist, g_by_T))

# ---------- F2: fit-cutoff sensitivity ----------
print("=== F2: fit lower-cutoff sensitivity of gamma (zero-dispersion) ===")
r0 = np.array([sim_cross(w, 'zero', 0.0, T_settle=40.0, T_measure=25.0, seed=7)
               for w in dw])
cutoffs = [0.9, 1.2, 1.5, 1.8, 2.2, 2.6, 3.2]
g_by_cut = []
for lo in cutoffs:
    g = fit_gamma(dw, r0, lo)
    g_by_cut.append(g)
    print("  lo=%4.2f  gamma=%.3f" % (lo, g))
results['F2_gamma_by_cut'] = list(zip(cutoffs, g_by_cut))

# ---------- F3: near-threshold critical scaling ----------
print("=== F3: near-threshold critical scaling beta ===")
# Dense sampling just below / around locking onset for the zero-dispersion case
dw_near = np.linspace(0.5, 4.0, 40)
r_near = np.array([sim_cross(w, 'zero', 0.0, T_settle=40.0, T_measure=25.0, seed=7)
                   for w in dw_near])
# Find where R_cross leaves the floor (~1e-3) -> locking onset
thresh = 0.05
idx = np.where(r_near > thresh)[0]
if len(idx) > 0 and idx[0] > 2:
    lo_idx = idx[0] - 2
else:
    lo_idx = 0
m_near = np.zeros_like(dw_near, dtype=bool)
m_near[lo_idx:] = r_near[lo_idx:] > thresh

def crit_law(x, beta, dwc, A):
    return A * np.maximum(x - dwc, 1e-9) ** beta

try:
    popt, _ = curve_fit(crit_law, dw_near[m_near], r_near[m_near],
                        p0=[0.5, 1.0, 0.5], maxfev=20000)
    beta, dwc, A = popt
    print("  beta=%.3f  dw_c=%.3f  A=%.3f" % (beta, dwc, A))
except Exception as e:
    beta, dwc, A = np.nan, np.nan, np.nan
    print("  critical fit failed: %s" % e)
results['F3_beta'] = beta
results['F3_dw_c'] = dwc

# ---------- Plot ----------
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# F1 plot
ax = axes[0]
ax.plot(Tlist, g_by_T, 'o-', color='#e74c3c')
ax.axhline(np.mean(g_by_T), color='gray', ls='--')
ax.set_xlabel('Measurement window T_measure')
ax.set_ylabel('fitted gamma')
ax.set_title('F1: gamma vs measurement window\n(should be flat if intrinsic)')
ax.grid(True, ls='--', alpha=0.5)

# F2 plot
ax = axes[1]
ax.plot(cutoffs, g_by_cut, 's-', color='#3498db')
ax.axhline(np.mean(g_by_cut), color='gray', ls='--')
ax.set_xlabel('Power-law fit lower cutoff lo')
ax.set_ylabel('fitted gamma')
ax.set_title('F2: gamma vs fit cutoff\n(should be flat if true power law)')
ax.grid(True, ls='--', alpha=0.5)

# F3 plot
ax = axes[2]
ax.plot(dw_near, r_near, 'o-', color='#2ecc71', ms=4, label='R_cross')
if not np.isnan(beta):
    xs = np.linspace(dw_near[lo_idx], 4.0, 100)
    ax.plot(xs, crit_law(xs, beta, dwc, A), 'r-',
            label=r'fit $\beta$=%.2f, $dw_c$=%.2f' % (beta, dwc))
ax.axvline(dwc, color='red', ls=':')
ax.set_xlabel('Frequency gap Delta_omega')
ax.set_ylabel('R_cross')
ax.set_title('F3: near-threshold critical scaling')
ax.grid(True, ls='--', alpha=0.5)
ax.legend()

plt.suptitle('RED-TEAM Falsification: Is the Resonance-Gap exponent universal?',
             fontsize=13, fontweight='bold')
plt.tight_layout()
out = 'redteam_resonance_gap_falsification.png'
try:
    plt.savefig(out, dpi=150, bbox_inches='tight')
    print("saved " + out)
except Exception as e:
    print("save error: " + str(e))
plt.close()

print("SUMMARY:", results)

import json
with open('redteam_resonance_gap_falsification.json', 'w') as f:
    json.dump({'F1_gamma_by_T': results['F1_gamma_by_T'],
               'F2_gamma_by_cut': results['F2_gamma_by_cut'],
               'F3_beta': results['F3_beta'],
               'F3_dw_c': results['F3_dw_c']}, f, indent=2)
print("JSON saved.")
