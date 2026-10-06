import numpy as np

def traj(K0, alpha, omega_std, N=1000, dt=0.05, T=100.0, seed=1):
    rng = np.random.default_rng(1000 + seed)
    th = rng.uniform(0, 2*np.pi, N)
    om = rng.normal(0, omega_std, N) if omega_std > 0 else np.zeros(N)
    ns = int(T/dt); Rs = []
    for i in range(ns):
        cm, sm = np.cos(th).mean(), np.sin(th).mean()
        R = np.hypot(cm, sm); psi = np.arctan2(sm, cm)
        Keff = K0 if alpha == 0.0 else K0*(R**alpha if R > 1e-12 else 0.0)
        th += dt * (om + Keff * np.sin(psi - th))
        if i % 50 == 0: Rs.append(round(float(R), 3))   # every 2.5 time units
    return Rs

for K in [0.2, 0.5, 1.3]:
    r = traj(K, 0.0, 0.7)
    print(f'K={K}: R(t) sampled every 2.5tu:\n  {r}\n')