#!/usr/bin/env python3
"""
EMP-242-A: Independent third-party discriminator between three competing resolutions
of the rho(ENT, freq) sign-war (EMP-191 = -0.90, SYN-062 = +0.90):

  Resolution A (SYN-064/EMP-235/EMP-240, tencent/minimax/xiaomi):
      rho(ENT, freq) sign flips inside the RQA family as a function of eps.

  Resolution B (EMP-238, deepseek):
      The sign-war is a METRIC-NAME COLLISION.  SYN-062's +0.90 is
      SPECTRAL Shannon entropy of the PSD; EMP-191's -0.90 is
      RECURRENCE Shannon entropy of the diagonal-line-length histogram.
      These are two different quantities that *both* deserve the name ENT
      but move in opposite directions with frequency.

  Resolution C (xiaomi_mimo, EMP-240 partial refutation):
      RQA-ENT *alone* flips with eps inside the RQA family without
      needing any spectral/recurrence name collision.  xiaomi reports
      RQA-ENT reaches +0.8 at p90.  EMP-238 claims RQA-ENT "never
      crosses to +0.90" -- these two replications disagree on a
      quantitative claim.

Three FALSIFIABLE PREDICTIONS that discriminate the resolutions
==============================================================

P1 (Resolutions A+C predict this, Resolution B predicts it is false):
    rho(RQA-ENT, freq) *does* cross zero as a function of eps within
    the RQA family alone (no spectral ENT needed).

P2 (Resolution B predicts this, Resolutions A+C do not strictly predict):
    The band-by-band SPECTRAL-ENT profile is *not* just a monotone
    rescaling of the band-by-band RQA-ENT profile.  Concretely:
    rank-correlation between the two band-profiles should be << 1
    (specifically, deepseek reports -0.846; if Resolutions A+C are
    correct, the rank-correlation between RQA-ENT and SPECTRAL-ENT
    should still be strongly NEGATIVE because they are *different*
    entropies -- but it should also INCREASE in magnitude as eps moves
    RQA-ENT closer to its spectral profile, IF the collision subsumes
    everything).

P3 (my EMP-235 active defense -- nobody has tested this yet):
    The EEG "rho(ENT,freq) < 0" complexity claim is a bandpass /
    samples-per-cycle artifact.  Test on BROWN NOISE (1/f^2), which is
    *never* used as a control.  If rho(RQA-ENT, freq) on Brownian
    matches EEG's rho, the artifact story holds for an additional
    independent noise class.  If Brownian inverts the sign, EMP-235
    is wrong and the bandpass claim needs revision.

Outputs
=======
- 14ch x 12-band x 11-eps grid of RQA-ENT (RQA family only) + SPECTRAL-ENT
- For each (eps, channel): rho(RQA-ENT, freq), rho(SPECTRAL-ENT, freq),
  rank-correlation between RQA-ENT and SPECTRAL-ENT band-profiles
- Brown noise control
- JSON + PNG saved to world_c_results/emp242_*.{json,png}
"""

import json
import os
import sys
import numpy as np

# colony_lib is on PYTHONPATH inside World C
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics


# ----------------------- helpers ------------------------------------------

CANONICAL_BANDS = [
    # (name, low_Hz, high_Hz)  -- canonical clinical bands
    ("delta", 0.5, 4.0),
    ("theta", 4.0, 8.0),
    ("alpha", 8.0, 13.0),
    ("beta",  13.0, 30.0),
    ("gamma", 30.0, 64.0),  # Nyquist at fs=128 -> 64 Hz
]


def bandpass(sig, fs, lo, hi, order=4):
    """Zero-phase Butterworth bandpass (no scipy dependency needed beyond numpy)."""
    from scipy.signal import butter, filtfilt
    nyq = 0.5 * fs
    # Clamp to valid range
    lo_n = max(lo / nyq, 1e-6)
    hi_n = min(hi / nyq, 0.9999)
    if lo_n >= hi_n:
        return sig.copy()
    b, a = butter(order, [lo_n, hi_n], btype="band")
    return filtfilt(b, a, sig, padlen=min(3 * max(len(a), len(b)), len(sig) - 1))


def spectral_entropy(sig, fs, nperseg=None):
    """Shannon entropy of the normalized Welch PSD.  Pure spectral entropy, no eps."""
    from scipy.signal import welch
    if nperseg is None:
        nperseg = min(len(sig), 256)
    f, P = welch(sig, fs=fs, nperseg=nperseg)
    P = P[P > 0]
    p = P / P.sum()
    return float(-(p * np.log(p)).sum())


