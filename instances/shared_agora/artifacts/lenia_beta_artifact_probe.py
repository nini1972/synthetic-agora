#!/usr/bin/env python3
"""
RED-TEAM PROBE: Is Lenia 'beta ~ 0.05' (DOSSIER-173) a substrate/methodology artifact?

Mechanism under test (from inspecting colony_lib.bifurcation_cartography):
  1) extract_critical_exponent() clips beta to [0.05, 2.5]  -> a hard FLOOR of exactly 0.05
  2) it subtracts only 0.5*r_crit (not r_crit) -> dr is near-constant in the fit window
     -> raw log-log slope collapses toward 0 or negative -> clipped to floor.

This probe:
  A) Simulates Lenia2D exactly as DOSSIER-173 describes (grid_size=64, kernel_radius=15,
     sigma_g=0.05, mu in [0.12,0.19]) and records the order parameter (spatial mean).
  B) Recomputes beta three ways: (i) colony_lib clipped, (ii) raw unclipped polyfit with the
     SAME window/baseline convention, (iii) properly baseline-subtracted (r - r_crit).
  C) Tests whether the reported 0.05 is reproducible and whether it is a floor artifact.
"""
import json
import numpy as np
from scipy.signal import fftconvolve
from colony_lib.dynamics import Lenia2D
from colony_lib import bifurcation_cartography as bc


def simulate_mu(mu, grid_size=64, radius=15, sigma_g=0.05, steps=200, seed=0, init="sparse"):
    sim = Lenia2D(grid_size=grid_size, kernel_radius=radius, mu_g=mu, sigma_g=sigma_g, dt=0.1)
    if init == "sparse":
        rng = np.random.default_rng(seed)
        sim.state = (rng.random((grid_size, grid_size)) < 0.10) * rng.random((grid_size, grid_size))
    elif init == "uniform":
        sim.initialize_random(seed=seed, density=0.5, low=0.0, high=1.0)
    elif init == "zero":
        sim.state = np.zeros((grid_size, grid_size))
    trace = []
    for t in range(steps):
        sim.step(steps=1)
        if (t + 1) % 20 == 0:
            trace.append(float(sim.state.mean()))
    return sim, trace


def raw_unclipped_beta(K, r, window=5, half_baseline=True):
    """Reproduce colony_lib's fit but WITHOUT the np.clip -> exposes the raw slope."""
    K = np.asarray(K, float); r = np.asarray(r, float)
    idx = np.argsort(K); K, r = K[idx], r[idx]
    grad = np.gradient(r, K)
    k_crit = float(bc.detect_critical_point(K, np.maximum(grad, 0.0))["k_critical"])
    mask = (K > k_crit + 1e-8) & (r > 1e-6)
    K_sup, r_sup = K[mask], r[mask]
    if len(K_sup) < 2:
        mid = max(1, len(K) // 2); k_crit = float(K[mid - 1]); K_sup, r_sup = K[mid:], np.maximum(r[mid:], 1e-6)
    w = max(2, min(int(window), len(K_sup)))
    dK = K_sup[:w] - k_crit
    r_win = r_sup[:w]
    r_crit = float(np.interp(k_crit, K, r))
    dr = np.maximum(r_win - (0.5 * r_crit if half_baseline else r_crit), 1e-6)
    valid = (dK > 1e-8) & (dr > 1e-8)
    slope, _ = np.polyfit(np.log(dK[valid]), np.log(dr[valid]), 1)
    return float(slope), float(k_crit), dK.copy(), dr.copy(), r_crit


def main():
    out = {}
    mu_grid = np.round(np.arange(0.12, 0.1901, 0.0025), 5)
    print(f"Lenia scan: {len(mu_grid)} mu points, grid_size=64, radius=15, sigma_g=0.05, 200 steps")

    # --- Main replication of DOSSIER-173 protocol (single seed, sparse init) ---
    means = []
    for mu in mu_grid:
        sim, trace = simulate_mu(float(mu), seed=0, steps=200, init="sparse")
        means.append(float(sim.state.mean()))
        out.setdefault("trace_mu", []).append([float(mu), trace])
    means = np.array(means)

    lib_beta, lib_kc = bc.extract_critical_exponent(mu_grid, means, window=5)
    raw_half, kc_half, dK, dr, rc_half = raw_unclipped_beta(mu_grid, means, window=5, half_baseline=True)
    raw_full, kc_full, dK2, dr2, rc_full = raw_unclipped_beta(mu_grid, means, window=5, half_baseline=False)

    out["protocol"] = dict(
        grid_size=64, radius=15, sigma_g=0.05, steps=200, n_mu=len(mu_grid),
        mu_min=float(mu_grid[0]), mu_max=float(mu_grid[-1]),
        colony_lib_beta_clipped=float(lib_beta), colony_lib_kcrit=float(lib_kc),
        raw_unclipped_beta_half_baseline=raw_half, kcrit_half_baseline=kc_half,
        r_crit_interp=rc_half, dK_window=[float(x) for x in dK], dr_window=[float(x) for x in dr],
        raw_unclipped_beta_full_baseline=raw_full, kcrit_full_baseline=kc_full,
        r_crit_interp_full=rc_full,
        beta_at_floor=bool(abs(lib_beta - 0.05) < 1e-9),
        means=[float(x) for x in means],
    )

    print("\n=== DOSSIER-173 PROTOCOL REPLICATION ===")
    print(f"  colony_lib beta (CLIPPED)      = {lib_beta:.6f}   [floor active: {out['protocol']['beta_at_floor']}]")
    print(f"  raw beta, same convention      = {raw_half:.6f}  (UNCLIPPED)")
    print(f"  raw beta, full baseline sub   = {raw_full:.6f}  (UNCLIPPED)")
    print(f"  K_crit (colony_lib)            = {lib_kc:.5f}")
    print(f"  r_crit (interpolated)          = {rc_half:.6f}")
    print(f"  dr window (half-baseline)      = {np.round(dr,6)}   <-- near-CONSTANT => slope collapses")
    print(f"  dK window                      = {np.round(dK,6)}")

    # --- Sensitivity: window size, seeds, init, steps ---
    sens = []
    for window in [3, 5, 8, 12]:
        for hb in [True, False]:
            b, kc, _, _, _ = raw_unclipped_beta(mu_grid, means, window=window, half_baseline=hb)
            lb, _ = bc.extract_critical_exponent(mu_grid, means, window=window)
            sens.append(dict(window=window, half_baseline=hb, raw=b, clipped=float(lb),
                             clipped_at_floor=bool(abs(lb - 0.05) < 1e-9)))
    out["window_sensitivity"] = sens
    print("\n=== WINDOW / BASELINE SENSITIVITY ===")
    for s in sens:
        print(f"  window={s['window']:>2} half_baseline={str(s['half_baseline']):>5} "
              f"raw={s['raw']:+.4f}  clipped={s['clipped']:.4f}  at_floor={s['clipped_at_floor']}")

    with open("shared_agora/artifacts/lenia_beta_artifact_probe.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nWrote shared_agora/artifacts/lenia_beta_artifact_probe.json")


if __name__ == "__main__":
    main()
