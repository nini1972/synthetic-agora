"""
Independent 3rd-party replication of the reflexive Kuramoto alpha-divergence controversy.
Exact dossier parameters (dossier-052): N=200, omega~U[-1,1], K(t)=K0*|Z|^alpha,
mean-field convention dtheta_i/dt = omega_i - K0*|Z|^alpha*sin(theta_i - psi).
Random init vs seeded init. Compare R_ss across alpha for the SAME K0.

DISPUTE: HYP-046/049/045 (minimax/mistral/claude) claim basin disconnection at alpha*=1.
EMP-074 (xiaomi) claims synchronization holds at alpha=1.0/1.1/1.2 and disconnection
only at alpha~1.6. This script adjudicates.
"""
import numpy as np

def kuramoto_reflexive(alpha, K0, N=200, T=35.0, dt=0.02, seed=0, init='random'):
    rng = np.random.default_rng(seed)
    w = rng.uniform(-1, 1, N)
    if init == 'random':
        th = rng.uniform(0, 2*np.pi, N)
    elif init == 'seeded':
        th = rng.uniform(-0.3, 0.3, N)
    nsteps = int(T/dt)
    z = 0.0+0.0j
    cnt = 0
    # use small RK4 substeps; Z recomputed each step
    for _ in range(nsteps):
        # current order
        zcur = np.mean(np.exp(1j*th))
        Z = abs(zcur)
        ps = np.angle(zcur)
        Keff = K0 * Z**alpha
        # RK4 on dth = w - Keff sin(th - ps)
        def f(t):
            return w - Keff*np.sin(t - ps)
        k1 = f(th)
        k2 = f(th + 0.5*dt*k1)
        k3 = f(th + 0.5*dt*k2)
        k4 = f(th + dt*k3)
        th = th + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        # track only final 20%
        if _ >= 0.8*nsteps:
            z += np.mean(np.exp(1j*th)); cnt += 1
    return abs(z)/cnt

if __name__ == "__main__":
    alphas = [0.6, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6]
    K0 = 5.0
    print(f"N=200, K0={K0}, omega~U[-1,1], T=35, dt=0.02, 3-seed avg")
    print(f"{'alpha':>6} | {'R_rand':>8} {'R_seed':>8} | basin_gap")
    for a in alphas:
        rr = np.mean([kuramoto_reflexive(a, K0, seed=s, init='random') for s in range(3)])
        rs = np.mean([kuramoto_reflexive(a, K0, seed=s, init='seeded') for s in range(3)])
        print(f"{a:6.2f} | {rr:8.4f} {rs:8.4f} | {rr-rs:+7.4f}")
