"""EMP-253 replication v2 — exact pipeline match to glm_5_2's stated protocol:
1024-sample window, z-score RAW signal ONCE, then Butterworth order-4 bandpass,
Takens m=3/tau=2 (no per-band renormalization), ENT via colony_lib compute_rqa_metrics.
Tests: (1) P(positive rho|saturation), (2) dose-response, (3) matched-RR mirror.
"""
import json
import numpy as np
from scipy.signal import butter, filtfilt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import (takens_embedding, recurrence_matrix,
                                   compute_rqa_metrics)

ds = load_dataset("neural_eeg")
X = ds.signal_matrix().astype(np.float64)
fs = float(ds.fs)
cols = ds.signal_columns
BANDS = {"Delta": (1, 4), "Theta": (4, 8), "Alpha": (8, 13),
         "Beta": (13, 30), "Gamma": (30, 45)}
band_names = list(BANDS.keys())
freq_idx = np.arange(len(band_names), dtype=float)

def bandpass(sig, lo, hi, fs):
    ny = fs / 2.0
    lo = max(lo, 0.5); hi = min(hi, ny - 1.0)
    b, a = butter(4, [lo / ny, hi / ny], btype="band")
    return filtfilt(b, a, sig)

def rr_ent_cl(E, eps):
    R = recurrence_matrix(E, epsilon=eps)
    m = compute_rqa_metrics(R)
    return float(m["RR"]), float(m["ENT"])

def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)

T = 1024
res = {}
for col in cols:
    x = X[:T, X.shape[1] and cols.index(col)]
    zc = (x - x.mean()) / (x.std() + 1e-12)      # z-score RAW once
    rr_f, ent_f, rr_q, ent_q = [], [], [], []
    for bn in band_names:
        lo, hi = BANDS[bn]
        xb = bandpass(zc, lo, hi, fs)             # bandpass after z-score, no renorm
        E = takens_embedding(xb, m=3, tau=2)
        rr, ent = rr_ent_cl(E, 0.3)               # fixed eps = 0.3
        rr_f.append(rr); ent_f.append(ent)
        # quantile-matched q=0.10 per band per channel
        from colony_lib.recurrence import recurrence_matrix as _rm
        Rfull = _rm(E, epsilon=0.3)               # need distances? use quantile on R-distance
        # build distance matrix for quantile threshold
        d = np.sqrt(((E[:, None, :] - E[None, :, :]) ** 2).sum(-1))
        iu = np.triu_indices(E.shape[0], 1)
        eps_q = float(np.quantile(d[iu], 0.10))
        rrq, entq = rr_ent_cl(E, eps_q)
        rr_q.append(rrq); ent_q.append(entq)
    rho_f = spearman(freq_idx, ent_f)
    rho_m = spearman(freq_idx, ent_q)
    res[col] = {"rr_fixed": [round(v, 4) for v in rr_f],
                "ent_fixed": [round(v, 3) for v in ent_f],
                "rr_q": [round(v, 4) for v in rr_q],
                "ent_q": [round(v, 3) for v in ent_q],
                "maxRR": round(max(rr_f), 4),
                "rho_fixed": round(rho_f, 4),
                "rho_matched": round(rho_m, 4)}

maxRR = np.array([res[c]["maxRR"] for c in cols])
rho_f = np.array([res[c]["rho_fixed"] for c in cols])
rho_m = np.array([res[c]["rho_matched"] for c in cols])
sat = maxRR > 0.90

summary = {
    "maxRR": maxRR.tolist(),
    "rho_fixed": rho_f.tolist(),
    "rho_matched": rho_m.tolist(),
    "n_saturated": int(sat.sum()),
    "P_pos_given_sat": float((rho_f[sat] > 0).mean()) if sat.any() else None,
    "P_pos_given_nosat": float((rho_f[~sat] > 0).mean()) if (~sat).sum() else None,
    "max_rho_where_nosat": float(rho_f[~sat].max()) if (~sat).sum() else None,
    "spearman_maxRR_rho": round(spearman(maxRR, rho_f), 4),
    "matched_all_negative": bool((rho_m < 0).all()),
    "matched_range": [float(rho_m.min()), float(rho_m.max())],
}
print(json.dumps(summary, indent=2))
with open("rep_emp253_v2_summary.json", "w") as f:
    json.dump({"summary": summary, "per_channel": res}, f, indent=2)
