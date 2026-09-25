"""
Robust multi-seed adjudication of reflexive Kuramoto alpha-divergence.
Determines where the random-init basin truly disconnects at N=200, K0=5.
Uses 8 seeds per alpha for statistical robustness. Reports mean + std of R_rand.
"""
import numpy as np

def kuramoto_reflexive(alpha, K0, N=200, T=35.0, dt=0.02, seed=0, init='random'):
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
    alphas = [1.0, 1.1, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0, 2.2, 2.5]
    K0 = 5.0; seeds = range(8)
    print(f"N=200, K0={K0}, T=35, dt=0.02, {len(list(seeds))} seeds. R_rand mean+/-std")
    print(f"{'alpha':>6} | {'R_rand_mean':>11} {'std':>6} | {'R_seed_mean':>11} | gap")
    for a in alphas:
        rr = [kuramoto_reflexive(a, K0, seed=s, init='random') for s in range(8)]
        rs = [kuramoto_reflexive(a, K0, seed=s, init='seeded') for s in range(8)]
        m, sd = np.mean(rr), np.std(rr)
        ms = np.mean(rs)
        print(f"{a:6.2f} | {m:11.4f} {sd:6.4f} | {ms:11.4f} | {m-ms:+7.4f}")
