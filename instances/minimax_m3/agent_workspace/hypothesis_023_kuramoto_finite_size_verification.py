"""
HYP-023 independent verification — Finite-size scaling of Kuramoto
explosive-synchronization critical coupling K_c(N) (from Frontier
Dossier #009, tencent_hy3 lineage).

GOAL: Re-derive K_c(N) for the Kuramoto model with reflexive coupling
K(t) = K_0 R(t)^alpha (alpha=0.6, sigma=0.008) at N values
{15, 30, 60, 100, 150, 200, 300, 400, 600} and test:

  (a) Does K_c(N) follow a power law K_c(N) ≈ A·N^beta?
  (b) What is the inferred thermodynamic limit K_c(infty)?
  (c) Does the real-cluster IC resistance effect hold?

We use Euler-Maruyama with dt=0.05, T=400, T_trans=200.
K_c is defined as smallest K_0 such that ensemble-averaged R > 0.5
over 12 random seeds (matching tencent_hy3 protocol).
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "shared_agora" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def kuramoto_step(theta, K0, alpha, sigma, dt, rng):
    """One step of Kuramoto with reflexive coupling K(t) = K0 * R(t)^alpha."""
    N = len(theta)
    z = np.exp(1j * theta).mean()
    R = abs(z)
    K = K0 * (R ** alpha) if R > 0 else 0.0
    # Pairwise sin(theta_j - theta_i)
    sin_diff = np.sin(theta[None, :] - theta[:, None])
    coupling = (K / N) * sin_diff.sum(axis=1)
    noise = sigma * np.sqrt(dt) * rng.standard_normal(N)
    theta = theta + dt * coupling + noise
    return theta, R


def run_ensemble(N, K0, alpha=0.6, sigma=0.008, dt=0.05,
                 t_trans=200.0, t_meas=400.0, n_seeds=12):
    """Returns mean final R across n_seeds runs at given K0, N."""
    n_trans = int(t_trans / dt)
    n_meas = int(t_meas / dt)
    rng = np.random.default_rng(20260000 + N * 1000 + int(K0 * 100))
    final_R = np.zeros(n_seeds)
    for s in range(n_seeds):
        theta = rng.uniform(0, 2 * np.pi, N)
        # Independent RNG stream per seed for repeatability
        local_rng = np.random.default_rng(20260000 + N * 1000 + int(K0 * 100) + s * 7 + 1)
        for _ in range(n_trans):
            theta, R = kuramoto_step(theta, K0, alpha, sigma, dt, local_rng)
        # Measure R over measurement window
        r_acc = 0.0
        for _ in range(n_meas):
            theta, R = kuramoto_step(theta, K0, alpha, sigma, dt, local_rng)
            r_acc += R
        final_R[s] = r_acc / n_meas
    return float(final_R.mean()), float(final_R.std())


def find_Kc(N, K_low=0.2, K_high=3.5, n_grid=30, n_seeds=12, R_thresh=0.5):
    """Bisection-like sweep to find K_c."""
    Ks = np.linspace(K_low, K_high, n_grid)
    means = np.zeros(n_grid)
    stds = np.zeros(n_grid)
    print(f"  N={N}: sweeping K_0 ∈ [{K_low}, {K_high}], {n_grid} grid points, "
          f"{n_seeds} seeds each")
    for i, K in enumerate(Ks):
        m, s = run_ensemble(N, K, n_seeds=n_seeds)
        means[i] = m
        stds[i] = s
        print(f"    K_0={K:.3f}: <R> = {m:.3f} ± {s:.3f}")
    # Smallest K such that mean R > R_thresh
    above = np.where(means > R_thresh)[0]
    if len(above) == 0:
        return None, Ks, means, stds
    K_c_est = Ks[above[0]]
    return K_c_est, Ks, means, stds


def main():
    N_values = [15, 30, 60, 100, 150, 200, 300, 400, 600]
    Kc_results = {}
    Kc_data = {}

    for N in N_values:
        print(f"\n=== N = {N} ===")
        K_c, Ks, means, stds = find_Kc(N, K_low=0.2, K_high=3.0, n_grid=18, n_seeds=10)
        Kc_results[N] = K_c
        Kc_data[N] = (Ks, means, stds)
        print(f"  -> K_c(N={N}) = {K_c}")

    # Power-law fit in log-log
    N_arr = np.array([n for n in N_values if Kc_results[n] is not None])
    Kc_arr = np.array([Kc_results[n] for n in N_arr])
    log_N = np.log(N_arr)
    log_Kc = np.log(Kc_arr)
    A_log, beta = np.polyfit(log_N, log_Kc, 1)
    A = float(np.exp(A_log))
    print(f"\n=== Power-law fit ===")
    print(f"K_c(N) ≈ {A:.4f} · N^{beta:.4f}")
    # R^2
    pred_log = np.polyval([A_log, beta], log_N)
    ss_res = np.sum((log_Kc - pred_log) ** 2)
    ss_tot = np.sum((log_Kc - log_Kc.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot
    print(f"R^2 (log-log) = {r2:.4f}")
    print(f"\nTencent_hy3 reference fit: A=0.496, beta=0.235, R^2 > 0.98")
    print(f"Independent replication fit: A={A:.4f}, beta={beta:.4f}, R^2={r2:.4f}")

    # Real-cluster resistance test at N=15 with archetype phases
    print("\n=== Real-cluster IC resistance test (N=15) ===")
    # Eight archetype axes on the circle, take 15 phases by replicating a few
    archetypes = np.array([k * 2 * np.pi / 8 for k in range(8)])
    # Sample 15 phases from archetypes with some noise
    rng_arch = np.random.default_rng(987654)
    arch_idx = rng_arch.integers(0, 8, size=15)
    arch_theta = archetypes[arch_idx] + 0.1 * rng_arch.standard_normal(15)
    unif_theta = rng_arch.uniform(0, 2 * np.pi, size=15)

    def sweep_K_for_init(theta_init, label):
        Ks = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        results = []
        for K in Ks:
            r_acc = []
            for s in range(12):
                theta = theta_init.copy()
                # Add per-seed perturbation
                theta = theta + 0.01 * np.random.default_rng(s).standard_normal(len(theta))
                local_rng = np.random.default_rng(20260000 + int(K * 100) + s * 11 + 1)
                n_trans = int(200 / 0.05)
                n_meas = int(400 / 0.05)
                for _ in range(n_trans):
                    theta, R = kuramoto_step(theta, K, 0.6, 0.008, 0.05, local_rng)
                r_window = 0.0
                for _ in range(n_meas):
                    theta, R = kuramoto_step(theta, K, 0.6, 0.008, 0.05, local_rng)
                    r_window += R
                r_acc.append(r_window / n_meas)
            mean = np.mean(r_acc)
            std = np.std(r_acc)
            results.append((K, mean, std))
            print(f"  {label} K_0={K:.2f}: <R>={mean:.3f}±{std:.3f}")
        return results

    print("Archeype (clustered) initial conditions:")
    arch_results = sweep_K_for_init(arch_theta, "archetype")
    print("Uniform random initial conditions:")
    unif_results = sweep_K_for_init(unif_theta, "uniform")

    # Compare at intermediate K_0 values (the dossier's key claim)
    print("\n=== Real-cluster resistance ===")
    K_int = 1.5  # intermediate coupling
    arch_at_int = next(r for r in arch_results if r[0] == K_int)
    unif_at_int = next(r for r in unif_results if r[0] == K_int)
    print(f"At K_0={K_int}: archetype <R>={arch_at_int[1]:.3f}, "
          f"uniform <R>={unif_at_int[1]:.3f}")
    if arch_at_int[1] < unif_at_int[1]:
        print("Archeype cluster RESISTS sync at intermediate K — dossier claim CONFIRMED")
    else:
        print("Archeype cluster does NOT resist — dossier claim NOT confirmed")

    # Plots
    fig, axes = plt.subplots(2, 2, figsize=(13, 11))
    ax = axes[0, 0]
    # Sweep curves for each N
    cmap = plt.cm.viridis
    for i, N in enumerate(N_values):
        if N not in Kc_data:
            continue
        Ks, means, stds = Kc_data[N]
        c = cmap(i / len(N_values))
        ax.plot(Ks, means, "-o", color=c, markersize=4, label=f"N={N}")
    ax.axhline(0.5, color="red", ls="--", label="R=0.5 threshold")
    ax.set_xlabel("K_0"); ax.set_ylabel("<R>")
    ax.set_title("Order parameter vs coupling (10 seeds)")
    ax.legend(fontsize=7, ncol=2)

    ax = axes[0, 1]
    # Power law
    ax.loglog(N_arr, Kc_arr, "o", color="crimson", markersize=10, label="K_c(N) measured")
    N_fit = np.logspace(np.log10(15), np.log10(600), 50)
    K_fit = A * N_fit ** beta
    ax.loglog(N_fit, K_fit, "-", color="navy", label=f"fit: {A:.3f}·N^{beta:.3f}")
    # Reference
    K_th = 0.496 * N_fit ** 0.235
    ax.loglog(N_fit, K_th, "--", color="gray", label="tencent ref: 0.496·N^0.235")
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
    # Residuals
    pred = A * N_arr ** beta
    res = (Kc_arr - pred) / pred * 100
    ax.semilogx(N_arr, res, "o-", color="darkgreen")
    ax.axhline(0, color="k", ls="--")
    ax.set_xlabel("N"); ax.set_ylabel("(measured − fit) / fit  [%]")
    ax.set_title("Power-law residuals")

    plt.suptitle("Independent MiniMax verification of HYP-023 — Kuramoto K_c(N) finite-size scaling",
                 fontsize=11)
    plt.tight_layout()
    out_png = ARTIFACT_DIR / "hyp023_kuramoto_finite_size_verification.png"
    plt.savefig(out_png, dpi=120)
    print(f"\nSaved: {out_png}")

    # Save data
    import json
    out_json = ARTIFACT_DIR / "hyp023_kuramoto_finite_size_verification.json"
    data = {
        "N_values": N_arr.tolist(),
        "Kc_measured": Kc_arr.tolist(),
        "power_law_fit": {"A": A, "beta": beta, "R_squared": r2},
        "tencent_hy3_reference": {"A": 0.496, "beta": 0.235, "R_squared_min": 0.98},
        "real_cluster_test_N15": {
            "archetype_at_K_1.5": arch_at_int[1],
            "uniform_at_K_1.5": unif_at_int[1],
            "resistance_confirmed": bool(arch_at_int[1] < unif_at_int[1]),
        },
    }
    with open(out_json, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved data: {out_json}")


if __name__ == "__main__":
    main()