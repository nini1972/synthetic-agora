#!/usr/bin/env python3
"""
Replication of EMP-042: Kuramoto Nonlinear Feedback Hysteresis & Lyapunov Exponents.
"""
import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Parameters
N = 200
dt = 0.01
T_trans = 100
T_meas = 50
K0_sweep = np.linspace(1.0, 4.5, 100)
alpha = 2.0  # Focus on α=2.0 for Lyapunov analysis
noise_std = 0.1

# Natural frequencies (Gaussian)
np.random.seed(42)
omega = np.random.normal(0, 1, N)

# Kuramoto dynamics
def kuramoto(theta, omega, K_eff):
    return omega + K_eff * np.mean(np.sin(theta - theta[:, None]), axis=1)

# Lyapunov exponent (tangent vector, zero-mode projection)
def lyapunov_exponent(theta, omega, K_eff, T_meas):
    delta = np.random.randn(N)
    delta /= np.linalg.norm(delta)
    lyap = 0.0
    for _ in range(int(T_meas / dt)):
        k1_theta = kuramoto(theta, omega, K_eff)
        k1_delta = kuramoto(theta + delta * 1e-6, np.zeros(N), K_eff) - k1_theta
        
        theta_new = theta + dt * k1_theta
        delta_new = delta + dt * k1_delta
        
        # Project out rotational zero-mode
        delta_new -= np.mean(delta_new)
        delta_new /= np.linalg.norm(delta_new)
        
        lyap += np.log(np.linalg.norm(delta_new) / 1e-6)
        theta, delta = theta_new, delta_new
    return lyap / T_meas

# Hysteresis sweep
def hysteresis_sweep(K0_sweep, alpha):
    R_forward = []
    R_backward = []
    lyap_forward = []
    lyap_backward = []
    
    # Forward sweep (K₀ ↑)
    theta = 2 * np.pi * np.random.rand(N)
    for K0 in K0_sweep:
        K_eff = K0 * (np.abs(np.mean(np.exp(1j * theta)))) ** alpha
        theta += dt * kuramoto(theta, omega, K_eff) + noise_std * np.sqrt(dt) * np.random.randn(N)
        R_forward.append(np.abs(np.mean(np.exp(1j * theta))))
        if np.isclose(K0, 2.0) or np.isclose(K0, 2.5) or np.isclose(K0, 3.0) or np.isclose(K0, 3.5) or np.isclose(K0, 4.0) or np.isclose(K0, 4.5):
            lyap = lyapunov_exponent(theta.copy(), omega, K_eff, T_meas)
            lyap_forward.append(lyap)
    
    # Backward sweep (K₀ ↓)
    for K0 in K0_sweep[::-1]:
        K_eff = K0 * (np.abs(np.mean(np.exp(1j * theta)))) ** alpha
        theta += dt * kuramoto(theta, omega, K_eff) + noise_std * np.sqrt(dt) * np.random.randn(N)
        R_backward.append(np.abs(np.mean(np.exp(1j * theta))))
        if np.isclose(K0, 2.0) or np.isclose(K0, 2.5) or np.isclose(K0, 3.0) or np.isclose(K0, 3.5) or np.isclose(K0, 4.0) or np.isclose(K0, 4.5):
            lyap = lyapunov_exponent(theta.copy(), omega, K_eff, T_meas)
            lyap_backward.append(lyap)
    
    return R_forward, R_backward, lyap_forward, lyap_backward

# Run simulation
R_forward, R_backward, lyap_forward, lyap_backward = hysteresis_sweep(K0_sweep, alpha)

# Plot hysteresis
plt.figure(figsize=(10, 5))
plt.plot(K0_sweep, R_forward, 'b-', label='Forward (K₀ ↑)')
plt.plot(K0_sweep, R_backward, 'r-', label='Backward (K₀ ↓)')
plt.xlabel('$K_0$')
plt.ylabel('$R$')
plt.title(f'Kuramoto Hysteresis (α={alpha})')
plt.legend()
plt.grid()
plt.savefig('../../shared_agora/artifacts/kuramoto_hysteresis_replication.png')
plt.close()

# Plot Lyapunov exponents
K0_lyap = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
plt.figure(figsize=(10, 5))
plt.plot(K0_lyap, lyap_forward, 'bo-', label='Forward (K₀ ↑)')
plt.plot(K0_lyap, lyap_backward, 'ro-', label='Backward (K₀ ↓)')
plt.xlabel('$K_0$')
plt.ylabel('Nontrivial Lyapunov Exponent')
plt.title(f'Lyapunov Exponents (α={alpha})')
plt.legend()
plt.grid()
plt.savefig('../../shared_agora/artifacts/kuramoto_lyapunov_replication.png')
plt.close()

# Save results
with open('../../shared_agora/artifacts/kuramoto_replication_results.txt', 'w') as f:
    f.write(f"Hysteresis Thresholds (α={alpha}):\n")
    f.write(f"Forward jump (R > 0.5): K₀ ≈ {K0_sweep[np.argmax(np.array(R_forward) > 0.5)]}\n")
    f.write(f"Backward drop (R < 0.5): K₀ ≈ {K0_sweep[len(K0_sweep) - np.argmax(np.array(R_backward)[::-1] < 0.5) - 1]}\n")
    f.write(f"Lyapunov Exponents (Forward): {lyap_forward}\n")
    f.write(f"Lyapunov Exponents (Backward): {lyap_backward}\n")