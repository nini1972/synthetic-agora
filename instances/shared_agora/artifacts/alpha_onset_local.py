"""Lean local version: deepseek cells + bug alpha=0 test only."""
import numpy as np, json

def run(N, alpha, K0, T=35.0, dt=0.02, seeds=8, seed0=31337, bug=False):
    rng = np.random.default_rng(seed0 + N + int(alpha * 10))
    n = int(round(T / dt)); meds = []
    for s in range(seeds):
        th = rng.uniform(0, 2 * np.pi, N)
        om = rng.uniform(-1, 1, N)
        acc = 0.0; nacc = 0
        for step in range(n):
            R = np.hypot(th.__len__() and np.cos(th).mean(), np.sin(th).mean())
            psi = np.arctan2(np.sin(th).mean(), np.cos(th).mean())
            K = K0 * R ** (alpha + 1.0) if bug else K0 * R ** alpha
            th = th + dt * (om - K * np.sin(th - psi))
            if step > n // 2: acc += R; nacc += 1
        meds.append(acc / nacc)
    return float(np.median(meds))

print("Part 2: deepseek cells (N=200, K0=5, T=35, 8 seeds):")
ds = {}
for a in (1.8, 2.0, 2.2, 2.5):
    r = run(200, a, 5.0)
    ds[str(a)] = r
    print(f"  alpha={a}: R_med={r:.3f}")

print("\nPart 3: alpha=0, K0=2, N=800, T=80:")
r_bug = run(800, 0.0, 2.0, bug=True, seeds=6, seed0=999)
r_cor = run(800, 0.0, 2.0, bug=False, seeds=6, seed0=999)
print(f"  extra-R: R_med={r_bug:.3f}   correct: R_med={r_cor:.3f}")
json.dump({'deepseek_rep': ds, 'bug_alpha0': {'bug': r_bug, 'correct': r_cor}},
          open('alpha_onset_local.json', 'w'), indent=1)
print("saved alpha_onset_local.json")