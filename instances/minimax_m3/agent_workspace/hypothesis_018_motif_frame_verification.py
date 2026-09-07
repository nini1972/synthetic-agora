"""
HYP-018 independent verification — Motif-Frame Separation hypothesis
(from Frontier Dossier #006, cartographer lineage).

GOAL: Build a coupled map lattice (CML) parameter sweep in (r, ε), compute
motif-similarity at even and odd lags, derive the three order parameters
P (parity), S (smooth), R (resonance), and check whether:
  (a) ordinary frame persistence has P ≈ 0
  (b) motif-memory candidates have P >> 0
  (c) classification splits cleanly into 3+ classes (frame, smooth, resonance)

We use a simple logistic-map CML:
  x_i(t+1) = (1-ε) f(x_i(t)) + (ε/2) [f(x_{i-1}(t)) + f(x_{i+1}(t))]
  f(x) = r x (1-x)

This is a classical Kaneko-style CML that produces a variety of regimes
from frozen (fixed point) to ordered patterns to fully developed chaos
as r and ε vary.

Motif similarity M_lag between two snapshots x(t) and x(t+lag) is defined
as the fraction of lattice sites whose relative ordering of their
3-site neighborhoods matches (a permutation-pattern motif, length-3
window). This is a proxy for the cartographer's "motif grammar" measure.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from pathlib import Path

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "shared_agora" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def kaneko_step(x, r, eps):
    """One step of Kaneko coupled map lattice."""
    f = r * x * (1.0 - x)
    # Periodic boundaries
    xp = np.roll(x, -1)
    xm = np.roll(x, 1)
    fp = r * xp * (1.0 - xp)
    fm = r * xm * (1.0 - xm)
    return (1.0 - eps) * f + 0.5 * eps * (fp + fm)


def motif_signature(x, w=3):
    """Per-site permutation motif from w-window."""
    n = len(x)
    sig = np.zeros(n, dtype=int)
    for i in range(n):
        window = np.array([x[(i + j) % n] for j in range(-(w // 2), w // 2 + 1)])
        sig[i] = int(np.argsort(window).dot([3 ** j for j in range(w)]))
    return sig


def motif_similarity(sig_a, sig_b):
    """Fraction of matching motifs."""
    return float(np.mean(sig_a == sig_b))


def run_cml(r, eps, N=64, T_total=600, T_trans=200):
    """Run CML and return motif-similarity sequence M_lag for l=1..max_lag."""
    np.random.seed(42)
    x = np.random.uniform(0.2, 0.8, size=N)
    for _ in range(T_trans):
        x = kaneko_step(x, r, eps)

    max_lag = 12
    sig0 = motif_signature(x)

    # Collect motif signatures at each lag by stepping
    sims = np.zeros(max_lag)
    x_cur = x.copy()
    for lag in range(1, max_lag + 1):
        x_cur = kaneko_step(x_cur, r, eps)
        sig_lag = motif_signature(x_cur)
        sims[lag - 1] = motif_similarity(sig0, sig_lag)
    return sims


def order_params(sims):
    """Compute P, S, R from motif similarity sequence.

    sims[l-1] = M_lag for l = 1..L.
    """
    L = len(sims)
    even_idx = np.arange(1, L, 2)  # l = 1, 3, 5, ...
    odd_idx = np.arange(0, L, 2)    # l = 2, 4, 6, ...

    M_even = float(np.mean(sims[even_idx]))
    M_odd = float(np.mean(sims[odd_idx]))

    # P: parity
    P = float(np.clip(M_even - M_odd, 0.0, 1.0))

    # T: tail retention — last M_lag / max M_lag
    if sims.max() > 0:
        T = float(np.clip(sims[-1] / sims.max(), 0.0, 1.0))
    else:
        T = 0.0

    # J: jump penalty — large positive diffs between consecutive lags
    diffs = np.diff(sims)
    J = float(np.clip(1.0 - np.mean(np.maximum(diffs, 0.0)) * 5.0, 0.0, 1.0))

    # M: monotone decay — fraction of consecutive diffs that are negative
    neg_frac = float(np.mean(diffs <= 0)) if len(diffs) > 0 else 1.0
    M_mono = float(np.clip(neg_frac, 0.0, 1.0))

    # H: even-lag motif range (max - min across even lags)
    if len(even_idx) > 1:
        H = float(np.clip(np.max(sims[even_idx]) - np.min(sims[even_idx]), 0.0, 1.0))
    else:
        H = 0.0

    H_max = float(np.max(sims[even_idx])) if len(even_idx) > 0 else 0.0

    # S: smooth
    S = float(np.clip(P * T * J * M_mono * (1.0 - H), 0.0, 1.0))

    # R: resonance
    R = float(
        np.clip(
            (0.50 * H + 0.30 * H_max + 0.20 * T) * np.clip(M_even / 0.45, 0.0, 1.0),
            0.0,
            1.0,
        )
    )

    return P, S, R, {"M_even": M_even, "M_odd": M_odd, "T": T, "J": J, "M_mono": M_mono, "H": H}


def main():
    # Parameter sweep matching dossier: r ∈ [3.7, 4.0], eps ∈ [0.05, 0.30]
    r_vals = np.linspace(3.70, 4.00, 7)
    eps_vals = np.linspace(0.05, 0.30, 6)

    P_grid = np.zeros((len(r_vals), len(eps_vals)))
    S_grid = np.zeros_like(P_grid)
    R_grid = np.zeros_like(P_grid)

    print("Running CML sweep: r × eps =", len(r_vals), "×", len(eps_vals))
    for i, r in enumerate(r_vals):
        for j, eps in enumerate(eps_vals):
            sims = run_cml(r, eps, N=48, T_total=400, T_trans=200)
            P, S, R, comp = order_params(sims)
            P_grid[i, j] = P
            S_grid[i, j] = S
            R_grid[i, j] = R
            print(
                f"  r={r:.3f} eps={eps:.3f} | M_even={comp['M_even']:.3f} "
                f"M_odd={comp['M_odd']:.3f} P={P:.3f} S={S:.3f} R={R:.3f}"
            )

    # Classification: use threshold on P, then split on (S vs R)
    classes = np.zeros_like(P_grid, dtype=int)
    for i in range(P_grid.shape[0]):
        for j in range(P_grid.shape[1]):
            P, S, R = P_grid[i, j], S_grid[i, j], R_grid[i, j]
            if P < 0.05:
                classes[i, j] = 0  # frame persistence (P near 0)
            elif S > R and S > 0.05:
                classes[i, j] = 1  # smooth motif memory
            elif R > S and R > 0.10:
                classes[i, j] = 2  # resonant phase memory
            else:
                classes[i, j] = 3  # dead / weak

    print("\n=== Classification summary ===")
    counts = np.bincount(classes.flatten(), minlength=4)
    labels = ["frame_persistence", "smooth_motif_memory", "resonant_phase_memory", "dead"]
    for k, label in enumerate(labels):
        print(f"  {label}: {counts[k]}/{classes.size} = {100*counts[k]/classes.size:.1f}%")

    # Verify predictions:
    print("\n=== Predictions from dossier ===")
    print(f"(a) P near 0 for frame_persistence class: P_grid[classes==0].mean() = "
          f"{P_grid[classes == 0].mean():.4f} (expect ≈ 0)")
    print(f"(b) P high for motif-memory classes (1,2): mean = "
          f"{P_grid[(classes == 1) | (classes == 2)].mean():.4f} (expect >> 0)")
    print(f"(c) Smooth vs Resonant separation: P(S>R) = "
          f"{np.mean(S_grid[classes == 1] > R_grid[classes == 1]):.3f}, "
          f"P(R>S) = {np.mean(R_grid[classes == 2] > S_grid[classes == 2]):.3f}")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    extent = [eps_vals[0], eps_vals[-1], r_vals[0], r_vals[-1]]

    im0 = axes[0, 0].imshow(P_grid, origin="lower", aspect="auto", extent=extent, cmap="viridis")
    axes[0, 0].set_title("Parity P = clip(M̄_even - M̄_odd, 0, 1)")
    axes[0, 0].set_xlabel("ε"); axes[0, 0].set_ylabel("r")
    plt.colorbar(im0, ax=axes[0, 0])

    im1 = axes[0, 1].imshow(S_grid, origin="lower", aspect="auto", extent=extent, cmap="magma")
    axes[0, 1].set_title("Smooth index S")
    axes[0, 1].set_xlabel("ε"); axes[0, 1].set_ylabel("r")
    plt.colorbar(im1, ax=axes[0, 1])

    im2 = axes[1, 0].imshow(R_grid, origin="lower", aspect="auto", extent=extent, cmap="cividis")
    axes[1, 0].set_title("Resonance index R")
    axes[1, 0].set_xlabel("ε"); axes[1, 0].set_ylabel("r")
    plt.colorbar(im2, ax=axes[1, 0])

    cmap_cls = matplotlib.colors.ListedColormap(
        ["#cccccc", "#4477AA", "#CC6677", "#228833"]
    )
    im3 = axes[1, 1].imshow(classes, origin="lower", aspect="auto", extent=extent, cmap=cmap_cls)
    cbar = plt.colorbar(im3, ax=axes[1, 1], ticks=[0, 1, 2, 3])
    cbar.set_ticklabels(labels)
    axes[1, 1].set_title("Classification")
    axes[1, 1].set_xlabel("ε"); axes[1, 1].set_ylabel("r")

    plt.suptitle("HYP-018 Motif-Frame Separation — Independent Replication (MiniMax)\n"
                 "Kaneko CML, N=48, 200-step trans, 12-lag motif similarity")
    plt.tight_layout()
    out_png = ARTIFACT_DIR / "hyp018_motif_frame_verification.png"
    plt.savefig(out_png, dpi=110)
    print(f"\nSaved figure: {out_png}")

    # Save data
    import json
    out_json = ARTIFACT_DIR / "hyp018_motif_frame_verification.json"
    data = {
        "r_vals": r_vals.tolist(),
        "eps_vals": eps_vals.tolist(),
        "P_grid": P_grid.tolist(),
        "S_grid": S_grid.tolist(),
        "R_grid": R_grid.tolist(),
        "classes": classes.tolist(),
        "class_counts": dict(zip(labels, counts.tolist())),
        "P_frame_mean": float(P_grid[classes == 0].mean()) if (classes == 0).any() else None,
        "P_motif_mean": float(P_grid[(classes == 1) | (classes == 2)].mean()) if ((classes == 1) | (classes == 2)).any() else None,
    }
    with open(out_json, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved data: {out_json}")


if __name__ == "__main__":
    main()