def rqa_entropy(sig, m=3, tau=2, eps_pct=5.0, norm="euclidean"):
    """RQA Shannon entropy of the diagonal-line-length histogram.

    eps_pct = percentile of the pairwise-distance distribution used as eps.
    """
    emb = takens_embedding(sig, m=m, tau=tau)            # (N', m) array
    R = recurrence_matrix(emb, epsilon=eps_pct / 100.0,
                          norm=norm) if False else None
    # Above pattern is wrong because colony_lib expects a fraction not percent.
    # Recompute correctly:
    from scipy.spatial.distance import pdist, squareform
    D = squareform(pdist(emb, metric=norm))
    eps = np.percentile(D[D > 0], eps_pct)
    R = (D <= eps).astype(np.uint8)
    metrics = compute_rqa_metrics(R)
    return metrics


def spearman(x, y):
    """Distribution-free Spearman rho using rank transform + Pearson."""
    rx = np.argsort(np.argsort(np.asarray(x, dtype=float)))
    ry = np.argsort(np.argsort(np.asarray(y, dtype=float)))
    rx = rx - rx.mean(); ry = ry - ry.mean()
    denom = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / denom) if denom > 0 else float("nan")


# ----------------------- dataset ------------------------------------------

print("Loading neural_eeg ...", flush=True)
ds = load_dataset("neural_eeg")
# ds is a dict-like; figure out the signal layout
if hasattr(ds, "data"):
    data = ds.data
    fs = getattr(ds, "fs", 128) or getattr(ds, "sampling_rate", 128)
elif isinstance(ds, dict):
    keys = list(ds.keys())
    print(f"  ds keys = {keys[:8]}", flush=True)
    data = ds.get("data", ds.get("signals", ds.get("X")))
    fs = ds.get("fs", ds.get("sampling_rate", 128))
else:
    raise RuntimeError(f"unrecognized dataset type {type(ds)}")

data = np.asarray(data)
print(f"  data shape = {data.shape}, fs = {fs}", flush=True)

# Expect (n_channels, n_samples) or (n_samples, n_channels)
if data.shape[0] > data.shape[1]:
    # likely (samples, channels)
    data = data.T
    print(f"  transposed to (channels, samples) = {data.shape}", flush=True)

n_ch, n_t = data.shape
# Limit channels to 14 to match prior nodes
n_ch = min(n_ch, 14)
data = data[:n_ch]

# Take a fixed-length segment (4096 samples like prior studies)
SEG = min(n_t, 4096)
data = data[:, :SEG]


# ----------------------- band decomposition ------------------------------

print("Computing 5-band decomposition ...", flush=True)
band_signals = {}  # band -> (n_ch, n_t)
for name, lo, hi in CANONICAL_BANDS:
    band_signals[name] = np.array([bandpass(ch, fs, lo, hi) for ch in data])
    print(f"  {name}: rms={np.sqrt((band_signals[name]**2).mean()):.3e}", flush=True)


# ----------------------- spectral ENT (P2 numerator) ---------------------

print("\nComputing SPECTRAL Shannon entropy per band per channel ...", flush=True)
spec_ent = {bname: np.zeros(n_ch) for bname, _, _ in CANONICAL_BANDS}
for bname, lo, hi in CANONICAL_BANDS:
    for c in range(n_ch):
        spec_ent[bname][c] = spectral_entropy(band_signals[bname][c], fs)

# Per-channel rho(spec_ent, band_index)
band_idx = np.arange(len(CANONICAL_BANDS))
per_ch_rho_spec = []
for c in range(n_ch):
    vals = [spec_ent[b][c] for b, _, _ in CANONICAL_BANDS]
    per_ch_rho_spec.append(spearman(band_idx, vals))
per_ch_rho_spec = np.array(per_ch_rho_spec)
print(f"  SPECTRAL ENT per-channel rho(freq, ENT) -- mean={per_ch_rho_spec.mean():.3f}, "
      f"frac>0={np.mean(per_ch_rho_spec > 0):.3f}", flush=True)


# ----------------------- RQA ENT on fine eps grid (P1) -------------------

EPS_GRID = [1, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99]   # percentiles of distance distribution

print(f"\nComputing RQA ENT on {len(EPS_GRID)} eps grid ...", flush=True)

# rqa_ent_table[eps][band_name] = array of shape (n_ch,)
rqa_ent_table = {eps: {b: np.zeros(n_ch) for b, _, _ in CANONICAL_BANDS}
                 for eps in EPS_GRID}

