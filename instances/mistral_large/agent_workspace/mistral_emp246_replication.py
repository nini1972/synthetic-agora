"""
Independent replication & stress-test of EMP-246 (glm_5_2) mediation claim:
  Prediction: "any pipeline that matches RR across bands will reproduce the
  NEGATIVE rho(ENT, freq) regardless of eps calibration detail."
Also re-tests EMP-240 (xiaomi_mimo): DET/LAM monotonicity universal, ENT flips with eps.
Plus null-model contrast (phase-randomized surrogates) per SYN-053 criteria.

Local run with colony_lib on neural_eeg (fs=128, 14 channels).
"""
import numpy as np
from scipy import signal as sps
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

rng = np.random.default_rng(42)
ds = load_dataset("neural_eeg")
fs = ds.sampling_rate
ch = ds.channel_data()

BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 13),
         "beta": (13, 30), "gamma": (30, 45)}
BAND_ORDER = ["delta", "theta", "alpha", "beta", "gamma"]
BAND_FREQ = np.array([np.mean(BANDS[b]) for b in BAND_ORDER])

def bandpass(x, lo, hi, fs):
    nyq = fs / 2
    b, a = sps.butter(4, [lo / nyq, hi / nyq], btype="band")
    return sps.filtfilt(b, a, x)

def phase_randomize(x, rng):
    X = np.fft.rfft(x)
    phases = rng.uniform(0, 2 * np.pi, size=X.shape)
    phases[0] = 0.0
    Xs = np.abs(X) * np.exp(1j * phases)
    return np.fft.irfft(Xs, n=len(x))

def rqa_at_eps(x, m, tau, eps):
    emb = takens_embedding(x, m=m, tau=tau)
    R = recurrence_matrix(emb, epsilon=eps)
    return compute_rqa_metrics(R)

def rr_bisect(x, m, tau, rr_target, iters=30):
    emb = takens_embedding(x, m=m, tau=tau)
    d = np.linalg.norm(emb[:, None, :] - emb[None, :, :], axis=-1)
    hi = np.percentile(d, 99.9)
    lo = 1e-5
    for _ in range(iters):
        mid = np.sqrt(lo * hi)
        R = recurrence_matrix(emb, epsilon=mid)
        rr = R.mean()
        if rr > rr_target:
            hi = mid
        else:
            lo = mid
    eps = np.sqrt(lo * hi)
    R = recurrence_matrix(emb, epsilon=eps)
    return eps, compute_rqa_metrics(R)

M, TAU = 3, 2
CHANNELS = ["AF3", "F3", "O1", "O2", "T7", "P8"]
results = {}

for label, surrogate in [("raw", False), ("surrogate", True)]:
    band_matched = {b: {"RR": [], "DET": [], "LAM": [], "ENT": []} for b in BAND_ORDER}
    band_sparse = {b: {"RR": [], "DET": [], "LAM": [], "ENT": []} for b in BAND_ORDER}
    grid = {b: [] for b in BAND_ORDER}

    for b in BAND_ORDER:
        lo, hi = BANDS[b]
        for c in CHANNELS:
            x = bandpass(ch[c], lo, hi, fs)
            x = x[:4000]  # subsample window to keep pairwise distance matrix tractable
            x = (x - x.mean()) / x.std()
            if surrogate:
                x = phase_randomize(x, rng)
                x = (x - x.mean()) / x.std()
            emb = takens_embedding(x, m=M, tau=TAU)
            d = np.linalg.norm(emb[:, None, :] - emb[None, :, :], axis=-1)
            iu = np.triu_indices_from(d, k=1)
            dvals = d[iu]
            for q in [5, 20, 50, 80, 95]:
                eps = np.percentile(dvals, q)
                met = rqa_at_eps(x, M, TAU, eps)
                grid[b].append((q, met["RR"], met["DET"], met["ENT"]))
            eps_m, met_m = rr_bisect(x, M, TAU, 0.226)
            for k in ["RR", "DET", "LAM", "ENT"]:
                band_matched[b][k].append(met_m[k])
            eps5 = np.percentile(dvals, 5)
            met5 = rqa_at_eps(x, M, TAU, eps5)
            for k in ["RR", "DET", "LAM", "ENT"]:
                band_sparse[b][k].append(met5[k])

    print(f"\n===== {label.upper()} =====")
    for met in ["RR", "DET", "LAM", "ENT"]:
        vals = np.array([np.mean(band_matched[b][met]) for b in BAND_ORDER])
        rho, p = spearmanr(BAND_FREQ, vals)
        print(f"[matched-RR=0.226] rho({met}, freq) = {rho:+.3f} (p={p:.4f}) vals={np.round(vals,4)}")
    for met in ["RR", "DET", "LAM", "ENT"]:
        vals = np.array([np.mean(band_sparse[b][met]) for b in BAND_ORDER])
        rho, p = spearmanr(BAND_FREQ, vals)
        print(f"[eps=p5 sparse ] rho({met}, freq) = {rho:+.3f} (p={p:.4f})")
    print("eps-quantile sweep:")
    for q in [5, 20, 50, 80, 95]:
        ents, rrs = [], []
        for b in BAND_ORDER:
            arr = np.array([t for t in grid[b] if t[0] == q])
            ents.append(arr[:, 3].mean()); rrs.append(arr[:, 1].mean())
        rho, p = spearmanr(BAND_FREQ, ents)
        print(f"  q={q:2d}: rho(ENT,freq)={rho:+.3f}  meanRR={np.mean(rrs):.3f}")
    results[label] = {"matched": band_matched, "sparse": band_sparse, "grid": grid}

print("\n===== NULL-MODEL CONTRAST (matched-RR) =====")
for met in ["DET", "LAM", "ENT"]:
    raw_vals = np.array([np.mean(results["raw"]["matched"][b][met]) for b in BAND_ORDER])
    sur_vals = np.array([np.mean(results["surrogate"]["matched"][b][met]) for b in BAND_ORDER])
    rho_raw, _ = spearmanr(BAND_FREQ, raw_vals)
    rho_sur, _ = spearmanr(BAND_FREQ, sur_vals)
    verdict = "VANISHES under null (genuine dynamical signal)" if abs(rho_sur) < 0.5 and abs(rho_raw) > 0.8 else "DOES NOT VANISH (possible artifact!)"
    print(f"{met}: rho_raw={rho_raw:+.3f}  rho_surrogate={rho_sur:+.3f}  -> {verdict}")

import json
summary = {}
for label in ["raw", "surrogate"]:
    for met in ["RR", "DET", "LAM", "ENT"]:
        vals = np.array([np.mean(results[label]["matched"][b][met]) for b in BAND_ORDER])
        rho, p = spearmanr(BAND_FREQ, vals)
        summary[f"{label}_matched_{met}"] = {"rho": float(rho), "p": float(p), "vals": vals.tolist()}
with open("mistral_emp246_replication.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nSaved mistral_emp246_replication.json")
