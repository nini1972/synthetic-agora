import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 200
sigma = 0.02
alpha = 2.0
dt = 0.02
T = 1000  # Steps per K value

np.random.seed(42)
omega = np.random.standard_cauchy(N)

def run_simulation(theta, K0, T=1000, dt=0.02):
    Rs = np.zeros(T)
    for t in range(T):
        complex_mean = np.mean(np.exp(1j * theta))
        R = np.abs(complex_mean)
        Rs[t] = R
        # Euler-Maruyama step
        K_eff = K0 * (R**alpha)
        noise = sigma * np.random.randn(N) * np.sqrt(dt)
        theta += (omega + K_eff * np.imag(complex_mean * np.exp(-1j * theta))) * dt + noise
    return theta, np.mean(Rs[-200:])

K_values = np.linspace(0.5, 6.0, 15)
print(f"Sweeping {len(K_values)} K-values with T={T}, dt={dt}")

# 1. Forward sweep starting from INCOHERENT
theta = np.random.uniform(0, 2*np.pi, N)
print("\n--- Forward (incoherent init) ---")
R_forward = []
for K in K_values:
    theta, R = run_simulation(theta, K)
    R_forward.append(R)
    print(f"  K={K:.2f}, R={R:.4f}")

# 2. Backward sweep starting from COHERENT
theta = np.zeros(N)
print("\n--- Backward (coherent init) ---")
R_backward = []
for K in reversed(K_values):
    theta, R = run_simulation(theta, K)
    R_backward.append(R)
    print(f"  K={K:.2f}, R={R:.4f}")
R_backward = R_backward[::-1]

plt.figure(figsize=(10, 6))
plt.plot(K_values, R_forward, 'o-', label='Forward (incoherent)', color='blue')
plt.plot(K_values, R_backward, 's-', label='Backward (coherent)', color='red')
plt.xlabel('$K_0$')
plt.ylabel('Order Parameter $R$')
plt.title(f'Bistability: $\\alpha={alpha}, \\sigma={sigma}$')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/r19z_bistability.png')
print("\nPlot saved.")