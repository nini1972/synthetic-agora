import numpy as np

def R_ss(K0, alpha, omega_std, N=1000, dt=0.05, T=60.0, seed=0):
    rng = np.random.default_rng(1000 + seed)
    th = rng.uniform(0, 2*np.pi, N)
    om = rng.normal(0, omega_std, N) if omega_std > 0 else np.zeros(N)
    ns = int(T/dt); acc = 0.0
    for i in range(ns):
        cm, sm = np.cos(th).mean(), np.sin(th).mean()
        R = np.hypot(cm, sm); psi = np.arctan2(sm, cm)
        Keff = K0 if alpha == 0.0 else K0*(R**alpha if R > 1e-12 else 0.0)
        th += dt * (om + Keff * np.sin(psi - th))
        if i > ns//3: acc += R
    return acc/(ns - ns//3)

# check omega sample statistics
rng = np.random.default_rng(1000)
om = rng.normal(0, 0.7, 1000)
print(f'omega sample: mean={om.mean():.4f} std={om.std():.4f} min={om.min():.3f} max={om.max():.3f}')
print(f'theory Kc(sigma=0.7) = {1.5958*0.7:.3f}')
print()
print('K0    R(alpha=0)   R(alpha=1)')
for K in [0.1,0.3,0.5,0.7,0.9,1.1,1.3,1.5,1.8,2.2]:
    r0 = R_ss(K, 0.0, 0.7, seed=1)
    r1 = R_ss(K, 1.0, 0.7, seed=1)
    print(f'{K:4.1f}  {r0:.3f}      {r1:.3f}')