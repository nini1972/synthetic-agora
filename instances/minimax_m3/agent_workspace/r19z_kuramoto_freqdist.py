"""
FINAL CONTROL EXPERIMENT: Test dossier claim with Gaussian frequencies.
Dossier claims K_c ≈ 1.42, which matches Gaussian Kuramoto (std~0.5) more than Cauchy (K_c=2).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)
N = 100
dt = 0.1
T_total = 300
n_steps = int(T_total / dt)
transient = int(150 / dt)

def run_simulation(omega_dist='cauchy', alpha=2.0, sigma=0.02):
    if omega_dist == 'cauchy':
        omegas = np.random.standard_cauchy(N)
    elif omega_dist == 'gaussian':
        omegas = np.random.randn(N) * 0.5  # std=0.5

    K_0_values = np.arange(0.0, 5.0, 0.2)
    R_fwd_all = []
    R_bwd_all = []
    theta = None

    # Forward sweep
    for K_0 in K_0_values:
        if theta is None:
            theta = np.random.uniform(-np.pi, np.pi, N)
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
        R_fwd_all.append(R_sum / R_count if R_count > 0 else 0.0)
        theta = theta_t

    # Backward sweep
    theta = None
    for K_0 in K_0_values[::-1]:
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
        R_bwd_all.append(R_sum / R_count if R_count > 0 else 0.0)
        theta = theta_t
    R_bwd_all = R_bwd_all[::-1]

    return K_0_values, np.array(R_fwd_all), np.array(R_bwd_all)


print("=" * 60)
print("FREQUENCY DISTRIBUTION COMPARISON")
print("=" * 60)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for idx, dist in enumerate(['cauchy', 'gaussian']):
    print(f"\nTesting {dist} frequencies...")
    K_vals, R_fwd, R_bwd = run_simulation(dist, alpha=2.0, sigma=0.02)

    diff = R_bwd - R_fwd
    hwidth = np.max(np.abs(diff))

    # Find K_c where forward R first exceeds 0.3
    K_c_idx = np.where(R_fwd > 0.3)[0]
    K_c_est = K_vals[K_c_idx[0]] if len(K_c_idx) > 0 else None
    print(f"  Estimated K_c (forward, R>0.3): {K_c_est}")
    print(f"  Hysteresis width: {hwidth:.3f}")
    print(f"  Max R (forward): {np.max(R_fwd):.3f}")

    ax = axes[idx]
    ax.plot(K_vals, R_fwd, 'b-o', label='Forward', markersize=5)
    ax.plot(K_vals, R_bwd, 'r-s', label='Backward', markersize=5)
    ax.axvline(1.42, color='green', linestyle='--', label='Dossier K_c=1.42')
    ax.set_xlabel('K_0')
    ax.set_ylabel('R')
    ax.set_title(f'{dist} (h={hwidth:.3f}, K_c~{K_c_est})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_kuramoto_freqdist.png', dpi=100)
print("\nSaved: r19z_kuramoto_freqdist.png")

# Save data summary
print("\n" + "=" * 60)
print("DATA SUMMARY TABLE")
print("=" * 60)
print("Distribution | Max R | Hysteresis | Sharp Transition at K_c~1.42?")
print("-" * 60)

for dist in ['cauchy', 'gaussian']:
    K_vals, R_fwd, R_bwd = run_simulation(dist, alpha=2.0, sigma=0.02)
    max_R = np.max(R_fwd)
    hwidth = np.max(np.abs(R_bwd - R_fwd))
    sharp = "YES" if (np.any(R_fwd > 0.5) and hwidth > 0.2) else "NO"
    print(f"{dist:12s} | {max_R:.3f} | {hwidth:.3f} | {sharp}")