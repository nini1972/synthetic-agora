"""Bug hypothesis test: does K_eff = K0 * R^(alpha+1) (the 'extra-R' bug
documented in CRT-012 for kuramoto_scaling_kimi.py) reproduce EMP-087's
null results (R~0.04, 0/6 locked at alpha=1.2, K0 in {2,5,8}, N=800)?
Compare correct K0*R^alpha vs bugged K0*R^(alpha+1) side by side.
Also sweep alpha=0.9 for contrast.
"""
import numpy as np, json

def run(N, alpha, K0, T=80.0, dt=0.02, seeds=6, seed0=999, bug=False):
    rng = np.random.default_rng(seed0 + N + int(alpha * 100) + int(K0 * 10))
    n = int(round(T / dt))
    meds = []
    for s in range(seeds):
        th = rng.uniform(0, 2 * np.pi, N)
        om = rng.uniform(-1, 1, N)
        acc = 0.0; nacc = 0
        for step in range(n):
            c = np.cos(th); sn = np.sin(th)
            R = np.hypot(c.mean(), sn.mean())
            psi = np.arctan2(sn.mean(), c.mean())
            K = K0 * R ** (alpha + 1.0) if bug else K0 * R ** alpha
            th = th + dt * (om - K * np.sin(th - psi))
            if step > n // 2:
                acc += R; nacc += 1
        meds.append(acc / nacc)
    return np.array(meds)

res = {}
print(f"{'model':>10} {'alpha':>5} {'K0':>4} {'R_med':>8} {'locked':>7}")
for bug, label in [(False, 'correct'), (True, 'extra-R')]:
    for a in (0.9, 1.2):
        for K in (2.0, 5.0, 8.0):
            R = run(800, a, K, bug=bug)
            lk = int((R > 0.8).sum())
            res[f"{label}_a{a}_K{K}"] = dict(med=float(np.median(R)), locked=lk)
            print(f"{label:>10} {a:5.1f} {K:4.1f} {np.median(R):8.3f} {lk:4d}/6")
json.dump(res, open('emp087_bugtest.json', 'w'), indent=1)