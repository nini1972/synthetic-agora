"""Recipe discriminator: WHY did xiaomi's fixed-eps=0.1 land at RR~0.0003
while qwen's landed at RR~0.1-0.3?

Hypothesis: the difference is the SIGNAL PREPROCESSING before Takens embedding,
specifically (a) whether z-scoring per-band is done, (b) whether the record is
truncated, (c) whether Euclidean distance in embedding space is scaled by
sqrt(m) or not, (d) whether R is computed on the raw amplitude scale or a
normalized scale.

Test: for the same band (e.g. Alpha, Gamma) on neural_eeg ch0, compute RR at
fixed eps=0.1 under a matrix of preprocessing choices and report which recipe
reproduces xiaomi's collapse (RR<0.01) vs qwen's mid-RR (0.1-0.3).
"""
import json
import numpy as np
from scipy.signal import butter, filtfilt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding

ds = load_dataset("neural_eeg")
X = ds.signal_matrix().astype(np.float64)
fs = float(ds.fs)
ch = ds.signal_columns[0]

BANDS = {"Delta": (1, 4), "Theta": (4, 8), "Alpha": (8, 13),
         "Beta": (13, 30), "Gamma": (30, 45)}

def bandpass(sig, lo, hi, fs):
    ny = fs / 2.0
    lo = max(lo, 0.5)
    hi = min(hi, ny - 1.0)
    b, a = butter(4, [lo / ny, hi / ny], btype="band")
    return filtfilt(b, a, sig)

def rr_at_eps(z, eps, m, tau):
    E = takens_embedding(z, m=m, tau=tau)
    N = E.shape[0]
    if N < 60:
        return np.nan
    d = np.sqrt(((E[:, None, :] - E[None, :, :]) ** 2).sum(-1))
    iu = np.triu_indices(N, 1)
    return float((d[iu] <= eps).mean())

T = min(4096, X.shape[0])
sig = X[:T, 0]

results = {}
for band, (lo, hi) in BANDS.items():
    raw = bandpass(sig, lo, hi, fs)
    recipes = {
        "A_zscore_then_embed": (raw - raw.mean()) / (raw.std() + 1e-12),
        "B_raw_no_zscore": raw,
        "C_zscore_div_by_range": (raw - raw.mean()) / (np.ptp(raw) + 1e-12),
        "D_zscore_then_sqrtm_scale": ((raw - raw.mean()) / (raw.std() + 1e-12)),
    }
    for name, z in recipes.items():
        scale = np.sqrt(3.0) if name == "D_zscore_then_sqrtm_scale" else 1.0
        for m, tau in [(3, 2), (3, 1), (5, 2)]:
            key = f"{band}|{name}|m{m}_t{tau}"
            E = takens_embedding(z, m=m, tau=tau)
            N = E.shape[0]
            d = np.sqrt(((E[:, None, :] - E[None, :, :]) ** 2).sum(-1)) / scale
            iu = np.triu_indices(N, 1)
            rr = float((d[iu] <= 0.1).mean())
            results[key] = round(rr, 6)

print(json.dumps(results, indent=2))
with open("emp251_recipe_discriminator.json", "w") as f:
    json.dump(results, f, indent=2)

# summary: classify each recipe as collapse / mid / dense
summary = {}
for k, v in results.items():
    cls = "collapse(<0.01)" if v < 0.01 else ("mid(0.01-0.5)" if v < 0.5 else "dense(>0.5)")
    summary[k] = cls
print("\n=== CLASSIFICATION ===")
for k, v in summary.items():
    print(f"{k}: {results[k]} -> {v}")