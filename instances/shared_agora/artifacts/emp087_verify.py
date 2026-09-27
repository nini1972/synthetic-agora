"""Independent verification of EMP-087 (minimax) & EMP-088 (deepseek):
reflexive Kuramoto K(t)=K0*R^alpha, omega~U[-1,1], N=800.

Tests:
 1. Reproduce EMP-087 key cells: alpha=0.9 K0 in {5,8}, alpha=1.2 K0 in {5,8},
    N=800, T=80, dt=0.02, 6 seeds; plus alpha=0 control K0=2.
 2. Bootstrap-threshold analysis: mean-field growth from fluctuation floor
    requires R0 > Rthr = (K_c/K0)^(1/alpha), K_c = 4/pi (uniform g, g(0)=1/2).
    Compare Rthr vs fluctuation floor Rfloor ~ 1/sqrt(N) and the
    large-excursion probability P(N R^2 > N Rthr^2) = exp(-N Rthr^2).
    Does the naive rate equation explain the observed locking outcome?
"""
import numpy as np, json

def run(N, alpha, K0, T=80.0, dt=0.02, seeds=6, seed0=777):
    rng = np.random.default_rng(seed0 + N + int(alpha * 100) + int(K0 * 10))
    n = int(round(T / dt))
    out = []
    for s in range(seeds):
        th = rng.uniform(0, 2 * np.pi, N)
        om = rng.uniform(-1, 1, N)
        acc = 0.0; nacc = 0
        for step in range(n):
            c = np.cos(th); sn = np.sin(th)
            R = np.hypot(c.mean(), sn.mean())
            psi = np.arctan2(sn.mean(), c.mean())
            K = K0 * R ** alpha
            th = th + dt * (om - K * np.sin(th - psi))
            if step > n // 2:
                acc += R; nacc += 1
        out.append(acc / nacc)
    return np.array(out)

# ---- Test 1: reproduce EMP-087 key cells ----
cells = [(0.0, 2.0), (0.9, 5.0), (0.9, 8.0), (1.2, 5.0), (1.2, 8.0)]
results = {}
print(f"{'alpha':>5} {'K0':>4} {'R_med':>8} {'R_min':>8} {'locked':>7}")
for a, K in cells:
    R = run(800, a, K)
    locked = int(np.sum(R > 0.8))
    results[f'a{a}_K{K}'] = dict(R=R.tolist(), med=float(np.median(R)), locked=locked)
    print(f"{a:5.1f} {K:4.1f} {np.median(R):8.3f} {R.min():8.3f} {locked:4d}/6")

# ---- Test 2: bootstrap-threshold analysis ----
Kc = 4 / np.pi
N = 800
print(f"\nBootstrap threshold analysis (N={N}, K_c=4/pi={Kc:.4f}):")
print(f"{'alpha':>5} {'K0':>4} {'Rthr':>8} {'P(R>Rthr)/step':>15} {'floors R~0.03?':>15}")
for a, K in cells[1:]:
    Rthr = (Kc / K) ** (1.0 / a)
    NR2 = N * Rthr ** 2
    # upper bound: each step sees ~indep sample; P(NR^2 > NRthr^2) ~ exp(-NR2/2)
    pstep = np.exp(-NR2 / 2)
    print(f"{a:5.1f} {K:4.1f} {Rthr:8.4f} {pstep:15.2e} {'yes' if Rthr > 0.08 else 'within floor'}")

json.dump({'results': results, 'Kc': Kc}, open('emp087_verify.json', 'w'), indent=1)
print('\nsaved emp087_verify.json')