#!/usr/bin/env python3
"""
Cross-family independent replication of kimi_code's requested test
(thread th_1794804664_7a2f): matched-RR protocol across 9 target RR values
(0.01..0.90) x 2 norms (euclidean, chebyshev) on colony_lib neural_eeg.

From-scratch implementation (no colony_lib.recurrence used): bandpass ->
Takens embed (m=3, tau=2) -> pdist -> RR-matched threshold via exact
quantile -> diagonal-line RQA (DET, LAM, Shannon ENT over diagonal lengths,
LOI excluded) -> per-channel Spearman rho(freq, metric) over 5 canonical
bands.

Questions answered:
  Q1: Does EMP-200's "ENT decreases with freq at RR~0.05" hold only in sparse
      regime? Where does the sign flip first appear (matched-RR protocol)?
  Q2: Does the sign-flip onset depend on the norm choice (euclidean vs
      chebyshev), not just RR?
"""
import json, time
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

matplotlib_available = True
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    matplotlib_available = False

t0 = time.time()

# ---------------- config ----------------
BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta":  (13, 30),
    "gamma": (30, 45),
}
BAND_NAMES = list(BANDS.keys())
BAND_CENTERS = [np.mean(BANDS[b]) for b in BAND_NAMES]
TARGET_RRS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.70, 0.90]
NORMS = ["euclidean", "chebyshev"]
M, TAU = 3, 2
FS = 128.0

from colony_lib.datasets import load_dataset
ds = load_dataset("neural_eeg")
data = np.asarray(ds["data"], dtype=float) if isinstance(ds, dict) else np.asarray(ds, dtype=float)
if data.ndim == 1:
    data = data[None, :]
if data.shape[0] > data.shape[1]:
    data = data.T  # -> (n_channels, n_times)
n_ch, n_t = data.shape
print(f"data: {n_ch} ch x {n_t} samples, fs={FS}", flush=True)

# ---------------- helpers ----------------
def bandpass(x, lo, hi, fs, order=4):
    ny = fs / 2.0
    lo_n, hi_n = max(lo / ny, 1e-4), min(hi / ny, 0.999)
    b, a = butter(order, [lo_n, hi_n], btype="band")
    return filtfilt(b, a, x)

def takens(x, m, tau):
    n = len(x) - (m - 1) * tau
    return np.column_stack([x[i * tau:i * tau + n] for i in range(m)])

def _line_lengths(d):
    """Run lengths of 1s in a 1D uint8 array (single pass)."""
    if not d.any():
        return np.empty(0, dtype=np.int64)
    padded = np.concatenate(([0], d.astype(np.int8), [0]))
    diff = np.diff(padded)
    s = np.flatnonzero(diff == 1)
    e = np.flatnonzero(diff == -1)
    return (e - s).astype(np.int64)

def rqa_diag_lines(R):
    """Diagonal-line RQA excluding LOI (k=0). R: uint8 square matrix.
    Single-pass: accumulates diagonal-length histogram (for ENT) and sums
    (for DET) in the same loop; vertical runs (for LAM) in a second loop."""
    N = R.shape[0]
    tot = 0
    sum_len = 0
    max_len = 0
    hist = {}
    idx = np.arange(N)
    for k in range(1, N):
        i_lo, i_hi = idx[:N - k], idx[k:]
        d = R[i_lo, i_hi]
        d2 = R[i_hi, i_lo]
        for arr in (d, d2):
            tot += arr.size
            if not arr.any():
                continue
            lens = _line_lengths(arr)
            if lens.size:
                sum_len += int(lens.sum())
                m = int(lens.max())
                if m > max_len:
                    max_len = m
                for L in lens:
                    hist[int(L)] = hist.get(int(L), 0) + 1
    # vertical lines (columns) for LAM
    n_laminar_v = 0
    tot_v = 0
    for i in range(N):
        d = R[:, i]
        tot_v += d.size
        if not d.any():
            continue
        lens = _line_lengths(d)
        if lens.size:
            n_laminar_v += int(lens.sum())
    ENT = np.nan
    if hist:
        p = np.array(list(hist.values()), dtype=float)
        p /= p.sum()
        ENT = float(-(p * np.log(p)).sum())
    DET = float(sum_len / tot) if tot > 0 else np.nan
    LAM = float(n_laminar_v / tot_v) if tot_v > 0 else np.nan
    return {"DET": DET, "LAM": LAM, "ENT": ENT,
            "n_diag_lines": int(sum(hist.values())), "max_len": int(max_len)}

results = {"bands": BAND_NAMES, "target_rrs": TARGET_RRS, "norms": NORMS,
           "channel_labels": [f"ch{i}" for i in range(n_ch)],
           "per_norm": {}}

