import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- Simulation Parameters ---
N = 200
sigma = 0.02  # Noise intensity
alpha = 2.0   # Non-linear feedback exponent
dt = 0.05
T = 1500      # Simulation steps per K value

# Natural frequencies (Lorentzian distribution, width=1)
np.random.seed(42)
omega = np.random.standard_cauchy(N)

def run_simulation_robust(K0, alpha, sigma, N=200, T=1500, dt=0.05):
    theta = np.random.uniform(0, 2*np.pi, N)
    Rs = np.zeros(T)
    for t in range(T):
        complex_mean = np.mean(np.exp(1j * theta))
        R = np.abs(complex_mean)
        Rs[t] = R
        # Apply non-linear feedback: K_eff = K0 * R^alpha
        # Note: standard Kuramoto scales by 1/N. Here K is the macroscopic coupling.
        # If K0 is macroscopic, K_eff/N is the microscopic coupling.
        K_eff = K0 * (R**alpha) / N
        d_theta = omega + K_eff * np.imag(complex_mean * np.exp(-1j * theta)) + sigma * np.random.randn(N)
        theta += d_theta * dt
    return np.mean(Rs[-200:])

# Sweep K0 up and down
K0_values_up = np.linspace(0.5, 4.0, 30)
K0_values_down = np.linspace(4.0, 0.5, 30)

print("Running Forward Sweep...")
R_up = [run_simulation_robust(K, alpha, sigma) for K in K0_values_up]
print("Running Backward Sweep...")
R_down = [run_simulation_robust(K, alpha, sigma) for K in K0_values_down]

print("\nK_up, R_up:")
for k, r in zip(K0_values_up, R_up):
    print(f"  K={k:.2f}, R={r:.4f}")
print("\nK_down, R_down:")
for k, r in zip(K0_values_down, R_down):
    print(f"  K={k:.2f}, R={r:.4f}")

plt.figure(figsize=(10, 6))
plt.plot(K0_values_up, R_up, 'o-', label='Forward Sweep (Increasing K)', color='blue')
plt.plot(K0_values_down, R_down, 's-', label='Backward Sweep (Decreasing K)', color='red')
plt.xlabel('$K_0$')
plt.ylabel('Order Parameter $R$')
plt.title(f'Kuramoto Hysteresis Replication ($\\alpha={alpha}, \\sigma={sigma}$)')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/r19z_hysteresis_replication.png')
print("\nPlot saved to ../../shared_agora/artifacts/r19z_hysteresis_replication.png")