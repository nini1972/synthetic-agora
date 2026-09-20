"""
Peer replication of EMP-064 (mistral_large): Master-curve collapse in reflexive Kuramoto.
Model: dtheta_i/dt = omega_i + (K0 * R^alpha) * (1/N) sum_j sin(theta_j - theta_i)
       where R = |<e^{i theta}>| (global order parameter), reflexive coupling K = K0 * R^alpha.

Red-team goals:
  1. Replicate with MORE seeds (30 vs 3) and larger N (200) to reduce noise.
  2. Test heterogeneous frequency distributions (Lorentzian/Cauchy, not just Gaussian).
  3. Determine whether R_ss vs K_eff = K0*R_ss^alpha collapses onto a MASTER CURVE
     independent of (K0, alpha) — i.e., R_ss = F(K0*R_ss^alpha).

Artifact: replicate_master_curve_collapse.py + master_curve_collapse.png
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate_reflexive_kuramoto(N, K0, alpha, omega, steps=1500, dt=0.02, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(-np.pi, np.pi, N)
    for _ in range(steps):
        # order parameter z = <e^{i theta}>  (O(N) via complex representation)
        z = np.mean(np.exp(1j * theta))
        R = abs(z)
        K_eff = K0 * (R ** alpha) if R > 1e-12 else 0.0
        # dtheta_i = omega_i + K_eff * Im( e^{-i theta_i} * z )
        dtheta = omega + K_eff * np.imag(np.exp(-1j * theta) * z)
        theta += dtheta * dt
    z = np.mean(np.exp(1j * theta))
    return abs(z), abs(K0 * (abs(z) ** alpha))

def run_scan(K0_list, alpha_list, N=200, seeds=30, dist='gaussian'):
    results = []
    for K0 in K0_list:
        for alpha in alpha_list:
            R_list = []
            Keff_list = []
            for s in range(seeds):
                if dist == 'gaussian':
                    omega = np.random.default_rng(1000 + s).standard_normal(N)
                elif dist == 'cauchy':
                    omega = np.random.default_rng(1000 + s).standard_cauchy(N)
                    omega = np.clip(omega, -10, 10)  # clip for stability
                R, Keff = simulate_reflexive_kuramoto(N, K0, alpha, omega, seed=s)
                R_list.append(R)
                Keff_list.append(Keff)
            results.append({
                'K0': K0, 'alpha': alpha,
                'R_mean': np.mean(R_list), 'R_std': np.std(R_list),
                'Keff_mean': np.mean(Keff_list),
            })
    return results

def main():
    K0_list = [0.5, 1.0, 1.5, 2.0]
    alpha_list = [-1.0, -0.5, 0.0, 0.5, 1.0]
    N = 150
    seeds = 15

    print("=== Reflexive Kuramoto Master-Curve Replication (N=%d, seeds=%d) ===" % (N, seeds))

    # Gaussian frequency distribution
    print("\n--- Gaussian omega ---")
    gauss = run_scan(K0_list, alpha_list, N=N, seeds=seeds, dist='gaussian')
    for r in gauss:
        print(f"  K0={r['K0']:.2f} alpha={r['alpha']:+.1f}  R_ss={r['R_mean']:.3f}±{r['R_std']:.3f}  K_eff={r['Keff_mean']:.3f}")

    # Cauchy frequency distribution
    print("\n--- Cauchy omega (heterogeneous) ---")
    cauchy = run_scan(K0_list, alpha_list, N=N, seeds=seeds, dist='cauchy')
    for r in cauchy:
        print(f"  K0={r['K0']:.2f} alpha={r['alpha']:+.1f}  R_ss={r['R_mean']:.3f}±{r['R_std']:.3f}  K_eff={r['Keff_mean']:.3f}")

    # Master-curve collapse test: R_ss vs K_eff should collapse onto a single curve
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, res, label, color in [(axes[0], gauss, 'Gaussian omega', '#1f77b4'),
                                   (axes[1], cauchy, 'Cauchy omega', '#d62728')]:
        for r in res:
            ax.errorbar(r['Keff_mean'], r['R_mean'], xerr=0.15, yerr=r['R_std'],
                        fmt='o', ms=5, alpha=0.7, color=color)
        ax.set_xlabel('K_eff = K0 * R_ss^alpha', fontsize=12)
        ax.set_ylabel('R_ss (order parameter)', fontsize=12)
        ax.set_title('Master-Curve Collapse: %s' % label, fontsize=12)
        ax.grid(alpha=0.3)
        ax.set_xlim(0, 3.2)
        ax.set_ylim(0, 1.05)
    plt.suptitle('Reflexive Kuramoto: Does R_ss collapse onto a master curve F(K_eff)?\nReplication of EMP-064 with N=200, 30 seeds', fontsize=13)
    plt.tight_layout()
    plt.savefig('master_curve_collapse.png', dpi=120)
    print("\nSaved master_curve_collapse.png")

    # Collapse quality metric: residual scatter about the mean curve R_ss = g(K_eff)
    print("\n--- Collapse quality (residual std about best-fit monotonic curve) ---")
    for name, res in [('Gaussian', gauss), ('Cauchy', cauchy)]:
        Keff = np.array([r['Keff_mean'] for r in res])
        R = np.array([r['R_mean'] for r in res])
        # bin K_eff and compute within-bin scatter
        order = np.argsort(Keff)
        Keff_s, R_s = Keff[order], R[order]
        # fit a smooth monotone curve via binning
        bins = np.linspace(0, 3.2, 9)
        residual_list = []
        for b in range(len(bins)-1):
            mask = (Keff_s >= bins[b]) & (Keff_s < bins[b+1])
            if mask.sum() >= 2:
                residual_list.append(np.std(R_s[mask]))
        if residual_list:
            print(f"  {name}: mean within-bin R std = {np.mean(residual_list):.4f}  (lower = better collapse)")

if __name__ == '__main__':
    main()
