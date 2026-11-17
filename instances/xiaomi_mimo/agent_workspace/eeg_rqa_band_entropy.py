#!/usr/bin/env python3
"""
Independent EEG RQA band analysis: resolve the EMP-191 vs SYN-062 sign question.

Question under debate (#sanity-check thread th_1794804664_7a2f):
  - EMP-191: rho(freq, ENT) = -0.90 under RR-matched Condition C.
  - SYN-062: rho(ENT) ~ +1.0 invariant across pipelines.

This script computes, from scratch, on colony_lib 'neural_eeg':
  1. Bandpass into canonical bands (delta..gamma), fixed center frequencies.
  2. RQA (Takens embedding + fixed-RR threshold) on each band signal,
     across multiple pipeline configs (m, tau, epsilon quantile).
  3. Spearman rho of ENT, DET, LAM vs band center frequency per config.
  4. Rank-order stability of the 5 bands under each metric per config.
Deliverables: results JSON + figure.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from scipy.stats import spearmanr
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
from colony_lib.datasets import load_dataset

# ---- Config ------------------------------------------------------------
BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta":  (13.0, 30.0),
    "gamma": (30.0, 45.0),
}
BAND_CENTER_HZ = {k: 0.5 * (a + b) for k, (a, b) in BANDS.items()}
FS_GUESS = None  # determined from dataset metadata if available
CHANNELS = list(range(14))   # first 14 columns are channels
SEG_LEN = 4096               # samples per analysis segment
T_EMB, TAU = 3, 1            # pipeline A defaults; also sweep
PIPELINES = [
    {"m": 3, "tau": 1, "eps_q": 0.05},
    {"m": 5, "tau": 2, "eps_q": 0.05},
    {"m": 3, "tau": 1, "eps_q": 0.10},
    {"m": 4, "tau": 3, "eps_q": 0.02},
]
BAND_ORDER = ["delta", "theta", "alpha", "beta", "gamma"]


def fixed_rr_epsilon(R_dists, rr_target):
    """Return scalar epsilon achieving recurrence rate ~ rr_target."""
    k = max(1, int(round(rr_target * R_dists.size)))
    idx = np.argpartition(R_dists.ravel(), k - 1)
    return float(np.sort(R_dist.ravel())[k - 1])


def rqa_of_signal(x, m, tau, eps_q):
    emb = takens_embedding(x, m=m, tau=tau)
    # pairwise distance matrix for thresholding
    diff = emb[:, None, :] - emb[None, :, :]
    d = np.sqrt((diff ** 2).sum(-1))
    eps = np.quantile(d[np.triu_indices_from(d, k=1)], eps_q)
    R = recurrence_matrix(emb, epsilon=eps)
    return compute_rqa_metrics(R)


def main():
    ds = load_dataset("neural_eeg")
    X = np.asarray(ds.data if hasattr(ds, "data") else ds, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    fs = None
    for attr in ("fs", "sampling_rate", "sfreq", "rate"):
        if hasattr(ds, attr):
            fs = float(getattr(ds, attr))
            break
    if fs is None:
        meta = getattr(ds, "metadata", None) or getattr(ds, "meta", None)
        if isinstance(meta, dict):
            for k in ("fs", "sampling_rate", "sfreq"):
                if k in meta:
                    fs = float(meta[k]); break
    if fs is None:
        fs = 256.0  # conservative default; documented in report
    n_chan = min(X.shape[1], len(CHANNELS))
    seg = X[:SEG_LEN, :n_chan]

    results = { "fs": fs, "n_channels": n_chan, "seg_len": SEG_LEN,
                "pipelines": [] }

    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    axes = axes.ravel()

    for pi, pipe in enumerate(PIPELINES):
        rows = []
        for b in BAND_ORDER:
            lo, hi = BANDS[b]
            lo = max(lo, 0.5); hi = min(hi, fs / 2 - 1.0)
            sos = butter(4, [lo / (fs / 2), hi / (fs / 2)], btype="band", output="sos")
            ents, dets, lams = [], [], []
            for c in range(n_chan):
                y = sosfiltfilt(sos, seg[:, c])
                if np.std(y) < 1e-12:
                    continue
                met = rqa_of_signal(y, pipe["m"], pipe["tau"], pipe["eps_q"])
                ents.append(met["ENT"]); dets.append(met["DET"]); lams.append(met["LAM"])
            rows.append({
                "band": b, "f_hz": BAND_CENTER_HZ[b],
                "ENT": float(np.mean(ents)), "DET": float(np.mean(dets)),
                "LAM": float(np.mean(lams)), "n": len(ents),
            })
        freqs = np.array([r["f_hz"] for r in rows])
        cors = {}
        for metric in ("ENT", "DET", "LAM"):
            vals = np.array([r[metric] for r in rows])
            rho, p = spearmanr(freqs, vals)
            cors[metric] = {"rho": float(rho), "p": float(p)}
            # rank order of bands (1 = highest metric value)
            order = [b for _, b in sorted(zip(vals, BAND_ORDER), reverse=True)]
            cors[metric]["band_rank_high_to_low"] = order
        results["pipelines"].append({
            "m": pipe["m"], "tau": pipe["tau"], "eps_q": pipe["eps_q"],
            "rows": rows, "spearman_vs_freq": cors,
        })

        ax = axes[pi]
        for metric, mk in (("ENT", "o"), ("DET", "s"), ("LAM", "^")):
            vals = [r[metric] for r in rows]
            ax.plot(BAND_ORDER, vals, mk, label=f"{metric} (rho={cors[metric]['rho']:+.2f})")
        ax.set_title(f"pipeline m={pipe['m']}, tau={pipe['tau']}, eps_q={pipe['eps_q']}")
        ax.set_xlabel("band (increasing center freq)"); ax.set_ylabel("RQA metric")
        ax.legend(fontsize=8)

    fig.suptitle(f"EEG RQA vs band frequency — pipeline sweep (n_ch={n_chan}, fs={fs:g})")
    fig.tight_layout()
    fig.savefig("eeg_rqa_band_entropy.png", dpi=140)

    # Cross-pipeline sign consistency summary
    sign_summary = {}
    for metric in ("ENT", "DET", "LAM"):
        rhos = [p["spearman_vs_freq"][metric]["rho"] for p in results["pipelines"]]
        sign_summary[metric] = rhos
    results["rho_across_pipelines"] = sign_summary

    with open("eeg_rqa_band_entropy.json", "w") as f:
        json.dump(results, f, indent=2)

    print("fs =", fs, "channels =", n_chan)
    for metric, rhos in sign_summary.items():
        print(f"{metric}: rhos across pipelines = {[round(r,3) for r in rhos]}")
    # print band values for pipeline 0
    p0 = results["pipelines"][0]
    for r in p0["rows"]:
        print(f"  {r['band']:6s} f={r['f_hz']:5.2f}Hz ENT={r['ENT']:.3f} DET={r['DET']:.3f} LAM={r['LAM']:.3f}")


if __name__ == "__main__":
    main()