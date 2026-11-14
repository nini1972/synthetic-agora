"""
RR-CONTROLLED ROOT-CAUSE TEST for the Condition C sign flip (EMP-191/EMP-201
rho=-0.90 vs CRT-033 rho=+1.0). Fast validated RQA, cached symmetric distance
matrix per band, 8 eps multipliers x 2 eps conventions x 5 bands.
"""
import json, time
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

t0 = time.time()
ds = load_dataset("neural_eeg")
X = np.asarray(ds.data)
fs = float(ds.sampling_rate)
cols = list(ds.metadata["columns"])
sig_full = X[:, cols.index("AF3")].astype(float)
print(f"N={len(sig_full)} fs={fs}", flush=True)

BANDS = [("delta", 0.5, 4, 2.0), ("theta", 4, 8, 5.5), ("alpha", 8, 12, 10.0),
         ("beta", 12, 30, 21.0), ("gamma", 30, 45, 37.5)]
MULTS = [0.5, 0.7, 0.85, 1.0, 1.3, 1.8, 2.5, 4.0]

def bandpass(x, lo, hi):
    sos = butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
    return sosfiltfilt(sos, x)

def diag_runs_ge2(Rb):
    """All diagonal run lengths >=2, upper triangle (offsets 1..N-1).
    Mirrors colony_lib compute_rqa_metrics (min_diag_len=2)."""
    N = Rb.shape[0]
    out = []
    for k in range(1, N):
        d = Rb.diagonal(k)
        dp = np.empty(len(d) + 2, dtype=np.int8)
        dp[0] = 0; dp[-1] = 0; dp[1:-1] = d
        diff = np.diff(dp)
        s = np.flatnonzero(diff == 1)
        if s.size == 0:
            continue
        e = np.flatnonzero(diff == -1)
        lens = e - s          # each run length (see derivation)
        lens = lens[lens >= 2]
        if lens.size:
            out.append(lens)
    return np.concatenate(out) if out else np.zeros(0, dtype=np.int64)

def fast_rqa(Rb):
    """Validated-equivalent of colony_lib compute_rqa_metrics (RR/DET/ENT)."""
    N = Rb.shape[0]
    rp = int(Rb.sum())
    lens = diag_runs_ge2(Rb)
    if rp > 0 and lens.size > 0:
        h = np.bincount(lens)
        probs = h[h > 0] / h.sum()
        entr = float(-np.sum(probs * np.log2(probs)))
        det = min(1.0, float(lens.sum() * 2) / float(rp))  # 2*SUM(lengths), colony_lib convention
    else:
        entr, det = 0.0, 0.0
    return {"RR": float(rp) / (N * N), "DET": det, "ENT": entr,
            "L": float(lens.mean()) if lens.size else 0.0,
            "Lmax": float(lens.max()) if lens.size else 0.0}

# --- VALIDATION vs colony_lib at small N ---
zz = (sig_full[:600] - sig_full[:600].mean()) / (sig_full[:600].std() + 1e-12)
emb_small = takens_embedding(zz, m=3, tau=2)
eps_v = float(np.percentile(pdist(emb_small), 5.0))
m_lib = compute_rqa_metrics(recurrence_matrix(emb_small, epsilon=eps_v))
Rb_v = np.ascontiguousarray((squareform(pdist(emb_small)) <= eps_v).astype(np.uint8))
m_fast = fast_rqa(Rb_v)
assert abs(m_lib["RR"] - m_fast["RR"]) < 1e-12, (m_lib["RR"], m_fast["RR"])
assert abs(m_lib["ENT"] - m_fast["ENT"]) < 1e-9, (m_lib["ENT"], m_fast["ENT"])
assert abs(m_lib["DET"] - m_fast["DET"]) < 1e-9, (m_lib["DET"], m_fast["DET"])
print(f"VALIDATION OK vs colony_lib: RR={m_fast['RR']:.4f} ENT={m_fast['ENT']:.4f} "
      f"DET={m_fast['DET']:.4f} ({time.time()-t0:.1f}s)", flush=True)

rows = []
for name, lo, hi, f in BANDS:
    x = bandpass(sig_full, lo, hi)
    z = (x - x.mean()) / (x.std() + 1e-12)
    emb = takens_embedding(z, m=3, tau=2)
    D = pdist(emb).astype(np.float32)
    Sq = squareform(D)                      # cached symmetric, zero diag
    eps_full = float(np.percentile(D, 5.0))
    rng = np.random.default_rng(7)
    idx = rng.choice(len(emb), min(1500, len(emb)), replace=False)
    eps_sub = float(np.percentile(pdist(emb[idx]), 5.0))
    print(f"{name}: eps_full={eps_full:.3f} eps_sub={eps_sub:.3f} "
          f"({time.time()-t0:.1f}s)", flush=True)
    for conv, eps0 in (("full", eps_full), ("sub", eps_sub)):
        for mult in MULTS:
            eps = eps0 * mult
            Rb = np.ascontiguousarray((Sq <= eps).astype(np.uint8))
            m = fast_rqa(Rb)
            rows.append({"band": name, "freq": f, "conv": conv, "mult": mult,
                         "eps": eps, "RR": m["RR"], "ENT": m["ENT"], "DET": m["DET"]})
    del Sq
    print(f"  band done ({time.time()-t0:.1f}s)", flush=True)

with open("rr_sweep_rows.json", "w") as fo:
    json.dump(rows, fo, indent=2, default=float)

# quick headline: rho(freq,ENT) at the nominal 5% operating points
for c in ("full", "sub"):
    g = [r for r in rows if r["conv"] == c and abs(r["mult"] - 1.0) < 1e-9]
    rho = float(spearmanr([r["freq"] for r in g], [r["ENT"] for r in g])[0])
    print(f"HEADLINE conv={c} mult=1.0: rho={rho:+.3f} "
          f"RR={[round(r['RR'],3) for r in g]} "
          f"ENT={[round(r['ENT'],2) for r in g]}", flush=True)
print("SWEEP DONE", flush=True)
