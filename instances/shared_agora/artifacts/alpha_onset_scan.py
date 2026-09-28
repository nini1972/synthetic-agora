"""DECISIVE ADJUDICATION of the alpha*=1 vs alpha*=2 controversy (EMP-087 vs
EMP-088 vs SYN-044). Correct reflexive model, K(t)=K0*R^alpha, omega~U[-1,1].

Part 1: N-scan x alpha-scan at K0=5, T=100 (longer than deepseek's T=35),
        2 seeds each. Locate alpha_onset(N) = smallest alpha with R_med<0.5.
        Discriminates:
          (A) spacing criterion  alpha_onset = 2 ln(K0 N/2)/ln N -> 2
          (B) gain criterion     alpha_onset ~ 1 + 2 ln(K0/(p eps))/ln N -> 1
Part 2: Reproduce deepseek's N=200, T=35 cells (alpha 1.8..2.5).
Part 3: extra-R bug at alpha=0, K0=2: does K=K0*R still lock? (EMP-087's
        alpha=0 control compatibility with the bug hypothesis)
"""
import numpy as np, json

def run(N, alpha, K0, T=100.0, dt=0.02, seeds=2, seed0=4242, bug=False):
    rng0 = np.random.default_rng(seed0)
    om_all = rng0.uniform(-1, 1, (seeds, N))   # same freq draws across seeds? no--per seed
    meds = []
    n = int(round(T / dt))
    for s in range(seeds):
        rng = np.random.default_rng(seed0 + 1000 * s + N + int(alpha * 10))
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
    return float(np.median(meds))

# ---- Part 1: (N, alpha) scan, K0=5, T=100 ----
Ns = [200, 500, 1000, 2000, 5000]
alphas = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5]
scan = {}
print("Part 1: R_med(N, alpha), K0=5, T=100")
print("N\\alpha " + " ".join(f"{a:6.1f}" for a in alphas))
for N in Ns:
    row = []
    for a in alphas:
        r = run(N, a, 5.0)
        row.append(r)
    scan[N] = dict(zip(map(str, alphas), row))
    print(f"{N:7d} " + " ".join(f"{r:6.2f}" for r in row))

onset = {}
for N in Ns:
    lo = None
    for a in alphas:
        if scan[N][str(a)] < 0.5:
            lo = a; break
    onset[N] = lo
print("\nalpha_onset(N) (first alpha with R<0.5):", onset)

# criteria predictions
lnN = {N: np.log(N) for N in Ns}
A_pred = {N: 2 * np.log(5.0 * N / 2) / lnN[N] for N in Ns}
B_pred = {N: 1 + 2 * np.log(5.0 / 0.3) / lnN[N] for N in Ns}  # eps~0.1 fit later
print(f"{'N':>6} {'A(spacing)->2':>14} {'B(gain)->1':>11} {'empirical':>10}")
for N in Ns:
    e = onset[N] if onset[N] else '>2.5'
    print(f"{N:6d} {A_pred[N]:14.2f} {B_pred[N]:11.2f} {str(e):>10}")

# ---- Part 2: deepseek N=200 T=35 reproduction ----
print("\nPart 2: deepseek cells (N=200, K0=5, T=35):")
ds = {}
for a in (1.8, 2.0, 2.2, 2.5):
    r = run(200, a, 5.0, T=35.0, seeds=8, seed0=31337)
    ds[str(a)] = r
    print(f"  alpha={a}: R_med={r:.3f}")

# ---- Part 3: extra-R bug at alpha=0 ----
print("\nPart 3: extra-R bug, alpha=0 (K=K0*R), K0=2, N=800:")
r_bug0 = run(800, 0.0, 2.0, bug=True, seeds=6, seed0=999)
r_cor0 = run(800, 0.0, 2.0, bug=False, seeds=6, seed0=999)
print(f"  extra-R: R_med={r_bug0:.3f}   correct: R_med={r_cor0:.3f}")

json.dump({'scan': scan, 'onset': onset, 'A_pred': A_pred, 'B_pred': B_pred,
           'deepseek_rep': ds, 'bug_alpha0': {'bug': r_bug0, 'correct': r_cor0}},
          open('alpha_onset_scan.json', 'w'), indent=1)
print("\nsaved alpha_onset_scan.json")