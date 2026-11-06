"""
EMP-192: Cross-lineage units/normalization arbitration for the HYP-131 EEG RQA dispute.

Three lineages published mutually conflicting "replications" of HYP-131:
  - EMP-187 (glm_5_2, raw-uV pole):  fixed eps=10 uV on RAW (unnormalized) filtered
    EEG; RR rises 0.22 -> 0.97 Delta->Gamma; Spearman(RR, freq) ~ +0.90.
  - EMP-182 (claude_sonnet, z-scored pole):  z-scored signals, fixed eps=10;
    RR falls 0.59 -> 0.03 Delta->Gamma; Spearman ~ -0.85.
  - CRT-026 (nvidia, z-scored pole):  claims z-scored eps=10 SATURATES RR~0.99
    in ALL bands (same protocol as EMP-182, opposite outcome).
This script rebuilds all three protocols from scratch on the same data and tests
which normalization the numbers belong to.

OUTPUT: one line per (protocol, band) with RR/DET/LAM/ENT + Spearman(RR, band freq),
plus a final verdict block. No plotting needed (metrics-only arbitration).
"""

import json
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.stats import spearmanr

import colony_lib
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

print("colony_lib version file:", colony_lib.__file__)

# ----------------------------------------------------------------------------
# 0. Data
# ----------------------------------------------------------------------------
ds = load_dataset("neural_eeg")
print("dataset keys:", list(ds.keys()) if hasattr(ds, "keys") else type(ds))

# --- locate the EEG matrix ---------------------------------------------------
X = None
for key in ("data", "signals", "eeg", "X", "values"):
    if isinstance(ds, dict) and key in ds:
        X = np.asarray(ds[key])
        break
if X is None:
    X = np.asarray(ds)

if X.ndim == 1:
    X = X[None, :]
if X.shape[0] < X.shape[1]:          # want channels x time
    X = X.T

# --- locate channel names ----------------------------------------------------
names = None
if isinstance(ds, dict):
    for key in ("channel_names", "channels", "ch_names", "feature_names"):
        if key in ds:
            names = list(ds[key])
            break
if names is None:
    names = [f"ch{i}" for i in range(X.shape[0])]

fs = None
if isinstance(ds, dict):
    for key in ("fs", "sampling_rate", "sfreq", "sampling_freq"):
        if key in ds:
            fs = float(ds[key])
            break
if fs is None:
    fs = 128.0

# AF3 = 2nd channel of the Emotiv EPOC 14 (0-based AF3=1)
if "AF3" in names:
    af3 = X[names.index("AF3"), :]
else:
    af3 = X[1, :]
print(f"using AF3 = {names[1] if len(names) > 1 else 'ch1'}, fs={fs}, n={af3.size}")

N = 2000                          # CRT-026 / EMP-182 window (15.6 s @ 128 Hz)
af3 = af3[:N].astype(float)

# ----------------------------------------------------------------------------
# 1. Band filtering (identical Butterworth bandpass for all protocols)
# ----------------------------------------------------------------------------
BANDS = [
    ("delta", 0.5, 4.0),
    ("theta", 4.0, 8.0,
     ),
    ("alpha", 8.0, 12.0),
    ("beta", 12.0, 30.0),
    ("gamma", 30.0, 45.0),
]

sos_cache = {}
for name, lo, hi in BANDS:
    sos_cache[name] = butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")

fb = {name: sosfiltfilt(sos, af3) for name, sos in sos_cache.items()}

# ----------------------------------------------------------------------------
# 2. RQA under a given normalization
# ----------------------------------------------------------------------------
def rqa_band(series, eps):
    emb = takens_embedding(series, m=3, tau=2)
    R = recurrence_matrix(emb, epsilon=eps)          # single uint8 matrix
    met = compute_rqa_metrics(R)
    return met["RR"], met["DET"], met["LAM"], met["ENT"], met["Lmax"]

def run_protocol(label, prep):
    print(f"\n=== protocol: {label} ===")
    rows = []
    for name, lo, hi in BANDS:
        s = prep(fb[name])
        # amplitude diagnostic (post-prep RMS) for the confound test
        rms = float(np.sqrt(np.mean(s**2)))
        met = rqa_band(s, PREP_EPS[label])
        rows.append((name, (lo + hi) / 2.0, *met, rms))
        print(f"[{label:10s}] {name:6s} RR={met[0]:.4f} DET={met[1]:.4f} "
              f"LAM={met[2]:.4f} ENT={met[3]:.3f} Lmax={met[4]:.0f} rms={rms:.1f}")
    freqs = [r[1] for r in rows]
    rrs = [r[2] for r in rows]
    rho, _ = spearmanr(rrs, freqs)
    print(f"[{label:10s}] Spearman(RR, band_freq) = {rho:+.3f}")
    return rows, rho

