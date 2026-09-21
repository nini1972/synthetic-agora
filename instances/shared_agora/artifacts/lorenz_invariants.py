#!/usr/bin/env python3
"""
Test HYP-047: Lorenz attractor invariants (fractal dimension, Lyapunov exponent, wing asymmetry).
- Parameters: σ=10, β=8/3, ρ ∈ [24, 32].
- Integration: 4th-order Runge-Kutta (dt=0.01, T=1000).
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from mpl_toolkits.mplot3d import Axes3D

# Lorenz equations
def lorenz(t, state, sigma, beta, rho):
    x, y, z = state
    dxdt = sigma * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - beta * z
    return [dxdt, dydt, dzdt]

# Lyapunov exponent (Benettin algorithm)
def lyapunov_exponent(sigma, beta, rho, T=1000, dt=0.01):
    state = np.random.rand(3) * 0.1 + np.array([1, 1, 1])
    ortho = np.eye(3) * 1e-6
    lyap = np.zeros(3)
    
    for _ in range(T):
        # Evolve state and perturbation
        sol = solve_ivp(lorenz, [0, dt], state, args=(sigma, beta, rho), method='RK45')
        state = sol.y[:, -1]
        
        # Evolve orthogonal perturbations
        for i in range(3):
            perturbed = state + ortho[i]
            sol_perturbed = solve_ivp(lorenz, [0, dt], perturbed, args=(sigma, beta, rho), method='RK45')
            ortho[i] = sol_perturbed.y[:, -1] - state
            lyap[i] += np.log(np.linalg.norm(ortho[i]))
            ortho[i] = ortho[i] / np.linalg.norm(ortho[i])  # Re-orthogonalize
    
    return lyap / (T * dt)

# Fractal dimension (box-counting)
def fractal_dimension(trajectory, box_size=0.5):
    x_min, y_min, z_min = np.min(trajectory, axis=0)
    x_max, y_max, z_max = np.max(trajectory, axis=0)
    
    x_bins = np.arange(x_min, x_max, box_size)
    y_bins = np.arange(y_min, y_max, box_size)
    z_bins = np.arange(z_min, z_max, box_size)
    
    # Assign points to boxes
    x_idx = np.digitize(trajectory[:, 0], x_bins)
    y_idx = np.digitize(trajectory[:, 1], y_bins)
    z_idx = np.digitize(trajectory[:, 2], z_bins)
    
    # Count non-empty boxes
    boxes = set(zip(x_idx, y_idx, z_idx))
    N = len(boxes)
    
    return np.log(N) / np.log(1 / box_size)

# Wing asymmetry (Monte Carlo)
def wing_asymmetry(trajectory, n_samples=10000):
    x, y, z = trajectory.T
    x_min, x_max = np.min(x), np.max(x)
    
    # Sample points in left/right wings
    left_mask = x < 0
    right_mask = x > 0
    
    left_volume = np.mean(left_mask) * (x_max - x_min) * (np.max(y) - np.min(y)) * (np.max(z) - np.min(z))
    right_volume = np.mean(right_mask) * (x_max - x_min) * (np.max(y) - np.min(y)) * (np.max(z) - np.min(z))
    
    return left_volume / right_volume

# Test HYP-047
def test_invariants():
    sigma, beta = 10, 8/3
    rho_values = np.linspace(24, 32, 9)
    results = []
    
    for rho in rho_values:
        # Solve Lorenz system
        sol = solve_ivp(lorenz, [0, 100], [1, 1, 1], args=(sigma, beta, rho), method='RK45', dense_output=True)
        trajectory = sol.y.T
        
        # Compute invariants
        D = fractal_dimension(trajectory)
        lyap = lyapunov_exponent(sigma, beta, rho)
        asymmetry = wing_asymmetry(trajectory)
        
        results.append({
            "rho": rho,
            "fractal_dimension": D,
            "lyapunov_max": np.max(lyap),
            "wing_asymmetry": asymmetry
        })
    
    return pd.DataFrame(results)

# Run test and plot
if __name__ == "__main__":
    import pandas as pd
    df = test_invariants()
    df.to_csv('../../shared_agora/artifacts/lorenz_invariants.csv', index=False)
    
    # Plot
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(df["rho"], df["fractal_dimension"], 'o-', label='Fractal Dimension')
    plt.axhline(2.06, color='red', linestyle='--', label='Canonical D')
    plt.xlabel('ρ')
    plt.ylabel('Fractal Dimension')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(df["rho"], df["lyapunov_max"], 'o-', label='λ_max')
    plt.axhline(0.9056, color='red', linestyle='--', label='Canonical λ_max')
    plt.xlabel('ρ')
    plt.ylabel('Max Lyapunov Exponent')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/lorenz_invariants.png')