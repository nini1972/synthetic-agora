"""STAGE B: direct measurement of ENT/DET/L at claude_sonnet CRT-033's exact
RR operating points via percentile-calibrated epsilon on the FULL distance
matrix (no binary search, no interpolation). Also a fine RR grid + headline
rho values. Decides: is rho=+1.0 an operating-point effect or a pipeline bug?"""
import json, time
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding

t0 = time.time()
def log(*a): print(*a, flush=True)

ds = load_dataset("neural_eeg")
X = np.asarray(ds.data); fs = float(ds.sampling_rate)
cols = list(ds.metadata["columns"])
sig = X[:, cols.index("AF3")].astype(float)
log(f"N={len(sig)} fs={fs}")

BANDS = [("delta", 0.5, 4, 2.0), ("theta", 4, 8, 5.5), ("alpha", 8, 12, 10.0),
         ("beta", 12, 30, 21.0), ("gamma", 30, 45, 37.5)]
FREQ = {b[0]: b[3] for b in BANDS}
CS_T = [0.107, 0.32, 0.43, 0.84, 0.97]
GRID = [0.02, 0.05, 0.107, 0.2, 0.32, 0.43, 0.6, 0.84, 0.97]

def diag_runs_ge2(Rb):
    N = Rb.shape[0]; out = []
    for k in range(1, N):
        d = Rb.diagonal(k)
        dp = np.empty(len(d) + 2, dtype=np.int8)
        dp[0] = 0; dp[-1] = 0; dp[1:-1] = d
        df = np.diff(dp)
        s = np.flatnonzero(df == 1)
        if s.size == 0: continue
        e = np.flatnonzero(df == -1)
        ln = e - s
        ln = ln[ln >= 2]
        if ln.size: out.append(ln)
    return np.concatenate(out) if out else np.zeros(0, dtype=np.int64)

def fast_rqa(Rb):
    N = Rb.shape[0]; rp = int(Rb.sum())
    lens = diag_runs_ge2(Rb)
    if rp > 0 and lens.size > 0:
        h = np.bincount(lens); pr = h[h > 0] / h.sum()
        ent = float(-(pr * np.log2(pr)).sum())
        det = min(1.0, float(lens.sum() * 2) / float(rp))
    else:
        ent, det = 0.0, 0.0
    return {"RR": float(rp) / (N * N), "ENT": ent, "DET": det,
            "L": float(lens.mean()) if lens.size else 0.0}

rows = []
for name, lo, hi, f in BANDS:
    sos = butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
    x = sosfiltfilt(sos, sig)
    z = (x - x.mean()) / (x.std() + 1e-12)
    emb = takens_embedding(z, m=3, tau=2)
    D = pdist(emb).astype(np.float32)
    Sq = squareform(D)
    rng = np.random.default_rng(7)
    idx = rng.choice(len(emb), min(1500, len(emb)), replace=False)
    Dsub = pdist(emb[idx]).astype(np.float32)
    for conv, Ddist in (("full", D), ("sub", Dsub)):
        for tgt in GRID:
            eps = float(np.percentile(Ddist, tgt * 100.0))
            Rb = np.ascontiguousarray((Sq <= eps).astype(np.uint8))
            m = fast_rqa(Rb)
            rows.append({"band": name, "freq": f, "conv": conv,
                         "RR_target": tgt, "eps": eps,
                         "RR": m["RR"], "ENT": m["ENT"],
                         "DET": m["DET"], "L": m["L"]})
    del Sq
    log(f"band {name} done ({time.time()-t0:.1f}s)")

json.dump(rows, open("cs_operating_points.json", "w"), indent=2, default=float)

def headline(conv, key, vals):
    g = {}
    for r in rows:
        if r["conv"] == conv and r[key] in vals:
            g[r["band"]] = r
    bs = ["delta", "theta", "alpha", "beta", "gamma"]
    if len(g) < 5: return None
    rho = float(spearmanr([FREQ[b] for b in bs], [g[b]["ENT"] for b in bs])[0])
    return rho, [round(g[b]["RR"], 3) for b in bs], \
           [round(g[b]["ENT"], 2) for b in bs], \
           [round(g[b]["DET"], 3) for b in bs]

for conv in ("full", "sub"):
    out = headline(conv, "RR_target", CS_T)
    if out:
        rho, rr, en, dt = out
        log(f"HEADLINE conv={conv} @CS targets: rho={rho:+.3f} "
            f"RR={rr} ENT={en} DET={dt}")
    for tgt in GRID:
        out = headline(conv, "RR_target", [tgt])
        if out:
            rho, rr, en, dt = out
            log(f"  conv={conv} tgt={tgt}: rho={rho:+.3f} "
                f"RR={rr} ENT={en} DET={dt}")
log("STAGE B DONE")
