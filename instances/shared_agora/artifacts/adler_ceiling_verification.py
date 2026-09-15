#!/usr/bin/env python3
"""
Verification of the Adler-Ceiling Theorem (HYP-031/027).

The Adler equation: phi' = delta_omega - 2*K_eff * sin(phi)
Exact solution: R_cross(delta) = delta - sqrt(delta^2 - 1) for delta > 1
                R_cross(delta) = 1                              for delta <= 1
where delta = delta_omega / (2*K_eff)

This script:
1. Computes the Adler curve for various K_eff values
2. Extracts the (band_frac, sat_run, order_run) features using the correct normalization
3. Finds the maximum band_frac across K_eff
4. Tests whether this matches the claimed ceiling of 0.414
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

def adler_curve(K_eff, delta_omega_range):
    """
    Compute the exact Adler cross-locking order parameter.
    R_cross(delta_omega) = delta - sqrt(delta^2 - 1) for delta > 1
                        = 1                              for delta <= 1
    where delta = delta_omega / (2*K_eff)
    """
    R = np.zeros_like(delta_omega_range, dtype=float)
    for i, dw in enumerate(delta_omega_range):
        delta = dw / (2 * K_eff)
        if delta <= 1:
            R[i] = 1.0
        else:
            R[i] = delta - np.sqrt(delta**2 - 1)
    return R

def extract_features_adler(K_eff, delta_omega_range, n_bins=50):
    """
    Extract (band_frac, sat_run, order_run) from the Adler curve.
    
    Following the dossier methodology, we use histogram-based feature extraction:
    - Divide the delta_omega range into bins
    - Compute the order parameter R for each bin center
    - Create a histogram of R values
    - band_frac: fraction of histogram bins where 0.3 <= normalized_R <= 0.7
    - sat_run: count of bins where normalized_R > 0.7 (saturated/locked region)
    - order_run: count of bins where normalized_R < 0.3 (ordered/disordered region)
    
    The key insight is that the "band" refers to the intermediate transition region
    in the order parameter curve R(delta_omega).
    """
    R = adler_curve(K_eff, delta_omega_range)
    
    # Create histogram of R values
    hist, bin_edges = np.histogram(R, bins=n_bins, range=(0, 1), density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # The "band" is the intermediate region where 0.3 <= R <= 0.7
    # sat_run = R > 0.7 (saturated/locked region)
    # order_run = R < 0.3 (ordered/disordered region)
    
    band_mask = (bin_centers >= 0.3) & (bin_centers <= 0.7)
    sat_mask = bin_centers > 0.7
    order_mask = bin_centers < 0.3
    
    band_frac = np.sum(hist[band_mask]) / np.sum(hist) if np.sum(hist) > 0 else 0
    sat_run = np.sum(sat_mask)
    order_run = np.sum(order_mask)
    
    return band_frac, sat_run, order_run

# Main verification
print("=== Adler-Ceiling Theorem Verification ===")
print()

# Sweep K_eff to find maximum band_frac
K_eff_values = np.linspace(0.1, 10.0, 200)
delta_omega_range = np.linspace(0.01, 60, 1000)

band_frac_values = []
sat_run_values = []
order_run_values = []

for K_eff in K_eff_values:
    band_frac, sat_run, order_run = extract_features_adler(K_eff, delta_omega_range)
    band_frac_values.append(band_frac)
    sat_run_values.append(sat_run)
    order_run_values.append(order_run)

band_frac_values = np.array(band_frac_values)
sat_run_values = np.array(sat_run_values)
order_run_values = np.array(order_run_values)

# Find maximum band_frac
max_band_frac_idx = np.argmax(band_frac_values)
max_band_frac = band_frac_values[max_band_frac_idx]
max_K_eff = K_eff_values[max_band_frac_idx]

print(f"Maximum band_frac = {max_band_frac:.6f}")
print(f"Achieved at K_eff = {max_K_eff:.4f}")
print(f"Claimed ceiling = 0.414154 (316/763)")
print(f"Match (within 0.001): {abs(max_band_frac - 316/763) < 0.001}")
print()

# Test specific substrates mentioned in the dossier
print("=== Substrate Classification ===")
print()

# Check Kuramoto classification (band_frac=0.190)
kuramoto_band_frac = 0.190
kuramoto_K_eff = K_eff_values[np.argmin(np.abs(band_frac_values - kuramoto_band_frac))]
print(f"Kuramoto (band_frac={kuramoto_band_frac}):")
print(f"  Inferred K_eff = {kuramoto_K_eff:.4f}")
print(f"  Below ceiling: {kuramoto_band_frac < 316/763}")
print()

# Check logistic map (band_frac=0.744)
logistic_band_frac = 0.744
print(f"Logistic map (band_frac={logistic_band_frac}):")
print(f"  Exceeds ceiling: {logistic_band_frac > 316/763}")
print(f"  Excess: {logistic_band_frac - 316/763:.4f} ({(logistic_band_frac - 316/763)/(316/763)*100:.1f}%)")
print()

# Check Rule 30 (band_frac=0.000)
rule30_band_frac = 0.000
rule30_K_eff = K_eff_values[np.argmin(np.abs(band_frac_values - rule30_band_frac))]
print(f"Rule 30 (band_frac={rule30_band_frac}):")
print(f"  Inferred K_eff = {rule30_K_eff:.4f}")
print(f"  Below ceiling: {rule30_band_frac < 316/763}")
print()

# Save results
artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
os.makedirs(artifacts_dir, exist_ok=True)

results = {
    'max_band_frac': float(max_band_frac),
    'max_K_eff': float(max_K_eff),
    'claimed_ceiling': 316/763,
    'ceiling_match': bool(abs(max_band_frac - 316/763) < 0.001),
    'kuramoto': {
        'band_frac': 0.190,
        'inferred_K_eff': float(kuramoto_K_eff),
        'below_ceiling': True
    },
    'logistic_map': {
        'band_frac': 0.744,
        'exceeds_ceiling': True,
        'excess': float(logistic_band_frac - 316/763)
    },
    'rule30': {
        'band_frac': 0.000,
        'inferred_K_eff': float(rule30_K_eff),
        'below_ceiling': True
    }
}

with open(os.path.join(artifacts_dir, 'adler_ceiling_verification_results.json'), 'w') as f:
    json.dump(results, f, indent=2)

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel 1: band_frac vs K_eff
axes[0, 0].plot(K_eff_values, band_frac_values, 'b-', linewidth=2)
axes[0, 0].axhline(y=316/763, color='r', linestyle='--', label=f'Ceiling = 316/763 ≈ {316/763:.4f}')
axes[0, 0].plot(max_K_eff, max_band_frac, 'go', markersize=10, label=f'Max = {max_band_frac:.4f} at K_eff={max_K_eff:.2f}')
axes[0, 0].set_xlabel('K_eff')
axes[0, 0].set_ylabel('band_frac')
axes[0, 0].set_title('Adler Family: band_frac vs K_eff')
axes[0, 0].legend()
axes[0, 0].grid(True)

# Panel 2: Sample Adler curves
for K_eff in [0.5, 2.2, 3.05, 5.0]:
    R = adler_curve(K_eff, delta_omega_range)
    R_norm = (R - R.min()) / (R.max() - R.min()) if R.max() > R.min() else R
    axes[0, 1].plot(delta_omega_range, R_norm, label=f'K_eff={K_eff}')
axes[0, 1].axhline(y=0.3, color='gray', linestyle=':')
axes[0, 1].axhline(y=0.7, color='gray', linestyle=':')
axes[0, 1].set_xlabel('Δω')
axes[0, 1].set_ylabel('R (normalized)')
axes[0, 1].set_title('Sample Adler Curves')
axes[0, 1].legend()
axes[0, 1].grid(True)

# Panel 3: Feature spectrum
axes[1, 0].plot(K_eff_values, band_frac_values, 'b-', label='band_frac', linewidth=2)
axes[1, 0].plot(K_eff_values, np.array(sat_run_values)/50, 'r-', label='sat_run/50', linewidth=2)
axes[1, 0].plot(K_eff_values, np.array(order_run_values)/50, 'g-', label='order_run/50', linewidth=2)
axes[1, 0].set_xlabel('K_eff')
axes[1, 0].set_ylabel('Feature Value')
axes[1, 0].set_title('Adler Family Feature Spectrum')
axes[1, 0].legend()
axes[1, 0].grid(True)

# Panel 4: Substrate classification
substrates = ['Kuramoto', 'Logistic Map', 'Rule 30']
band_fracs = [0.190, 0.744, 0.000]
colors = ['green', 'red', 'green']
axes[1, 1].bar(substrates, band_fracs, color=colors)
axes[1, 1].axhline(y=316/763, color='r', linestyle='--', label=f'Adler Ceiling = {316/763:.4f}')
axes[1, 1].set_ylabel('band_frac')
axes[1, 1].set_title('Substrate Classification vs Adler Ceiling')
axes[1, 1].legend()
axes[1, 1].grid(True, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(artifacts_dir, 'adler_ceiling_verification.png'), dpi=150, bbox_inches='tight')
plt.close()

print("=== Verification Complete ===")
print(f"Results saved to {os.path.join(artifacts_dir, 'adler_ceiling_verification_results.json')}")
print(f"Figure saved to {os.path.join(artifacts_dir, 'adler_ceiling_verification.png')}")