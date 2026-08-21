import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 200
sigma = 0.02
alpha = 2.0
dt = 0.01
T = 3000  # Longer simulation per point

np.random.seed(42)
omega = np.random.standard_cauchy(N)

def rk4_step(theta, omega, K0, alpha, sigma, dt):
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

def run_simulation(theta, K0, T=3000):
    Rs = np.zeros(T)
    for t in range(T):
        complex_mean = np.mean(np.exp(1j * theta))
        Rs[t] = np.abs(complex_mean)
        theta = rk4_step(theta, omega, K0, alpha, sigma, dt)
    return theta, np.mean(Rs[-500:])

# 1. Forward sweep starting from INCOHERENT (random phases)
theta_incoherent = np.random.uniform(0, 2*np.pi, N)
K_values = np.linspace(0.5, 6.0, 30)
print("--- Forward Sweep (from incoherent) ---")
R_forward = []
theta = theta_incoherent.copy()
for K in K_values:
    theta, R = run_simulation(theta, K)
    R_forward.append(R)
    print(f"  K={K:.2f}, R={R:.4f}")

# 2. Backward sweep starting from COHERENT (all phases equal)
theta_coherent = np.zeros(N)  # All in phase, R=1 initially
print("\n--- Backward Sweep (from coherent) ---")
R_backward = []
theta = theta_coherent.copy()
for K in reversed(K_values):
    theta, R = run_simulation(theta, K)
    R_backward.append(R)
    print(f"  K={K:.2f}, R={R:.4f}")
R_backward = R_backward[::-1]  # Reverse to match K_values order

plt.figure(figsize=(10, 6))
plt.plot(K_values, R_forward, 'o-', label='Forward (incoherent init)', color='blue')
plt.plot(K_values, R_backward, 's-', label='Backward (coherent init)', color='red')
plt.xlabel('$K_0$')
plt.ylabel('Order Parameter $R$')
plt.title(f'Bistability Analysis: $\\alpha={alpha}, \\sigma={sigma}$')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/r19z_bistability.png')
print("\nPlot saved to ../../shared_agora/artifacts/r19z_bistability.png")