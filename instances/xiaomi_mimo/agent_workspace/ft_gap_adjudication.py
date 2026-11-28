"""Preregistered adjudication of the FT-surrogate ENT gap dispute:
deepseek (+0.036 null, N=400/12 surr) vs claude (+1.926, T=1024/12 surr) vs gemini (+0.694).

Forks tested (all on colony_lib neural_eeg, 14 channels, m=3, tau=2):
  A. window length N   : 400, 768, 1024, 2048
  B. surrogate count   : 1 vs 12 (tests single-surrogate variance)
  C. epsilon regime    : sparse p5, dense p95
Metric: ENT_real - mean(ENT_surr) at given epsilon (per band), averaged.
FT surrogate applied to the BAND-PASSED SIGNAL (signal-space), then Takens-embedded,
for both real and surrogate (both sides identical except phase randomization).
Falsifiers (preregistered):
  F1: if gap(N=400) is near null while gap(N=1024) >= +0.5 -> window-length fork confirmed
  F2: if gap(mean of 12 surr) differs from gap(single surr) by > 1.0 nat -> surrogate-count fork
  F3: if dense p95 gap <= +0.2 at ALL N -> dense collapse is N-independent (claude F2)
"""
import json
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

rng = np.random.default_rng(20261127)
ds = load_dataset("neural_eeg")
X = ds.signal_matrix().astype(float)
fs = float(ds.fs)
cols = ds.signal_columns
BANDS = {"Delta": (1, 4), "Theta": (4, 8), "Alpha": (8, 13),
         "Beta": (13, 30), "Gamma": (30, 45)}

def bp(sig, lo, hi):
    ny = fs / 2
    b, a = butter(4, [max(lo, .5) / ny, min(hi, ny - 1) / ny], btype="band")
    return filtfilt(b, a, sig)

def ft_surrogate(x):
    n = len(x)
    F = np.fft.rfft(x)
    amp = np.abs(F)
    ph = rng.uniform(0, 2 * np.pi, size=len(F))
    ph[0] = np.angle(F[0])
    if n % 2 == 0:
        ph[-1] = np.angle(F[-1])
    return np.fft.irfft(amp * np.exp(1j * ph), n=n)

def ent_at(x, q):
    E = takens_embedding(x, m=3, tau=2)
    d = np.sqrt(((E[:, None] - E[None, :]) ** 2).sum(-1))
    iu = np.triu_indices(len(E), 1)
    eps = np.quantile(d[iu], q)
    R = recurrence_matrix(E, epsilon=float(eps))
    return float(compute_rqa_metrics(R)["ENT"])

N_LIST = [400, 768, 1024, 2048]
Q = {"sparse_p5": 0.05, "dense_p95": 0.95}
NSURR = {"single": 1, "ensemble12": 12}

out = {}
for N in N_LIST:
    for qname, q in Q.items():
        for sname, ns in NSURR.items():
            gaps = []
            for ci, ch in enumerate(cols):
                x = X[:N, ci]
                z = (x - x.mean()) / (x.std() + 1e-12)
                for lo, hi in BANDS.values():
                    xb = bp(z, lo, hi)
                    try:
                        g_real = ent_at(xb, q)
                        gs = [ent_at(ft_surrogate(xb), q) for _ in range(ns)]
                        gaps.append(g_real - np.mean(gs))
                    except Exception:
                        pass
            key = f"N{N}_{qname}_{sname}"
            out[key] = {"mean_gap": round(float(np.mean(gaps)), 4),
                        "median_gap": round(float(np.median(gaps)), 4),
                        "frac_pos": round(float(np.mean(np.array(gaps) > 0)), 3),
                        "n": len(gaps)}
            print(key, out[key], flush=True)

# Falsifiers
f1 = (out["N400_sparse_p5_ensemble12"]["mean_gap"] < 0.2 and
      out["N1024_sparse_p5_ensemble12"]["mean_gap"] >= 0.5)
f2 = abs(out["N1024_sparse_p5_single"]["mean_gap"] -
         out["N1024_sparse_p5_ensemble12"]["mean_gap"]) > 1.0
f3 = all(out[f"N{N}_dense_p95_ensemble12"]["mean_gap"] <= 0.2 for N in N_LIST)
summary = {"F1_window_fork": bool(f1),
           "F2_surrogate_count_fork": bool(f2),
           "F3_dense_collapse_Nindep": bool(f3),
           "detail": out}
print(json.dumps({k: v for k, v in summary.items() if k != "detail"}, indent=2))
with open("ft_gap_adjudication.json", "w") as f:
    json.dump(summary, f, indent=2)