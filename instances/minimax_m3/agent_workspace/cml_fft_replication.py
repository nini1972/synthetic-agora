"""
HYP-126 REPLICATION -- CORRECTED METRICS
=========================================
Earlier metric (normalized-frame Hamming distance) saturated at 0.5 for any
chaotic attractor -- it was measuring whether two random points on a sphere
are different, which is always true in high dim. Replacing with three metrics
that actually test the *dynamical* claim of HYP-126:

  (1) Single-site temporal power spectrum P(f). A period-2 lock means a
      spectral peak at f = 1/2 exactly (Nyquist). A period-4 lock means
      a peak at f = 1/4.
  (2) Spatial anti-phase correlation rho_anti = corr(x_i, x_{i+N/2}) if N even.
      True period-2 anti-phase gives rho_anti ~ -1.
  (3) True Delta_2 = ||x^{n+2} - x^n||_inf  over the attractor -- ZERO iff
      period-2 holds exactly on every site.
"""
import numpy as np
import json


def cml_step(x, eps, bc):
    """Two standard variants; HYP-126 is ambiguous which."""
    f = 4.0*x*(1.0 - x)
    N = len(x)
    if bc == "periodic":
        L = np.roll(f, 1); R = np.roll(f, -1)
    elif bc == "open":
        L = np.empty(N); L[0] = 0.0;  L[1:] = f[:-1]
        R = np.empty(N); R[-1] = 0.0; R[:-1] = f[1:]
    return (1.0 - eps)*f + 0.5*eps*(L + R)


def measure(x_attractor, eps, bc):
    """Take a list of 2048 stored spatial snapshots, return metrics."""
    arr = np.asarray(x_attractor)  # shape (T, N)
    T, N = arr.shape
    # ---- (1) FFT peak of a single central site
    site = arr[:, N//2]
    site = site - site.mean()
    spec = np.abs(np.fft.rfft(site))**2
    freqs = np.fft.rfftfreq(T)
    if spec.max() == 0:
        peak_f = 0.0
    else:
        peak_f = freqs[np.argmax(spec[1:]) + 1]  # ignore DC
    # ---- (2) Spatial anti-phase correlation (only if N even)
    if N % 2 == 0:
        left  = arr.mean(axis=0)[:N//2]
        right = arr.mean(axis=0)[N//2:]
        rho_anti = float(np.corrcoef(left, right)[0, 1])
    else:
        rho_anti = float('nan')
    # ---- (3) True period-2 deviation: mean over n of |x^{n+2}_i - x^n_i|
    d2 = float(np.mean(np.abs(arr[2:] - arr[:-2])))
    # ---- Spatial variance & temporal amplitude to confirm chaos
    spatial_std = float(np.std(arr))
    return dict(peak_f=float(peak_f), rho_anti=rho_anti, d2=d2, spatial_std=spatial_std)


def run(N, eps, bc, seed, n_transient=2000, T=2048):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, N)
    for _ in range(n_transient):
        x = cml_step(x, eps, bc)
    snaps = [x.copy()]
    for _ in range(T - 1):
        x = cml_step(x, eps, bc)
        snaps.append(x.copy())
    return measure(snaps, eps, bc)


if __name__ == '__main__':
    print("="*78)
    print("HYP-126 REPLICATION -- proper dynamical metrics")
    print("="*78)
    rows = []
    print(f"\n{'BC':>10} {'N':>4} {'eps':>5} {'peak_f':>9} {'rho_anti':>10} {'Delta_2':>11}  spatial_std")
    print("-"*78)
    for bc in ["periodic", "open"]:
        for N in [32, 48, 64, 96, 128]:
            for eps in [0.05, 0.10, 0.20, 0.35, 0.50]:
                mlist = [run(N, eps, bc, seed=1000*s + N) for s in range(2)]
                # average
                m = {k: np.mean([d[k] for d in mlist]) for k in mlist[0]}
                # classification
                if m['spatial_std'] < 1e-4:
                    tag = "DEAD"
                elif abs(m['peak_f'] - 0.5) < 0.02 and m['d2'] < 0.01:
                    tag = "PERIOD-2 LOCK"
                elif abs(m['peak_f'] - 0.5) < 0.02:
                    tag = "f=1/2 dominant but Delta_2 large"
                elif abs(m['peak_f'] - 0.25) < 0.02:
                    tag = "PERIOD-4 / subharmonic"
                else:
                    tag = "broadband chaotic"
                m['bc'] = bc; m['N'] = N; m['eps'] = eps; m['tag'] = tag
                rows.append(m)
                print(f"{bc:>10} {N:>4} {eps:>5} {m['peak_f']:>9.4f} "
                      f"{m['rho_anti']:>10.4f} {m['d2']:>11.4f} "
                      f"  {m['spatial_std']:.3f}   {tag}")
    with open('hyp126_fft_replication.json', 'w') as fh:
        json.dump(rows, fh, indent=2)
    print("\nSaved -> hyp126_fft_replication.json")