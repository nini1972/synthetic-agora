"""
DOSSIER-052 REPLICATION: Alpha-divergence of the accessible ordering threshold
in the reflexive Kuramoto model K(t) = K0 * |Z(t)|^alpha.

CLAIM: alpha* = 1 is the divergence point of the accessible ordering threshold
K_c^acc(alpha) -> infinity as alpha -> 1 from below.
For alpha > 1, the synchronized attractor still exists (basin-disconnected)
but cannot be reached from random initial conditions.

REPLICATION PROTOCOL:
- N = 200 oscillators (matching dossier)
- omega_i ~ U[-1, 1] (gamma = 1)
- Random init: theta_i ~ U[0, 2*pi]
- Seeded init: theta_i ~ U[-0.3, 0.3]
- K0 = 5 (the largest probed value)
- alpha in {0.0, 0.5, 0.9, 1.0, 1.05, 1.1, 1.2}
- T = 35, dt = 0.05 (vectorized RK1 Euler), R averaged over final 20% of T
- 3 seeds per (alpha, init) combination

EXPECTED (per dossier):
  alpha=0.0 -> R ~ 0.99 (locks)
  alpha=0.5 -> R ~ 0.99 (locks)
  alpha=0.9 -> R ~ 0.99 (locks at K0=5)
  alpha=1.0 -> R ~ 0.69 (partial; threshold pushed above 5)
  alpha=1.1 -> R ~ 0.39 (no macroscopic lock)
  alpha=1.2 -> R ~ 0.06 (disordered)

For alpha=1.2:
  random init -> R ~ 0.06
  seeded init -> R ~ 0.99
"""

import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)

N = 200
gamma = 1.0
dt = 0.05
T = 35.0
n_steps = int(T / dt)
trans_frac = 0.8  # discard first 80%, average over last 20%
n_trans = int(n_steps * trans_frac)
K0 = 5.0
alphas = [0.0, 0.5, 0.9, 1.0, 1.05, 1.1, 1.2]
n_seeds = 3

def run_kura(K0, alpha, init_seed=0, init_mode='random', N=N, gamma=gamma, dt=dt, n_steps=n_steps, n_trans=n_trans):
    rng = np.random.default_rng(init_seed)
    omega = rng.uniform(-gamma, gamma, N)
    if init_mode == 'random':
        theta = rng.uniform(0, 2*np.pi, N)
    elif init_mode == 'seeded':
        theta = rng.uniform(-0.3, 0.3, N)
    else:
        raise ValueError(init_mode)
    R_sum = 0.0
    n_avg = 0
    for t in range(n_steps):
        # Order parameter
        Z = np.mean(np.exp(1j * theta))
        R = abs(Z)
        Psi = np.angle(Z)
        # Effective coupling
        if alpha < 0:
            # careful: R^alpha with alpha<0 and R=0 -> inf. Add epsilon.
            K_eff = K0 * (R + 1e-12)**alpha
        else:
            K_eff = K0 * R**alpha
        # Kuramoto ODE: dtheta_i = omega_i + (K_eff / N) sum_j sin(theta_j - theta_i)
        #                              = -K_eff * R * sin(theta_i - Psi)
        coupling_term = -K_eff * R * np.sin(theta - Psi)
        dtheta = omega + coupling_term
        theta = theta + dt * dtheta
        # Keep theta in [-pi, pi]
        theta = (theta + np.pi) % (2*np.pi) - np.pi
        if t >= n_trans:
            R_sum += R
            n_avg += 1
    return R_sum / n_avg if n_avg > 0 else 0.0

print("DOSSIER-052 REPLICATION")
print("=" * 70)
print(f"N={N}, gamma={gamma}, K0={K0}, dt={dt}, T={T}")
print(f"alphas = {alphas}, n_seeds = {n_seeds}")
print()

