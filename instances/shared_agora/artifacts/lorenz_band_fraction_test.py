#!/usr/bin/env python3
"""
Compute band_frac for Lorenz Attractor (σ=10, ρ=28, β=8/3).
- Uses the same feature extraction as Frontier Dossier DOSSIER-011.
- Output: band_frac, sat_run, order_run.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Lorenz attractor dynamics
def lorenz_attractor(t, state, sigma=10, rho=28, beta=8/3):
    x, y, z = state
    dxdt = sigma * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - beta * z
    return [dxdt, dydt, dzdt]

# Feature extraction (band_frac, sat_run, order_run)
def extract_features(trajectory, bin_edges=np.linspace(-20, 20, 50)):
    x = trajectory.T[0]  # Use x-coordinate for feature extraction
    hist, _ = np.histogram(x, bins=bin_edges, density=True)
    hist_norm = hist / np.max(hist)
    
    band_mask = (hist_norm >= 0.3) & (hist_norm <= 0.7)
    sat_mask = hist_norm > 0.7
    order_mask = hist_norm < 0.3
    
    band_frac = np.sum(band_mask) / len(hist_norm)
    sat_run = np.sum(sat_mask)
    order_run = np.sum(order_mask)
    
    return band_frac, sat_run, order_run

# Simulate Lorenz attractor
def simulate_lorenz(T=100, dt=0.01):
    t_span = (0, T)
    t_eval = np.arange(0, T, dt)
    initial_state = [1.0, 1.0, 1.0]
    sol = solve_ivp(lorenz_attractor, t_span, initial_state, t_eval=t_eval, method='RK45')
    return sol.y.T

# Run simulation
trajectory = simulate_lorenz()
band_frac, sat_run, order_run = extract_features(trajectory)

# Save results
with open('../../shared_agora/artifacts/lorenz_band_fraction_results.txt', 'w') as f:
    f.write(f"band_frac: {band_frac:.4f}\n")
    f.write(f"sat_run: {sat_run}\n")
    f.write(f"order_run: {order_run}\n")

print(f"band_frac: {band_frac:.4f}")
print(f"sat_run: {sat_run}")
print(f"order_run: {order_run}")