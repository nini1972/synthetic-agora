import numpy as np

def sim_alpha(N, alpha, K0, T=35.0, dt=0.02, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, N)
    omega = rng.uniform(-1, 1, N)
    n_steps = int(T/dt)
    for _ in range(n_steps):
        z = np.exp(1j*theta).mean()
        R = abs(z)
        Psi = np.angle(z)
        Keff = K0 * R**alpha
        theta += (omega - Keff*np.sin(theta-Psi))*dt
    return abs(np.exp(1j*theta).mean())

alphas = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5]
Ns = [200, 500, 1000, 2000, 5000]
K0 = 5.0
print("alpha_onset scan (DOCUMENTED model, no extra-R bug):")
print("N\\alpha", "  ".join(f"{a:.1f}" for a in alphas))
for N in Ns:
    row = []
    for a in alphas:
        vals = [sim_alpha(N, a, K0, seed=s) for s in range(3)]
        row.append(f"{np.mean(vals):.3f}")
    print(f"{N:5d}", "  ".join(row))
