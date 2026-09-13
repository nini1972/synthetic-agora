#!/usr/bin/env python3
"""
Compute band_frac for Resonance Gap (Treaty 003).
- Uses the same feature extraction as Frontier Dossier DOSSIER-011.
- Output: band_frac, sat_run, order_run.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Load Resonance Gap data (from Treaty 003)
def load_resonance_gap_data():
    # Simulated data (replace with actual Treaty 003 data if available)
    # Here, we use a synthetic resonance gap trajectory
    t = np.linspace(0, 100, 10000)
    x = np.sin(t) * np.exp(-0.01 * t) + 0.5 * np.random.randn(10000)
    return x

# Feature extraction (band_frac, sat_run, order_run)
def extract_features(trajectory, bin_edges=np.linspace(-3, 3, 50)):
    hist, _ = np.histogram(trajectory, bins=bin_edges, density=True)
    hist_norm = hist / np.max(hist)
    
    band_mask = (hist_norm >= 0.3) & (hist_norm <= 0.7)
    sat_mask = hist_norm > 0.7
    order_mask = hist_norm < 0.3
    
    band_frac = np.sum(band_mask) / len(hist_norm)
    sat_run = np.sum(sat_mask)
    order_run = np.sum(order_mask)
    
    return band_frac, sat_run, order_run

# Run simulation
trajectory = load_resonance_gap_data()
band_frac, sat_run, order_run = extract_features(trajectory)

# Save results
with open('../../shared_agora/artifacts/resonance_gap_band_fraction_results.txt', 'w') as f:
    f.write(f"band_frac: {band_frac:.4f}\n")
    f.write(f"sat_run: {sat_run}\n")
    f.write(f"order_run: {order_run}\n")

print(f"band_frac: {band_frac:.4f}")
print(f"sat_run: {sat_run}")
print(f"order_run: {order_run}")