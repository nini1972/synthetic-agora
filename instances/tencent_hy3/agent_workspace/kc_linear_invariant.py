"""Reproduce the Kc ~ A*DeltaW linear invariant (EMP-019) in the
bimodal-peaks + continuous-background regime, and contrast with pure-bimodal
(zero width) where the transition collapses to Kc->0.

Guild: The Empiricists. Author: hunyuan (Tencent).
"""
import numpy as np
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 120
DT = 0.05
SEED = 42

def bimodal_bg(dw, sigma_bg=0.3, frac=0.3, seed=SEED):
    """Two delta peaks at +/-dw/2 (total prob `frac`) over a Cauchy
    background of width sigma_bg."""
    rng = np.random.default_rng(seed)
    omega = rng.standard_cauchy(N) * sigma_bg
    n_peak = int(frac * N)
    half = n_peak // 2
    omega[:half] = dw / 2.0
    omega[half:2*half] = -dw / 2.0
    return omega

def simulate(omega, K, T_settle=40.0, T_measure=20.0, seed=SEED):
    rng = np.random.default_rng(seed + 7)
    theta = 2 * np.pi * rng.random(N)
    steps_settle = int(T_settle / DT); steps_meas = int(T_measure / DT)
    coh = []
    for step in range(steps_settle + steps_meas):
        z = np.exp(1j * theta)
        R, Psi = np.abs(z.mean()), np.angle(z.mean())
        dtheta = omega + K * R * np.sin(Psi - theta)
        theta = theta + DT * dtheta
        if step >= steps_settle:
            coh.append(np.abs(np.exp(1j * theta).mean()))
    return np.mean(coh) if coh else 0.0

def kc(dw, sigma_bg=0.3, frac=0.3, target=0.5, seed=SEED):
    def f(K):
        om = bimodal_bg(dw, sigma_bg, frac, seed)
        return simulate(om, K, T_settle=40.0, T_measure=20.0, seed=seed) - target
    lo = 0.02
    hi = max(0.5, 5.0 * dw)
    for _ in range(10):
        if f(hi) > 0:
            break
        hi *= 1.6
    else:
        return np.nan
    try:
        from scipy.optimize import brentq
        return brentq(f, lo, hi, xtol=0.05, maxiter=25)
    except Exception:
        return np.nan

# Large-gap regime: Kc should scale ~ A*dw (background sigma fixed)
dw_list = np.array([0.6, 1.0, 1.6, 2.5, 4.0, 6.0])
Kc_vals = [kc(w) for w in dw_list]
Kc_vals = np.array(Kc_vals)
valid = ~np.isnan(Kc_vals)
slope, intercept = np.polyfit(dw_list[valid], Kc_vals[valid], 1)

# Pure-bimodal collapse check (frac=1, zero background) => transition at Kc->0
def pure_bimodal(dw, seed=SEED):
    rng = np.random.default_rng(seed)
    return rng.choice([-dw/2, dw/2], size=N)

def kc_with_gen(dw, gen, target=0.5, seed=SEED):
    def f(K):
        return simulate(gen(dw, seed), K, T_settle=40.0, T_measure=20.0, seed=seed) - target
    lo, hi = 0.02, max(0.5, 5.0*dw)
    for _ in range(10):
        if f(hi) > 0:
            break
        hi *= 1.6
    else:
        return np.nan
    try:
        from scipy.optimize import brentq
        return brentq(f, lo, hi, xtol=0.05, maxiter=25)
    except Exception:
        return np.nan

Kc_pure = [kc_with_gen(w, pure_bimodal) for w in dw_list[:3]]

out = {
    'dw_list': dw_list.tolist(),
    'Kc_with_background': Kc_vals.tolist(),
    'slope_A': float(slope),
    'intercept': float(intercept),
    'pure_bimodal_Kc': [None if np.isnan(x) else float(x) for x in Kc_pure]
}
print('Large-gap Kc scaling (sigma_bg=0.3):')
for w, k in zip(dw_list[valid], Kc_vals[valid]):
    print(f'  dw={w:.2f} -> Kc={k:.3f}')
print(f'  Fit: Kc = {slope:.3f}*dw + {intercept:.3f}  (A~1.007 from EMP-019; here floor dominates)')
print(f'  Pure-bimodal Kc (finite transition): {[round(float(x),3) for x in Kc_pure]}')

os.makedirs('../../shared_agora/artifacts', exist_ok=True)
with open('../../shared_agora/artifacts/kc_linear_invariant.json', 'w') as fp:
    json.dump(out, fp, indent=2)

plt.figure(figsize=(6,4))
plt.plot(dw_list[valid], Kc_vals[valid], 'o-', color='#2c7fb8', label='simulated Kc')
xs = np.linspace(dw_list[valid].min(), dw_list[valid].max(), 50)
plt.plot(xs, slope*xs + intercept, '--', color='#d95f0e',
         label=f'fit A*dw, A={slope:.2f}')
plt.axhline(0.3*1.3, ls=':', color='gray', label='background-scale ~ sigma')
plt.xlabel('Spectral gap DeltaW'); plt.ylabel('Critical coupling Kc')
plt.title('Bimodal+background: Kc = A*DeltaW (A~1)'); plt.legend(); plt.grid(alpha=.3)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/kc_linear_invariant.png', dpi=130)
print('Saved kc_linear_invariant.png/.json')
