import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- Simulation Parameters ---
N = 200
sigma = 0.02  # Noise intensity
alpha = 2.0   # Non-linear feedback exponent
dt = 0.01     # Smaller time step for RK4 stability
T = 2000      # Simulation steps per K value (20 time units)

np.random.seed(42)
omega = np.random.standard_cauchy(N)

def rk4_step(theta, omega, K0, alpha, sigma, N, dt):
    """RK4 step for Kuramoto model with non-linear feedback."""
    def deriv(th):
        complex_mean = np.mean(np.exp(1j * th))
        R = np.abs(complex_mean)
        K_eff = K0 * (R**alpha)
        return omega + K_eff * np.imag(complex_mean * np.exp(-1j * th)) + sigma * np.random.randn(N)

    k1 = deriv(theta)
    k2 = deriv(theta + 0.5 * dt * k1)
    k3 = deriv(theta + 0.5 * dt * k2)
    k4 = deriv(theta + dt * k3)
    return theta + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

def run_simulation(theta, K0, alpha, sigma, N=200, T=2000, dt=0.01):
    Rs = np.zeros(T)
    for t in range(T):
        complex_mean = np.mean(np.exp(1j * theta))
        R = np.abs(complex_mean)
        Rs[t] = R
        theta = rk4_step(theta, omega, K0, alpha, sigma, N, dt)
    return theta, np.mean(Rs[-200:])

# Adiabatic sweep: pass the final state to the next K value
K0_values_up = np.linspace(0.5, 4.0, 25)
K0_values_down = np.linspace(4.0, 0.5, 25)

theta = np.random.uniform(0, 2*np.pi, N)
print("Running Forward Sweep (Adiabatic)...")
R_up = []
for K in K0_values_up:
    theta, R = run_simulation(theta, K, alpha, sigma)
    R_up.append(R)
    print(f"  K={K:.2f}, R={R:.4f}")

print("\nRunning Backward Sweep (Adiabatic)...")
R_down = []
for K in K0_values_down:
    theta, R = run_simulation(theta, K, alpha, sigma)
    R_down.append(R)
    print(f"  K={K:.2f}, R={R:.4f}")

plt.figure(figsize=(10, 6))
plt.plot(K0_values_up, R_up, 'o-', label='Forward Sweep', color='blue')
plt.plot(K0_values_down, R_down, 's-', label='Backward Sweep', color='red')
plt.xlabel('$K_0$')
plt.ylabel('Order Parameter $R$')
plt.title(f'Kuramoto Hysteresis (RK4, $\\alpha={alpha}, \\sigma={sigma}$)')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/r19z_hysteresis_replication_rk4.png')
print("\nPlot saved to ../../shared_agora/artifacts/r19z_hysteresis_replication_rk4.png")