"""Fine scan around alpha=1 to locate the transition."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

N = 200
gamma = 1.0
dt = 0.02
T = 50.0  # longer integration to ensure steady state
n_steps = int(T / dt)
trans = int(n_steps * 0.8)
K0 = 5.0

def run(K0, alpha, init_seed=0, init_mode='random', N=N, gamma=gamma, dt=dt, n_steps=n_steps, trans=trans):
    rng = np.random.default_rng(init_seed)
    omega = rng.uniform(-gamma, gamma, N)
    if init_mode == 'random':
        theta = rng.uniform(0, 2*np.pi, N)
    else:
        theta = rng.uniform(-0.3, 0.3, N)
    R_sum = 0.0
    n_avg = 0
    for t in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = abs(Z)
        Psi = np.angle(Z)
        K_eff = K0 * (R + 1e-12 if alpha < 0 else R)**alpha if alpha >= 0 else K0 * (R + 1e-12)**alpha
        coupling_term = -K_eff * R * np.sin(theta - Psi)
        dtheta = omega + coupling_term
        theta = theta + dt * dtheta
        theta = (theta + np.pi) % (2*np.pi) - np.pi
        if t >= trans:
            R_sum += R
            n_avg += 1
    return R_sum / n_avg

# Fine scan
alphas = [0.90, 0.95, 0.98, 1.00, 1.02, 1.05, 1.08, 1.10, 1.12, 1.15, 1.20]
n_seeds = 5
random_R = []
seeded_R = []
for a in alphas:
    rr = [run(K0, a, init_seed=s*100, init_mode='random') for s in range(n_seeds)]
    sr = [run(K0, a, init_seed=s*100, init_mode='seeded') for s in range(n_seeds)]
    random_R.append({'mean': float(np.mean(rr)), 'std': float(np.std(rr))})
    seeded_R.append({'mean': float(np.mean(sr)), 'std': float(np.std(sr))})
    print(f"alpha={a:.3f}: random={np.mean(rr):.3f}±{np.std(rr):.3f}, seeded={np.mean(sr):.3f}±{np.std(sr):.3f}")

with open('dossier052_finescan.json', 'w') as f:
    json.dump({'K0': K0, 'alphas': alphas, 'random': random_R, 'seeded': seeded_R}, f, indent=2)

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.errorbar(alphas, [r['mean'] for r in random_R], yerr=[r['std'] for r in random_R],
            fmt='o-', label='random init', capsize=4, color='blue')
ax.errorbar(alphas, [r['mean'] for r in seeded_R], yerr=[r['std'] for r in seeded_R],
            fmt='s--', label='seeded init', capsize=4, color='orange')
ax.axvline(1.0, color='red', linestyle=':', linewidth=2, label=r'$\alpha^*=1$ conjecture')
ax.fill_between([0.9, 1.15], 0, 1.0, alpha=0.05, color='red')
ax.set_xlabel(r'feedback exponent $\alpha$', fontsize=13)
ax.set_ylabel(r'steady-state order $R_{ss}$', fontsize=13)
ax.set_title(f'FINE SCAN: Basin-Disconnection Transition (K0={K0}, N={N}, T={T})')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
ax.set_ylim(-0.05, 1.05)
plt.tight_layout()
plt.savefig('dossier052_finescan.png', dpi=120)
print("Saved dossier052_finescan.png")

# Identify the crossover alpha
print("\nCrossover analysis:")
gaps = [seeded_R[i]['mean'] - random_R[i]['mean'] for i in range(len(alphas))]
for i, a in enumerate(alphas):
    print(f"  alpha={a:.3f}: gap = {gaps[i]:.3f}")
# Where gap > 0.5?
critical = None
for i, a in enumerate(alphas):
    if gaps[i] > 0.5 and (i == 0 or gaps[i-1] <= 0.5):
        critical = a
        break
print(f"\nCrossover alpha (gap > 0.5): {critical}")