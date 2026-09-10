"""
HYP-023 v3 — proper K range and finer grid.
Tencent predicts K_c(N=15) ≈ 0.91, K_c(N=400) ≈ 2.4.
Use K_low=0.05 (well below any expected K_c) and K_high=3.0.
Finer 12-point grid. Same sin-trick O(N) update.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "shared_agora" / "artifacts"


def run_ensemble(N, K0, alpha=0.6, sigma=0.008, dt=0.05,
                 t_trans=80.0, t_meas=200.0, n_seeds=6):
    n_trans = int(t_trans / dt)
    n_meas = int(t_meas / dt)
    rng = np.random.default_rng(20260000 + N * 7 + int(K0 * 100) + 3)
    theta = rng.uniform(0, 2 * np.pi, size=(n_seeds, N))
    sin_th = np.sin(theta); cos_th = np.cos(theta)
    for _ in range(n_trans):
        sum_sin = sin_th.sum(axis=1)
        sum_cos = cos_th.sum(axis=1)
        R = np.sqrt(sum_sin ** 2 + sum_cos ** 2) / N
        K_t = K0 * (R ** alpha)
        coupling = (K_t[:, None] / N) * (
            cos_th * sum_sin[:, None] - sin_th * sum_cos[:, None]
        )
        noise = sigma * np.sqrt(dt) * rng.standard_normal((n_seeds, N))
        theta_new = np.arctan2(sin_th, cos_th) + dt * coupling + noise
        sin_th = np.sin(theta_new); cos_th = np.cos(theta_new)
    R_acc = np.zeros(n_seeds)
    for _ in range(n_meas):
        sum_sin = sin_th.sum(axis=1)
        sum_cos = cos_th.sum(axis=1)
        R = np.sqrt(sum_sin ** 2 + sum_cos ** 2) / N
        K_t = K0 * (R ** alpha)
        coupling = (K_t[:, None] / N) * (
            cos_th * sum_sin[:, None] - sin_th * sum_cos[:, None]
        )
        noise = sigma * np.sqrt(dt) * rng.standard_normal((n_seeds, N))
        theta_new = np.arctan2(sin_th, cos_th) + dt * coupling + noise
        sin_th = np.sin(theta_new); cos_th = np.cos(theta_new)
        R_acc += R
    final_R = R_acc / n_meas
    return float(final_R.mean()), float(final_R.std())


def find_Kc(N, K_low=0.05, K_high=3.0, n_grid=12, n_seeds=6, R_thresh=0.5):
    Ks = np.linspace(K_low, K_high, n_grid)
    means = np.zeros(n_grid)
    stds = np.zeros(n_grid)
    for i, K in enumerate(Ks):
        m, s = run_ensemble(N, K, n_seeds=n_seeds)
        means[i] = m
        stds[i] = s
        print(f"  N={N} K={K:.3f}: <R>={m:.3f}±{s:.3f}")
    above = np.where(means > R_thresh)[0]
    if len(above) == 0:
        return None, Ks, means, stds
    return float(Ks[above[0]]), Ks, means, stds


def main():
    N_values = [15, 60, 150, 400]
    Kc_results = {}
    Kc_data = {}
    for N in N_values:
        print(f"\n=== N = {N} ===")
        K_c, Ks, means, stds = find_Kc(N, n_grid=12, n_seeds=6)
        Kc_results[N] = K_c
        Kc_data[N] = (Ks, means, stds)
        print(f"=> K_c(N={N}) = {K_c}\n")

    valid = [(n, Kc_results[n]) for n in N_values if Kc_results[n] is not None]
    if len(valid) < 2:
        print("Not enough valid K_c points for fit")
        return
    N_arr = np.array([n for n, _ in valid])
    Kc_arr = np.array([k for _, k in valid])
    log_N = np.log(N_arr)
    log_Kc = np.log(Kc_arr)
    A_log, beta = np.polyfit(log_N, log_Kc, 1)
    A = float(np.exp(A_log))
    pred_log = np.polyval([A_log, beta], log_N)
    ss_res = np.sum((log_Kc - pred_log) ** 2)
    ss_tot = np.sum((log_Kc - log_Kc.mean()) ** 2)
    r2 = 1.0 - ss_res / max(ss_tot, 1e-10)
    print(f"=== Fit: K_c(N) ≈ {A:.4f}·N^{beta:.4f}, R^2={r2:.4f} ===")
    print(f"Tencent ref: A=0.496, beta=0.235, R^2>0.98")
    A_diff = abs(A - 0.496) / 0.496 * 100
    beta_diff = abs(beta - 0.235) / 0.235 * 100
    print(f"Relative diff: A={A_diff:.1f}%, beta={beta_diff:.1f}%")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    cmap = plt.cm.viridis
    for i, N in enumerate(N_values):
        if N not in Kc_data:
            continue
        Ks, means, stds = Kc_data[N]
        c = cmap(i / len(N_values))
        ax.errorbar(Ks, means, yerr=stds, fmt="-o", color=c, markersize=4,
                    capsize=2, label=f"N={N}")
    ax.axhline(0.5, color="red", ls="--", label="R=0.5 threshold")
    ax.set_xlabel("K_0"); ax.set_ylabel("<R>")
    ax.set_title("Order parameter vs coupling (O(N) update, 6 seeds)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.loglog(N_arr, Kc_arr, "o", color="crimson", markersize=10, label="measured")
    N_fit = np.logspace(np.log10(10), np.log10(500), 50)
    K_fit = A * N_fit ** beta
    K_th = 0.496 * N_fit ** 0.235
    ax.loglog(N_fit, K_fit, "-", color="navy", label=f"fit {A:.3f}·N^{beta:.3f}")
    ax.loglog(N_fit, K_th, "--", color="gray", label="tencent ref 0.496·N^0.235")
    ax.set_xlabel("N"); ax.set_ylabel("K_c")
    ax.set_title(f"Finite-size scaling (R^2={r2:.3f})")
    ax.legend(); ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    out_png = ARTIFACT_DIR / "hyp023_kuramoto_finite_size_verification.png"
    plt.savefig(out_png, dpi=110)
    print(f"Saved: {out_png}")

    out_json = ARTIFACT_DIR / "hyp023_kuramoto_finite_size_verification.json"
    with open(out_json, "w") as f:
        json.dump({
            "N_values": N_arr.tolist(),
            "Kc_measured": Kc_arr.tolist(),
            "fit": {"A": A, "beta": beta, "R_squared": r2},
            "tencent_ref": {"A": 0.496, "beta": 0.235, "R_squared_min": 0.98},
            "fit_divergence_pct": {"A": A_diff, "beta": beta_diff},
        }, f, indent=2)
    print(f"Saved: {out_json}")


if __name__ == "__main__":
    main()