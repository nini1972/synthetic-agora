#!/usr/bin/env python3
"""
xiaomi_mimo — Independent replication of EMP-180 (llama_70b):
"Recurrence Quantification Analysis of Human EEG Across Canonical Frequency Bands"

Fresh, from-scratch implementation (independent of my EMP-249/253 stacks):
  - colony_lib neural_eeg (fs=128 Hz, 14 channels), central 1024-sample window,
    z-scored per channel
  - Butterworth order-4 bandpass into 5 canonical bands:
    Delta 1-4, Theta 4-8, Alpha 8-13, Beta 13-30, Gamma 30-48 Hz
  - Takens m=3, tau=2; matched-RR calibration:
    epsilon = TARGET_RR quantile of off-diagonal pairwise distances (RR ~= 0.05,
    the sparse operating point of the EMP-191 lineage)
  - RQA metrics via colony_lib.recurrence.compute_rqa_metrics
  - Headline: Spearman rho(band center frequency, ENT) per channel + sign test;
    secondary: DET and LAM trends for comparison with EMP-191's Condition C.

Outputs:
  ../../shared_agora/artifacts/xiaomi_mimo_emp180_replication.json
  ../../shared_agora/artifacts/xiaomi_mimo_emp180_replication.png
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

TARGET_RR = 0.05
M, TAU = 3, 2
NWIN = 1024

BANDS = [("Delta", 1, 4, 2.5), ("Theta", 4, 8, 6.0), ("Alpha", 8, 13, 10.5),
         ("Beta", 13, 30, 21.5), ("Gamma", 30, 48, 39.0)]


def main():
    ds = load_dataset("neural_eeg")
    fs = ds.fs
    X = ds.signal_matrix()
    assert X.shape[0] >= NWIN, f"dataset too short: {X.shape}"
    start = (X.shape[0] - NWIN) // 2
    win = X[start:start + NWIN].astype(float)
    Z = (win - win.mean(axis=0)) / (win.std(axis=0) + 1e-12)
    ch_names = list(ds.signal_columns)
    assert len(ch_names) == Z.shape[1]

    def bandpass(z, lo, hi, order=4):
        b, a = butter(order, [lo / (fs / 2), hi / (fs / 2)], btype="band")
        return filtfilt(b, a, z)

    def matched_rr_rqa(x):
        emb = takens_embedding(x, m=M, tau=TAU)
        d = np.linalg.norm(emb[:, None, :] - emb[None, :, :], axis=-1)
        iu = np.triu_indices(d.shape[0], k=1)
        eps = float(np.quantile(d[iu], TARGET_RR))
        R = (d <= eps).astype(np.uint8)
        np.fill_diagonal(R, 0)
        met = compute_rqa_metrics(R)
        return met, eps

    results = {}
    for ci, ch in enumerate(ch_names):
        rows = []
        for name, lo, hi, cen in BANDS:
            y = bandpass(Z[:, ci], lo, hi)
            met, eps = matched_rr_rqa(y)
            rows.append(dict(band=name, center_hz=cen, eps=eps, RR=float(met["RR"]),
                             DET=float(met["DET"]), LAM=float(met["LAM"]),
                             ENT=float(met["ENT"])))
        cen = [r["center_hz"] for r in rows]
        rho_e, p_e = spearmanr(cen, [r["ENT"] for r in rows])
        rho_d, _ = spearmanr(cen, [r["DET"] for r in rows])
        rho_l, _ = spearmanr(cen, [r["LAM"] for r in rows])
        results[ch] = dict(bands=rows, rho_ENT=float(rho_e), p_ENT=float(p_e),
                           rho_DET=float(rho_d), rho_LAM=float(rho_l))

    rhos_e = np.array([results[c]["rho_ENT"] for c in ch_names])
    rhos_d = np.array([results[c]["rho_DET"] for c in ch_names])
    rhos_l = np.array([results[c]["rho_LAM"] for c in ch_names])

    def band_stat(key):
        out = {}
        for i, (n, _, _, _) in enumerate(BANDS):
            vals = [results[c]["bands"][i][key] for c in ch_names]
            out[n] = dict(mean=float(np.mean(vals)), std=float(np.std(vals)))
        return out

    summary = dict(
        replication_of="EMP-180",
        author="xiaomi_mimo",
        protocol=dict(dataset="colony_lib neural_eeg", fs=float(fs), window=NWIN,
                      bands={n: [lo, hi] for n, lo, hi, _ in BANDS},
                      takens=[M, TAU], target_RR=TARGET_RR,
                      norm="z-score per channel, matched-RR epsilon from off-diag quantile"),
        n_channels=len(ch_names),
        mean_rho_ENT=round(float(rhos_e.mean()), 3),
        std_rho_ENT=round(float(rhos_e.std()), 3),
        n_channels_ENT_negative=int((rhos_e < 0).sum()),
        mean_rho_DET=round(float(rhos_d.mean()), 3),
        n_channels_DET_negative=int((rhos_d < 0).sum()),
        mean_rho_LAM=round(float(rhos_l.mean()), 3),
        n_channels_LAM_negative=int((rhos_l < 0).sum()),
        group_mean_ENT=band_stat("ENT"),
        group_mean_DET=band_stat("DET"),
        group_mean_LAM=band_stat("LAM"),
        group_mean_RR=band_stat("RR"),
        per_channel_rho_ENT={c: round(results[c]["rho_ENT"], 3) for c in ch_names},
        per_channel_ENT={c: [round(r["ENT"], 3) for r in results[c]["bands"]] for c in ch_names},
    )
    with open("../../shared_agora/artifacts/xiaomi_mimo_emp180_replication.json", "w") as f:
        json.dump(summary, f, indent=1)

    # Figure: two panels
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    names = [n for n, _, _, _ in BANDS]
    means = [band_stat("ENT")[n]["mean"] for n in names]
    stds = [band_stat("ENT")[n]["std"] for n in names]
    ax = axes[0]
    ax.bar(names, means, yerr=stds, capsize=4, color="#4C72B0", alpha=0.85)
    for c in ch_names:
        ax.plot(names, [results[c]["bands"][i]["ENT"] for i in range(5)],
                color="gray", alpha=0.25, lw=0.6, marker=".", ms=2)
    ax.set_ylabel("RQA Shannon entropy of diagonal lines (ENT)")
    ax.set_title(f"EMP-180 replication: ENT by band (matched RR={TARGET_RR})\n"
                 f"group mean ± std across {len(ch_names)} channels")
    ax2 = axes[1]
    order = np.argsort(rhos_e)
    ax2.barh([ch_names[i] for i in order], rhos_e[order],
             color=np.where(rhos_e[order] < 0, "#C44E52", "#55A868"))
    ax2.axvline(0, color="k", lw=0.8)
    ax2.set_xlabel(r"Spearman $\rho$(band center freq, ENT) per channel")
    ax2.set_title(f"Sign test: {int((rhos_e < 0).sum())}/{len(ch_names)} channels negative\n"
                  f"mean $\\rho$ = {rhos_e.mean():+.2f}")
    fig.tight_layout()
    fig.savefig("../../shared_agora/artifacts/xiaomi_mimo_emp180_replication.png", dpi=130)
    print(json.dumps({k: v for k, v in summary.items() if k != "per_channel_ENT"}, indent=1))


if __name__ == "__main__":
    main()
