import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sim_alpha_vec(N, alpha, K0, T=20.0, dt=0.02, n_seed=3):
    rng = np.random.default_rng(999)
    theta = rng.uniform(0, 2*np.pi, (n_seed, N))
    omega = rng.uniform(-1, 1, (n_seed, N))
    n_steps = int(T/dt)
    for _ in range(n_steps):
        z = np.exp(1j*theta).mean(axis=1)
        R = np.abs(z); Psi = np.angle(z)
        Keff = K0 * R**alpha
        theta += (omega - Keff[:,None]*np.sin(theta-Psi[:,None]))*dt
    return np.abs(np.exp(1j*theta).mean(axis=1))

N = 3200
K0 = 5.0
alphas = np.linspace(1.0, 2.2, 13)
onset = None
for a in alphas:
    Rvals = sim_alpha_vec(N, a, K0, n_seed=3)
    print(f"N={N} alpha={a:.2f} Rmean={Rvals.mean():.3f}", flush=True)
    if Rvals.mean() > 0.5:
        onset = a
print(f"ONSET N=3200: {onset}")
