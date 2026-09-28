"""Decisive check of the DISPUTED low-noise case: does sigma=0.05 collapse the
intermediate band (EMP-069 claim) or leave it flat (EMP-082 / my CF)?

Use direct Euler-Maruyama Monte-Carlo. Reduced size for turn budget.
"""
import numpy as np


def R_monte_carlo(dw, K, sigma, n_walkers=2000, T=40.0, dt=0.01, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, n_walkers)
    n_steps = int(T/dt)
    for _ in range(n_steps):
        theta += (dw - 2*K*np.sin(theta))*dt + sigma*np.sqrt(dt)*rng.standard_normal(n_walkers)
    return abs(np.exp(1j*theta).mean())


if __name__ == "__main__":
    print("=== Direct MC R(dw) at the optimum K*~1.67 for low sigma ===")
    for sigma in [0.05, 0.10]:
        K = 1.67
        print(f"  sigma={sigma:.2f}, K={K}:")
        for dw in [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0]:
            R = R_monte_carlo(dw, K, sigma, seed=int(dw*10))
            in_band = (0.3 <= R <= 0.7)
            print(f"    dw={dw:.1f} -> R={R:.4f}  {'[in band]' if in_band else ''}")
        print()
    print("  EMP-069 claimed sigma=0.05 -> band_frac ~0.0025 (near-total collapse)")
    print("  EMP-082 / my CF claimed sigma=0.05 -> band_frac ~0.41 (flat, no collapse)")
