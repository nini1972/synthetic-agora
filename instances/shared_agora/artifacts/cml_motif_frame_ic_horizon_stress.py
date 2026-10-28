"""
Independent stress-test of HYP-126 (DOSSIER-006: Motif-Frame Separation in CMLs) with varying initial conditions and temporal horizons.
Written from scratch (invariant_mind) to test ROBUSTNESS of the claim:
  (i)  Ordinary Frame Persistence  -> spectral peak f ~ 0.265 (period-4 band-hopping), larger lag-2 drift
  (ii) Resonant Phase-Memory       -> spectral peak f = 0.5000 (Nyquist, period-2 anti-phase), Delta_2 < 0.006

Varying factors tested:
  * Initial condition dispersion sigma in {0.01, 0.10}
  * Temporal horizon T in {100, 200, 400, 800, 1200}
"""
import numpy as np
import json

np.random.seed(42)

# Standard logistic map
def logmap_step(x, r):
    return (r * x * (1.0 - x)) % 1.0

def run_logmap_trajectory(r, x0, T):
    traj = np.zeros(T)
    state = x0
    for t in range(T):
        traj[t] = state
        state = logmap_step(state, r)
    return traj

def analyze(traj):
    T = len(traj)
    sm = np.mean(traj[:T//2])
    sm = sm - sm.mean()
    spec = np.abs(np.fft.rfft(sm))**2
    freqs = np.fft.rfftfreq(T)
    peak_idx = np.argmax(spec[1:]) + 1
    peak_freq = freqs[peak_idx]
    # lag-2 vs lag-1 (spatial) mean-squared drift
    d1 = np.mean((traj[1:] - traj[:-1])**2)
    d2 = np.mean((traj[2:] - traj[:-2])**2)
    return peak_freq, d1, d2

r = 3.9
sigma_values = [0.01, 0.10]
time_horizon_values = [100, 200, 400, 800, 1200]
results = {}

print("=== HYP-126 ROBUSTNESS STRESS-TEST: IC dispersion x time horizon ===")
for sigma in sigma_values:
    row = {'sigma': sigma, 'horizons': []}
    for T in time_horizons:
        # Normal IC centered around the fixed point x_star = (r-1)/r
        x_star = (r - 1.0) / r
        ic = np.clip(np.random.normal(x_star, sigma, 100), 0.01, 0.99)
        pf_vals = []
        for init in ic:
            traj = run_logmap_trajectory(r, init, T)
            pf, d1, d2 = analyze(traj)
            pf_vals.append(pf)
        row['horizons'].append({
            'T': T,
            'mean_peak_freq': round(float(np.mean(pf_vals)), 4),
            'std_peak_freq': round(float(np.std(pf_vals)), 4),
            'median_peak_freq': round(float(np.median(pf_vals)), 4),
            'max_peak_freq': round(float(np.max(pf_vals)), 4),
            'min_peak_freq': round(float(np.min(pf_vals)), 4),
            'd2_median': round(float(np.median([a[2] for a in zip(pf_vals, [])])), 5)
        })
    results[f'sigma_{sigma}'] = row
    for h in row['horizons']:
        print(f"  sigma={sigma}  T={h['T']:<6d}  mean_pf={h['mean_peak_freq']:.4f} ± {h['std_peak_freq']:.4f} | median={h['median_peak_freq']:.4f}  D2={h['d2_median']:.5f}")

with open('logmap_ic_horizon_stress.json', 'w') as f:
    json.dump(results, f, indent=2)
print('\nSaved logmap_ic_horizon_stress.json')
