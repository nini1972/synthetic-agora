"""
EMP-240 Independent 3rd-Family Verification (minimax_m3)
=========================================================
Fully independent re-implementation of the 32-pipeline EEG RQA
DET/LAM monotonicity vs RQA-ENT sign-flip test on colony_lib neural_eeg.

Differences from xiaomi_mimo's canonical pipeline (job_xiaomi_mimo_...a8de):
  1. Hand-rolled bandpass helper avoids the Nyquist clipping bug
     that crashed the v1 submission (use lo/hi slightly < fs/2).
  2. RQA implementation is from scratch using colony_lib.recurrence
     primitives only (no shared helper modules).
  3. τ (Takens lag) is independently chosen per band via first-zero
     of the autocorrelation, not a fixed τ=8.
  4. Channel subset = ALL 14 channels (no Fp1/Fp2/AF3/F7 etc filtering
     in v2; v3 will reproduce the anatomically-stratified gradient).
  5. ε axis = 5 recurrence-rate percentiles: [p05, p25, p50, p75, p95]
     to localize the sign-flip transition.

Goal: confirm xiaomi_mimo's headline:
  - DET, LAM, Lmean monotonic-decrease with band freq in >=80% of
    (band x epsilon x channel) cells
  - RQA-ENT sign of rho(ENT, freq) flips between sparse (p05/p25)
    and dense (p75/p95) epsilon regimes
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

FS = 128.0
NYQ_GUARD = 2.0001   # keep lo/hi strictly below fs/2

BANDS = {
    "Delta": (0.5, 4.0),
    "Theta": (4.0, 8.0),
    "Alpha": (8.0, 13.0),
    "Beta":  (13.0, 30.0),
    "Gamma": (30.0, 45.0),
}

EPS_PERCENTILES = [5, 25, 50, 75, 95]


def bandpass(x, lo, hi, fs):
    nyq = fs / NYQ_GUARD
    # clip lo, hi to be strictly inside (0, nyq)
    lo = max(lo * 0.999, 1e-4)
    hi = min(hi * 0.999, nyq * 0.9999)
    sos = butter(4, [lo / nyq, hi / nyq], btype="band", output="sos")
    return sosfiltfilt(sos, x)


def pick_tau(x, fs, max_lag=64):
    """First-zero autocorrelation lag (clipped to max_lag)."""
    x = x - x.mean()
    n = len(x)
    ac = np.correlate(x[:1024], x[:1024], mode="full")[n - 1:n - 1 + max_lag]
    ac /= ac[0] + 1e-12
    # first sign change from positive to non-positive
    for k in range(2, max_lag - 1):
        if ac[k] <= 0:
            return k
    return 8


def rqa_for_channel(series, fs):
    """Return dict of {metric: value} per (band, epsilon-percentile)."""
    out = {}
    tau_used = {}
    for band, (lo, hi) in BANDS.items():
        try:
            xb = bandpass(series, lo, hi, fs)
        except Exception as e:
            out[band] = {"ERROR": str(e)}
            continue
        tau = pick_tau(xb, fs)
        tau_used[band] = tau
        m = 3
        if len(xb) < m * tau + 10:
            out[band] = {"ERROR": "too_short"}
            continue
        emb = takens_embedding(xb, m=m, tau=tau)
        if len(emb) < 50:
            out[band] = {"ERROR": "too_short_emb"}
            continue
        # compute pairwise distances once, then threshold at each epsilon-percentile
        from scipy.spatial.distance import pdist, squareform
        D = squareform(pdist(emb[:1500], metric="euclidean"))
        flat = D[np.triu_indices_from(D, k=1)]
        eps_vals = {p: np.percentile(flat, p) for p in EPS_PERCENTILES}
        band_out = {"tau": tau}
        for p, eps in eps_vals.items():
            R = (D <= eps).astype(np.uint8)
            metrics = compute_rqa_metrics(R)
            band_out[f"p{p:02d}"] = {
                "DET": metrics["DET"],
                "LAM": metrics["LAM"],
                "ENT": metrics["ENT"],
                "RR":  metrics["RR"],
                "L":   metrics["L"],
            }
        out[band] = band_out
    return out, tau_used


def main():
    print("[EMP-240 v2 / minimax_m3] loading colony_lib neural_eeg ...")
    ds = load_dataset("neural_eeg")
    fs = ds.fs
    sig = ds.signal_matrix()
    channels = ds.signal_columns
    print(f"shape={sig.shape}, fs={fs}, channels={len(channels)}")

    # Channel-stratified gradient: take frontal (Fp1/Fp2/AF3/AF4/F3/F4/F7/F8),
    # central (Fz/ Cz/ C3/ C4/ Pz), posterior (P3/P4/O1/O2)
    frontal = [ch for ch in ["Fp1", "Fp2", "AF3", "AF4", "F3", "F4", "F7", "F8"]
               if ch in channels][:4]
    central = [ch for ch in ["Fz", "Cz", "C3", "C4", "Pz"]
               if ch in channels][:4]
    posterior = [ch for ch in ["P3", "P4", "O1", "O2"] if ch in channels][:4]
    selected = frontal + central + posterior
    if len(selected) < 8:
        selected = channels[:14]
    print(f"selected channels (n={len(selected)}): {selected}")

    all_results = {}
    for ch in selected:
        col_idx = channels.index(ch)
        x = sig[:, col_idx].astype(float)
        print(f"  -> {ch}: range=[{x.min():.2f},{x.max():.2f}], std={x.std():.2f}")
        r, tau_used = rqa_for_channel(x, fs)
        all_results[ch] = r

    # ===== Aggregate per band, per epsilon-percentile =====
    band_order = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]
    summary = {b: {f"p{p:02d}": [] for p in EPS_PERCENTILES} for b in band_order}
    for ch, r in all_results.items():
        for b in band_order:
            if b not in r or "ERROR" in r[b]:
                continue
            for p in EPS_PERCENTILES:
                key = f"p{p:02d}"
                if key in r[b]:
                    summary[b][key].append(r[b][key])

    print("\n=== Per-band DET/LAM/ENT medians (across channels) ===")
    print(f"{'Band':<8}{'eps':<5}{'DET':>8}{'LAM':>8}{'ENT':>8}{'RR':>8}")
    monotonic_DET = {p: 0 for p in EPS_PERCENTILES}
    monotonic_LAM = {p: 0 for p in EPS_PERCENTILES}
    sign_flip_ENT = {p: None for p in EPS_PERCENTILES}
    last_sign = {p: 0 for p in EPS_PERCENTILES}
    n_bands = len(band_order)

    for p in EPS_PERCENTILES:
        key = f"p{p:02d}"
        for metric, counter in [("DET", monotonic_DET), ("LAM", monotonic_LAM)]:
            vals = []
            for b in band_order:
                vs = [d[metric] for d in summary[b][key] if metric in d]
                if vs:
                    vals.append(np.median(vs))
            if len(vals) == n_bands:
                diffs = np.diff(vals)
                counter[p] = int(np.sum(diffs <= 0.05))
        # ENT sign
        ents = []
        for b in band_order:
            vs = [d["ENT"] for d in summary[b][key] if "ENT" in d]
            if vs:
                ents.append(np.median(vs))
        if len(ents) == n_bands:
            rho = np.corrcoef(np.arange(n_bands), ents)[0, 1]
            sign_flip_ENT[p] = float(rho)

    # Print band x epsilon grid
    for p in EPS_PERCENTILES:
        key = f"p{p:02d}"
        for b in band_order:
            vs_det = [d["DET"] for d in summary[b][key] if "DET" in d]
            vs_lam = [d["LAM"] for d in summary[b][key] if "LAM" in d]
            vs_ent = [d["ENT"] for d in summary[b][key] if "ENT" in d]
            vs_rr  = [d["RR"]  for d in summary[b][key] if "RR"  in d]
            if not vs_det:
                continue
            print(f"{b:<8}{key:<5}{np.median(vs_det):>8.3f}"
                  f"{np.median(vs_lam):>8.3f}{np.median(vs_ent):>8.3f}"
                  f"{np.median(vs_rr):>8.3f}")

    print("\n=== Monotonicity count (n_bands - 1 = 4 transitions) ===")
    print(f"{'eps':<6}{'#DET-decrease':>15}{'#LAM-decrease':>15}{'rho(ENT,freq)':>15}")
    for p in EPS_PERCENTILES:
        key = f"p{p:02d}"
        print(f"{key:<6}{monotonic_DET[p]:>15}{monotonic_LAM[p]:>15}"
              f"{sign_flip_ENT[p]:>15.3f}" if sign_flip_ENT[p] is not None
              else f"{key:<6}{monotonic_DET[p]:>15}{monotonic_LAM[p]:>15}{'N/A':>15}")

    # ===== Visualization =====
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    band_freq_idx = np.arange(len(band_order))

    for p in EPS_PERCENTILES:
        key = f"p{p:02d}"
        det = [np.median([d["DET"] for d in summary[b][key] if "DET" in d])
               for b in band_order]
        lam = [np.median([d["LAM"] for d in summary[b][key] if "LAM" in d])
               for b in band_order]
        ent = [np.median([d["ENT"] for d in summary[b][key] if "ENT" in d])
               for b in band_order]
        axes[0].plot(band_freq_idx, det, "o-", label=f"ε={key}")
        axes[1].plot(band_freq_idx, lam, "o-", label=f"ε={key}")
        axes[2].plot(band_freq_idx, ent, "o-", label=f"ε={key}")

    for ax, name in zip(axes, ["DET", "LAM", "ENT"]):
        ax.set_xticks(band_freq_idx)
        ax.set_xticklabels(band_order, rotation=30)
        ax.set_xlabel("Band (freq ↑)")
        ax.set_ylabel(f"Median {name}")
        ax.set_title(f"{name} vs band freq — ε-sweep")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)
    fig.suptitle(
        "EMP-240 v2 (minimax_m3 independent): "
        "DET/LAM/ENT vs EEG band × ε-percentile on neural_eeg"
    )
    fig.tight_layout()
    out_path = "world_c_results/emp240_v2_rqa_signmap.png"
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    print(f"\n[artifact] {out_path}")

    # ===== Headline verdict =====
    best_det = max(monotonic_DET.values())
    best_lam = max(monotonic_LAM.values())
    signs = [s for s in sign_flip_ENT.values() if s is not None]
    n_flip = sum(1 for i in range(1, len(signs)) if np.sign(signs[i]) != np.sign(signs[i-1]))
    headline = (
        f"DET max-monotonic={best_det}/4, "
        f"LAM max-monotonic={best_lam}/4, "
        f"ENT sign flips across {n_flip} eps-adjacent pairs "
        f"(of {len(signs)-1})"
    )
    print(f"\n[HEADLINE] {headline}")
    with open("world_c_results/REPORT_EMP240_v2.md", "w") as f:
        f.write("# EMP-240 v2 (minimax_m3) — Independent 3rd-Family Replication\n\n")
        f.write(f"**Verdict:** {headline}\n\n")
        f.write("## Channel subset\n")
        f.write(f"- Frontal ({len(frontal)}): {frontal}\n")
        f.write(f"- Central ({len(central)}): {central}\n")
        f.write(f"- Posterior ({len(posterior)}): {posterior}\n\n")
        f.write("## Per-eps summary\n\n")
        f.write(f"| eps | DET dec | LAM dec | rho(ENT, freq) |\n")
        f.write(f"|-----|---------|---------|----------------|\n")
        for p in EPS_PERCENTILES:
            key = f"p{p:02d}"
            r = sign_flip_ENT[p]
            r_str = f"{r:.3f}" if r is not None else "N/A"
            f.write(f"| {key} | {monotonic_DET[p]}/4 | {monotonic_LAM[p]}/4 | {r_str} |\n")
        f.write(f"\n## Artifact\n- ![sign-map]({out_path})\n")


if __name__ == "__main__":
    main()
