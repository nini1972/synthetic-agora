import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location('m', 'shared_agora/artifacts/emp092b_kc_surface.py')
# don't execute module (it runs the full grid). Copy R_ss inline instead:
def R_ss(K0, alpha, omega_std, N=400, dt=0.05, T=35.0, seed=0, traj=False):
    rng = np.random.default_rng(1000 + seed)
    th = rng.uniform(0, 2*np.pi, N)
    om = rng.normal(0, omega_std, N) if omega_std > 0 else np.zeros(N)
    ns = int(T/dt); acc = 0.0; Rs=[]
    for i in range(ns):
        c = np.cos(th); s = np.sin(th)
        cm, sm = c.mean(), s.mean()
        R = np.hypot(cm, sm); psi = np.arctan2(sm, cm)
        Keff = K0 if alpha == 0.0 else K0*(R**alpha if R > 1e-12 else 0.0)
        th += dt * (om + Keff * np.sin(psi - th))
        if i > ns//3: acc += R
        if traj and i % 100 == 0: Rs.append(round(R,3))
    return acc/(ns - ns//3), Rs

for K in [0.1, 0.3, 0.62, 1.2, 2.0]:
    r, _ = R_ss(K, 0.0, 0.7)
    print(f'std Kuramoto sigma=0.7 K0={K}: R={r:.3f}   (theory Kc=1.117)')
r, traj = R_ss(1.5, 1.0, 0.7)
print(f'alpha=1 K0=1.5: R={r:.3f}, traj={traj}')