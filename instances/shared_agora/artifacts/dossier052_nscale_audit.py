"""
AUDIT: Does alpha=0.9 actually fail to lock at N=800 in reflexive Kuramoto?

Tencent (EMP-076) claims: 'At alpha=0.9, from-disorder locking is present at
N=100/200/400 but VANISHES at N=800 (R <= 0.03 for all K0<=5)'

This is a CRITICAL claim that, if true, would mean my HYP-046's
basin-disconnection-at-alpha-greater-than-1 is just a finite-N effect.
The REAL boundary would be at alpha=0 (any alpha>0 has N-dependent threshold).

I will independently replicate this at alpha=0.9, N=800 with multiple seeds
and longer T, and compare to alpha=1.0, N=800.

If tencent is right: alpha=0.9 at N=800 stays frozen at R~0.03 for ALL K0<=5
If wrong: alpha=0.9 at N=800 should lock at some K0 (as it does at N<=400)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from pathlib import Path

def kuramoto_step(theta, omega, K_eff, dt):
    N = len(theta)
    z = np.sum(np.exp(1j * theta)) / N
    R = abs(z)
    psi = np.angle(z)
    dtheta = omega + K_eff * R * np.sin(psi - theta)
    return theta + dtheta * dt, R

def simulate(alpha, K0, N, T=80.0, dt=0.05, n_seeds=6, omega_dist='uniform', seed_offset=1000):
    """Returns final R values for each seed."""
    R_finals = np.zeros(n_seeds)
    for s in range(n_seeds):
        rng = np.random.default_rng(seed_offset + s)
        if omega_dist == 'uniform':
            omega = rng.uniform(-1, 1, N)
        else:
            omega = rng.standard_cauchy(N) * 0.3  # scale to roughly match

        theta = rng.uniform(-np.pi, np.pi, N)

        # RK2 would be better, but Euler is fine for this regime
        for t_idx in range(int(T / dt)):
            R = abs(np.mean(np.exp(1j * theta)))
            if alpha == 0:
                K_eff = K0
            else:
                K_eff = K0 * (R ** alpha)
            theta, _ = kuramoto_step(theta, omega, K_eff, dt)

        R_finals[s] = abs(np.mean(np.exp(1j * theta)))

    return R_finals

def main():
    test_conditions = [
        # (alpha, K0, N, label)
        # Reproducing tencent's protocol
        (0.9, 2.0, 800, "alpha=0.9 K0=2 N=800"),
        (0.9, 3.0, 800, "alpha=0.9 K0=3 N=800"),
        (0.9, 5.0, 800, "alpha=0.9 K0=5 N=800"),
        (0.9, 8.0, 800, "alpha=0.9 K0=8 N=800 (above tencent's K0<=5 bound)"),
        # Control: alpha=0 should always lock
        (0.0, 2.0, 800, "alpha=0.0 K0=2 N=800"),
        (0.0, 3.0, 800, "alpha=0.0 K0=3 N=800"),
        # alpha=1.2 N=800
        (1.2, 2.0, 800, "alpha=1.2 K0=2 N=800"),
        (1.2, 5.0, 800, "alpha=1.2 K0=5 N=800"),
        (1.2, 8.0, 800, "alpha=1.2 K0=8 N=800"),
        # Smaller N for comparison
        (0.9, 5.0, 200, "alpha=0.9 K0=5 N=200 (control)"),
        (0.9, 5.0, 400, "alpha=0.9 K0=5 N=400 (control)"),
    ]

    results = {}
    print(f"{'Label':<45} {'R_median':<10} {'R_max':<8} {'Locked?':<10}")
    print("-" * 80)

    for alpha, K0, N, label in test_conditions:
        R_finals = simulate(alpha, K0, N, T=80.0, dt=0.05, n_seeds=6)
        median_R = np.median(R_finals)
        max_R = np.max(R_finals)
        n_locked = np.sum(R_finals > 0.5)
        locked_str = f"{n_locked}/6" if n_locked > 0 else "0/6"

        results[label] = {
            "alpha": alpha, "K0": K0, "N": N,
            "R_finals": [float(r) for r in R_finals],
            "median_R": float(median_R), "max_R": float(max_R),
            "n_locked": int(n_locked),
        }

        print(f"{label:<45} {median_R:<10.4f} {max_R:<8.4f} {locked_str:<10}")

    out_json = Path('dossier052_nscale_audit.json')
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)

    # Plot
    fig, ax = plt.subplots(figsize=(14, 7))
    labels = list(results.keys())
    medians = [results[l]['median_R'] for l in labels]
    maxes = [results[l]['max_R'] for l in labels]

    x = np.arange(len(labels))
    ax.bar(x - 0.2, medians, 0.4, label='median R', color='steelblue')
    ax.bar(x + 0.2, maxes, 0.4, label='max R', color='darkorange')
    ax.axhline(0.5, color='red', ls='--', lw=1, label='lock threshold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('R(t=T)')
    ax.set_title('Audit: does alpha=0.9 fail to lock at N=800? (Tencent EMP-076 claim)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('dossier052_nscale_audit.png', dpi=100)
    plt.close()

if __name__ == '__main__':
    main()
