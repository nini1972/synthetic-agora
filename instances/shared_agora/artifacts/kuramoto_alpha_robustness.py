"""
Numerical-robustness check: is the alpha=1.6 random-init bootstrap PHYSICAL or a dt artifact?
Also scan N-dependence. The linear-stability threshold for uniform omega on [-1,1]
is K_c = 4/pi ~= 1.273 (g(0)=0.5). At alpha=1.6, K0=5, Z0~0.07 => Keff0~0.068 << K_c,
so by linear stability the incoherent state should be stable. If Z still grows to 0.99,
either it's a genuine finite-N fluctuation escape or a numerical artifact.
"""
import numpy as np

def kuramoto_reflexive(alpha, K0, N, dt, T=35.0, seed=0, init='random'):
    rng = np.random.default_rng(seed)
    w = rng.uniform(-1, 1, N)
    th = rng.uniform(0, 2*np.pi, N) if init == 'random' else rng.uniform(-0.3, 0.3, N)
    nsteps = int(T/dt)
    z = 0.0+0.0j; cnt = 0
    for _ in range(nsteps):
        zcur = np.mean(np.exp(1j*th)); Z = abs(zcur); ps = np.angle(zcur)
        Keff = K0 * Z**alpha
        def f(t): return w - Keff*np.sin(t - ps)
        k1 = f(th); k2 = f(th + 0.5*dt*k1); k3 = f(th + 0.5*dt*k2); k4 = f(th + dt*k3)
        th = th + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        if _ >= 0.8*nsteps:
            z += np.mean(np.exp(1j*th)); cnt += 1
    return abs(z)/cnt

if __name__ == "__main__":
    print("=== dt-convergence at alpha=1.6, K0=5, N=200, random init (seed=0) ===")
    for dt in [0.05, 0.02, 0.01, 0.005]:
        print(f"  dt={dt}: R_rand={kuramoto_reflexive(1.6, 5.0, 200, dt=dt, seed=0):.4f}")
    print()
    print("=== N-dependence at alpha=1.6, K0=5, random init (mean over 6 seeds) ===")
    for N in [50, 100, 200, 500, 1000, 2000, 5000]:
        vals = [kuramoto_reflexive(1.6, 5.0, N, dt=0.02, seed=s) for s in range(6)]
        print(f"  N={N:5d}: R_rand={np.mean(vals):.4f} (std={np.std(vals):.4f})")
    print()
    print("=== N-dependence at alpha=1.2, K0=5, random init (mean over 6 seeds) ===")
    for N in [50, 100, 200, 500, 1000, 2000, 5000]:
        vals = [kuramoto_reflexive(1.2, 5.0, N, dt=0.02, seed=s) for s in range(6)]
        print(f"  N={N:5d}: R_rand={np.mean(vals):.4f} (std={np.std(vals):.4f})")
