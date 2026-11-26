"""Independent from-scratch replication of EMP-253 (glm_5_2).

Claims to test on colony_lib neural_eeg (fs=128, 14 channels):
 (1) Fixed-eps=0.3 protocol: gamma-band RR saturates (maxRR>0.90) on a subset
     of channels; rho(ENT,freq) is POSITIVE on exactly those channels
     (P(positive|saturation)=~1, low otherwise).
 (2) Dose-response: Spearman rho(maxRR_fixed, rho_fixed) ~ +0.94.
 (3) Mirror control: quantile-matched RR (q=0.10 per band per channel)
     yields rho(ENT,freq) < 0 on 14/14 channels.

Fresh implementation: no reuse of glm/xiaomi artifacts.
"""
import json
import numpy as np
from scipy.signal import butter, filtfilt
from colony_lib.datasets import load_dataset

rng = np.random.default_rng(0)

ds = load_dataset("neural_eeg")
X = ds.signal_matrix().astype(np.float64)   # (N, 14)
fs = float(ds.fs)
cols = ds.signal_columns
BANDS = {"Delta": (1, 4), "Theta": (4, 8), "Alpha": (8, 13),
         "Beta": (13, 30), "Gamma": (30, 45)}
band_names = list(BANDS.keys())
freq_idx = np.arange(len(band_names))       # band index as frequency proxy

def bandpass(sig, lo, hi, fs):
    ny = fs / 2.0
    lo = max(lo, 0.5); hi = min(hi, ny - 1.0)
    b, a = butter(4, [lo / ny, hi / ny], btype="band")
    return filtfilt(b, a, sig)

def takens(z, m=3, tau=2):
    N = len(z)
    L = N - (m - 1) * tau
    return np.stack([z[i * tau: i * tau + L] for i in range(m)], axis=1)

def ent_of_diagonal_lines(R, emb_diag_only=True):
    """Shannon entropy of diagonal line-length histogram (RQA-ENT style)."""
    N = R.shape[0]
    # extract diagonal line lengths (exclude main diagonal per convention)
    lengths = []
    for k in range(1, N):                    # super-diagonals
        d = np.diff(R[np.arange(N - k), np.arange(N - k) + k].astype(np.int8))
        starts = np.where(d == 1)[0]
        ends = np.where(d == -1)[0]
        if len(ends) and len(starts):
            if ends[0] < starts[0]:
                ends = ends[1:]
            n = min(len(starts), len(ends))
            lengths.extend((ends[:n] - starts[:n] + 1).tolist())
    if not lengths:
        return 0.0
    lengths = np.array(lengths)
    p = np.bincount(lengths)
    p = p[p > 0] / p.sum()
    return float(-(p * np.log(p)).sum())

def rr_and_ent(E, eps):
    N = E.shape[0]
    d = np.sqrt(((E[:, None, :] - E[None, :, :]) ** 2).sum(-1))
    iu = np.triu_indices(N, 1)
    R = (d[iu] <= eps)
    rr = float(R.mean())
    # rebuild full R for line stats (cheap: N<=1024)
    Rm = np.zeros((N, N), dtype=np.uint8)
    Rm[iu] = R.astype(np.uint8)
    Rm = Rm + Rm.T
    np.fill_diagonal(Rm, 0)
    ent = ent_of_diagonal_lines(Rm)
    return rr, ent

def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)

T = 1024
res = {c: {} for c in cols}

for ci, col in enumerate(cols):
    x = X[:T, ci]
    zc = (x - x.mean()) / (x.std() + 1e-12)
    rr_fixed, ent_fixed, rr_q, ent_q = [], [], [], []
    for bn in band_names:
        lo, hi = BANDS[bn]
        xb = bandpass(zc, lo, hi, fs)
        xb = (xb - xb.mean()) / (xb.std() + 1e-12)
        E = takens(xb, 3, 2)
        # --- fixed eps = 0.3 ---
        rr, ent = rr_and_ent(E, 0.3)
        rr_fixed.append(rr); ent_fixed.append(ent)
        # --- quantile-matched q=0.10 ---
        N = E.shape[0]
        d = np.sqrt(((E[:, None, :] - E[None, :, :]) ** 2).sum(-1))
        iu = np.triu_indices(N, 1)
        eps_q = float(np.quantile(d[iu], 0.10))
        rrq, entq = rr_and_ent(E, eps_q)
        rr_q.append(rrq); ent_q.append(entq)
    res[col] = {
        "rr_fixed": [round(v, 4) for v in rr_fixed],
        "ent_fixed": [round(v, 4) for v in ent_fixed],
        "rr_q": [round(v, 4) for v in rr_q],
        "ent_q": [round(v, 4) for v in ent_q],
    }
    res[col]["maxRR"] = round(max(rr_fixed), 4)
    res[col]["rho_fixed"] = round(spearman(freq_idx, ent_fixed), 4)
    res[col]["rho_matched"] = round(spearman(freq_idx, ent_q), 4)

maxRR = np.array([res[c]["maxRR"] for c in cols])
rho_f = np.array([res[c]["rho_fixed"] for c in cols])
rho_m = np.array([res[c]["rho_matched"] for c in cols])

sat = maxRR > 0.90
summary = {
    "channels": cols,
    "maxRR": maxRR.tolist(),
    "rho_fixed": rho_f.tolist(),
    "rho_matched": rho_m.tolist(),
    "n_saturated": int(sat.sum()),
    "P_positive_given_sat": float((rho_f[sat] > 0).mean()) if sat.any() else None,
    "P_positive_given_nosat": float((rho_f[~sat] > 0).mean()) if (~sat).sum() else None,
    "max_rho_fixed_where_nosat": float(rho_f[~sat].max()) if (~sat).sum() else None,
    "spearman_maxRR_vs_rho": round(spearman(maxRR, rho_f), 4),
    "pearson_maxRR_vs_rho": round(float(np.corrcoef(maxRR, rho_f)[0, 1]), 4),
    "matched_all_negative": bool((rho_m < 0).all()),
    "matched_rho_range": [float(rho_m.min()), float(rho_m.max())],
}
print(json.dumps(summary, indent=2))
with open("rep_emp253_summary.json", "w") as f:
    json.dump({"summary": summary, "per_channel": res}, f, indent=2)
