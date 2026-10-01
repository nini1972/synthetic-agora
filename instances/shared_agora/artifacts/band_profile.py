import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sim_alpha_vec(N, alpha, K0, T=20.0, dt=0.02, n_seed=4):
    rng = np.random.default_rng(42)
    theta = rng.uniform(0, 2*np.pi, (n_seed, N))
    omega = rng.uniform(-1, 1, (n_seed, N))
    n_steps = int(T/dt)
    for _ in range(n_steps):
        z = np.exp(1j*theta).mean(axis=1)
        R = np.abs(z); Psi = np.angle(z)
        Keff = K0 * R**alpha
        theta += (omega - Keff[:,None]*np.sin(theta-Psi[:,None]))*dt
    return np.abs(np.exp(1j*theta).mean(axis=1))

K0 = 5.0
fig, axes = plt.subplots(1, 3, figsize=(16,5), sharey=True)
for ax, N in zip(axes, [200, 800, 3200]):
    alphas = np.linspace(0.0, 2.6, 27)
    Rm = []
    for a in alphas:
        Rv = sim_alpha_vec(N, a, K0, n_seed=4)
        Rm.append(Rv.mean())
    Rm = np.array(Rm)
    ax.plot(alphas, Rm, 'o-', label=f'N={N}')
    ax.axhline(0.5, color='gray', ls=':')
    ax.set_xlabel('alpha'); ax.set_ylabel('R')
    ax.set_title(f'N={N}: sync band upper edge={alphas[np.argmax(Rm>0.5)] if (Rm>0.5).any() else "none"}')
    ax.grid(True)
    # find edges
    above = Rm > 0.5
    if above.any():
        idx = np.where(above)[0]
        lo, hi = alphas[idx[0]], alphas[idx[-1]]
        print(f"N={N}: sync band = [{lo:.2f}, {hi:.2f}]")
plt.legend()
plt.tight_layout()
plt.savefig('band_profile.png', dpi=100, bbox_inches='tight')
print("saved band_profile.png")
