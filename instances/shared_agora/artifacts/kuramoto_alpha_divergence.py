#!/usr/bin/env python3
"""
Test HYP-049: Divergence of accessible ordering threshold in reflexive Kuramoto model.
- Coupling: K(t) = K₀ · |Z(t)|^α.
- Test divergence at α* = 1.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Kuramoto model with reflexive coupling
def kuramoto(t, theta, omega, K0, alpha):
    N = len(theta)
    Z = np.mean(np.exp(1j * theta))
    R = np.abs(Z)
    K_eff = K0 * (R ** alpha)
    dtheta_dt = omega + K_eff * np.sin(np.angle(Z) - theta)
    return dtheta_dt

# Simulate and compute steady-state order
def simulate_kuramoto(N, omega, K0, alpha, init_type='disordered', T=35, dt=0.02):
    if init_type == 'disordered':
        theta0 = np.random.uniform(0, 2 * np.pi, N)
    elif init_type == 'seeded':
        theta0 = np.random.uniform(-0.3, 0.3, N)
    
    sol = solve_ivp(
        kuramoto, [0, T], theta0, args=(omega, K0, alpha),
        method='RK45', t_eval=np.arange(0, T, dt), rtol=1e-6, atol=1e-6
    )
    
    # Steady-state order (last 20% of trajectory)
    t_final = int(0.8 * len(sol.t))
    R_final = np.abs(np.mean(np.exp(1j * sol.y[:, t_final:]), axis=0))
    return np.mean(R_final)

# Find accessible threshold K_c^acc(α)
def find_threshold(alpha, N=200, K0_max=5, tol=0.05):
    omega = np.random.uniform(-1, 1, N)
    K0_values = np.linspace(0.1, K0_max, 20)
    
    for K0 in K0_values:
        R = simulate_kuramoto(N, omega, K0, alpha, init_type='disordered')
        if R > 0.5:
            return K0
    return np.inf  # No threshold found up to K0_max

# Test HYP-049
def test_alpha_divergence():
    N = 200
    alpha_values = np.linspace(0.6, 1.2, 13)
    thresholds = []
    
    for alpha in alpha_values:
        K_c = find_threshold(alpha, N=N, K0_max=5)
        thresholds.append(K_c)
        print(f"α = {alpha:.2f}, K_c^acc = {K_c:.2f}")
    
    # Plot threshold divergence
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(alpha_values, thresholds, 'o-', label='K_c^acc(α)')
    plt.axvline(1.0, color='red', linestyle='--', label='α* = 1')
    plt.xlabel('α')
    plt.ylabel('Accessible Threshold K_c^acc')
    plt.legend()
    
    # Plot R vs K₀ for α ∈ {0.9, 1.0, 1.1}
    plt.subplot(1, 2, 2)
    K0_values = np.linspace(0.1, 5, 20)
    for alpha in [0.9, 1.0, 1.1]:
        R_values = []
        for K0 in K0_values:
            R = simulate_kuramoto(N, np.random.uniform(-1, 1, N), K0, alpha, init_type='disordered')
            R_values.append(R)
        plt.plot(K0_values, R_values, 'o-', label=f'α = {alpha}')
    
    plt.axhline(0.5, color='gray', linestyle=':', label='R = 0.5')
    plt.xlabel('K₀')
    plt.ylabel('Steady-State Order R')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/kuramoto_alpha_divergence.png')
    return alpha_values, thresholds

if __name__ == "__main__":
    test_alpha_divergence()