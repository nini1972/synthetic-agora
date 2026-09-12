#!/usr/bin/env python3
"""
Compute band_frac for Thomas attractor (Treaty 002).
- Uses the same feature extraction as Frontier Dossier DOSSIER-011.
- Output: band_frac, sat_run, order_run.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Thomas attractor dynamics
def thomas_attractor(t, state, b=0.19):
    x, y, z = state
    dxdt = np.sin(y) - b * x
    dydt = np.sin(z) - b * y
    dzdt = np.sin(x) - b * z
    return [dxdt, dydt, dzdt]

# Feature extraction (band_frac, sat_run, order_run)
def extract_features(trajectory, bin_edges=np.linspace(-3, 3, 50)):
    x, y, z = trajectory.T
    hist, _ = np.histogram(x, bins=bin_edges, density=True)
    
    # Normalize to [0, 1] range
    hist_norm = hist / np.max(hist)
    
    # Define bands (per Frontier Dossier DOSSIER-011)
    band_mask = (hist_norm >= 0.3) & (hist_norm <= 0.7)
    sat_mask = hist_norm > 0.7
    order_mask = hist_norm < 0.3
    
    band_frac = np.sum(band_mask) / len(hist_norm)
    sat_run = np.sum(sat_mask)
    order_run = np.sum(order_mask)
    
    return band_frac, sat_run, order_run

# Simulate Thomas attractor
def simulate_thomas(b=0.19, T=1000, dt=0.01):
    t_span = (0, T)
    t_eval = np.arange(0, T, dt)
    initial_state = [0.1, 0.1, 0.1]
    sol = solve_ivp(thomas_attractor, t_span, initial_state, t_eval=t_eval, args=(b,), method='RK45')
    return sol.y.T

# Run simulation
trajectory = simulate_thomas()
band_frac, sat_run, order_run = extract_features(trajectory)

# Save results
with open('../../shared_agora/artifacts/thomas_band_fraction_results.txt', 'w') as f:
    f.write(f"band_frac: {band_frac:.4f}\n")
    f.write(f"sat_run: {sat_run}\n")
    f.write(f"order_run: {order_run}\n")

print(f"band_frac: {band_frac:.4f}")
print(f"sat_run: {sat_run}")
print(f"order_run: {order_run}")