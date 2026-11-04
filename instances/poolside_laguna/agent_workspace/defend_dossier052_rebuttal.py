import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Reflexive Kuramoto Model (α=1.2, K₀=4, N=500)
def kuramoto_reflexive(t, theta, omega, alpha, K0):
    N = len(theta)
    exp_theta = np.exp(1j * theta)
    R = np.abs(np.mean(exp_theta))
    psi = np.angle(np.mean(exp_theta))
    dtheta_dt = omega + K0 * R**alpha * np.sin(psi - theta)
    return dtheta_dt

# Simulation parameters
N = 500
alpha = 1.2
K0 = 4.0
t_span = (0, 20)
t_eval = np.linspace(0, 20, 1000)
seeds = 100

# Run simulations
R_final = np.zeros(seeds)
for seed in range(seeds):
    np.random.seed(seed)
    theta0 = 2 * np.pi * np.random.rand(N)
    omega = np.random.uniform(-1, 1, N)
    
    sol = solve_ivp(
        kuramoto_reflexive, t_span, theta0, args=(omega, alpha, K0),
        t_eval=t_eval, method='RK45', rtol=1e-6, atol=1e-8
    )
    
    # Compute order parameter
    exp_theta = np.exp(1j * sol.y[:, -1])
    R_final[seed] = np.abs(np.mean(exp_theta))

# Plot results
plt.figure(figsize=(8, 5))
plt.hist(R_final, bins=20, color='skyblue', edgecolor='black')
plt.axvline(np.mean(R_final), color='red', linestyle='--', label=f'Mean R = {np.mean(R_final):.4f}')
plt.xlabel('Order Parameter R', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title(f'Reflexive Kuramoto: α={alpha}, K₀={K0}, N={N} (100 seeds)', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('dossier052_rebuttal_refined.png', dpi=150)

# Save data
np.save('dossier052_rebuttal_refined.npy', R_final)
with open('dossier052_rebuttal_refined.txt', 'w') as f:
    f.write(f"Mean R: {np.mean(R_final):.6f} ± {np.std(R_final):.6f}\n")
    f.write(f"99.9% CI: [{np.percentile(R_final, 0.05):.6f}, {np.percentile(R_final, 99.95):.6f}]")

print("✅ Refined rebuttal artifacts generated.")
