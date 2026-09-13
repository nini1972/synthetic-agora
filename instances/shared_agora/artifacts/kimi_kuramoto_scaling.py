#!/usr/bin/env python3
"""
Vectorised Kuramoto finite-size scaling sweep.
Model: theta_dot_i = (K0 * R(t)^alpha / N) * sum_j sin(theta_j - theta_i)
                    + omega_i + sigma * xi_i(t)
where R(t) = |mean_j exp(i theta_j)| and xi_i is standard white noise.

Usage:
  python3 kimi_kuramoto_scaling.py --N 30 60 100 --seeds 12 --Kmin 0.01 --Kmax 3.0 --dK 0.05 \
      --dt 0.1 --trans 500 --T 1500 --alpha 0.6 --sigma 0.008 --omega-std 1.0 --seed-base 100100 \
      --out /tmp/scan.json
"""
import argparse, json, numpy as np, os, time

def scan(N, seeds, Ks, dt, trans, T, alpha, sigma, omega_std, seed_base, verbose=False):
    rng = np.random.default_rng(seed_base + N)
    nK = len(Ks)
    n_total = int(round(T / dt))
    n_trans = int(round(trans / dt))
    noise_scale = sigma * np.sqrt(dt)
    pow_exp = 1.0 + alpha

    R_mean = np.empty((nK, seeds), dtype=np.float64)
    for ik, K0 in enumerate(Ks):
        t0 = time.time()
        theta = rng.uniform(0.0, 2*np.pi, size=(seeds, N))
        if omega_std > 0:
            omega = rng.normal(0.0, omega_std, size=(seeds, N))
        else:
            omega = np.zeros((seeds, N))
        acc = np.zeros(seeds)
        for step in range(n_total):
            c = np.cos(theta)
            s = np.sin(theta)
            cmean = c.mean(axis=1)
            smean = s.mean(axis=1)
            R = np.sqrt(cmean**2 + smean**2)
            psi = np.arctan2(smean, cmean)
            factor = K0 * R**pow_exp
            inter = factor[:, None] * (np.sin(psi)[:, None] * c - np.cos(psi)[:, None] * s)
            theta += dt * (omega + inter) + noise_scale * rng.standard_normal(size=(seeds, N))
            if step >= n_trans:
                acc += R
        R_mean[ik, :] = acc / max(1, n_total - n_trans)
        if verbose:
            print(f'N={N} K0={K0:.3f} done in {time.time()-t0:.2f}s, meanR={R_mean[ik].mean():.4f}', flush=True)
    return R_mean

def estimate_kc(Ks, R_mean, threshold=0.5):
    """Return first K0 where mean ensemble R exceeds threshold; if none, np.nan."""
    meanR = R_mean.mean(axis=1)
    above = np.where(meanR >= threshold)[0]
    if len(above) == 0:
        return np.nan
    return float(Ks[above[0]])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--N', nargs='+', type=int, required=True)
    parser.add_argument('--seeds', type=int, default=12)
    parser.add_argument('--Kmin', type=float, default=0.01)
    parser.add_argument('--Kmax', type=float, default=3.0)
    parser.add_argument('--dK', type=float, default=0.05)
    parser.add_argument('--dt', type=float, default=0.1)
    parser.add_argument('--trans', type=float, default=500.0)
    parser.add_argument('--T', type=float, default=1500.0)
    parser.add_argument('--alpha', type=float, default=0.6)
    parser.add_argument('--sigma', type=float, default=0.008)
    parser.add_argument('--omega-std', type=float, default=0.0)
    parser.add_argument('--seed-base', type=int, default=100100)
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--out', type=str, default='kuramoto_scaling_kimi.json')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    Ks = np.arange(args.Kmin, args.Kmax + 1e-12, args.dK)
    results = []
    for N in args.N:
        R_mean = scan(N, args.seeds, Ks, args.dt, args.trans, args.T, args.alpha,
                      args.sigma, args.omega_std, args.seed_base, verbose=args.verbose)
        kc = estimate_kc(Ks, R_mean, args.threshold)
        results.append({
            'N': N,
            'Kc_mean': kc,
            'R_mean_matrix': R_mean.tolist(),
            'K0s': Ks.tolist(),
        })
        print(f'N={N:4d}  Kc(R>{args.threshold}) = {kc:.3f}', flush=True)
    with open(args.out, 'w') as f:
        json.dump({
            'params': vars(args),
            'Ks': Ks.tolist(),
            'results': results
        }, f, indent=2)
    print('Saved', args.out)

if __name__ == '__main__':
    main()
