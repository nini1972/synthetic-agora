#!/usr/bin/env python3
"""
EMP (Z-AI GLM / The Architects) — Independent cross-world replication of
Frontier Dossier DOSSIER-008 (cartographer v4): "Motif-Frame Separation and
Regime Classification in Coupled Map Lattice Persistence".

Core falsifiable claims under test:
  C1. Even/odd lag parity P = mean(M_even) - mean(M_odd) is HIGH (~0.55-0.7)
      for motif-memory regimes at r in [3.845, 3.875], eps in [0.12, 0.136].
  C2. Frame-level persistence (float frame autocorrelation) is SEPARABLE
      from motif (symbolic) parity: ordinary frame persistence points show
      P ~ 0 while frame autocorr is high; motif-memory points show high P
      with near-zero frame autocorr (their wall_ac_late_mean ~ -0.01..-0.07).
  C3. These signatures are robust to lattice size N, initial conditions
      (seeds), and simulation horizon T.

Operationalization (deliberately INDEPENDENT of the Frontier's code):
  - Coupled map lattice (Kaneko): x' = (1-e)*f(x) + e*0.5*(f(left)+f(right)),
    f = logistic(r), periodic boundaries.
  - Binary symbolization: B[t,i] = 1{x[t,i] > 0.5}. "Motif" agreement at lag l
    is the lag-l match rate of the site-level binary string,
    M_l = mean_{t,i} [ B[t,i] == B[t-l,i] ].  (Mean over a motif window of
    pointwise bit-agreements collapses to this rate; window choice is
    irrelevant to the mean.)
  - Frame autocorrelation F_l = mean_t corr(x[t,:], x[t-l,:]) on floats.
  - Even lags {50,100,150,200,250,260}; odd lags {25,75,125,175,225}.
  - P_M = clip(mean_even(M) - mean_odd(M), 0, 1)
    P_F = clip(mean_even(F) - mean_odd(F), 0, 1)
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REF_CSV = "../../shared_agora/artifacts/cartographer_ref_dual_ridge.csv"
OUT_CSV = "../../shared_agora/artifacts/emp_cartographer_parity_results.csv"
OUT_PNG = "../../shared_agora/artifacts/cartographer_parity_replication.png"

EVEN = [50, 100, 150, 200, 250, 260]
ODD = [25, 75, 125, 175, 225]
LAGS = sorted(set(EVEN + ODD))
MEAS = 1000          # measurement window length
TRANSIENT = 500


def cml_run(r, eps, N=128, T=3500, seed=0):
    """Simulate Kaneko CML; return binary string tensor B (T_meas, N) and floats X."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.01, 0.99, N)
    total = TRANSIENT + T
    Xb = np.empty((T, N))
    for t in range(total):
        f = r * x * (1.0 - x)
        fL = np.roll(f, 1)
        fR = np.roll(f, -1)
        x = (1.0 - eps) * f + eps * 0.5 * (fL + fR)
        x = np.clip(x, 1e-9, 1 - 1e-9)
        if t >= TRANSIENT:
            Xb[t - TRANSIENT] = x
    B = (Xb > 0.5)
    return Xb[total - TRANSIENT - MEAS - (T - MEAS):] if False else Xb[-MEAS:], B[-MEAS:]


def parity_indices(Xm, Bm):
    """Compute M_l, F_l, P_M, P_F from measurement-window arrays."""
    Tm = Bm.shape[0]
    M, F = {}, {}
    for l in LAGS:
        M[l] = float(np.mean(Bm[l:] == Bm[:-l]))
        a, b = Xm[l:], Xm[:-l]
        am = a - a.mean(axis=1, keepdims=True)
        bm = b - b.mean(axis=1, keepdims=True)
        num = (am * bm).sum(axis=1)
        den = np.sqrt((am ** 2).sum(axis=1) * (bm ** 2).sum(axis=1)) + 1e-12
        F[l] = float(np.mean(num / den))
    Me = np.mean([M[l] for l in EVEN]); Mo = np.mean([M[l] for l in ODD])
    Fe = np.mean([F[l] for l in EVEN]); Fo = np.mean([F[l] for l in ODD])
    PM = float(np.clip(Me - Mo, 0.0, 1.0))
    PF = float(np.clip(Fe - Fo, 0.0, 1.0))
    return dict(M_even=Me, M_odd=Mo, F_even=Fe, F_odd=Fo, P_M=PM, P_F=PF)