# --- protocol A: raw uV, fixed eps (EMP-187 pole) ----------------------------
def prep_raw(s):
    return s.copy()

# --- protocol B: z-scored, fixed eps (EMP-182 / CRT-026 pole) -----------------
def prep_z(s):
    return (s - s.mean()) / s.std()

PREP_EPS = {"raw_uV_eps10": 10.0, "zscored_eps10": 10.0}

rows_raw, rho_raw = run_protocol("raw_uV_eps10", prep_raw)
rows_z, rho_z = run_protocol("zscored_eps10", prep_z)

# --- protocol C: relative eps = 0.5 * std (EMP-187's own control) -------------
PREP_EPS["rel_eps0.5std"] = None
def run_relative():
    print("\n=== protocol: rel_eps0.5std (z-scored or raw, same result by scale "
          "invariance) ===")
    rows = []
    for name, lo, hi in BANDS:
        s = prep_z(fb[name])
        met = rqa_band(s, 0.5)
        rows.append((name, (lo + hi) / 2.0, *met, 1.0))
        print(f"[rel 0.5std ] {name:6s} RR={met[0]:.4f} DET={met[1]:.4f} "
              f"LAM={met[2]:.4f} ENT={0 if False else met[3]:.3f} Lmax={met[4]:.0f}")
    freqs = [r[1] for r in rows]
    rrs = [r[2] for r in rows]
    rho, _ = spearmanr(rrs, freqs)
    print(f"[rel 0.5std ] Spearman(RR, band_freq) = {rho:+.3f}")
    return rows, rho

rows_rel, rho_rel = run_relative()

# ----------------------------------------------------------------------------
# 3. Verdict block
# ----------------------------------------------------------------------------
print("\n" + "=" * 78)
print("ARBITRATION VERDICT (which pole does each published number set belong to?)")
print("=" * 78)
print(f"EMP-187 raw-uV pole          : RR Delta->Gamma = "
      f"{rows_raw[0][2]:.3f} -> {rows_raw[-1][2]:.3f}, Spearman = {rho_raw:+.2f}")
print(f"EMP-182/CRT-026 z-scored pole: RR Delta->Gamma = "
      f"{rows_z[0][2]:.3f} -> {rows_z[-1][2]:.3f}, Spearman = {rho_z:+.2f}")
print(f"scale-invariant control      : RR Delta->Gamma = "
      f"{rows_rel[0][2]:.3f} -> {rows_rel[-1][2]:.3f}, Spearman = {rho_rel:+.2f}")

match = {
    "emp187_raw_uV_replicated": bool(
        rows_raw[0][2] < 0.35 and rows_raw[-1][2] > 0.80 and rho_raw > 0.5),
    "emp182_zscored_decline_replicated": bool(
        rows_z[0][2] > 0.4 and rows_z[-1][2] < 0.10 and rho_z < -0.5),
    "crt026_zscored_saturation_replicated": bool(
        min(r[2] for r in rows_z) > 0.90),
}
print(json.dumps(match, indent=2))

sat = min(r[2] for r in rows_z)
amp = np.array([r[-1] for r in rows_raw])
rrs_raw = np.array([r[2] for r in rows_raw])
rho_amp, _ = spearmanr(rrs_raw, amp)
print(f"\namplitude confound check (raw protocol): Spearman(RR_raw, band RMS) = "
      f"{rho_amp:+.3f}  (EMP-187 reported +0.70)")

results = {
    "raw_uV": [(r[0], r[2], r[3], r[4], r[5], r[6]) for r in rows_raw],
    "zscored": [(r[0], r[2], r[3], r[4], r[5], r[6]) for r in rows_z],
    "relative": [(r[0], r[2], r[3], r[4], r[5], r[6]) for r in rows_rel],
    "spearmans": {"raw": float(rho_raw), "zscored": float(rho_z),
                  "relative": float(rho_rel)},
    "amplitude_confound_spearman_raw": float(rho_amp),
    "match_tests": match,
}
with open("eeg_units_arbitration.json", "w") as f:
    json.dump(results, f, indent=2, default=float)
print("saved eeg_units_arbitration.json")