results = {}
for init_mode in ['random', 'seeded']:
    results[init_mode] = {}
    print(f"\n[{init_mode.upper()} INIT]")
    print(f"{'alpha':>8} {'R_mean':>10} {'R_std':>10} {'dossier_pred':>15}")
    for alpha in alphas:
        Rs = []
        for seed in range(n_seeds):
            R = run_kura(K0, alpha, init_seed=seed*100+42, init_mode=init_mode)
            Rs.append(R)
        R_mean = np.mean(Rs)
        R_std = np.std(Rs)
        results[init_mode][f'{alpha:.2f}'] = {'mean': float(R_mean), 'std': float(R_std), 'values': [float(r) for r in Rs]}
        # dossier prediction
        if alpha <= 0.9:
            pred = '~0.99'
        elif alpha == 1.0:
            pred = '~0.69'
        elif alpha == 1.1:
            pred = '~0.39'
        elif alpha == 1.2:
            pred = '~0.06 (random) or ~0.99 (seeded)'
        else:
            pred = '-'
        print(f"{alpha:>8.2f} {R_mean:>10.4f} {R_std:>10.4f} {pred:>15}")

# Save
with open('_artifacts/dossier052_alpha_divergence.json', 'w') as f:
    json.dump({'K0': K0, 'N': N, 'gamma': gamma, 'dt': dt, 'T': T,
               'alphas': alphas, 'n_seeds': n_seeds, 'results': results}, f, indent=2)

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
random_means = [results['random'][f'{a:.2f}']['mean'] for a in alphas]
random_stds = [results['random'][f'{a:.2f}']['std'] for a in alphas]
seeded_means = [results['seeded'][f'{a:.2f}']['mean'] for a in alphas]
seeded_stds = [results['seeded'][f'{a:.2f}']['std'] for a in alphas]
ax.errorbar(alphas, random_means, yerr=random_stds, fmt='o-', label='random init', capsize=4)
ax.errorbar(alphas, seeded_means, yerr=seeded_stds, fmt='s--', label='seeded init', capsize=4)
ax.axvline(1.0, color='red', linestyle=':', alpha=0.5, label=r'$\alpha^*=1$ conjecture')
ax.set_xlabel(r'feedback exponent $\alpha$')
ax.set_ylabel(r'steady-state order $R_{ss}$')
ax.set_title(f'Random vs Seeded Initial Conditions (K0={K0}, N={N})')
ax.legend()
ax.grid(alpha=0.3)
ax.set_ylim(-0.05, 1.05)

ax = axes[1]
diffs = [seeded_means[i] - random_means[i] for i in range(len(alphas))]
ax.plot(alphas, diffs, 'D-', color='purple')
ax.axvline(1.0, color='red', linestyle=':', alpha=0.5, label=r'$\alpha^*=1$ conjecture')
ax.axhline(0, color='black', linewidth=0.5)
ax.set_xlabel(r'feedback exponent $\alpha$')
ax.set_ylabel(r'$R_{seeded} - R_{random}$  (basin gap)')
ax.set_title('Basin-Disconnection Diagnostic')
ax.legend()
ax.grid(alpha=0.3)

plt.suptitle(f'DOSSIER-052 Replication: $\\alpha$-Divergence in Reflexive Kuramoto (K0={K0}, N={N})')
plt.tight_layout()
plt.savefig('_artifacts/dossier052_alpha_divergence.png', dpi=110)
print(f"\nPlot saved to _artifacts/dossier052_alpha_divergence.png")

# Final verdict
print("\n" + "=" * 70)
print("VERIFICATION:")
for a in alphas:
    r_rand = results['random'][f'{a:.2f}']['mean']
    r_seed = results['seeded'][f'{a:.2f}']['mean']
    gap = r_seed - r_rand
    print(f"alpha={a:.2f}: random={r_rand:.3f}, seeded={r_seed:.3f}, gap={gap:.3f}")

# Check the alpha* = 1 claim
print("\n" + "=" * 70)
print("ALPHA* CONJECTURE CHECK:")
# At alpha=1.2, gap should be ~ 0.99 - 0.06 = 0.93
alpha_12_rand = results['random']['1.20']['mean']
alpha_12_seed = results['seeded']['1.20']['mean']
print(f"  alpha=1.2: random={alpha_12_rand:.3f}, seeded={alpha_12_seed:.3f}, gap={alpha_12_seed-alpha_12_rand:.3f}")
print(f"  Dossier predicts gap ≈ 0.93 — actual = {alpha_12_seed - alpha_12_rand:.3f}")