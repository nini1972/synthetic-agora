#!/usr/bin/env python3
"""
Final verification of the Adler-Ceiling Theorem.

The key insight is that the "band_frac" for the Adler curve depends on how
the delta_omega range is scaled relative to K_eff. When properly calibrated
(dw_max = 2*K_eff * delta_R03), the band_frac equals:

  (delta_R03 - delta_R07) / delta_R03 = (109/60 - 149/140) / (109/60) = 316/763

This is exactly the claimed ceiling value.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os
from fractions import Fraction

def adler_curve(K_eff, delta_omega_range):
    """Compute exact Adler cross-locking order parameter."""
    R = np.ones_like(delta_omega_range, dtype=float)
    delta = delta_omega_range / (2 * K_eff)
    mask = delta > 1
    R[mask] = delta[mask] - np.sqrt(delta[mask]**2 - 1)
    return R

def band_frac_histogram(R, n_bins=50):
    """Compute band_frac from histogram normalized by max."""
    hist, _ = np.histogram(R, bins=np.linspace(0, 1, n_bins + 1))
    if np.max(hist) > 0:
        hist_norm = hist / np.max(hist)
    else:
        hist_norm = hist
    band_mask = (hist_norm >= 0.3) & (hist_norm <= 0.7)
    sat_mask = hist_norm > 0.7
    order_mask = hist_norm < 0.3
    band_frac = np.mean(band_mask)
    sat_run = np.sum(sat_mask)
    order_run = np.sum(order_mask)
    return band_frac, sat_run, order_run

# === Analytical Derivation ===
print("=== Analytical Derivation of the Adler Ceiling ===")
print()

# For R(δ) = δ - sqrt(δ² - 1), solve R = c for c in [0, 1]:
# δ = (1 + c²) / (2c)
delta_R07 = (1 + 0.7**2) / (2 * 0.7)  # = 1.0642857...
delta_R03 = (1 + 0.3**2) / (2 * 0.3)  # = 1.8166667...

# Exact fraction computation
# δ = (1 + c²) / (2c)
# For c = 0.3 = 3/10: δ = (1 + 9/100) / (6/10) = (109/100) / (6/10) = 109/60
# For c = 0.7 = 7/10: δ = (1 + 49/100) / (14/10) = (149/100) / (14/10) = 149/140
d03_frac = Fraction(109, 60)
d07_frac = Fraction(149, 140)

ceiling_frac = (d03_frac - d07_frac) / d03_frac
analytical_ceiling = float(ceiling_frac)

print(f"Solving R(δ) = c for δ = (1 + c²)/(2c):")
print(f"  δ at R=0.7 = {float(d07_frac):.10f} = {d07_frac}")
print(f"  δ at R=0.3 = {float(d03_frac):.10f} = {d03_frac}")
print()
print(f"Ceiling = (δ_R=0.3 - δ_R=0.7) / δ_R=0.3")
print(f"  = ({float(d03_frac):.10f} - {float(d07_frac):.10f}) / {float(d03_frac):.10f}")
print(f"  = {analytical_ceiling:.10f}")
print(f"  = {ceiling_frac}")
print()
print(f"316/763 = {316/763:.10f}")
print(f"Exact match: {ceiling_frac == Fraction(316, 763)}")
print()

# Numerical verification
print("=== Numerical Verification ===")
print()

# The ceiling is achieved when dw_max = 2*K_eff * delta_R03
K_eff = 3.0
dw_max = 2 * K_eff * delta_R03
dw_range = np.linspace(0.001, dw_max, 10000)
R = adler_curve(K_eff, dw_range)
bf_hist, sat, order = band_frac_histogram(R, n_bins=50)
bf_points = np.mean((R >= 0.3) & (R <= 0.7))

print(f"K_eff = {K_eff}, dw_max = {dw_max:.6f} (= 2*K_eff*delta_R03)")
print(f"  band_frac (histogram) = {bf_hist:.10f}")
print(f"  band_frac (point frac) = {bf_points:.10f}")
print(f"  Analytical ceiling = {analytical_ceiling:.10f}")
print(f"  Match (histogram, within 0.01): {abs(bf_hist - analytical_ceiling) < 0.01}")
print(f"  Match (points, within 0.01): {abs(bf_points - analytical_ceiling) < 0.01}")
print()

# === 2D Scan ===
print("=== 2D Scan: K_eff x (dw_max / (2*K_eff)) ===")
K_eff_arr = np.linspace(0.1, 20, 100)
ratio_arr = np.linspace(0.5, 5, 100)

max_bf = 0
max_K = 0
max_ratio = 0
results_grid = np.zeros((len(ratio_arr), len(K_eff_arr)))

for i, ratio in enumerate(ratio_arr):
    for j, K_eff in enumerate(K_eff_arr):
        dw_max = 2 * K_eff * ratio
        dw_range = np.linspace(0.001, dw_max, 5000)
        R = adler_curve(K_eff, dw_range)
        bf, _, _ = band_frac_histogram(R, n_bins=50)
        results_grid[i, j] = bf
        if bf > max_bf:
            max_bf = bf
            max_K = K_eff
            max_ratio = ratio

print(f"Maximum band_frac (histogram method) = {max_bf:.10f}")
print(f"  at K_eff = {max_K:.4f}, ratio = {max_ratio:.4f}")
print(f"  delta_R03 = {delta_R03:.10f}")
print(f"  Analytical ceiling = {analytical_ceiling:.10f}")
print()

# === Substrate Classification ===
print("=== Substrate Classification ===")
print()

kuramoto_band_frac = 0.190
print(f"Kuramoto (band_frac={kuramoto_band_frac}):")
print(f"  Below ceiling: {kuramoto_band_frac < analytical_ceiling}")
print(f"  Margin: {analytical_ceiling - kuramoto_band_frac:.4f}")
print()

logistic_band_frac = 0.744
print(f"Logistic map (band_frac={logistic_band_frac}):")
print(f"  Exceeds ceiling: {logistic_band_frac > analytical_ceiling}")
print(f"  Excess: {logistic_band_frac - analytical_ceiling:.4f} ({(logistic_band_frac - analytical_ceiling)/analytical_ceiling*100:.1f}%)")
print()

rule30_band_frac = 0.000
print(f"Rule 30 (band_frac={rule30_band_frac}):")
print(f"  Below ceiling: {rule30_band_frac < analytical_ceiling}")
print()

# === Save Results ===
artifacts_dir = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts'
os.makedirs(artifacts_dir, exist_ok=True)

results = {
    'analytical_ceiling': float(analytical_ceiling),
    'claimed_ceiling_316_763': 316/763,
    'exact_fraction': str(ceiling_frac),
    'match_exact': bool(ceiling_frac == Fraction(316, 763)),
    'delta_R07': float(d07_frac),
    'delta_R03': float(d03_frac),
    'max_band_frac_numerical': float(max_bf),
    'K_eff_at_max': float(max_K),
    'ratio_at_max': float(max_ratio),
    'substrates': {
        'kuramoto': {'band_frac': 0.190, 'below_ceiling': True},
        'logistic_map': {'band_frac': 0.744, 'exceeds_ceiling': True, 'excess': float(logistic_band_frac - analytical_ceiling)},
        'rule30': {'band_frac': 0.0, 'below_ceiling': True}
    }
}

with open(os.path.join(artifacts_dir, 'adler_ceiling_verification_results.json'), 'w') as f:
    json.dump(results, f, indent=2)

# === Plot ===
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel 1: 2D heatmap of band_frac
im = axes[0, 0].imshow(results_grid, aspect='auto', origin='lower',
                       extent=[K_eff_arr[0], K_eff_arr[-1], ratio_arr[0], ratio_arr[-1]],
                       cmap='viridis', vmin=0, vmax=analytical_ceiling + 0.05)
axes[0, 0].axhline(y=delta_R03, color='r', linestyle='--', label=f'delta_R03 = {delta_R03:.4f}')
axes[0, 0].plot(max_K, max_ratio, 'w*', markersize=15, label=f'Max = {max_bf:.4f}')
plt.colorbar(im, ax=axes[0, 0])
axes[0, 0].set_xlabel('K_eff')
axes[0, 0].set_ylabel('dw_max / (2*K_eff)')
axes[0, 0].set_title('Adler Family: band_frac Heatmap')
axes[0, 0].legend()

# Panel 2: band_frac vs K_eff for specific ratios
for ratio in [0.5, 1.0, delta_R03, 2.0, 3.0]:
    bf_slice = []
    for K_eff in K_eff_arr:
        dw_max = 2 * K_eff * ratio
        dw_range = np.linspace(0.001, dw_max, 5000)
        R = adler_curve(K_eff, dw_range)
        bf, _, _ = band_frac_histogram(R, n_bins=50)
        bf_slice.append(bf)
    label = f'ratio={ratio:.3f}' if ratio != delta_R03 else f'ratio=delta_R03={delta_R03:.3f}'
    axes[0, 1].plot(K_eff_arr, bf_slice, label=label)
axes[0, 1].axhline(y=analytical_ceiling, color='r', linestyle='--', label=f'Ceiling={analytical_ceiling:.4f}')
axes[0, 1].set_xlabel('K_eff')
axes[0, 1].set_ylabel('band_frac')
axes[0, 1].set_title('band_frac vs K_eff for different dw_max ratios')
axes[0, 1].legend(fontsize=8)
axes[0, 1].grid(True)

# Panel 3: Sample Adler curves showing the ceiling
for K_eff in [1.0, 3.0, 10.0]:
    dw_max = 2 * K_eff * delta_R03
    dw_range = np.linspace(0.001, dw_max, 1000)
    R = adler_curve(K_eff, dw_range)
    axes[1, 0].plot(dw_range / (2 * K_eff), R, label=f'K_eff={K_eff}')
axes[1, 0].axhline(y=0.3, color='r', linestyle=':', label='R=0.3')
axes[1, 0].axhline(y=0.7, color='r', linestyle=':', label='R=0.7')
axes[1, 0].axvline(x=1.0, color='g', linestyle='--', label='threshold (d=1)')
axes[1, 0].axvline(x=delta_R07, color='orange', linestyle='--', label=f'd_R0.7={delta_R07:.3f}')
axes[1, 0].axvline(x=delta_R03, color='purple', linestyle='--', label=f'd_R0.3={delta_R03:.3f}')
axes[1, 0].set_xlabel('dw / (2*K_eff) = delta')
axes[1, 0].set_ylabel('R')
axes[1, 0].set_title('Adler Curves at Ceiling Conditions')
axes[1, 0].legend(fontsize=8)
axes[1, 0].grid(True)

# Panel 4: Substrate classification
substrates = ['Kuramoto', 'Logistic Map', 'Rule 30']
band_fracs = [0.190, 0.744, 0.000]
colors = ['green' if bf < analytical_ceiling else 'red' for bf in band_fracs]
bars = axes[1, 1].bar(substrates, band_fracs, color=colors, edgecolor='black')
axes[1, 1].axhline(y=analytical_ceiling, color='r', linestyle='--', label=f'Adler Ceiling = {analytical_ceiling:.4f}')
axes[1, 1].set_ylabel('band_frac')
axes[1, 1].set_title('Substrate Classification vs Adler Ceiling')
axes[1, 1].legend()
axes[1, 1].grid(True, axis='y')

# Add value labels
for bar, bf in zip(bars, band_fracs):
    axes[1, 1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                    f'{bf:.3f}', ha='center', va='bottom')

plt.tight_layout()
plt.savefig(os.path.join(artifacts_dir, 'adler_ceiling_final_verification.png'), dpi=150, bbox_inches='tight')
plt.close()

print("=== All Complete ===")
print(f"Results saved to {os.path.join(artifacts_dir, 'adler_ceiling_verification_results.json')}")
print(f"Figure saved to {os.path.join(artifacts_dir, 'adler_ceiling_final_verification.png')}")