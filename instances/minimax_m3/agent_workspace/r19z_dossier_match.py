"""
MATCH DOSSIER PARAMETERS: N=200, attempt to reproduce K_c=1.42
Theoretical K_c for Gaussian Kuramoto: 2*sqrt(2/pi)*sigma_omega = 1.5955*sigma_omega
If K_c ≈ 1.42, then sigma_omega ≈ 0.89
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)
N = 200
dt = 0.05
T_total = 200
n_steps = int(T_total / dt)
transient = int(100 / dt)

def simulate(omegas, K_0, alpha, sigma, init_type):
    theta = None
    if init_type == 'forward':
        theta = np.random.uniform(-np.pi, np.pi, N)
    else:
        theta = np.random.normal(0, 0.5, N)  # partially coherent

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
    return R_sum / R_count if R_count > 0 else 0.0


# Test multiple Gaussian widths to find K_c ≈ 1.42
print("=" * 60)
print("DOSSIER PARAMETER MATCHING ATTEMPT")
print("=" * 60)

sigma_omega_candidates = [0.5, 0.7, 0.89, 1.0, 1.2]
alpha = 2.0
sigma = 0.02

fig, axes = plt.subplots(1, len(sigma_omega_candidates), figsize=(20, 4))

for idx, sigma_omega in enumerate(sigma_omega_candidates):
    omegas = np.random.randn(N) * sigma_omega
    K_0_values = np.arange(0.5, 4.0, 0.1)

    R_fwd = []
    theta = None
    for K_0 in K_0_values:
        if theta is None:
            theta = np.random.uniform(-np.pi, np.pi, N)
        # Run forward sweep carrying theta across
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
        R_fwd.append(R_sum / R_count if R_count > 0 else 0.0)
        theta = theta_t
    R_fwd = np.array(R_fwd)

    # Find K_c as first K where R_fwd > 0.3
    K_c_idx = np.where(R_fwd > 0.3)[0]
    K_c_est = K_0_values[K_c_idx[0]] if len(K_c_idx) > 0 else None
    theoretical_Kc = 1.5955 * sigma_omega
    print(f"\nsigma_omega={sigma_omega}: theoretical K_c={theoretical_Kc:.3f}, measured K_c={K_c_est}")

    ax = axes[idx]
    ax.plot(K_0_values, R_fwd, 'b-o', markersize=5)
    ax.axvline(theoretical_Kc, color='red', linestyle='--', label=f'theory={theoretical_Kc:.2f}')
    ax.axvline(1.42, color='green', linestyle=':', label='dossier K_c=1.42')
    ax.set_xlabel('K_0')
    ax.set_ylabel('R (forward)')
    ax.set_title(f'sigma_omega={sigma_omega}, K_c~{K_c_est}')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_kuramoto_dossier_match.png', dpi=100)
print("\nSaved: r19z_kuramoto_dossier_match.png")