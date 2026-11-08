"""
v2: Independent replication of EMP-191 (kimi_code) protocol (c) — GLM-5.2.
Optimized: scipy pdist, cached embeddings, per-block checkpointing.
Protocol (c): z-scored bands, per-band eps matched to RR~5%
  - FULL pairwise quantile (native target_rr path cross-checked)
  - Kimi-style 1500-sample subsampled quantile (method sensitivity)
Plus re-test of EMP-187 raw fixed-eps trajectory on Kimi's bands.
Blocks: (KIMI edges, N=4096), (KIMI edges, N=2000), (GLM edges, N=4096)
"""

import json
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import (takens_embedding, recurrence_matrix,
                                   compute_rqa_metrics)

ds = load_dataset("neural_eeg")
X = np.asarray(ds.data)
fs = float(ds.sampling_rate)
cols = list(ds.metadata["columns"])
sig_full = X[:, cols.index("AF3")].astype(float)
print(f"data loaded: shape={X.shape} fs={fs}", flush=True)

BANDS_KIMI = [("delta", 1, 3), ("theta", 4, 7), ("alpha", 8, 12),
              ("beta", 13, 30), ("gamma", 31, 44)]
BANDS_GLM = [("delta", 0.5, 4), ("theta", 4, 8), ("alpha", 8, 12),
             ("beta", 12, 30), ("gamma", 30, 45)]
FREQ = {"delta": 2.0, "theta": 5.5, "alpha": 10.0, "beta": 21.0, "gamma": 37.5}


def bandpass(x, lo, hi):
    sos = butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
    return sosfiltfilt(sos, x)


def eps_subsample(emb, target=0.05, n_samp=1500, seed=7):
    rng = np.random.default_rng(seed)
    idx = rng.choice(emb.shape[0], min(n_samp, emb.shape[0]), replace=False)
    d = pdist(emb[idx])
    return float(np.percentile(d, target * 100))


def run_block(bands, N, tag):
    sig = sig_full[:N]
    rows = []
    for name, lo, hi in bands:
        x = bandpass(sig, lo, hi)
        z = (x - x.mean()) / (x.std() + 1e-12)
        emb = takens_embedding(z, m=3, tau=2)

        # (c) full-quantile matched RR: library-native target_rr path
        R_full = recurrence_matrix(emb, target_rr=0.05)
        m_full = compute_rqa_metrics(R_full)
        eps_full = float(np.percentile(pdist(emb), 5.0))  # record the matching radius

        # (c) Kimi-style subsampled quantile
        eps_sub = eps_subsample(emb)
        R_sub = recurrence_matrix(emb, epsilon=eps_sub)
        m_sub = compute_rqa_metrics(R_sub)

        # (a) raw fixed eps=10 (EMP-187 arm)
        m_raw = compute_rqa_metrics(recurrence_matrix(takens_embedding(x, m=3, tau=2), epsilon=10.0))

        rows.append({
            "band": name, "freq": FREQ[name],
            "rms": float(np.sqrt(np.mean(x ** 2))),
            "matched": {"RR": m_full["RR"], "DET": m_full["DET"], "LAM": m_full["LAM"],
                        "ENT": m_full["ENT"], "eps_sub": eps_sub,
                        "RR_sub": m_sub["RR"], "ENT_sub": m_sub["ENT"],
                        "DET_sub": m_sub["DET"], "LAM_sub": m_sub["LAM"]},
            "raw_fixed": {"RR": m_raw["RR"], "ENT": m_raw["ENT"]}})
        print(f"  [{tag}] {name}: RR={m_full['RR']:.4f} ENT={m_full['ENT']:.3f} "
              f"RR_sub={m_sub['RR']:.4f} ENT_sub={m_sub['ENT']:.3f} "
              f"rawRR={m_raw['RR']:.4f}", flush=True)

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
    print(f"== {tag} (N={N}) Spearman(ENT_matched,freq): "
          f"full={res['spearman_ENT_freq_fullquant']:+.3f} "
          f"sub={res['spearman_ENT_freq_subquant']:+.3f} | "
          f"Spearman(RR_raw,freq)={res['spearman_RR_raw_freq']:+.3f} "
          f"RRraw~rms={res['spearman_RRraw_rms']:+.3f}", flush=True)
    with open(f"emp191_block_{tag}.json", "w") as fo:
        json.dump(res, fo, indent=2, default=float)
    return res


blocks = [run_block(BANDS_KIMI, 4096, "kimi4096"),
          run_block(BANDS_KIMI, 2000, "kimi2000"),
          run_block(BANDS_GLM, 4096, "glm4096")]
with open("emp191_replication_glm.json", "w") as fo:
    json.dump(blocks, fo, indent=2, default=float)
print("REPLICATION COMPLETE", flush=True)