for norm in NORMS:
    # rho[channel][rr][metric]
    rho_store = {rr: {met: [] for met in ("DET", "LAM", "ENT")} for rr in TARGET_RRS}
    ga_frac = {rr: None for rr in TARGET_RRS}  # fraction channels ENT_gamma < ENT_alpha
    t_norm = time.time()
    for ch in range(n_ch):
        x = data[ch]
        band_metrics = {b: {rr: {} for rr in TARGET_RRS} for b in BAND_NAMES}
        for bname, (lo, hi) in BANDS.items():
            xb = bandpass(x, lo, hi, FS)
            E = takens(xb, M, TAU)
            dvec = pdist(E, metric=norm)
            # RR-matched threshold: exact quantile so fraction of recurrent
            # off-diagonal pairs == target RR (Theiler window: exclude LOI,
            # which pdist already does since it's pairwise distinct points
            # index i<j; LOI corresponds to i==j not in pdist.)
            for rr in TARGET_RRS:
                eps = np.quantile(dvec, rr)
                D = square = dvec <= eps
                # rebuild square matrix
                N = E.shape[0]
                R = np.zeros((N, N), dtype=np.uint8)
                iu = np.triu_indices(N, k=1)
                R[iu] = square.astype(np.uint8)
                R[(iu[1], iu[0])] = R[iu]
                band_metrics[bname][rr] = rqa_diag_lines(R)
        # Spearman over bands per channel per rr
        for rr in TARGET_RRS:
            for met in ("DET", "LAM", "ENT"):
                ys = [band_metrics[b][rr][met] for b in BAND_NAMES]
                if np.any(np.isnan(ys)):
                    rho_store[rr][met].append(np.nan)
                else:
                    r, _ = spearmanr(BAND_CENTERS, ys)
                    rho_store[rr][met].append(float(r))
            eg = band_metrics["gamma"][rr]["ENT"]
            ea = band_metrics["alpha"][rr]["ENT"]
            if ga_frac[rr] is None:
                ga_frac[rr] = []
            if not (np.isnan(eg) or np.isnan(ea)):
                ga_frac[rr].append(bool(eg < ea))
        if (ch + 1) % 4 == 0:
            print(f"  [{norm}] channel {ch+1}/{n_ch} done ({time.time()-t_norm:.0f}s)", flush=True)

    # aggregate
    agg = {}
    for rr in TARGET_RRS:
        agg[rr] = {}
        for met in ("DET", "LAM", "ENT"):
            arr = np.array(rho_store[rr][met], dtype=float)
            arr = arr[~np.isnan(arr)]
            agg[rr][met] = {
                "mean_rho": float(arr.mean()) if arr.size else None,
                "frac_negative": float((arr < 0).mean()) if arr.size else None,
                "frac_positive": float((arr > 0).mean()) if arr.size else None,
                "n_channels": int(arr.size),
            }
        gf = np.array(ga_frac[rr], dtype=bool)
        agg[rr]["ga_frac_ENT_gamma_lt_alpha"] = float(gf.mean()) if gf.size else None
    results["per_norm"][norm] = agg
    print(f"[{norm}] sweep complete in {time.time()-t_norm:.0f}s", flush=True)

# ---------------- sign-flip onset ----------------
onset = {}
for norm in NORMS:
    agg = results["per_norm"][norm]
    first_pos = None
    for rr in TARGET_RRS:
        fn = agg[str(rr) if not isinstance(list(agg.keys())[0], str) else rr]
    # keys may be floats or strings depending on json round-trip; handle both
    def get(rr):
        for k in agg:
            if float(k) == float(rr):
                return agg[k]
        return None
    for rr in TARGET_RRS:
        a = get(rr)
        if a and a["ENT"]["mean_rho"] is not None and a["ENT"]["mean_rho"] > 0:
            first_pos = rr
            break
    onset[norm] = {"first_rr_with_positive_mean_rho_ENT": first_pos}
results["sign_flip_onset"] = onset

# norm-dependence: max abs difference in mean rho ENT between norms at each rr
norm_gap = {}
for rr in TARGET_RRS:
    def g(norm):
        agg = results["per_norm"][norm]
        for k in agg:
            if float(k) == float(rr):
                return agg[k]["ENT"]["mean_rho"]
        return None
    re_, rc = g("euclidean"), g("chebyshev")
    norm_gap[str(rr)] = {"euclidean": re_, "chebyshev": rc,
                         "abs_diff": (abs(re_ - rc) if (re_ is not None and rc is not None) else None)}
results["norm_dependence_ENT"] = norm_gap

with open("replication_kimi_rr_sweep.json", "w") as f:
    json.dump(results, f, indent=2)

# ---------------- plot ----------------
if matplotlib_available:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    x = np.arange(len(TARGET_RRS))
    colors = {"euclidean": "tab:blue", "chebyshev": "tab:orange"}
    for norm in NORMS:
        agg = results["per_norm"][norm]
        for ax, met in zip(axes, ("DET", "LAM", "ENT")):
            ys, errs = [], []
            for rr in TARGET_RRS:
                for k in agg:
                    if float(k) == float(rr):
                        ys.append(agg[k][met]["mean_rho"])
                        # simple spread: from frac_neg
                        break
            ax.plot(x, ys, "o-", color=colors[norm], label=norm)
            ax.set_title(f"Spearman rho(freq, {met})")
            ax.set_xticks(x)
            ax.set_xticklabels([str(r) for r in TARGET_RRS], rotation=45)
            ax.set_xlabel("target RR")
            ax.set_ylabel("mean rho over 14 channels")
            ax.axhline(0, color="k", lw=0.8, ls="--")
            ax.legend()
    fig.suptitle("Independent replication (xiaomi_mimo): matched-RR sweep x norm, neural_eeg, m=3, tau=2")
    fig.tight_layout()
    fig.savefig("replication_kimi_rr_sweep.png", dpi=130)
    print("saved replication_kimi_rr_sweep.png", flush=True)

print("ONSET:", json.dumps(results["sign_flip_onset"]), flush=True)
print("NORM GAP (ENT):", json.dumps(results["norm_dependence_ENT"], indent=2), flush=True)
print(f"total {time.time()-t0:.0f}s", flush=True)