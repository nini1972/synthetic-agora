"""
RR-CONTROLLED ROOT-CAUSE TEST for the Condition C sign flip.
Q: Is the ENT-vs-frequency sign in matched-RR RQA governed by the ACHIEVED RR
   vector, or by diffuse pipeline choices?
Method: re-run EMP-201's exact pipeline (AF3, m=3, tau=2, butter order-4,
   z-score) under BOTH eps conventions (full-pairwise 5% quantile = native
   target_rr cross-check; Kimi-style 1500-sample quantile), collecting
   (band, freq, eps, achieved RR, ENT) per band. Then compute
   Spearman rho(freq, ENT) within achieved-RR strata pooled across conventions.
Prediction (RR-governance hypothesis): within each RR stratum, the rho is
   same-sign across conventions; the sign flips only as a function of RR.
"""
import json
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

ds = load_dataset("neural_eeg")
X = np.asarray(ds.data)
fs = float(ds.sampling_rate)
cols = list(ds.metadata["columns"])
sig_full = X[:, cols.index("AF3")].astype(float)
N = len(sig_full)
print(f"N={N} fs={fs}", flush=True)

BANDS = [("delta", 0.5, 4, 2.0), ("theta", 4, 8, 5.5), ("alpha", 8, 12, 10.0),
         ("beta", 12, 30, 21.0), ("gamma", 30, 45, 37.5)]

def bandpass(x, lo, hi):
    sos = butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
    return sosfiltfilt(sos, x)

def eps_subsample(emb, target=0.05, n_samp=1500, seed=7):
    rng = np.random.default_rng(seed)
    idx = rng.choice(emb.shape[0], min(n_samp, emb.shape[0]), replace=False)
    return float(np.percentile(pdist(emb[idx]), target * 100))

# Sweep eps grid around the 5% quantile to populate RR strata densely
MULTS = [0.3, 0.5, 0.7, 0.85, 1.0, 1.3, 1.8, 2.5, 3.5, 5.0]

rows = []
for name, lo, hi, f in BANDS:
    x = bandpass(sig_full, lo, hi)
    z = (x - x.mean()) / (x.std() + 1e-12)
    emb = takens_embedding(z, m=3, tau=2)
    eps_full = float(np.percentile(pdist(emb), 5.0))
    eps_sub = eps_subsample(emb)
    eps_base = {"full": eps_full, "sub": eps_sub}
    for conv in ("full", "sub"):
        for mult in MULTS:
            eps = eps_base[conv] * mult
            R = recurrence_matrix(emb, epsilon=eps)
            m = compute_rqa_metrics(R)
            rows.append({"band": name, "freq": f, "conv": conv, "mult": mult,
                         "eps": eps, "RR": m["RR"], "ENT": m["ENT"],
                         "DET": m["DET"], "LAM": m["LAM"]})
    print(f"{name}: eps_full={eps_full:.3f} eps_sub={eps_sub:.3f} done", flush=True)

with open("rr_controlled_sweep_rows.json", "w") as fo:
    json.dump(rows, fo, indent=2, default=float)

# --- RR-stratified analysis, pooling both conventions ---
RR_BINS = [(0.00, 0.02), (0.02, 0.05), (0.05, 0.10), (0.10, 0.25),
           (0.25, 0.50), (0.50, 0.75), (0.75, 1.01)]
strata = {}
for lo_, hi_ in RR_BINS:
    grp = [r for r in rows if lo_ <= r["RR"] < hi_]
    strata[f"{lo_:.2f}-{hi_:.2f}"] = grp

print("\n=== RR-STRATIFIED Spearman rho(freq, ENT), pooled across conventions ===", flush=True)
strat_out = {}
for key, grp in strata.items():
    if len(grp) < 4:
        strat_out[key] = {"n": len(grp), "rho": None}
        print(f"RR in [{key}]: n={len(grp)} (too few)", flush=True)
        continue
    convs = sorted(set(r["conv"] for r in grp))
    rhos = {}
    for c in convs:
        g = [r for r in grp if r["conv"] == c]
        if len(g) >= 4 and len(set(r["freq"] for r in g)) >= 4:
            rhos[c] = float(spearmanr([r["freq"] for r in g],
                                      [r["ENT"] for r in g])[0])
    pooled = float(spearmanr([r["freq"] for r in grp],
                             [r["ENT"] for r in grp])[0])
    strat_out[key] = {"n": len(grp), "rho_pooled": pooled, "rho_by_conv": rhos,
                      "mean_RR": float(np.mean([r["RR"] for r in grp]))}
    print(f"RR in [{key}]: n={len(grp)} pooled rho={pooled:+.3f} "
          f"by-conv={ {k: round(v,3) for k,v in rhos.items()} }", flush=True)

# Also: per-convention rho at EXACT 5% quantile (the Condition C operating point)
print("\n=== At the nominal 5% quantile (mult=1.0) ===", flush=True)
for c in ("full", "sub"):
    g = [r for r in rows if r["conv"] == c and abs(r["mult"] - 1.0) < 1e-9]
    rho = float(spearmanr([r["freq"] for r in g], [r["ENT"] for r in g])[0])
    rrs = {r["band"]: round(r["RR"], 4) for r in g}
    ents = {r["band"]: round(r["ENT"], 2) for r in g}
    print(f"conv={c}: rho={rho:+.3f} RR={rrs} ENT={ents}", flush=True)
    strat_out[f"nominal5_{c}"] = {"rho": rho, "RR": rrs, "ENT": ents}

with open("rr_controlled_sweep_strata.json", "w") as fo:
    json.dump(strat_out, fo, indent=2, default=float)
print("\nDONE", flush=True)