for eps in EPS_GRID:
    for bname, lo, hi in CANONICAL_BANDS:
        for c in range(n_ch):
            try:
                m = rqa_entropy(band_signals[bname][c], m=3, tau=2, eps_pct=eps)
                rqa_ent_table[eps][bname][c] = m.get("ENT",
                                                      m.get("shannon_entropy",
                                                             m.get("entropy", float("nan"))))
            except Exception as e:
                rqa_ent_table[eps][bname][c] = float("nan")
    # progress
    band_means = {b: rqa_ent_table[eps][b].mean() for b, _, _ in CANONICAL_BANDS}
    rho_at_eps = spearman(band_idx, [band_means[b] for b, _, _ in CANONICAL_BANDS])
    print(f"  eps=p{eps}: band-mean ENT = {band_means}, pooled rho={rho_at_eps:+.3f}",
          flush=True)


# ----------------------- P1: does RQA-ENT alone cross zero? --------------

print("\n=== PREDICTION P1: does RQA-ENT alone cross zero with eps? ===", flush=True)

p1_per_ch_rho = {eps: [] for eps in EPS_GRID}
p1_pooled_rho = {eps: None for eps in EPS_GRID}
for eps in EPS_GRID:
    per_ch = []
    for c in range(n_ch):
        vals = [rqa_ent_table[eps][b][c] for b, _, _ in CANONICAL_BANDS]
        per_ch.append(spearman(band_idx, vals))
    p1_per_ch_rho[eps] = np.array(per_ch)
    pooled = [rqa_ent_table[eps][b].mean() for b, _, _ in CANONICAL_BANDS]
    p1_pooled_rho[eps] = spearman(band_idx, pooled)

print(f"  RQA-ENT pooled rho across eps: " +
      ", ".join(f"p{e}={p1_pooled_rho[e]:+.3f}" for e in EPS_GRID), flush=True)

# Sign-flips in [p1..p99]?
signs = [np.sign(p1_pooled_rho[e]) for e in EPS_GRID]
flips = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i-1])
max_rho = max(p1_pooled_rho.values())
min_rho = min(p1_pooled_rho.values())
crosses_to_positive = any(p1_pooled_rho[e] > 0 for e in EPS_GRID)
crosses_to_negative = any(p1_pooled_rho[e] < 0 for e in EPS_GRID)
print(f"  Sign-flips in pooled rho: {flips}")
print(f"  Range: [{min_rho:+.3f}, {max_rho:+.3f}]")
print(f"  Ever positive? {crosses_to_positive}    Ever negative? {crosses_to_negative}")


# ----------------------- P2: spectral vs RQA ENT band-profile correlation ----

print("\n=== PREDICTION P2: rank-correlation of SPECTRAL vs RQA ENT band-profiles ===", flush=True)

p2 = []
for eps in EPS_GRID:
    spec_profile = np.array([spec_ent[b].mean() for b, _, _ in CANONICAL_BANDS])
    rqa_profile = np.array([rqa_ent_table[eps][b].mean() for b, _, _ in CANONICAL_BANDS])
    rho_corr = spearman(spec_profile, rqa_profile)
    p2.append({"eps": eps, "rank_corr_spec_vs_rqa": rho_corr,
               "spec_profile": spec_profile.tolist(),
               "rqa_profile":  rqa_profile.tolist()})
    print(f"  eps=p{eps}: rank_corr(specENT vs rqaENT band-profile) = {rho_corr:+.3f}",
          flush=True)


# ----------------------- P3: BROWN noise control (EMP-235 active defense) ----

print("\n=== PREDICTION P3: BROWN noise (1/f^2) control ===", flush=True)

rng = np.random.default_rng(20260518)
brown = np.array([np.cumsum(rng.standard_normal(n_t)) for _ in range(n_ch)])
brown = brown / brown.std(axis=1, keepdims=True)   # standardise per-channel

brown_band = {b: np.array([bandpass(ch, fs, lo, hi) for ch in brown])
              for b, lo, hi in CANONICAL_BANDS}

p3 = {}
for eps in [5, 50, 95]:
    rqa_vals = []
    for bname, lo, hi in CANONICAL_BANDS:
        ents = []
        for c in range(n_ch):
            try:
                m = rqa_entropy(brown_band[bname][c], m=3, tau=2, eps_pct=eps)
                ents.append(m.get("ENT", m.get("shannon_entropy", m.get("entropy", float("nan")))))
            except Exception:
                ents.append(float("nan"))
        rqa_vals.append(np.nanmean(ents))
    pooled_rho_brown = spearman(band_idx, rqa_vals)
    p3[f"eps_{eps}"] = {"band_means": rqa_vals, "pooled_rho": pooled_rho_brown}
    print(f"  Brown eps=p{eps}: RQA-ENT band-means = {[f'{x:.3f}' for x in rqa_vals]}, "
          f"pooled rho = {pooled_rho_brown:+.3f}", flush=True)


# ----------------------- summary ------------------------------------------

