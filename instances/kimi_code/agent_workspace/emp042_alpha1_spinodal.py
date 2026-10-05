import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, time

np.random.seed(42)
N = 200
sigma = 0.1
alpha = 1.0
dt = 0.02
T_per = 40.0
T_trans = 20.0
trans_steps = int(T_trans / dt)
per_steps = int(T_per / dt)
K_grid = np.arange(0.5, 4.51, 0.2)
n_seeds = 15

omega = sigma * np.random.randn(N)

def integrate(theta, omega, K0, steps):
    for _ in range(steps):
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        Psi = np.angle(z)
        theta += dt * (omega + K0 * (R ** alpha) * np.sin(Psi - theta))
    return theta

all_R = np.zeros((n_seeds, len(K_grid)))
for s in range(n_seeds):
    theta = np.random.rand(N) * 2 * np.pi
    theta = integrate(theta, omega, K_grid[0], trans_steps)
    for ik, K in enumerate(K_grid):
        theta = integrate(theta, omega, K, per_steps)
        z = np.mean(np.exp(1j * theta))
        all_R[s, ik] = np.abs(z)

mean_R = all_R.mean(axis=0)
high_frac = (all_R > 0.5).mean(axis=0)

# find jump
jump_K = None
for i in range(1, len(K_grid)):
    if mean_R[i] > 0.4 and mean_R[i-1] < 0.4:
        jump_K = K_grid[i]
        break

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for s in range(n_seeds):
    axes[0].plot(K_grid, all_R[s], 'k-', alpha=0.2)
axes[0].plot(K_grid, mean_R, 'r-', lw=2, label='mean')
axes[0].axhline(0.5, color='gray', ls='--')
axes[0].set_xlabel('K')
axes[0].set_ylabel('R')
axes[0].set_title(f'Forward noisy sweep α={alpha}, {n_seeds} seeds')
axes[0].legend()

axes[1].plot(K_grid, high_frac, 'b-o', lw=2)
axes[1].set_xlabel('K')
axes[1].set_ylabel('fraction R>0.5')
axes[1].set_title(f'Spinodal transition (jump K ≈ {jump_K})')
axes[1].set_ylim(-0.05, 1.05)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/emp042_alpha1_spinodal.png', dpi=150)
plt.close()

out = {
    'N': N, 'alpha': alpha, 'dt': dt, 'T_per': T_per, 'T_trans': T_trans,
    'n_seeds': n_seeds, 'K_grid': K_grid.tolist(),
    'mean_R': mean_R.tolist(), 'high_fraction': high_frac.tolist(),
    'jump_K': jump_K
}
with open('../../shared_agora/artifacts/emp042_alpha1_spinodal.json', 'w') as f:
    json.dump(out, f, indent=2)
print('jump_K', jump_K)
print('mean_R', mean_R)
print('high_frac', high_frac)
