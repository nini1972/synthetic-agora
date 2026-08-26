"""
Refined Kuramoto Dossier Replication - FAST VERSION
Reduced integration time and N for tractable runtime.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)

N = 100  # Reduced from 200
dt = 0.1
T_total = 300
n_steps = int(T_total / dt)
transient = int(150 / dt)

omegas = np.random.standard_cauchy(N)

def sweep(K_0_values, alpha, sigma, init_type='forward_chain'):
    R_values = []
    theta = None

    for K_0 in K_0_values:
        if init_type == 'forward_chain':
            if theta is None:
                theta = np.random.uniform(-np.pi, np.pi, N)
        elif init_type == 'backward_chain':
            if theta is None:
                theta = np.random.normal(0, 0.1, N)

        theta_t = theta.copy()
        R_sum = 0.0
        R_count = 0
        sqrt_2_sigma_dt = np.sqrt(2 * sigma * dt)

        for t in range(n_steps):
            z = np.exp(1j * theta_t).mean()
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K_0 * (R ** alpha)

            coupling = K_eff * np.sin(psi - theta_t)
            noise = sqrt_2_sigma_dt * np.random.randn(N)
            theta_t += (omegas + coupling) * dt + noise
            theta_t = np.mod(theta_t + np.pi, 2 * np.pi) - np.pi

            if t > transient:
                R_sum += R
                R_count += 1

        R_avg = R_sum / R_count if R_count > 0 else 0.0
        R_values.append(R_avg)
        theta = theta_t

    return np.array(R_values)


print("=" * 60)
print("KURAMOTO NON-LINEAR FEEDBACK - FAST REPLICATION")
print("=" * 60)

K_0_values = np.arange(0.5, 5.5, 0.25)
alphas = [1.0, 2.0, 3.0]
sigma = 0.02

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for idx, alpha in enumerate(alphas):
    print(f"alpha={alpha}...")
    R_forward = sweep(K_0_values, alpha, sigma, 'forward_chain')
    R_backward = sweep(K_0_values[::-1], alpha, sigma, 'backward_chain')[::-1]
    diff = R_backward - R_forward
    hwidth = np.max(np.abs(diff))
    print(f"  hysteresis width: {hwidth:.3f}")

    ax = axes[idx]
    ax.plot(K_0_values, R_forward, 'b-o', label='Forward', markersize=4)
    ax.plot(K_0_values, R_backward, 'r-s', label='Backward', markersize=4)
    ax.axvline(1.42, color='green', linestyle='--', alpha=0.5)
    ax.set_xlabel('K_0')
    ax.set_ylabel('R')
    ax.set_title(f'alpha={alpha} (h={hwidth:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_kuramoto_fast.png', dpi=100)
print("Saved: r19z_kuramoto_fast.png")

# Print sample values
print("\nFinal results:")
print(f"K_0 | R_fwd | R_bwd | diff")
for i, K in enumerate(K_0_values):
    if i < len(R_forward):
        print(f"{K:.2f} | {R_forward[i]:.3f} | {R_backward[i]:.3f} | {R_backward[i]-R_forward[i]:+.3f}")
