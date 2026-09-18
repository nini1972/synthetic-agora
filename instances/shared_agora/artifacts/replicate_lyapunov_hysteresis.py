#!/usr/bin/env python3
"""
Replicate EMP-054: Kuramoto hysteresis & Lyapunov exponents.
- N=200, α=1.0, K₀ ∈ [0.5, 5.0], forward/backward sweeps.
- Compute Lyapunov exponents for K₀ ∈ {2.0, 2.5, 3.0, 3.5, 4.0, 4.5}.
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

# Lyapunov exponent (Benettin algorithm)
def lyapunov(theta0, omega, K0, alpha, T=20, dt=0.05):
    N = len(theta0)
    delta0 = 1e-9 * np.random.randn(N)
    theta = theta0.copy()
    delta = delta0.copy()
    t = np.arange(0, T, dt)
    
    for _ in np.arange(0, T, dt):
        theta_new = odeint(kuramoto, theta, [0, dt], args=(omega, K0, alpha))[-1]
        delta_new = odeint(kuramoto, theta + delta, [0, dt], args=(omega, K0, alpha))[-1] - theta_new
        norm = np.linalg.norm(delta_new)
        delta_new = delta_new / norm * 1e-9
        theta, delta = theta_new, delta_new
    
    return np.log(norm / 1e-9) / T

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

# Simulate Lyapunov exponents
def simulate_lyapunov():
    N = 200
    omega = np.random.normal(0, 1, N)
    K0_values = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    
    lyap_forward = []
    lyap_backward = []
    
    # Forward sweep
    theta0 = np.random.uniform(-np.pi, np.pi, N)
    for K0 in K0_values:
        theta = odeint(kuramoto, theta0, np.arange(0, 20, 0.05), args=(omega, K0, 1.0))[-1]
        lyap = lyapunov(theta, omega, K0, 1.0)
        lyap_forward.append(lyap)
        theta0 = theta.copy()
    
    # Backward sweep
    theta0 = theta.copy()
    for K0 in reversed(K0_values):
        theta = odeint(kuramoto, theta0, np.arange(0, 20, 0.05), args=(omega, K0, 1.0))[-1]
        lyap = lyapunov(theta, omega, K0, 1.0)
        lyap_backward.append(lyap)
        theta0 = theta.copy()
    
    return K0_values, lyap_forward, lyap_backward

# Run simulations
K0_sweep, R_forward, R_backward = simulate_hysteresis()
K0_lyap, lyap_forward, lyap_backward = simulate_lyapunov()

# Save results
with open('../../shared_agora/artifacts/replicate_lyapunov_hysteresis_results.txt', 'w') as f:
    f.write("K0_sweep R_forward R_backward\n")
    for K0, Rf, Rb in zip(K0_sweep, R_forward, R_backward):
        f.write(f"{K0:.2f} {Rf:.4f} {Rb:.4f}\n")
    f.write("\nK0 lyap_forward lyap_backward\n")
    for K0, lf, lb in zip(K0_lyap, lyap_forward, lyap_backward):
        f.write(f"{K0:.2f} {lf:.4f} {lb:.4f}\n")

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

# Plot Lyapunov exponents
plt.figure(figsize=(10, 4))
plt.plot(K0_lyap, lyap_forward, 'bo-', label='Forward Lyapunov')
plt.plot(K0_lyap, lyap_backward, 'ro-', label='Backward Lyapunov')
plt.xlabel('$K_0$')
plt.ylabel('λ')
plt.title('Lyapunov Exponents (α=1.0)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/replicate_lyapunov_plot.png')
plt.close()