"""
CORRECTED INDEPENDENT REPLICATION of HYP-126.
==============================================
Previous version had a bug: I wrote a linear diffusive smoother without the
inner logistic map. Without the f(x) = 4x(1-x) the system relaxes to a
constant and 'f=0.5000' was a floating-point artifact, not a dynamical lock.
Discarding those results and re-running with the proper nonlinear CML.

Proper CML:  x_i^{n+1} = (1-eps)*f(x_i^n) + (eps/2)*(f(x_{i-1}^n) + f(x_{i+1}^n))
with f(x) = 4x(1-x).

Frame metric (re-defined cleanly):
   f in [0, 0.5]  = 0.5 * (fraction of consecutive normalized frames that differ)
                    0.5 = every frame flips = strict period-2 in the spatial pattern
                    0.25 = period-4 / subharmonic band hop
   Delta_2 = mean over n of ||x^{n+2} - x^n||_inf  -> 0 iff period-2 is exact.
"""
import numpy as np
import json


def cml_step(x, eps, bc):
    f = 4.0*x*(1.0 - x)
    N = len(x)
    if bc == "periodic":
        L = np.roll(f, 1); R = np.roll(f, -1)
    elif bc == "open":
        L = np.empty(N); L[0] = 0.0;  L[1:] = f[:-1]
        R = np.empty(N); R[-1] = 0.0; R[:-1] = f[1:]
    return (1.0 - eps)*f + 0.5*eps*(L + R)


def run(N, eps, bc, seed, n_transient=600, n_measure=1200):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, N)
    for _ in range(n_transient):
        x = cml_step(x, eps, bc)
    # history ring of length 2
    history = [x.copy(), cml_step(x, eps, bc)]
    flips, total = 0, 0
    d2s = []
    prev = history[1]/np.linalg.norm(history[1])
    for step in range(n_measure - 1):
        x_next = cml_step(history[-1], eps, bc)
        history.append(x_next)
        # Delta_2 between states two steps apart
        d2s.append(np.mean(np.abs(history[-1] - history[-3])))
        cur = x_next/np.linalg.norm(x_next)
        flips += int(np.linalg.norm(cur - prev) > 1e-3)
        total += 1
        prev = cur
    f_val = 0.5*flips/total if total else 0.0
    d2 = float(np.mean(d2s)) if d2s else float('nan')
    return f_val, d2, history[-1]  # final state for amplitude check


if __name__ == '__main__':
    print("="*78)
    print("HYP-126 CORRECTED REPLICATION  (proper nonlinear CML with f(x)=4x(1-x))")
    print("="*78)
    results = []
    print(f"\n{'BC':>10} {'N':>4} {'eps':>5} {'f':>8} {'Delta_2':>11}  final-state-amplitude")
    print("-"*78)
    for bc in ["periodic", "open"]:
        for N in [32, 48, 64, 96, 128]:
            for eps in [0.10, 0.20, 0.35, 0.50]:
                fs, ds, amplitudes = [], [], []
                for s in range(3):
                    f, d2, x = run(N, eps, bc, seed=1000*s + N + int(eps*100))
                    fs.append(f); ds.append(d2)
                    amplitudes.append(float(np.std(x)))
                fm, dm = np.mean(fs), np.mean(ds)
                amp = np.mean(amplitudes)
                if amp < 1e-4:
                    tag = "DEAD (constant fp)"
                elif fm > 0.49 and dm < 0.02:
                    tag = "NYQUIST-LOCK"
                elif 0.20 < fm < 0.32:
                    tag = "subharmonic"
                else:
                    tag = f"f={fm:.3f}"
                results.append(dict(bc=bc, N=N, eps=eps, f=fm, d2=dm, amp=amp, tag=tag))
                print(f"{bc:>10} {N:>4} {eps:>5} {fm:>8.4f} {dm:>11.2e} "
                      f"amp={amp:.3f}  {tag}")
    with open('hyp126_proper_replication.json', 'w') as fh:
        json.dump(results, fh, indent=2)
    print("\nSaved -> hyp126_proper_replication.json")