#!/usr/bin/env python3
"""
Verify master-curve collapse R_ss = f(K₀ R_ss^α) for reflexive Kuramoto.
- Simulate Kuramoto with reflexive coupling K = K₀ R^α.
- Test α ∈ [-1, 1], K₀ ∈ [0.1, 4.0].
- Plot R_ss vs K_eff = K₀ R_ss^α.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Kuramoto dynamics
def kuramoto(theta, t, omega, K0, alpha):
    """Reflexive Kuramoto ODE."""
    N = len(theta)
    R = np.abs(np.mean(np.exp(1j * theta)))
    K_eff = K0 * (R ** alpha)
    coupling = np.sin(theta[:, None] - theta[None, :])
    dtheta = omega + (K_eff / N) * np.sum(coupling, axis=1)
    return dtheta

# Simulate steady-state R_ss
def simulate_R_ss(K0, alpha, N=100, gamma=1.0, steps=500, dt=0.1):
    """Simulate and return steady-state R_ss."""
    omega = np.random.uniform(-gamma, gamma, N)
    theta0 = np.random.uniform(-np.pi, np.pi, N)
    t = np.arange(0, steps * dt, dt)
    
    theta = odeint(kuramoto, theta0, t, args=(omega, K0, alpha))
    R = np.abs(np.mean(np.exp(1j * theta[-int(0.1 * steps):]), axis=1))
    return np.mean(R)

# Test grid
K0_values = np.linspace(0.5, 2.0, 4)
alpha_values = [-1.0, -0.5, 0.0, 0.5, 1.0]

# Simulate
results = []
for K0 in K0_values:
    for alpha in alpha_values:
        R_ss = simulate_R_ss(K0, alpha)
        K_eff = K0 * (R_ss ** alpha)
        results.append((K0, alpha, R_ss, K_eff))
        print(f"K0={K0:.2f}, α={alpha:.2f}, R_ss={R_ss:.3f}, K_eff={K_eff:.3f}")

# Save results
with open('../../shared_agora/artifacts/master_curve_collapse_results.txt', 'w') as f:
    for K0, alpha, R_ss, K_eff in results:
        f.write(f"K0={K0:.2f}, α={alpha:.2f}, R_ss={R_ss:.3f}, K_eff={K_eff:.3f}\n")

# Plot master curve
K_effs = [r[3] for r in results]
R_ss_values = [r[2] for r in results]

plt.figure(figsize=(8, 4))
plt.scatter(K_effs, R_ss_values, c='blue', alpha=0.7)
plt.xlabel('$K_{eff} = K_0 R_{ss}^\alpha$')
plt.ylabel('$R_{ss}$')
plt.title('Master-Curve Collapse: $R_{ss} = f(K_{eff})$')
plt.grid(True)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/master_curve_collapse_plot.png')
plt.close()