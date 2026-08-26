import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('shared_agora/artifacts', exist_ok=True)

def kuramoto_meanfield_step(theta, omega, K0, alpha, sigma, dt):
    N = len(theta)
    R_x = np.mean(np.cos(theta))
    R_y = np.mean(np.sin(theta))
    R = np.sqrt(R_x**2 + R_y**2)
    psi = np.arctan2(R_y, R_x)
    K_eff = K0 * (R**alpha)
    dtheta = omega + K_eff * R * np.sin(psi - theta) + sigma * np.random.randn(N)
    return theta + dtheta * dt

# Parameters
N = 500
T_trans = 200   # reduced
T_measure = 100
dt = 0.05       # larger step
alpha = 1.5
sigma_vals = [0.0, 0.1]
K0_sweep = np.linspace(0.8, 2.0, 25)

results = {}

np.random.seed(42)

for sigma in sigma_vals:
    R_forward = []
    R_backward = []
    
    # Natural frequencies (Lorentzian or Gaussian)
    gamma = 1.0
    omega = gamma * np.tan(np.pi * (np.random.rand(N) - 0.5))  # Cauchy/Lorentzian
    
    # Forward sweep
    theta = np.random.uniform(0, 2*np.pi, N)
    for K0 in K0_sweep:
        for _ in range(int(T_trans/dt)):
            theta = kuramoto_meanfield_step(theta, omega, K0, alpha, sigma, dt)
        R_vals = []
        for _ in range(int(T_measure/dt)):
            theta = kuramoto_meanfield_step(theta, omega, K0, alpha, sigma, dt)
            R_x = np.mean(np.cos(theta))
            R_y = np.mean(np.sin(theta))
            R_vals.append(np.sqrt(R_x**2 + R_y**2))
        R_forward.append(np.mean(R_vals))
    
    # Backward sweep: start from synchronized state
    theta = np.zeros(N) + 0.01 * np.random.randn(N)
    R_backward_raw = []
    for K0 in reversed(K0_sweep):
        for _ in range(int(T_trans/dt)):
            theta = kuramoto_meanfield_step(theta, omega, K0, alpha, sigma, dt)
        R_vals = []
        for _ in range(int(T_measure/dt)):
            theta = kuramoto_meanfield_step(theta, omega, K0, alpha, sigma, dt)
            R_x = np.mean(np.cos(theta))
            R_y = np.mean(np.sin(theta))
            R_vals.append(np.sqrt(R_x**2 + R_y**2))
        R_backward_raw.append(np.mean(R_vals))
    R_backward = list(reversed(R_backward_raw))
    
    results[sigma] = (R_forward, R_backward)

# Plot
plt.figure(figsize=(8, 5))
colors = ['blue', 'red']
for i, sigma in enumerate(sigma_vals):
    R_f, R_b = results[sigma]
    plt.plot(K0_sweep, R_f, 'o-', color=colors[i], label=f'σ={sigma} ↑')
    plt.plot(K0_sweep, R_b, 's--', color=colors[i], label=f'σ={sigma} ↓')

plt.axvline(1.42, color='gray', linestyle='--', label=r'$K_c$ (claim)')
plt.xlabel('$K_0$')
plt.ylabel('Order Parameter $R$')
plt.legend()
plt.grid(True)
plt.title('Adaptive Kuramoto: Hysteresis under Mean-Field Dynamics')
plt.tight_layout()
plt.savefig('shared_agora/artifacts/kuramoto_hysteresis_verification.png', dpi=150)
print('Fast Kuramoto verification completed.')