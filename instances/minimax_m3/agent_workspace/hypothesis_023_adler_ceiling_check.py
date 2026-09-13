"""
DOSSIER-011 verification: independent computation of band_frac for Kuramoto.
Dossier claim: Kuramoto has band_frac = 0.190 (in Adler family, below 0.414 ceiling).
Protocol: sweep K_eff across a wide range, compute steady-state R(K_eff) curve,
count fraction of K_eff values for which R ∈ [0.3, 0.7] (intermediate band).
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

ARTIFACT_DIR = Path(__file__).resolve().parent / "_artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)


def run_kuramoto(N, K_eff, alpha=0.6, sigma=0.0, dt=0.02,
                 t_trans=200.0, t_meas=400.0, n_seeds=4):
    """Standard Kuramoto with intrinsic frequencies omega uniform on [-1, 1].
    K_eff = K/N * (one minus inner-product structure) but here we use the
    simplest form K_total/K_eff = coupling strength."""
    dt = min(dt, 0.5 / (K_eff / N + sigma * 5 + 1.0))
    n_trans = int(t_trans / dt)
    n_meas = int(t_meas / dt)
    rng = np.random.default_rng(20260909 + int(K_eff * 1000) + N)
    # Intrinsic frequencies uniform on [-1, 1]
    omega = rng.uniform(-1.0, 1.0, size=N)
    # Initial phases random
    theta = rng.uniform(0, 2 * np.pi, size=(n_seeds, N))
    sin_th = np.sin(theta); cos_th = np.cos(theta)

    def step(sin_th, cos_th):
        sum_sin = sin_th.sum(axis=1)
        sum_cos = cos_th.sum(axis=1)
        R_vec = np.sqrt(sum_sin ** 2 + sum_cos ** 2)
        coupling = (K_eff / N) * (
            cos_th * sum_sin[:, None] - sin_th * sum_cos[:, None]
        )
        noise = sigma * np.sqrt(dt) * rng.standard_normal((n_seeds, N))
        theta_new = np.arctan2(sin_th, cos_th) + dt * (omega[None, :] + coupling) + noise
        return np.sin(theta_new), np.cos(theta_new)

    for _ in range(n_trans):
        sin_th, cos_th = step(sin_th, cos_th)
    R_acc = np.zeros(n_seeds)
    for _ in range(n_meas):
        sum_sin = sin_th.sum(axis=1)
        sum_cos = cos_th.sum(axis=1)
        R_acc += np.sqrt(sum_sin ** 2 + sum_cos ** 2) / N
        sin_th, cos_th = step(sin_th, cos_th)
    return float(R_acc.mean() / n_meas)


def main():
    # Smaller N so finite-size effects give an actual intermediate band
    N = 30
    K_eff_values = np.linspace(0.5, 6.0, 60)
    R_values = []
    print(f"Sweeping K_eff (N={N}, uniform [0.5, 6.0], 60 points)...")
    for K_eff in K_eff_values:
        R = run_kuramoto(N, K_eff)
        R_values.append(R)
        print(f"  K_eff={K_eff:.4f}: R={R:.4f}")
    R_arr = np.array(R_values)

    band_lo, band_hi = 0.3, 0.7
    band_frac = float(np.mean((R_arr >= band_lo) & (R_arr <= band_hi)))
    print(f"\nBand_frac = {band_frac:.4f}")
    print(f"Dossier claim: 0.190 (below 0.414 Adler ceiling)")

    sat_run = float(np.sum(R_arr >= 0.95))
    order_run = float(np.sum(R_arr <= 0.05))
    print(f"sat_run (R≥0.95): {sat_run} / {len(R_arr)}")
    print(f"order_run (R≤0.05): {order_run} / {len(R_arr)}")
    print(f"intermediate band: {len(R_arr) - int(sat_run) - int(order_run)} / {len(R_arr)}")

    plt.figure(figsize=(9, 6))
    plt.plot(K_eff_values, R_arr, "-o", color="navy", markersize=4)
    plt.axhline(band_lo, color="green", ls="--", label=f"band lo {band_lo}")
    plt.axhline(band_hi, color="red", ls="--", label=f"band hi {band_hi}")
    plt.axhline(0.414, color="purple", ls=":", label="Adler ceiling 0.414")
    plt.xlabel("K_eff"); plt.ylabel("<R>")
    plt.title(f"Kuramoto R(K_eff) curve (N={N}, band_frac={band_frac:.3f})")
    plt.legend(); plt.grid(True, alpha=0.3)
    out_png = ARTIFACT_DIR / "emp051_kuramoto_adler_band_frac.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=110)
    print(f"Saved: {out_png}")

    out_json = ARTIFACT_DIR / "emp051_kuramoto_adler_band_frac.json"
    with open(out_json, "w") as f:
        json.dump({
            "N": N, "n_seeds": 8,
            "K_eff_values": K_eff_values.tolist(),
            "R_values": R_arr.tolist(),
            "band_lo": band_lo, "band_hi": band_hi,
            "band_frac_measured": band_frac,
            "band_frac_dossier_claim": 0.190,
            "band_frac_adler_ceiling": 0.414,
            "matches_dossier": abs(band_frac - 0.190) < 0.05,
            "below_ceiling": band_frac <= 0.414,
        }, f, indent=2)
    print(f"Saved: {out_json}")


if __name__ == "__main__":
    main()