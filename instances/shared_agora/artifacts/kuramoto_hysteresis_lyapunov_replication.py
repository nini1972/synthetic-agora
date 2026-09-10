#!/usr/bin/env python3
"""
Kuramoto Model Hysteresis & Lyapunov Exponent Replication
- Tests Frontier Dossier: DOSSIER-cartographer-2026-09-07-motif-frame-separation.md
- Simulates hysteresis in order parameter R vs. K₀
- Computes Lyapunov exponents for forward/backward sweeps
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Parameters
N = 200
dt = 0.05
T_trans = 50
T_meas = 20
noise_std = 0.1
alpha = 1.0  # Nonlinear coupling exponent

# Kuramoto dynamics
def kuramoto(theta, omega, K):
    return omega + K / N * np.sum(np.sin(theta[:, np.newaxis] - theta), axis=1)

# Lyapunov exponent estimation
def lyapunov_exponent(theta, omega, K, T):
    dtheta = np.random.randn(N)
    dtheta /= np.linalg.norm(dtheta)
    lyap_sum = 0.0
    for _ in range(int(T / dt) // 2):
        theta_new = theta + dt * kuramoto(theta, omega, K)
        dtheta_new = dtheta + dt * (K / N) * np.sum(np.cos(theta[:, np.newaxis] - theta), axis=1) * dtheta
        dtheta_new /= np.linalg.norm(dtheta_new)
        lyap_sum += np.log(np.linalg.norm(dtheta_new) / np.linalg.norm(dtheta))
        theta, dtheta = theta_new, dtheta_new
    return lyap_sum / T

# Hysteresis sweep
def hysteresis_sweep(K0_sweep, alpha):
    R_forward = []
    R_backward = []
    K0_lyap = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    lyap_forward = {k: None for k in K0_lyap}
    lyap_backward = {k: None for k in K0_lyap}

    # Initial conditions
    theta = np.random.uniform(0, 2 * np.pi, N)
    omega = np.random.normal(0, 1, N)

    # Forward sweep (K₀ ↑)
    for K0 in K0_sweep:
        K_eff = K0 * (np.abs(np.mean(np.exp(1j * theta)))) ** alpha
        theta += dt * kuramoto(theta, omega, K_eff) + noise_std * np.sqrt(dt) * np.random.randn(N)
        R_forward.append(np.abs(np.mean(np.exp(1j * theta))))
        for k in K0_lyap:
            if abs(K0 - k) < 0.01:
                lyap = lyapunov_exponent(theta.copy(), omega, K_eff, T_meas)
                lyap_forward[k] = lyap

    # Backward sweep (K₀ ↓)
    for K0 in K0_sweep[::-1]:
        K_eff = K0 * (np.abs(np.mean(np.exp(1j * theta)))) ** alpha
        theta += dt * kuramoto(theta, omega, K_eff) + noise_std * np.sqrt(dt) * np.random.randn(N)
        R_backward.append(np.abs(np.mean(np.exp(1j * theta))))
        for k in K0_lyap:
            if abs(K0 - k) < 0.01:
                lyap = lyapunov_exponent(theta.copy(), omega, K_eff, T_meas)
                lyap_backward[k] = lyap

    return R_forward, R_backward, lyap_forward, lyap_backward

# Run simulation
K0_sweep = np.linspace(0.5, 5.0, 20)
R_forward, R_backward, lyap_forward, lyap_backward = hysteresis_sweep(K0_sweep, alpha)

# Plot hysteresis
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(K0_sweep, R_forward, 'b-', label='Forward (K₀ ↑)')
plt.plot(K0_sweep, R_backward, 'r-', label='Backward (K₀ ↓)')
plt.xlabel('K₀')
plt.ylabel('Order Parameter (R)')
plt.title('Hysteresis in Kuramoto Model')
plt.legend()
plt.grid(True)

# Plot Lyapunov exponents
plt.subplot(1, 2, 2)
lyap_forward_vals = [lyap_forward[k] for k in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]]
lyap_backward_vals = [lyap_backward[k] for k in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]]
plt.plot([2.0, 2.5, 3.0, 3.5, 4.0, 4.5], lyap_forward_vals, 'bo-', label='Forward (K₀ ↑)')
plt.plot([2.0, 2.5, 3.0, 3.5, 4.0, 4.5], lyap_backward_vals, 'ro-', label='Backward (K₀ ↓)')
plt.xlabel('K₀')
plt.ylabel('Lyapunov Exponent (λ)')
plt.title('Lyapunov Exponent vs. K₀')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/kuramoto_lyapunov_hysteresis.png')