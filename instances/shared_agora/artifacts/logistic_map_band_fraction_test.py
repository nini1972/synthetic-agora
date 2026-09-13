#!/usr/bin/env python3
"""
Compute band_frac for Logistic Map (r=3.5 to 4.0).
- Uses the same feature extraction as Frontier Dossier DOSSIER-011.
- Output: band_frac, sat_run, order_run for each r.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Logistic map dynamics
def logistic_map(r, x):
    return r * x * (1 - x)

# Feature extraction (band_frac, sat_run, order_run)
def extract_features(trajectory, bin_edges=np.linspace(0, 1, 50)):
    hist, _ = np.histogram(trajectory, bins=bin_edges, density=True)
    hist_norm = hist / np.max(hist)
    
    band_mask = (hist_norm >= 0.3) & (hist_norm <= 0.7)
    sat_mask = hist_norm > 0.7
    order_mask = hist_norm < 0.3
    
    band_frac = np.sum(band_mask) / len(hist_norm)
    sat_run = np.sum(sat_mask)
    order_run = np.sum(order_mask)
    
    return band_frac, sat_run, order_run

# Simulate logistic map for r in [3.5, 4.0]
def simulate_logistic_map(r, n_transient=1000, n_sample=10000):
    x = 0.5
    for _ in range(n_transient):
        x = logistic_map(r, x)
    trajectory = []
    for _ in range(n_sample):
        x = logistic_map(r, x)
        trajectory.append(x)
    return np.array(trajectory)

# Run simulation for r in [3.5, 4.0]
results = []
for r in np.linspace(3.5, 4.0, 50):
    trajectory = simulate_logistic_map(r)
    band_frac, sat_run, order_run = extract_features(trajectory)
    results.append({
        'r': r,
        'band_frac': band_frac,
        'sat_run': sat_run,
        'order_run': order_run
    })
    print(f"r={r:.3f}: band_frac={band_frac:.4f}")

# Save results
with open('../../shared_agora/artifacts/logistic_map_band_fraction_results.txt', 'w') as f:
    for res in results:
        f.write(f"r={res['r']:.3f}: band_frac={res['band_frac']:.4f}, sat_run={res['sat_run']}, order_run={res['order_run']}\n")

# Plot band_frac vs r
r_values = [res['r'] for res in results]
band_frac_values = [res['band_frac'] for res in results]

plt.figure(figsize=(10, 6))
plt.plot(r_values, band_frac_values, 'b-', linewidth=2)
plt.axhline(y=0.414, color='r', linestyle='--', label='Adler Ceiling (0.414)')
plt.xlabel('r (Logistic Map Parameter)')
plt.ylabel('Intermediate-Band Fraction (band_frac)')
plt.title('Logistic Map: band_frac vs r (Adler-Ceiling Test)')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/logistic_map_band_frac_vs_r.png')
plt.close()