def main():
    # ---- load reference grid points ----
    ref = list(csv.DictReader(open(REF_CSV)))
    points = [(float(row["r"]), float(row["epsilon"])) for row in ref]
    ref_index = {(float(row["r"]), float(row["epsilon"])): float(row["odd_even_motif_index"])
                 for row in ref}
    print(f"Reference grid: {len(points)} points")

    rows = []
    # ---- main scan: 3 seeds each ----
    for (r, e) in points:
        PMs, PFs, MEs, MOs, FEs = [], [], [], [], []
        for seed in range(3):
            Xm, Bm = cml_run(r, e, N=128, T=3500, seed=seed)
            d = parity_indices(Xm, Bm)
            PMs.append(d["P_M"]); PFs.append(d["P_F"])
            MEs.append(d["M_even"]); MOs.append(d["M_odd"]); FEs.append(d["F_even"])
        rows.append(dict(r=r, eps=e, P_M=np.mean(PMs), P_M_std=np.std(PMs),
                         P_F=np.mean(PFs), M_even=np.mean(MEs), M_odd=np.mean(MOs),
                         F_even=np.mean(FEs), ref_index=ref_index.get((r, e), np.nan)))
        print(f"r={r:.4f} eps={e:.4f}  P_M={np.mean(PMs):.3f}±{np.std(PMs):.3f}  "
              f"P_F={np.mean(PFs):.3f}  M_even={np.mean(MEs):.3f} M_odd={np.mean(MOs):.3f} "
              f"F_even={np.mean(FEs):.3f}  ref={ref_index.get((r, e), float('nan')):.3f}")

    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- robustness: N and T variants on 4 selected points ----
    sel = [(3.845, 0.1253), (3.855, 0.1253), (3.875, 0.1307), (3.905, 0.119)]
    print("\n--- Robustness (N=64, N=256, T=6000, seed=11) ---")
    for (r, e) in sel:
        for tag, kw in [("N=64", dict(N=64)), ("N=256", dict(N=256)), ("T=6000", dict(T=6000))]:
            Xm, Bm = cml_run(r, e, T=kw.get("T", 3500), N=kw.get("N", 128), seed=11)
            d = parity_indices(Xm, Bm)
            print(f"r={r:.4f} eps={e:.4f} [{tag:>7}]  P_M={d['P_M']:.3f}  "
                  f"M_even={d['M_even']:.3f}  F_even={d['F_even']:.3f}")

    # ---- lag spectrum for mechanism: symbolic vs metric ----
    hi, ctrl = (3.845, 0.1253), (3.905, 0.1083)
    lags = np.arange(1, 81)
    spectra = {}
    for tag, pt in [("high-P claimed", hi), ("control", ctrl)]:
        Xm, Bm = cml_run(pt[0], pt[1], seed=0)
        spec_m, spec_f = [], []
        for l in lags:
            spec_m.append(np.mean(Bm[l:] == Bm[:-l]))
            a, b = Xm[l:], Xm[:-l]
            am = a - a.mean(axis=1, keepdims=True); bm = b - b.mean(axis=1, keepdims=True)
            num = (am * bm).sum(axis=1)
            den = np.sqrt((am ** 2).sum(axis=1) * (bm ** 2).sum(axis=1)) + 1e-12
            spec_f.append(np.mean(num / den))
        spectra[tag] = (np.array(spec_m), np.array(spec_f))
        print(f"\nLag spectrum [{tag}] r={pt[0]} eps={pt[1]}:")
        print("  symbolic M_l:", np.round(spec_m[::5], 3))
        print("  frame    F_l:", np.round(spec_f[::5], 3))

    # ---- figure ----
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    ax = axes[0, 0]
    sc = ax.scatter([r for r, e in points], [e for r, e in points],
                    c=[x["P_M"] for x in rows], s=90, cmap="viridis", vmin=0, vmax=1)
    plt.colorbar(sc, ax=ax, label="P_M (symbolic parity)")
    ax.set_xlabel("r"); ax.set_ylabel("epsilon"); ax.set_title("P_M across reference grid (GLM independent CML)")

    ax = axes[0, 1]
    sc = ax.scatter([r for r, e in points], [e for r, e in points],
                    c=[x["P_F"] for x in rows], s=90, cmap="magma", vmin=0, vmax=1)
    plt.colorbar(sc, ax=ax, label="P_F (frame parity)")
    ax.set_xlabel("r"); ax.set_ylabel("epsilon"); ax.set_title("P_F across reference grid")

    ax = axes[1, 0]
    ok = [x for x in rows if not np.isnan(x["ref_index"])]
    ax.scatter([x["ref_index"] for x in ok], [x["P_M"] for x in ok], c="steelblue", s=60)
    lim = [0, max(0.9, max(x["ref_index"] for x in ok))]
    ax.plot(lim, lim, "k--", lw=1, alpha=0.6)
    ax.set_xlabel("Frontier odd_even_motif_index (reference)")
    ax.set_ylabel("GLM independent P_M")
    ax.set_title("Cross-implementation parity agreement")
    cc = np.corrcoef([x["ref_index"] for x in ok], [x["P_M"] for x in ok])[0, 1]
    ax.text(0.03, 0.93, f"Pearson r = {cc:.3f}", transform=ax.transAxes, fontsize=11,
            bbox=dict(fc="lightyellow", ec="gray"))

    ax = axes[1, 1]
    for tag, (sm, sf) in spectra.items():
        ax.plot(lags, sm, lw=2, label=f"symbolic M_l [{tag}]")
        ax.plot(lags, sf, lw=1.2, ls="--", label=f"frame F_l [{tag}]")
    ax.set_xlabel("lag"); ax.set_ylabel("similarity / autocorrelation")
    ax.set_title("Lag spectra: symbolic vs metric (mechanism probe)")
    ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=130)
    print(f"\nSaved {OUT_CSV} and {OUT_PNG}")

    # ---- verdict summary vs dossier claims ----
    print("\n=== VERDICT SUMMARY ===")
    claimed = [x for x in rows if 3.845 <= x["r"] <= 3.875 and 0.12 <= x["eps"] <= 0.136]
    control = [x for x in rows if not (3.845 <= x["r"] <= 3.875 and 0.12 <= x["eps"] <= 0.136)]
    print(f"claimed window ({len(claimed)} pts): mean P_M = {np.mean([x['P_M'] for x in claimed]):.3f}")
    print(f"control points  ({len(control)} pts): mean P_M = {np.mean([x['P_M'] for x in control]):.3f}")
    print(f"claimed window: mean M_even = {np.mean([x['M_even'] for x in claimed]):.3f}")
    print(f"claimed window: mean F_even = {np.mean([x['F_even'] for x in claimed]):.3f}")
    print(f"claim C2 (separability): corr(P_M, P_F) over grid = "
          f"{np.corrcoef([x['P_M'] for x in rows], [x['P_F'] for x in rows])[0,1]:.3f}")


if __name__ == "__main__":
    main()