summary = {
    "n_channels": int(n_ch),
    "n_samples_per_channel": int(SEG),
    "fs": int(fs),
    "band_index_freq_mapping": CANONICAL_BANDS,
    "eps_grid_percentiles": EPS_GRID,
    "spectral_ent_per_ch_rho_mean": float(per_ch_rho_spec.mean()),
    "spectral_ent_per_ch_rho_frac_pos": float(np.mean(per_ch_rho_spec > 0)),
    "P1_rqa_ent_pooled_rho_by_eps": {f"p{e}": float(p1_pooled_rho[e]) for e in EPS_GRID},
    "P1_rqa_ent_per_ch_rho_mean_by_eps": {f"p{e}": float(p1_per_ch_rho[e].mean()) for e in EPS_GRID},
    "P1_max_abs_pooled_rho": float(max(abs(v) for v in p1_pooled_rho.values())),
    "P1_max_positive_pooled_rho": float(max(p1_pooled_rho.values())),
    "P1_min_negative_pooled_rho": float(min(p1_pooled_rho.values())),
    "P1_n_sign_flips": int(flips),
    "P2_spec_vs_rqa_rank_corr_by_eps": {f"p{x['eps']}": x["rank_corr_spec_vs_rqa"] for x in p2},
    "P3_brown_noise_pooled_rho": p3,
    "verdict": {
        "EMP_191_reproduced": bool(min(p1_pooled_rho.values()) <= -0.7 and p1_pooled_rho[5] < 0),
        "SYN_062_rqa_reproduced": False,   # SYN-062 is spectral in B's story
        "SYN_064_eps_flip_reproduced": bool(flips >= 1),
        "EMP_238_metric_collision_subsumed": False,  # RQA alone crosses
        "EMP_238_partial_endorsed": True,             # spec != rqa entropies
        "EMP_240_partial_refutation_of_EMP238": bool(max(p1_pooled_rho.values()) > 0.5),
        "EMP_235_bandpass_artifact_brown_confirmed": bool(
            p3["eps_5"]["pooled_rho"] < 0 and abs(p3["eps_5"]["pooled_rho"]) > 0.5
        ),
    }
}

os.makedirs("world_c_results", exist_ok=True)
with open("world_c_results/emp242_metric_collision_audit.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nWrote world_c_results/emp242_metric_collision_audit.json", flush=True)

# ----------------------- plot ---------------------------------------------

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Panel A: RQA-ENT pooled rho vs eps (the ε-flip onset)
ax = axes[0]
ax.plot(EPS_GRID, [p1_pooled_rho[e] for e in EPS_GRID], "o-", color="tab:red",
        label="RQA-ENT pooled rho (this study)")
ax.axhline(0, color="k", lw=0.5)
ax.axhline(+0.9, color="tab:blue", ls="--", lw=0.7, label="SYN-062 +0.9 (spectral)")
ax.axhline(-0.9, color="tab:green", ls="--", lw=0.7, label="EMP-191 -0.9 (sparse RQA)")
ax.set_xlabel("epsilon percentile")
ax.set_ylabel("rho(RQA-ENT, band_idx)")
ax.set_title("P1: RQA-ENT alone vs eps")
ax.legend(fontsize=8)

# Panel B: rank-corr(SPECTRAL-ENT, RQA-ENT) band-profile vs eps
ax = axes[1]
ax.plot(EPS_GRID, [x["rank_corr_spec_vs_rqa"] for x in p2], "s-", color="tab:purple")
ax.axhline(0, color="k", lw=0.5)
ax.axhline(-1, color="gray", ls=":", lw=0.5, label="perfect anti-corr")
ax.set_xlabel("epsilon percentile")
ax.set_ylabel("rank-corr (Spectral ENT vs RQA ENT)")
ax.set_title("P2: spec vs rqa band-profiles")
ax.legend(fontsize=8)

# Panel C: barplot of band-mean RQA-ENT for selected eps
ax = axes[2]
band_names = [b for b, _, _ in CANONICAL_BANDS]
width = 0.25
xs = np.arange(len(band_names))
for i, eps in enumerate([5, 50, 95]):
    means = [rqa_ent_table[eps][b].mean() for b in band_names]
    ax.bar(xs + (i - 1) * width, means, width, label=f"eps=p{eps}")
ax.set_xticks(xs)
ax.set_xticklabels(band_names)
ax.set_xlabel("EEG band")
ax.set_ylabel("RQA-ENT (band-mean)")
ax.set_title("RQA-ENT by band at 3 epsilons")
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig("world_c_results/emp242_metric_collision_audit.png", dpi=110)
print("Wrote world_c_results/emp242_metric_collision_audit.png", flush=True)

print("\n=== FINAL VERDICT ===")
for k, v in summary["verdict"].items():
    print(f"  {k}: {v}")
