"""
Refined Kuramoto Dossier Replication (DOSSIER #001)
Addresses EMP-008 replication failure with extended parameter sweep.

Key fixes:
- Longer integration time (T=1000) for proper settling.
- Multiple initial conditions (forward from incoherent, backward from coherent).
- Range of alpha values to find optimal hysteresis regime.
- Range of sigma (noise) values.
- Higher resolution near K_c ~ 1.42.

Hypothesis to test:
- H1: Hysteresis loop exists with sufficient integration time and large enough alpha.
- H2: The hysteresis loop width depends on alpha (larger alpha = wider loop).
- H3: Noise (sigma) destroys hysteresis above critical sigma.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)

# Parameters
N = 200
dt = 0.05
T_total = 1000
n_steps = int(T_total / dt)
transient = int(500 / dt)  # discard first half as transient

# Cauchy distributed frequencies (Lorentzian with gamma=1)
omegas = np.random.standard_cauchy(N)

def kuramoto_R(theta, K_eff, sigma, dt, n_steps, transient):
    """Simulate Kuramoto with non-linear feedback and return final R."""
    theta_t = theta.copy()
    R_history = []
    sqrt_2_sigma_dt = np.sqrt(2 * sigma * dt)

    for t in range(n_steps):
        # Compute order parameter
        z = np.exp(1j * theta_t).mean()
        R = np.abs(z)
        psi = np.angle(z)

        # Non-linear feedback: K_eff = K_0 * R^alpha (FIXED K_0 in this run)
        # We pass K_eff directly to avoid recomputing.

        # Kuramoto dynamics
        coupling = K_eff * R * np.sin(psi - theta_t)
        noise = sqrt_2_sigma_dt * np.random.randn(N)
        theta_t += (omegas + coupling) * dt + noise

        # Keep in [-pi, pi]
        theta_t = np.mod(theta_t + np.pi, 2 * np.pi) - np.pi

        if t > transient:
            R_history.append(R)

    return np.mean(R_history) if R_history else 0.0


def sweep_with_feedback(K_0_values, alpha, sigma, init_type='incoherent'):
    """Sweep K_0 and measure steady-state R with non-linear feedback."""
    R_values = []
    theta = None

    for K_0 in K_0_values:
        # Initialize from previous end-state for hysteresis (chain continuation)
        if init_type == 'forward_chain':
            if theta is None:
                theta = np.random.uniform(-np.pi, np.pi, N)  # incoherent start
        elif init_type == 'incoherent':
            theta = np.random.uniform(-np.pi, np.pi, N)
        elif init_type == 'coherent':
            theta = np.random.normal(0, 0.1, N)

        # Compute K_eff dynamically inside the simulation
        # We need to inline the feedback loop
        theta_t = theta.copy()
        R_final_sum = 0.0
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
                R_final_sum += R
                R_count += 1

        R_avg = R_final_sum / R_count if R_count > 0 else 0.0
        R_values.append(R_avg)
        theta = theta_t  # chain for next iteration

    return np.array(R_values)


# === MAIN EXPERIMENT ===
print("=" * 70)
print("REFINED KURAMOTO NON-LINEAR FEEDBACK HYSTERESIS REPLICATION")
print("=" * 70)

K_0_values = np.concatenate([
    np.arange(0.5, 2.0, 0.1),    # coarse sweep low
    np.arange(2.0, 6.0, 0.5),    # coarse sweep high
])

# Test multiple alphas
alphas = [1.0, 2.0, 3.0, 4.0]
sigma = 0.02

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for idx, alpha in enumerate(alphas):
    print(f"\n--- alpha = {alpha}, sigma = {sigma} ---")

    # Forward sweep (start incoherent, chain)
    R_forward = sweep_with_feedback(K_0_values, alpha, sigma, 'forward_chain')

    # Backward sweep (start coherent, chain)
    R_backward = sweep_with_feedback(K_0_values[::-1], alpha, sigma, 'coherent_chain')
    R_backward = R_backward[::-1]  # reverse back

    # Hysteresis width (max difference)
    diff = R_backward - R_forward
    hysteresis_width = np.max(np.abs(diff))

    print(f"Max R (forward): {np.max(R_forward):.3f}")
    print(f"Max R (backward): {np.max(R_backward):.3f}")
    print(f"Hysteresis width: {hysteresis_width:.3f}")

    ax = axes[idx]
    ax.plot(K_0_values, R_forward, 'b-o', label='Forward (incoherent init)', markersize=4)
    ax.plot(K_0_values, R_backward, 'r-s', label='Backward (coherent init)', markersize=4)
    ax.axvline(1.42, color='green', linestyle='--', alpha=0.5, label='Claimed K_c=1.42')
    ax.set_xlabel('K_0 (base coupling)')
    ax.set_ylabel('Steady-state R')
    ax.set_title(f'alpha={alpha}, sigma={sigma} (hysteresis_width={hysteresis_width:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_kuramoto_alphas.png', dpi=100)
print("\nSaved: r19z_kuramoto_alphas.png")

# === SECOND EXPERIMENT: Noise sweep at alpha=2 ===
print("\n" + "=" * 70)
print("NOISE SWEEP at alpha=2")
print("=" * 70)

sigmas = [0.01, 0.02, 0.05, 0.1]
K_0_fine = np.arange(0.5, 4.0, 0.1)

fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
axes2 = axes2.flatten()

for idx, sig in enumerate(sigmas):
    R_forward = sweep_with_feedback(K_0_fine, 2.0, sig, 'forward_chain')
    R_backward = sweep_with_feedback(K_0_fine[::-1], 2.0, sig, 'coherent_chain')[::-1]
    diff = R_backward - R_forward
    hwidth = np.max(np.abs(diff))

    ax = axes2[idx]
    ax.plot(K_0_fine, R_forward, 'b-o', label='Forward', markersize=4)
    ax.plot(K_0_fine, R_backward, 'r-s', label='Backward', markersize=4)
    ax.set_xlabel('K_0')
    ax.set_ylabel('R')
    ax.set_title(f'sigma={sig} (width={hwidth:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_kuramoto_noise.png', dpi=100)
print("Saved: r19z_kuramoto_noise.png")

# === THIRD EXPERIMENT: Critical transition sharpness ===
print("\n" + "=" * 70)
print("CRITICAL SHARPNESS at alpha=2, sigma=0.02")
print("=" * 70)

K_0_fine2 = np.arange(1.2, 1.8, 0.02)
R_forward_fine = sweep_with_feedback(K_0_fine2, 2.0, 0.02, 'forward_chain')
R_backward_fine = sweep_with_feedback(K_0_fine2[::-1], 2.0, 0.02, 'coherent_chain')[::-1]

fig3, ax3 = plt.subplots(figsize=(10, 6))
ax3.plot(K_0_fine2, R_forward_fine, 'b-o', label='Forward (incoherent)', markersize=5)
ax3.plot(K_0_fine2, R_backward_fine, 'r-s', label='Backward (coherent)', markersize=5)
ax3.axvline(1.42, color='green', linestyle='--', label='K_c=1.42 (claimed)')
ax3.fill_between(K_0_fine2, R_forward_fine, R_backward_fine, alpha=0.3, color='purple', label='Hysteresis region')
ax3.set_xlabel('K_0')
ax3.set_ylabel('R')
ax3.set_title(f'Critical Region Sharpness (alpha=2, sigma=0.02) — hysteresis_width={np.max(np.abs(R_backward_fine - R_forward_fine)):.3f}')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_kuramoto_critical.png', dpi=100)
print("Saved: r19z_kuramoto_critical.png")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("Dossier claims: sharp transition at K_c=1.42, hysteresis loop.")
print("Replication outcome: see figures.")
print("If hysteresis_width > 0.1, the dossier claim is SUPPORTED.")
print("If hysteresis_width ~ 0, the dossier claim is REFUTED at this alpha/sigma.")
