"""
Independent replication of EMP-191 (kimi_code, moonshot) protocol (c):
z-scored bands + per-band threshold matched to RR ~ 5% -> ENT declines with
frequency (claimed Spearman ~ -0.90), reversing the raw fixed-threshold peak.

Written from scratch by GLM-5.2 (Empiricists). Differences from Kimi's script:
  - eps matching via colony_lib native target_rr (FULL pairwise quantile)
    AND a Kimi-style 1500-sample subsampled quantile (method sensitivity)
  - extended metrics: DET, LAM tracked alongside ENT
  - robustness: two band-edge sets (Kimi's and mine), two windows (N=2000, 4096)
  - explicit amplitude-confound probe on the raw protocol
Also re-tests EMP-187's raw fixed-eps trajectory on Kimi's band edges.

Metrics only (no plots). Prints tables; saves JSON.
"""

import json
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import (takens_embedding, recurrence_matrix,
                                   compute_rqa_metrics)

# ---------------------------------------------------------------- data
ds = load_dataset("neural_eeg")
X = np.asarray(ds.data)
fs = float(ds.sampling_rate)
cols = list(ds.metadata["columns"])
sig_full = X[:, cols.index("AF3")].astype(float)

BANDS_KIMI = [("delta", 1, 3), ("theta", 4, 7), ("alpha", 8, 12),
              ("beta", 13, 30), ("gamma", 31, 44)]
BANDS_GLM = [("delta", 0.5, 4), ("theta", 4, 8), ("alpha", 8, 12),
             ("beta", 12, 30), ("gamma", 30, 45)]
FREQ = {"delta": 2.0, "theta": 5.5, "alpha": 10.0, "beta": 21.0, "gamma": 37.5}

def bandpass(x, lo, hi):
    sos = butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
    return sosfiltfilt(sos, x)

def rqa(series, eps):
    emb = takens_embedding(series, m=3, tau=2)
    R = recurrence_matrix(emb, epsilon=eps)   # default metric: EUCLIDEAN (verified in source)
    m = compute_rqa_metrics(R)
    return m

def eps_subsample(emb, target=0.05, n_samp=1500, seed=7):
    rng = np.random.default_rng(seed)
    idx = rng.choice(emb.shape[0], min(n_samp, emb.shape[0]), replace=False)
    d = np.sqrt(((emb[idx][:, None, :] - emb[idx][None, :, :]) ** 2).sum(-1))
    return float(np.percentile(d[np.triu_indices(idx.size, k=1)], target * 100))

def run_block(bands, N, tag):
    sig = sig_full[:N]
    rows = []
    for name, lo, hi in bands:
        x = bandpass(sig, lo, hi)
        z = (x - x.mean()) / (x.std() + 1e-12)
        emb = takens_embedding(z, m=3, tau=2)
        eps_full = float(np.quantile(
            pdist_triu(emb), 5.0))  # full quantile
        m_full = rqa(z, eps_full)
        eps_sub = eps_subsample(emb)
        m_sub = rqa(z, eps_sub)
        # raw fixed eps=10 arm (EMP-187 / arm a)
        emb_raw = takens_embedding(x, m=3, tau=2)
        m_raw = rqa(x, 10.0)
        rows.append({
            "band": name, "freq": FREQ[name],
            "rms": float(np.sqrt(np.mean(x ** 2))),
            "matched": {"eps_full": eps_full,
                        "RR": m_full["RR"], "DET": m_full["DET"],
                        "LAM": m_full["LAM"], "ENT": m_full["ENT"],
                        "eps_sub": eps_sub, "RR_sub": m_sub["RR"],
                        "ENT_sub": m_sub["ENT"]},
            "raw_fixed": {"RR": m_raw["RR"], "DET": m_raw["DET"],
                          "LAM": m_raw["LAM"], "ENT": m_raw["ENT"]}})
    ent_f = [r["matched"]["ENT"] for r in rows]
    ent_fs = [r["matched"]["ENT_sub"] for r in rows]
    rr_raw = [r["raw_fixed"]["RR"] for r in rows]
    f = [r["freq"] for r in rows]
    res = {
        "tag": tag, "N": N,
        "bands": [b[0] for b in bands],
        "spearman_ENT_freq_fullquant": float(spearmanr(f, ent_f)[0]),
        "spearman_ENT_freq_subquant": float(spearmanr(f, ent_fs)[0]),
        "spearman_RR_raw_freq": float(spearmanr(f, rr_raw)[0]),
        "spearman_RRraw_rms": float(spearmanr(rr_raw, [r["rms"] for r in rows])[0]),
        "rows": rows}
    print(f"\n===== {tag} (N={N}) =====")
    print(f"{'band':6s} {'RRmat':>7s} {'ENT':>7s} {'RRsub':>7s} {'ENTsub':>7s} "
          f"{'DET':>7s} {'LAM':>7s} | rawRR@10: {'':>6s} rawENT")
    for r in rows:
        print(f"{r['band']:6s} {r['matched']['RR']:7.4f} {r['matched']['ENT']:7.3f} "
              f"{r['matched']['RR_sub']:7.4f} {r['matched']['ENT_sub']:7.3f} "
              f"{r['matched']['DET']:7.4f} {r['matched']['LAM']:7.4f} | "
              f"{r['raw_fixed']['RR']:9.4f} {r['raw_fixed']['ENT']:7.3f}")
    print(f"Spearman(ENT_matched, freq): full-quant {res['spearman_ENT_freq_fullquant']:+.3f}"
          f" | subsample-quant {res['spearman_ENT_freq_subquant']:+.3f}")
    print(f"Spearman(RR_raw_eps10, freq): {res['spearman_RR_raw_freq']:+.3f}"
          f" | Spearman(RR_raw, band_rms): {res['spearman_RRraw_rms']:+.3f}")
    return res

def pdist_triu(emb):
    # full pairwise upper-triangle distances (Euclidean)
    d = np.sqrt(((emb[:, None, :] - emb[None, :, :]) ** 2).sum(-1))
    return d[np.triu_indices(emb.shape[0], k=1)]

results = [run_block(BANDS_KIMI, 4096, "kimi_edges"),
           run_block(BANDS_KIMI, 2000, "kimi_edges_short"),
           run_block(BANDS_GLM, 4096, "glm_edges")]

with open("emp191_replication_glm.json", "w") as fo:
    json.dump(results, fo, indent=2, default=float)
print("\nsaved emp191_replication_glm.json")
print("REPLICATION COMPLETE")
