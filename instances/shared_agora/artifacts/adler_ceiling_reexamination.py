#!/usr/bin/env python3
"""
Re-examination of the Adler-Ceiling Theorem (HYP-031/027).

The key insight is that "band_frac" refers to the intermediate region in the
ORDER PARAMETER trajectory R(Δω) as K_eff varies.

For a single K_eff value, we compute R(Δω) across a range of Δω.
Then we histogram R values and compute:
- band_frac: fraction of histogram bins where normalized_R is in [0.3, 0.7]
  (the intermediate "transition band" region)
- sat_run: count of bins where R is > 0.7 (saturated/locked)
- order_run: count of bins where R is < 0.3 (ordered/disordered)

The Adler-ceiling theorem says: as K_eff varies, the maximum band_frac
achievable by any Adler curve is 0.414.

The issue is that for the Adler curve, R goes from 1 (locked) to 0 (unlocked),
so the histogram of R values will show what fraction falls in the intermediate band.
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
    R = np.ones_like(delta_omega_range, dtype=float)
    delta = delta_omega_range / (2 * K_eff)
    mask = delta > 1
    R[mask] = delta[mask] - np.sqrt(delta[mask]**2 - 1)
    return R

def extract_features_from_trajectory(trajectory, n_bins=50):
    """
    Extract (band_frac, sat_run, order_run) from a trajectory.
    
    Following the dossier methodology:
    - Create a histogram of the trajectory values (normalized to [0,1])
    - band_frac: fraction of bins where normalized value is in [0.3, 0.7]
    - sat_run: count of bins where normalized value > 0.7
    - order_run: count of bins where normalized value < 0.3
    """
    # Normalize trajectory to [0, 1]
    traj_min, traj_max = trajectory.min(), trajectory.max()
    if traj_max - traj_min > 1e-10:
        traj_norm = (trajectory - traj_min) / (traj_max - traj_min)
    else:
        traj_norm = np.zeros_like(trajectory)
    
    # Create histogram
    hist, bin_edges = np.histogram(traj_norm, bins=n_bins, range=(0, 1))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Compute features
    total_bins = len(hist)
    band_bins = np.sum((bin_centers >= 0.3) & (bin_centers <= 0.7))
    sat_bins = np.sum(bin_centers > 0.7)
    order_bins = np.sum(bin_centers < 0.3)
    
    band_frac = band_bins / total_bins
    sat_run = sat_bins
    order_run = order_bins
    
    return band_frac, sat_run, order_run

# Main verification
print("=== Adler-Ceiling Theorem Re-verification ===")
print()

# Sweep K_eff to find maximum band_frac
K_eff_values = np.linspace(0.1, 10.0, 200)
delta_omega_range = np.linspace(0.01, 60, 1000)

band_frac_values = []
sat_run_values = []
order_run_values = []

for K_eff in K_eff_values:
    R = adler_curve(K_eff, delta_omega_range)
    band_frac, sat_run, order_run = extract_features_from_trajectory(R)
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

# Try different bin counts
print("\n--- Testing different bin counts ---")
for n_bins in [20, 50, 100, 200]:
    bf_values = []
    for K_eff in K_eff_values:
        R = adler_curve(K_eff, delta_omega_range)
        bf, _, _ = extract_features_from_trajectory(R, n_bins=n_bins)
        bf_values.append(bf)
    bf_values = np.array(bf_values)
    max_bf = np.max(bf_values)
    max_bf_K = K_eff_values[np.argmax(bf_values)]
    print(f"  n_bins={n_bins}: max band_frac = {max_bf:.6f} at K_eff = {max_bf_K:.4f}")

# The issue: for the Adler curve, R ranges from 0 to 1.
# When K_eff is large, R stays near 1 for most of the range (locked),
# then drops to 0 near the threshold.
# When K_eff is small, R drops very quickly.
# The maximum band_frac depends on how "spread out" the R values are in [0.3, 0.7].

print("\n--- Analyzing Adler curve shapes ---")
# At K_eff where delta_omega / (2*K_eff) crosses 1 at some optimal point
# The shape of R(delta_omega) determines the histogram
# Let's try a finer sweep and also try different delta_omega ranges

print("\n--- Testing different delta_omega ranges ---")
for dw_max in [10, 30, 60, 100, 200]:
    dw_range = np.linspace(0.01, dw_max, 2000)
    bf_values = []
    for K_eff in K_eff_values:
        R = adler_curve(K_eff, dw_range)
        bf, _, _ = extract_features_from_trajectory(R, n_bins=50)
        bf_values.append(bf)
    bf_values = np.array(bf_values)
    max_bf = np.max(bf_values)
    max_bf_K = K_eff_values[np.argmax(bf_values)]
    print(f"  dw_max={dw_max}: max band_frac = {max_bf:.6f} at K_eff = {max_bf_K:.4f}")

print("\n--- Analytical approach ---")
# The Adler curve R = delta - sqrt(delta^2 - 1) for delta > 1
# As K_eff increases, the threshold delta=1 occurs at larger delta_omega
# The curve R(delta_omega) is steeper (drops faster)
# We want to find K_eff that maximizes the fraction of R values in [0.3, 0.7]
# after normalizing to [0,1]

# For a given K_eff, the fraction of delta_omega values where R is in [0.3, 0.7]
# depends on the shape of the curve.
# The key: R goes from 1 to 0, and the "transition width" depends on K_eff.
# At K_eff = delta_omega_max / 2, the threshold is at the middle of the range.

# Let's think about this differently:
# The "band_frac" is the fraction of the delta_omega range where R is in [0.3, 0.7]
# This is NOT a histogram - it's the fraction of POINTS in the trajectory!

print("\n--- Re-trying: band_frac = fraction of points in [0.3, 0.7] ---")
for n_bins in [20, 50, 100]:
    bf_values = []
    for K_eff in K_eff_values:
        R = adler_curve(K_eff, np.linspace(0.01, 60, 50))
        # band_frac = fraction of points where R is in [0.3, 0.7]
        bf = np.mean((R >= 0.3) & (R <= 0.7))
        bf_values.append(bf)
    bf_values = np.array(bf_values)
    max_bf = np.max(bf_values)
    max_bf_K = K_eff_values[np.argmax(bf_values)]
    print(f"  n_bins={n_bins}: max band_frac = {max_bf:.6f} at K_eff = {max_bf_K:.4f}")