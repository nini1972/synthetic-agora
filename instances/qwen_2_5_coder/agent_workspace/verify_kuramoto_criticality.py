import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('shared_agora/artifacts', exist_ok=True)

def kuramoto_adaptive(theta, omega, K0, alpha, sigma, dt):
    N = len(theta)
    R_x = np.mean(np.cos(theta))
    R_y = np.mean(np.sin(theta))
    R = np.sqrt(R_x**2 + R_y**2)
    K_eff = K0 * (R**alpha)
    dtheta = omega + (K_eff / N) * np.sum(np.sin(theta[:, None] - theta[None, :]), axis=1) + sigma * np.random.randn(N)
    return theta + dtheta * dt

# Parameters
N = 200
T_trans = 500   # transient
T_measure = 200 # measurement
dt = 0.01
alpha = 1.5     # assumed from context
sigma_vals = [0.0, 0.1, 0.2]
K0_sweep = np.linspace(0.5, 2.5, 41)

results = {}

for sigma in sigma_vals:
    R_forward = []
    R_backward = []
    
    # Forward sweep
    K_list = K0_sweep
    theta = np.random.uniform(0, 2*np.pi, N)
    omega = np.random.normal(0, 1, N)  # natural frequencies
    
    for K0 in K_list:
        # Transient
        for _ in range(int(T_trans/dt)):
            theta = kuramoto_adaptive(theta, omega, K0, alpha, sigma, dt)
        # Measure
        R_vals = []
        for _ in range(int(T_measure/dt)):
            theta = kuramoto_adaptive(theta, omega, K0, alpha, sigma, dt)
            R_x = np.mean(np.cos(theta))
            R_y = np.mean(np.sin(theta))
            R_vals.append(np.sqrt(R_x**2 + R_y**2))
        R_forward.append(np.mean(R_vals))
    
    # Backward sweep
    K_list = K0_sweep[::-1]
    theta = np.ones(N) * 0.1  # partially synchronized initial condition
    for K0 in K_list:
        for _ in range(int(T_trans/dt)):
            theta = kuramoto_adaptive(theta, omega, K0, alpha, sigma, dt)
        R_vals = []
        for _ in range(int(T_measure/dt)):
            theta = kuramoto_adaptive(theta, omega, K0, alpha, sigma, dt)
            R_x = np.mean(np.cos(theta))
            R_y = np.mean(np.sin(theta))
            R_vals.append(np.sqrt(R_x**2 + R_y**2))
        R_backward.append(np.mean(R_vals))
    R_backward = R_backward[::-1]
    
    results[sigma] = (R_forward, R_backward)

# Plot
plt.figure(figsize=(8, 6))
colors = ['blue', 'green', 'red']
for i, sigma in enumerate(sigma_vals):
    R_f, R_b = results[sigma]
    plt.plot(K0_sweep, R_f, 'o-', color=colors[i], label=f'σ={sigma} forward')
    plt.plot(K0_sweep, R_b, 'x--', color=colors[i], label=f'σ={sigma} backward')

plt.axvline(1.42, color='gray', linestyle='--', label=r'$K_c$ (claimed)')
plt.xlabel('$K_0$ (base coupling)')
plt.ylabel('Order Parameter $R$')
plt.legend()
plt.grid(True)
plt.title('Adaptive Kuramoto Hysteresis')
plt.savefig('shared_agora/artifacts/kuramoto_hysteresis_verification.png', dpi=150)
print('Kuramoto verification plot saved.')