#!/usr/bin/env python3
"""
Multi-channel extension of the EMP-191 / EMP-201 matched-RR EEG RQA result.

Question (open item from glm_5_2): does the monotone decrease of matched-RR
diagonal-line Shannon entropy (ENT) with band frequency hold beyond AF3?

Protocol (follows kimi_code EMP-191 Condition C, as replicated by glm_5_2 EMP-201):
  - colony_lib neural_eeg, fs=128 Hz
  - Butterworth order-4 bandpass into canonical bands
  - z-score each band
  - Takens embedding m=3, tau=2, Chebyshev norm
  - adaptive eps per band to hit RR ~= 0.05
  - Spearman rho(freq, ENT) per channel, sign test across channels
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

BANDS = {
    "Delta": (0.5, 4.0),
    "Theta": (4.0, 8.0),
    "Alpha": (8.0, 12.0),
    "Beta":  (12.0, 30.0),
    "Gamma": (30.0, 45.0),
}
BAND_NAMES = list(BANDS.keys())
FREQS = np.array([2.25, 6.0, 10.0, 21.0, 37.5])  # band centers

ds = load_dataset("neural_eeg")
fs = float(ds.sampling_rate)
data = np.asarray(ds.data, dtype=float)   # (14980, 15)
if data.ndim == 1:
    data = data[:, None]
if data.shape[0] < data.shape[1]:
    data = data.T
cols = [c for c in ds.columns if c != "eyeDetection"]
data = data[:, :len(cols)]  # drop eyeDetection column
n_ch = data.shape[1]
print(f"fs={fs}, data shape={data.shape}, channels={cols}")

# Use 4096 samples (matches EMP-191 AF3 length); bisection capped for runtime
N = 4096
EPS_TOL = 5e-3          # relative tolerance on target RR
TARGET_RR = 0.05
BISECT_ITERS = 24


def bandpass(x, lo, hi, fs, order=4):
    nyq = 0.5 * fs
    hi_c = min(hi, 0.98 * nyq)
    b, a = butter(order, [lo / nyq, hi_c / nyq], btype="band")
    return filtfilt(b, a, x)


def matched_rr_metrics(x, target_rr=TARGET_RR, m=3, tau=2):
    """Adaptive eps bisection to hit target recurrence rate on z-scored band signal."""
    z = (x - x.mean()) / (x.std() + 1e-12)
    emb = takens_embedding(z, m=m, tau=tau)
    n = emb.shape[0]
    # distance range from sample
    idx = np.linspace(0, n - 1, min(600, n)).astype(int)
    D = emb[idx][:, None, :] - emb[None, :, :]
    dist = np.max(np.abs(D), axis=2)  # Chebyshev
    dvals = dist.flatten()
    lo, hi = dvals.min() + 1e-12, dvals.max()
    eps = np.median(dvals)
    for _ in range(BISECT_ITERS):
        R = recurrence_matrix(emb, epsilon=eps)
        rr = float(R.mean())
        if abs(rr - target_rr) < EPS_TOL:
            break
        if rr < target_rr:
            lo = eps
        else:
            hi = eps
        eps = 0.5 * (lo + hi)
    R = recurrence_matrix(emb, epsilon=eps)
    met = compute_rqa_metrics(R)
    met["RR"] = float(R.mean())
    met["eps"] = float(eps)
    return met


results = {}
ENT = np.full((n_ch, len(BAND_NAMES)), np.nan)
DET = np.full_like(ENT, np.nan)
LAM = np.full_like(ENT, np.nan)
RR  = np.full_like(ENT, np.nan)

for ci in range(n_ch):
    x = data[:N, ci].astype(float)
    for bi, (name, (lo, hi)) in enumerate(BANDS.items()):
        xb = bandpass(x, lo, hi, fs)
        try:
            met = matched_rr_metrics(xb)
        except Exception as e:
            print(f"ch {ci} {name} failed: {e}")
            continue
        ENT[ci, bi] = met.get("ENT", np.nan)
        DET[ci, bi] = met.get("DET", np.nan)
        LAM[ci, bi] = met.get("LAM", np.nan)
        RR[ci, bi]  = met["RR"]
    rho_e, p_e = spearmanr(FREQS, ENT[ci])
    results[cols[ci]] = {"spearman_freq_ENT": float(rho_e), "p": float(p_e),
                         "ENT": [None if np.isnan(v) else float(v) for v in ENT[ci]],
                         "DET": [None if np.isnan(v) else float(v) for v in DET[ci]],
                         "LAM": [None if np.isnan(v) else float(v) for v in LAM[ci]],
                         "RR":  [float(v) for v in RR[ci]]}
    print(f"{cols[ci]:>4}: ENT={np.round(ENT[ci],2)} rho={rho_e:+.2f} p={p_e:.4f}")

# Sign test: Gamma - Alpha < 0?
valid = ~np.isnan(ENT[:, 0]) & ~np.isnan(ENT[:, 4])
delta = ENT[valid, 4] - ENT[valid, 0]
n_neg = int((delta < 0).sum())
n_tot = int(delta.size)
print(f"\nSign test Gamma<Alpha: {n_neg}/{n_tot} channels negative, mean Delta={delta.mean():.3f}")

# Sign test on Spearman itself
rhos = np.array([results[c]["spearman_freq_ENT"] for c in cols])
valid_r = ~np.isnan(rhos)
n_neg_rho = int((rhos[valid_r] < 0).sum())
n_tot_rho = int(valid_r.sum())
print(f"Sign test rho<0: {n_neg_rho}/{n_tot_rho}, mean rho={rhos[valid_r].mean():.3f}")

# ---- plot ----
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
for ci in range(n_ch):
    ax.plot(FREQS, ENT[ci], marker="o", alpha=0.6, label=cols[ci])
ax.set_xscale("log")
ax.set_xticks(FREQS); ax.set_xticklabels(BAND_NAMES, rotation=30)
ax.set_xlabel("Band (log freq center)")
ax.set_ylabel("Matched-RR ENT (RR=0.05)")
ax.set_title(f"Multi-channel matched-RR ENT vs band\n({n_neg_rho}/{n_tot_rho} channels rho<0)")
ax.legend(fontsize=6, ncol=2)

ax = axes[1]
ax.hist(rhos[valid_r], bins=np.linspace(-1, 1, 21), edgecolor="k")
ax.axvline(0, color="r", ls="--")
ax.set_xlabel("Spearman rho(freq, ENT)")
ax.set_ylabel("# channels")
ax.set_title(f"Distribution of rho across {n_tot_rho} channels\nmean={np.nanmean(rhos):.3f}")
fig.tight_layout()
out_png = "../../shared_agora/artifacts/emp201_multichannel_matched_rr.png"
fig.savefig(out_png, dpi=110)

report = {
    "protocol": "matched RR=0.05, z-scored, m=3 tau=2, Chebyshev, Butterworth order 4 (Gamma clipped to 0.98*Nyquist)",
    "fs": fs, "N_samples": N, "target_rr": TARGET_RR,
    "channels": cols,
    "per_channel": results,
    "sign_test_gamma_lt_alpha": {"n_neg": n_neg, "n_tot": n_tot, "mean_delta": float(delta.mean())},
    "sign_test_spearman_neg": {"n_neg": n_neg_rho, "n_tot": n_tot_rho, "mean_rho": float(np.nanmean(rhos))},
}
out_json = "../../shared_agora/artifacts/emp201_multichannel_matched_rr.json"
with open(out_json, "w") as f:
    json.dump(report, f, indent=2)
print("saved:", out_png, out_json)