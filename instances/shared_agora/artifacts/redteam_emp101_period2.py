#!/usr/bin/env python3
"""
Red-team: Is the "parity-bias/motif memory" in EMP-101 / HYP-087 actually just a
period-2 orbit? We examine the raw time series, the symbolic motif sequence under
median partitioning, and the structure of the autocorrelation.
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
        f_left = np.roll(f, 1)
        f_right = np.roll(f, -1)
        x_new = (1 - eps) * f + (eps / 2.0) * (f_left + f_right)
        x = x_new
        traj[t] = x
    return traj

def main():
    N, r, eps, T = 320, 3.8625, 0.132, 1440
    traj = coupled_map_lattice(N, r, eps, T, seed=42)

    # Look at a single site's trajectory
    site = traj[:, 5]
    print("=== Single-site time series (first 20 steps) ===")
    print(np.round(site[:20], 4))

    # Check period-2: distance between x_t and x_{t+2}
    print("\n=== Period-2 test ===")
    diff2 = np.mean(np.abs(traj[:-2, :] - traj[2:, :]))
    diff1 = np.mean(np.abs(traj[:-1, :] - traj[1:, :]))
    diff3 = np.mean(np.abs(traj[:-3, :] - traj[3:, :]))
    print(f"  mean |x_t - x_(t+2)| = {diff2:.6f}   <- should be ~0 if period-2")
    print(f"  mean |x_t - x_(t+1)| = {diff1:.6f}")
    print(f"  mean |x_t - x_(t+3)| = {diff3:.6f}")

    # Standard deviation within vs across the two sub-orbits
    even_states = traj[::2, :]
    odd_states = traj[1::2, :]
    print(f"\n  mean of even-time states: {even_states.mean():.4f}")
    print(f"  mean of odd-time states:  {odd_states.mean():.4f}")
    print(f"  std of even-time states:  {even_states.std():.4f}")
    print(f"  std of odd-time states:   {odd_states.std():.4f}")
    print(f"  std within even (temporal): {np.mean(even_states.std(axis=0)):.4f}")
    print(f"  std within odd (temporal):  {np.mean(odd_states.std(axis=0)):.4f}")

    # Median-partition symbolic sequence for a site
    med = np.median(traj[:, 5])
    symbolic = (traj[:, 5] > med).astype(int)
    print("\n=== Median-partitioned symbolic sequence (first 30) ===")
    print(''.join(str(s) for s in symbolic[:30]))

    # Count transitions
    trans = np.mean(symbolic[1:] != symbolic[:-1])
    print(f"  transition rate between median-partitioned symbols: {trans:.3f}")
    print(f"  (0.5 = random alternation, 1.0 = perfect 2-cycle, ~0 = frozen)")

    # Plot
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    axes[0].plot(site[:100], 'o-', ms=3)
    axes[0].set_title(f'Single site trajectory (first 100), r={r}, eps={eps}')
    axes[0].set_ylabel('x')

    axes[1].plot(symbolic[:100], 'o-', ms=3)
    axes[1].set_title('Median-partitioned symbolic sequence (site 5)')
    axes[1].set_ylabel('symbol')

    # Autocorr
    lags = np.arange(1, 21)
    ac = []
    for lag in lags:
        a = traj[:-lag, :]; b = traj[lag:, :]
        am = a - a.mean(axis=0, keepdims=True); bm = b - b.mean(axis=0, keepdims=True)
        d = np.sqrt((am**2).sum(axis=0))*np.sqrt((bm**2).sum(axis=0))
        ac.append(np.nanmean((am*bm).sum(axis=0)/(d+1e-12)))
    axes[2].plot(lags, ac, 'o-', color='crimson')
    axes[2].axhline(0, color='gray')
    axes[2].set_title('Mean site autocorrelation: clear period-2 (even>0, odd<0)')
    axes[2].set_xlabel('lag'); axes[2].set_ylabel('autocorr')
    axes[2].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('shared_agora/artifacts/redteam_emp101_period2.png', dpi=200, bbox_inches='tight')
    plt.close()
    print("\nSaved redteam_emp101_period2.png")

if __name__ == "__main__":
    main()
