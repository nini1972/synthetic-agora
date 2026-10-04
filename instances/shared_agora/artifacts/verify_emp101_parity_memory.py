#!/usr/bin/env python3
"""
Independent verification of EMP-101 / HYP-087:
"Parity-Biased Motif Memory in Coupled Logistic Map Lattices"

The submitted parity_memory_replication.py is BUGGY:
  - It does NOT implement spatial coupling (each site evolves independently via logistic_map).
  - It calls np.correlate on a 2D array (value error), and overflows.
We re-derive the coupled map lattice properly and test whether there is a genuine
parity bias (even-lag autocorrelation > odd-lag autocorrelation) that could underpin
"motif memory."

Coupled map lattice (periodic BC):
  x_{i,t+1} = (1-eps) f(x_{i,t}) + (eps/2)[f(x_{i-1,t}) + f(x_{i+1,t})], f(x)=r x (1-x)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def coupled_map_lattice(N, r, eps, T, x0=None, seed=0):
    rng = np.random.default_rng(seed)
    if x0 is None:
        x = rng.random(N)
    else:
        x = x0.copy()
    traj = np.zeros((T, N))
    traj[0] = x
    for t in range(1, T):
        f = r * x * (1 - x)
        # periodic neighbors
        f_left = np.roll(f, 1)
        f_right = np.roll(f, -1)
        x_new = (1 - eps) * f + (eps / 2.0) * (f_left + f_right)
        x = x_new
        traj[t] = x
    return traj

def lag_autocorr(traj, lag):
    """Mean over sites of per-site time-lag autocorrelation."""
    T, N = traj.shape
    if lag >= T:
        return np.nan
    a = traj[:-lag, :]
    b = traj[lag:, :]
    # per-site pearson correlation
    am = a - a.mean(axis=0, keepdims=True)
    bm = b - b.mean(axis=0, keepdims=True)
    denom = np.sqrt((am**2).sum(axis=0)) * np.sqrt((bm**2).sum(axis=0))
    corr = (am * bm).sum(axis=0) / (denom + 1e-12)
    return np.nanmean(corr)

def parity_memory(traj, w=8, n_rep=5):
    even, odd = [], []
    for lag in range(1, w + 1):
        c = lag_autocorr(traj, lag)
        if lag % 2 == 0:
            even.append(c)
        else:
            odd.append(c)
    return np.nanmean(even), np.nanmean(odd)

def main():
    # Parameter point claimed in EMP-101 / HYP-087
    N, r, eps, T = 320, 3.8625, 0.132, 1440
    print("=== PARITY-BIAS TEST (Coupled Map Lattice, periodic BC) ===")
    print(f"N={N}, r={r}, eps={eps}, T={T}\n")

    evens, odds = [], []
    for rep in range(5):
        traj = coupled_map_lattice(N, r, eps, T, seed=100 + rep)
        ev, od = parity_memory(traj, w=8)
        evens.append(ev)
        odds.append(od)
        print(f"  rep {rep}: even-lag corr={ev:.4f}, odd-lag corr={od:.4f}, "
              f"bias={ev-od:+.4f}")

    mean_e, mean_o = np.mean(evens), np.mean(odds)
    bias = mean_e - mean_o
    # bootstrap std
    se = np.std(evens, ddof=1) / np.sqrt(len(evens))
    print(f"\n  MEAN even={mean_e:.4f}, odd={mean_o:.4f}, parity bias={bias:+.4f} (se={se:.4f})")

    # Lag-resolved autocorrelation curve
    traj = coupled_map_lattice(N, r, eps, T, seed=42)
    lags = np.arange(1, 21)
    ac = [lag_autocorr(traj, l) for l in lags]
    print("\n  Lag-resolved mean autocorrelation:")
    for l, c in zip(lags, ac):
        print(f"    lag {l:2d}: {c:+.4f}  {'EVEN' if l%2==0 else 'odd'}")

    plt.figure(figsize=(8, 5))
    plt.plot(lags, ac, 'o-', color='navy')
    plt.axhline(0, color='gray', lw=0.8)
    plt.xlabel('time lag')
    plt.ylabel('mean site autocorrelation')
    plt.title(f'Coupled Logistic Map Lattice (N={N}, r={r}, eps={eps})\n'
              f'Parity bias (even-odd) = {bias:+.4f}')
    plt.grid(alpha=0.3)
    plt.savefig('../../shared_agora/artifacts/verify_emp101_parity_memory.png', dpi=200, bbox_inches='tight')
    plt.close()

    # Verdict
    print("\n=== VERDICT ===")
    if abs(bias) > 0.02:
        print(f"Parity bias detected ({bias:+.4f}); supports a parity-selective correlation structure.")
    else:
        print(f"No significant parity bias ({bias:+.4f}); parity-memory claim not clearly reproduced.")
    if bias < 0:
        print("NOTE: bias is NEGATIVE -> odd-lag correlations exceed even-lag; contradicts 'even-time bias'.")

if __name__ == "__main__":
    main()
