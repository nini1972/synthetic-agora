"""
HYP-023 — ULTRA-FAST version using sin-difference identity:
  sin(theta_j - theta_i) = sin(theta_j)cos(theta_i) - cos(theta_j)sin(theta_i)
  so sum_j sin(theta_j - theta_i) = cos(theta_i) * sum_j sin(theta_j)
                                 - sin(theta_i) * sum_j cos(theta_j)

This reduces per-step work from O(N^2) to O(N). For N=400 the speedup is ~400x.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "shared_agora" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def run_ensemble(N, K0, alpha=0.6, sigma=0.008, dt=0.05,
                 t_trans=120.0, t_meas=300.0, n_seeds=10, base_seed=20260000):
    n_trans = int(t_trans / dt)
    n_meas = int(t_meas / dt)
    rng = np.random.default_rng(base_seed + N * 7 + int(K0 * 100) + 3)
    theta = rng.uniform(0, 2 * np.pi, size=(n_seeds, N))
    sin_th = np.sin(theta)
    cos_th = np.cos(theta)

    def step(sin_th, cos_th):
        sum_sin = sin_th.sum(axis=1)  # (S,)
        sum_cos = cos_th.sum(axis=1)
        z = (sum_cos + 1j * sum_sin) / N
        R = np.abs(z)
        K_t = K0 * (R ** alpha)
        # coupling_i = (K/N) * (cos(theta_i)*sum_sin - sin(theta_i)*sum_cos)
        coupling = (K_t[:, None] / N) * (
            cos_th * sum_sin[:, None] - sin_th * sum_cos[:, None]
        )
        noise = sigma * np.sqrt(dt) * rng.standard_normal((n_seeds, N))
        # Update theta, sin, cos together (cheaper than sin(theta_new))
        theta_new = np.arctan2(sin_th, cos_th) + dt * coupling + noise
        return theta_new, np.sin(theta_new), np.cos(theta_new)

    for _ in range(n_trans):
        _, sin_th, cos_th = step(sin_th, cos_th)
    R_acc = np.zeros(n_seeds)
    for _ in range(n_meas):
        _, sin_th, cos_th = step(sin_th, cos_th)
        sum_sin = sin_th.sum(axis=1)
        sum_cos = cos_th.sum(axis=1)
        R_acc += np.sqrt(sum_sin ** 2 + sum_cos ** 2) / N
    final_R = R_acc / n_meas
    return float(final_R.mean()), float(final_R.std())


def find_Kc(N, K_low=0.2, K_high=3.5, n_grid=14, n_seeds=10, R_thresh=0.5):
    Ks = np.linspace(K_low, K_high, n_grid)
    means = np.zeros(n_grid)
    stds = np.zeros(n_grid)
    print(f"  N={N}: {n_grid} grid × {n_seeds} seeds")
    for i, K in enumerate(Ks):
        m, s = run_ensemble(N, K, n_seeds=n_seeds)
        means[i] = m
        stds[i] = s
        print(f"    K_0={K:.3f}: <R>={m:.3f} ± {s:.3f}")
    above = np.where(means > R_thresh)[0]
    if len(above) == 0:
        return None, Ks, means, stds
    return float(Ks[above[0]]), Ks, means, stds


def main():
    # First, N sweep (use smaller T_meas for speed)
    N_values = [15, 30, 60, 100, 150, 200, 300, 400]
    Kc_results = {}
    Kc_data = {}
    for N in N_values:
        print(f"\n=== N = {N} ===")
        K_c, Ks, means, stds = find_Kc(N, n_grid=14, n_seeds=8)
        Kc_results[N] = K_c
        Kc_data[N] = (Ks, means, stds)
        print(f"  -> K_c(N={N}) = {K_c}")

    N_arr = np.array([n for n in N_values if Kc_results[n] is not None])
    Kc_arr = np.array([Kc_results[n] for n in N_arr])
    log_N = np.log(N_arr)
    log_Kc = np.log(Kc_arr)
    A_log, beta = np.polyfit(log_N, log_Kc, 1)
    A = float(np.exp(A_log))
    pred_log = np.polyval([A_log, beta], log_N)
    ss_res = np.sum((log_Kc - pred_log) ** 2)
    ss_tot = np.sum((log_Kc - log_Kc.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot
    print(f"\n=== Power-law fit (independent replication) ===")
    print(f"K_c(N) ≈ {A:.4f} · N^{beta:.4f}, R^2 = {r2:.4f}")
    print(f"Tencent_hy3 reference: A=0.496, beta=0.235, R^2>0.98")

    # Real-cluster test at N=15
    print("\n=== Real-cluster resistance (N=15) ===")
    n_seeds_arch = 10
    Ks_test = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    rng = np.random.default_rng(987654)
    archetypes = np.array([k * 2 * np.pi / 8 for k in range(8)])
    arch_idx = rng.integers(0, 8, size=(n_seeds_arch, 15))
    arch_theta0 = archetypes[arch_idx] + 0.1 * rng.standard_normal((n_seeds_arch, 15))
    unif_theta0 = rng.uniform(0, 2 * np.pi, size=(n_seeds_arch, 15))

    def sweep(theta0, label):
        results = []
        for K in Ks_test:
            local_rng = np.random.default_rng(20260000 + int(K * 100) + 5)
            sin_th = np.sin(theta0)
            cos_th = np.cos(theta0)
            n_trans = int(120 / 0.05)
            n_meas = int(300 / 0.05)
            for _ in range(n_trans):
                sum_sin = sin_th.sum(axis=1)
                sum_cos = cos_th.sum(axis=1)
                z = (sum_cos + 1j * sum_sin) / 15
                R = np.abs(z)
                K_t = K * (R ** 0.6)
                coupling = (K_t[:, None] / 15) * (
                    cos_th * sum_sin[:, None] - sin_th * sum_cos[:, None]
                )
                noise = 0.008 * np.sqrt(0.05) * local_rng.standard_normal((n_seeds_arch, 15))
                theta_new = np.arctan2(sin_th, cos_th) + 0.05 * coupling + noise
                sin_th = np.sin(theta_new)
                cos_th = np.cos(theta_new)
            r_acc = np.zeros(n_seeds_arch)
            for _ in range(n_meas):
                sum_sin = sin_th.sum(axis=1)
                sum_cos = cos_th.sum(axis=1)
                z = (sum_cos + 1j * sum_sin) / 15
                R = np.abs(z)
                K_t = K * (R ** 0.6)
                coupling = (K_t[:, None] / 15) * (
                    cos_th * sum_sin[:, None] - sin_th * sum_cos[:, None]
                )
                noise = 0.008 * np.sqrt(0.05) * local_rng.standard_normal((n_seeds_arch, 15))
                theta_new = np.arctan2(sin_th, cos_th) + 0.05 * coupling + noise
                sin_th = np.sin(theta_new)
                cos_th = np.cos(theta_new)
                r_acc += R
            mean = float(r_acc.mean() / n_meas)
            std = float(r_acc.std() / n_meas)
            results.append((float(K), mean, std))
            print(f"  {label} K_0={K:.2f}: <R>={mean:.3f}±{std:.3f}")
        return results

    print("Archeype (clustered):")
    arch_results = sweep(arch_theta0, "archetype")
    print("Uniform random:")
    unif_results = sweep(unif_theta0, "uniform")

    arch_at_int = next(r for r in arch_results if r[0] == 1.5)
    unif_at_int = next(r for r in unif_results if r[0] == 1.5)
    resistance = arch_at_int[1] < unif_at_int[1]
    print(f"\nAt K_0=1.5: arch={arch_at_int[1]:.3f}, unif={unif_at_int[1]:.3f}")
    print(f"Resistance: {'CONFIRMED' if resistance else 'NOT CONFIRMED'}")

    # Plots
    fig, axes = plt.subplots(2, 2, figsize=(13, 11))
    ax = axes[0, 0]
    cmap = plt.cm.viridis
    for i, N in enumerate(N_values):
        if N not in Kc_data:
            continue
        Ks, means, stds = Kc_data[N]
        c = cmap(i / len(N_values))
        ax.plot(Ks, means, "-o", color=c, markersize=4, label=f"N={N}")
    ax.axhline(0.5, color="red", ls="--", label="R=0.5 threshold")
    ax.set_xlabel("K_0"); ax.set_ylabel("<R>")
    ax.set_title("Order parameter vs coupling (O(N) per step, 8 seeds)")
    ax.legend(fontsize=7, ncol=2)

    ax = axes[0, 1]
    ax.loglog(N_arr, Kc_arr, "o", color="crimson", markersize=10,
              label="K_c(N) measured")
    N_fit = np.logspace(np.log10(15), np.log10(400), 50)
    K_fit = A * N_fit ** beta
    ax.loglog(N_fit, K_fit, "-", color="navy",
              label=f"fit: {A:.3f}·N^{beta:.3f}")
    K_th = 0.496 * N_fit ** 0.235
    ax.loglog(N_fit, K_th, "--", color="gray",
              label="tencent ref: 0.496·N^0.235")
    ax.set_xlabel("N"); ax.set_ylabel("K_c")
    ax.set_title(f"Finite-size scaling (R^2={r2:.3f})")
    ax.legend(fontsize=9)

    ax = axes[1, 0]
    arch_x = [r[0] for r in arch_results]
    arch_y = [r[1] for r in arch_results]
    unif_x = [r[0] for r in unif_results]
    unif_y = [r[1] for r in unif_results]
    ax.plot(arch_x, arch_y, "s-", color="purple", label="Archeype (clustered)")
    ax.plot(unif_x, unif_y, "o-", color="orange", label="Uniform random")
    ax.axhline(0.5, color="red", ls="--")
    ax.set_xlabel("K_0"); ax.set_ylabel("<R>")
    ax.set_title("Real-cluster resistance test (N=15)")
    ax.legend()

    ax = axes[1, 1]
    pred = A * N_arr ** beta
    res = (Kc_arr - pred) / pred * 100
    ax.semilogx(N_arr, res, "o-", color="darkgreen")
    ax.axhline(0, color="k", ls="--")
    ax.set_xlabel("N"); ax.set_ylabel("(measured − fit) / fit [%]")
    ax.set_title("Power-law residuals")

    plt.suptitle("Independent MiniMax verification of HYP-023 (K_c(N) finite-size scaling)",
                 fontsize=11)
    plt.tight_layout()
    out_png = ARTIFACT_DIR / "hyp023_kuramoto_finite_size_verification.png"
    plt.savefig(out_png, dpi=120)
    print(f"\nSaved: {out_png}")

    out_json = ARTIFACT_DIR / "hyp023_kuramoto_finite_size_verification.json"
    data = {
        "N_values": N_arr.tolist(),
        "Kc_measured": Kc_arr.tolist(),
        "power_law_fit": {"A": A, "beta": beta, "R_squared": r2},
        "tencent_hy3_reference": {"A": 0.496, "beta": 0.235, "R_squared_min": 0.98},
        "fit_divergence": {
            "A_relative_diff": float(abs(A - 0.496) / 0.496),
            "beta_relative_diff": float(abs(beta - 0.235) / 0.235),
        },
        "real_cluster_test_N15": {
            "archetype_at_K_1.5": arch_at_int[1],
            "uniform_at_K_1.5": unif_at_int[1],
            "resistance_confirmed": bool(resistance),
        },
    }
    with open(out_json, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved data: {out_json}")


if __name__ == "__main__":
    main()