#!/usr/bin/env python3
"""
Replicate EMP-054 hysteresis ONLY (skip Lyapunov for speed).
- N=200, α=1.0, K₀ ∈ [0.5, 5.0], forward/backward sweeps.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Kuramoto dynamics
def kuramoto(theta, t, omega, K0, alpha):
    N = len(theta)
    R = np.abs(np.mean(np.exp(1j * theta)))
    K_eff = K0 * (R ** alpha)
    coupling = np.sin(theta[:, None] - theta[None, :])
    dtheta = omega + (K_eff / N) * np.sum(coupling, axis=1)
    return dtheta

# Simulate hysteresis
def simulate_hysteresis():
    N = 200
    omega = np.random.normal(0, 1, N)
    K0_sweep = np.linspace(0.5, 5.0, 46)
    
    # Forward sweep (reduced T_meas)
    theta0 = np.random.uniform(-np.pi, np.pi, N)
    R_forward = []
    for K0 in K0_sweep:
        theta = odeint(kuramoto, theta0, np.arange(0, 5, 0.05), args=(omega, K0, 1.0))[-1]
        R = np.abs(np.mean(np.exp(1j * theta)))
        R_forward.append(R)
        theta0 = theta.copy()
    
    # Backward sweep (reduced T_meas)
    theta0 = theta.copy()
    R_backward = []
    for K0 in K0_sweep[::-1]:
        theta = odeint(kuramoto, theta0, np.arange(0, 5, 0.05), args=(omega, K0, 1.0))[-1]
        R = np.abs(np.mean(np.exp(1j * theta)))
        R_backward.append(R)
        theta0 = theta.copy()
    
    return K0_sweep, R_forward, R_backward

# Run simulation
K0_sweep, R_forward, R_backward = simulate_hysteresis()

# Save results
with open('../../shared_agora/artifacts/replicate_hysteresis_results.txt', 'w') as f:
    f.write("K0_sweep R_forward R_backward\n")
    for K0, Rf, Rb in zip(K0_sweep, R_forward, R_backward):
        f.write(f"{K0:.2f} {Rf:.4f} {Rb:.4f}\n")

# Plot hysteresis
plt.figure(figsize=(10, 4))
plt.plot(K0_sweep, R_forward, 'b-', label='Forward Sweep')
plt.plot(K0_sweep, R_backward, 'r-', label='Backward Sweep')
plt.xlabel('$K_0$')
plt.ylabel('$R$')
plt.title('Kuramoto Hysteresis (α=1.0)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/replicate_hysteresis_plot.png')
plt.close()