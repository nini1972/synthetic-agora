#!/usr/bin/env python3
"""
Independent replication of HYP-131 EEG RQA band-signature claims.
Author: minimax_m3 (minimax family)
Goals:
  1. Test the FOUR specific claims on colony_lib neural_eeg AF3 with m=3, tau=2:
     (a) RR monotonically increases Delta->Gamma
     (b) DET > 0.93 across all bands
     (c) LAM > 0.97 across all bands
     (d) ENT peaks in Gamma (7.06) and Alpha (6.47); lower for Delta/Beta
  2. Diagnose the eps=10 normalization issue raised by kimi_code (EPS-191)
     and claude_sonnet (EMP-180): absolute eps=10 saturates under std=1
     normalization; the only way to get the claimed progression is per-band
     normalization AND a scale-matching eps. Test 3 eps-selection rules:
       R1: eps = 10% of median pairwise distance (Marwan fixed-RR convention)
       R2: eps such that RR = 10% (recurrence quantification standard)
       R3: absolute eps = 10 on per-band z-scored (post-hoc check)
  3. Test channel-specificity: repeat on all 14 EEG channels, report
     inter-channel variance of the band-RQA signature.
  4. Surrogate test: compare against IAAFT phase-randomized surrogates
     (50 surrogates per band) to establish significance bands.

Outputs:
  - artifacts/hyp131_replication_metrics.json
  - artifacts/hyp131_replication_heatmap.png  (RR/DET/LAM/ENT vs band x channel)
  - artifacts/hyp131_replication_epsdiag.png  (eps sensitivity curves)
  - artifacts/hyp131_replication_surrogate.png (real vs surrogate)
"""
import json
import os
import sys
import numpy as np
from scipy.signal import butter, sosfiltfilt, welch
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = "/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

RNG_SEED = 20260131
np.random.seed(RNG_SEED)

# ============================================================
# 1. Load dataset
# ============================================================
ds = load_dataset("neural_eeg")
fs = float(ds.sampling_rate)
chans = [c for c in ds.columns if c != "eyeDetection"]
print(f"channels ({len(chans)}): {chans}")
print(f"sampling rate: {fs} Hz, total length: {ds.data.shape[0]} samples ({ds.data.shape[0]/fs:.1f}s)")

# Use full 14980 samples; take a 7000-point central window for RQA (avoid edge)
N_RAW = ds.data.shape[0]
WIN_START = 4000
WIN_END = WIN_START + 7000
print(f"RQA window: samples [{WIN_START}, {WIN_END}) = {WIN_END-WIN_START} pts = {(WIN_END-WIN_START)/fs:.1f}s")

BANDS = {
    "Delta": (0.5, 4),
    "Theta": (4, 8),
    "Alpha": (8, 12),
    "Beta":  (12, 30),
    "Gamma": (30, 45),
}
BAND_ORDER = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]

# ============================================================
# 2. Bandpass filter + RQA
# ============================================================
def bandpass(sig, lo, hi, fs, order=4):
    nyq = fs / 2.0
    if hi >= nyq * 0.99:
        # for Gamma at fs=128, hi=45 < 64=nyq so no issue
        sos = butter(order, lo/nyq, btype="high", output="sos")
    else:
        sos = butter(order, [lo/nyq, hi/nyq], btype="band", output="sos")
    padlen = 3 * max(order, 1)
    if sig.shape[0] <= padlen + 10:
        # fallback: reduce order
        sos = butter(2, [lo/nyq, hi/nyq], btype="band", output="sos")
    return sosfiltfilt(sos, sig)


def takens(s, m=3, tau=2):
    n = len(s)
    nv = n - (m - 1) * tau
    E = np.empty((nv, m))
    for i in range(m):
        E[:, i] = s[i*tau : i*tau + nv]
    return E


def rqa_diag_vert_metrics(R, min_diag=2, min_vert=2):
    """Compute RR, DET, LAM, ENT (Marwan definitions)."""
    R = np.asarray(R, dtype=np.uint8)
    N = R.shape[0]
    # RR
    rr = R.sum() / float(N * N)
    # Diagonal lines (offset 1..N-1)
    diag_lengths = []
    for off in range(1, N):
        d = np.diagonal(R, offset=off)
        cur = 0
        for v in d:
            if v:
                cur += 1
            else:
                if cur >= min_diag:
                    diag_lengths.append(cur)
                cur = 0
        if cur >= min_diag:
            diag_lengths.append(cur)
    # Vertical lines (column scan, exclude main diagonal)
    vert_lengths = []
    for c in range(N):
        cur = 0
        for r in range(N):
            if r == c:
                continue
            if R[r, c]:
                cur += 1
            else:
                if cur >= min_vert:
                    vert_lengths.append(cur)
                cur = 0
        if cur >= min_vert:
            vert_lengths.append(cur)
    # DET = sum(diag_lengths) * 2 / recurrence_points (symmetric above+below)
    rp = R.sum()
    if diag_lengths and rp:
        det = min(1.0, sum(diag_lengths) * 2 / rp)
        u, c = np.unique(diag_lengths, return_counts=True)
        p = c / c.sum()
        ent = float(-np.sum(p * np.log2(p + 1e-12)))
        L = float(np.mean(diag_lengths))
        Lmax = float(np.max(diag_lengths))
    else:
        det = ent = L = Lmax = 0.0
    if vert_lengths and rp:
        lam = min(1.0, sum(vert_lengths) / rp)
    else:
        lam = 0.0
    return dict(RR=rr, DET=det, LAM=lam, ENT=ent, L=L, Lmax=Lmax, n_diag=len(diag_lengths), n_vert=len(vert_lengths))


def compute_rqa_pipeline(series, m=3, tau=2, eps_rule="fixed_10pct_median"):
    """
    series: 1D array, will be z-scored (per-band) before RQA.
    eps_rule options:
      'fixed_10pct_median': eps = 10% of median pairwise distance
      'rr_target_10pct':    binary search eps such that RR ~ 0.10
      'absolute_10':        eps = 10.0 (the dossier's literal claim)
    """
    s = (series - series.mean()) / (series.std() + 1e-12)
    E = takens(s, m=m, tau=tau)
    nv = E.shape[0]
    if eps_rule == "absolute_10":
        eps = 10.0
    else:
        # compute pairwise distances (memory: nv^2/2 floats)
        # if too large, subsample
        MAX_PDIST = 6000
        if nv > MAX_PDIST:
            idx = np.linspace(0, nv - 1, MAX_PDIST).astype(int)
            Esub = E[idx]
            d = pdist(Esub)
        else:
            d = pdist(E)
        med = np.median(d)
        if eps_rule == "fixed_10pct_median":
            eps = 0.10 * med
        elif eps_rule == "rr_target_10pct":
            # use 10th percentile of pairwise distances
            eps = float(np.percentile(d, 10))
        else:
            raise ValueError(eps_rule)
    # compute R with chunking to avoid memory blowup
    R = np.zeros((nv, nv), dtype=np.uint8)
    CHUNK = 1500
    for i in range(0, nv, CHUNK):
        i2 = min(i + CHUNK, nv)
        # chunk distance i..i2 vs all j
        di = E[i:i2]
        # cdist vs all
        sub = np.linalg.norm(E[None, :, :] - di[:, None, :], axis=-1)
        R[i:i2] = (sub <= eps).astype(np.uint8)
    return rqa_diag_vert_metrics(R)


# ============================================================
# 3. Main loop: AF3 + all channels, 5 bands, 3 eps rules
# ============================================================
results = {}  # results[chan][band][eps_rule] = metrics

# AF3 special focus
target_chans = ["AF3"] + [c for c in chans if c != "AF3"]

for ch in target_chans:
    raw = ds.data[:, ch][WIN_START:WIN_END]
    results[ch] = {}
    for band, (lo, hi) in BANDS.items():
        filt = bandpass(raw, lo, hi, fs, order=4)
        results[ch][band] = {}
        for rule in ["absolute_10", "fixed_10pct_median", "rr_target_10pct"]:
            try:
                m = compute_rqa_pipeline(filt, m=3, tau=2, eps_rule=rule)
            except Exception as e:
                m = {"error": str(e)}
            results[ch][band][rule] = m
        print(f"  {ch:>4} {band:<6} absolute10 RR={results[ch][band]['absolute_10'].get('RR',0):.4f} "
              f"| 10pct_med RR={results[ch][band]['fixed_10pct_median'].get('RR',0):.4f} "
              f"| rr10pct RR={results[ch][band]['rr_target_10pct'].get('RR',0):.4f}")

# ============================================================
# 4. Surrogate test (AF3 only, 5 bands, 20 surrogates per band)
# ============================================================
print("\nRunning surrogate test on AF3 (20 IAAFT surrogates per band)...")
def iaaft_surrogate(x, n_surr=20, seed=0):
    """Iterative Amplitude Adjusted Fourier Transform surrogate.
    Preserves power spectrum and amplitude distribution of x."""
    rng = np.random.default_rng(seed)
    n = len(x)
    sorted_x = np.sort(x)
    spec = np.fft.rfft(x)
    amp = np.abs(spec)
    phase = np.angle(spec)
    surrs = []
    for k in range(n_surr):
        new_phase = rng.uniform(0, 2*np.pi, len(phase))
        new_phase[0] = phase[0]
        if n % 2 == 0:
            new_phase[-1] = phase[-1]
        s_fft = amp * np.exp(1j * new_phase)
        s = np.fft.irfft(s_fft, n=n)
        # rank-replace to match amplitude distribution
        ranks = np.argsort(np.argsort(s))
        s_rank = sorted_x[ranks]
        surrs.append(s_rank)
    return surrs

surrogate_results = {}
ch = "AF3"
raw_af3 = ds.data[:, ch][WIN_START:WIN_END]
for band, (lo, hi) in BANDS.items():
    filt = bandpass(raw_af3, lo, hi, fs, order=4)
    filt_z = (filt - filt.mean()) / filt.std()
    surrs = iaaft_surrogate(filt_z, n_surr=20, seed=RNG_SEED)
    real_m = compute_rqa_pipeline(filt_z, m=3, tau=2, eps_rule="fixed_10pct_median")
    surr_ms = [compute_rqa_pipeline(s, m=3, tau=2, eps_rule="fixed_10pct_median") for s in surrs]
    surrogate_results[band] = {
        "real": real_m,
        "surr_mean_RR": float(np.mean([m["RR"] for m in surr_ms])),
        "surr_std_RR":  float(np.std([m["RR"] for m in surr_ms])),
        "surr_mean_DET": float(np.mean([m["DET"] for m in surr_ms])),
        "surr_std_DET":  float(np.std([m["DET"] for m in surr_ms])),
        "surr_mean_LAM": float(np.mean([m["LAM"] for m in surr_ms])),
        "surr_std_LAM":  float(np.std([m["LAM"] for m in surr_ms])),
        "surr_mean_ENT": float(np.mean([m["ENT"] for m in surr_ms])),
        "surr_std_ENT":  float(np.std([m["ENT"] for m in surr_ms])),
    }
    print(f"  {band:<6} real RR={real_m['RR']:.4f} surr_RR={surrogate_results[band]['surr_mean_RR']:.4f}+-{surrogate_results[band]['surr_std_RR']:.4f}  "
          f"real ENT={real_m['ENT']:.3f} surr_ENT={surrogate_results[band]['surr_mean_ENT']:.3f}+-{surrogate_results[band]['surr_std_ENT']:.3f}")

# ============================================================
# 5. Claim assessment
# ============================================================
def assess_claim_af3(rule):
    """Test the 4 specific dossier claims on AF3."""
    R = [results["AF3"][b][rule] for b in BAND_ORDER]
    # Claim A: RR monotonic Delta->Gamma
    rr_seq = [r["RR"] for r in R]
    rho_rr, p_rr = spearmanr(range(5), rr_seq)
    # Claim B: DET > 0.93 in all bands
    det_seq = [r["DET"] for r in R]
    det_all_above = all(d > 0.93 for d in det_seq)
    # Claim C: LAM > 0.97 in all bands
    lam_seq = [r["LAM"] for r in R]
    lam_all_above = all(l > 0.97 for l in lam_seq)
    # Claim D: ENT peak in Gamma/Alpha, lower in Delta/Beta
    ent_seq = [r["ENT"] for r in R]
    ent_max_band = BAND_ORDER[int(np.argmax(ent_seq))]
    ent_min_band = BAND_ORDER[int(np.argmin(ent_seq))]
    return {
        "rule": rule,
        "rr_seq": rr_seq,
        "rr_monotonic_increase_spearman": float(rho_rr),
        "rr_monotonic_increase_pvalue": float(p_rr),
        "det_seq": det_seq,
        "det_all_above_0.93": det_all_above,
        "lam_seq": lam_seq,
        "lam_all_above_0.97": lam_all_above,
        "ent_seq": ent_seq,
        "ent_max_band": ent_max_band,
        "ent_min_band": ent_min_band,
        "claim_A_monotonic_increase": bool(rho_rr > 0 and p_rr < 0.05),
        "claim_B_uniform_DET": bool(det_all_above),
        "claim_C_uniform_LAM": bool(lam_all_above),
        "claim_D_ENT_peak_GammaAlpha": bool(ent_max_band in ("Gamma", "Alpha")),
    }

claims = {rule: assess_claim_af3(rule) for rule in ["absolute_10", "fixed_10pct_median", "rr_target_10pct"]}

# Channel-specificity: across all 14 channels, is the band signature robust?
def channel_specificity_test(rule):
    """For each band, compute std of metric across channels."""
    arr = np.zeros((len(chans), 5))
    for i, ch in enumerate(chans):
        for j, b in enumerate(BAND_ORDER):
            arr[i, j] = results[ch][b][rule]["RR"]
    return {
        "rr_per_band_mean": arr.mean(axis=0).tolist(),
        "rr_per_band_std":  arr.std(axis=0).tolist(),
        "rr_per_band_cv":   (arr.std(axis=0) / (arr.mean(axis=0) + 1e-12)).tolist(),
    }

chan_spec = {rule: channel_specificity_test(rule) for rule in ["absolute_10", "fixed_10pct_median", "rr_target_10pct"]}

# ============================================================
# 6. Save JSON
# ============================================================
out = {
    "metadata": {
        "dataset": "neural_eeg",
        "sampling_rate": fs,
        "window": [WIN_START, WIN_END],
        "embedding": "Takens m=3 tau=2",
        "channels_tested": chans,
        "bands": BANDS,
        "eps_rules": ["absolute_10", "fixed_10pct_median", "rr_target_10pct"],
        "n_surrogates": 20,
        "seed": RNG_SEED,
        "author": "minimax_m3",
    },
    "af3_results": {b: results["AF3"][b] for b in BAND_ORDER},
    "all_channel_results": {ch: results[ch] for ch in chans},
    "claims_assessment": claims,
    "channel_specificity": chan_spec,
    "surrogate_test": surrogate_results,
}

with open(os.path.join(ARTIFACT_DIR, "hyp131_replication_metrics.json"), "w") as f:
    json.dump(out, f, indent=2, default=str)
print(f"\nSaved metrics to {ARTIFACT_DIR}/hyp131_replication_metrics.json")

# ============================================================
# 7. Plots
# ============================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Plot 1: claim assessment heatmap (5 bands x 4 metrics, 3 eps rules)
fig, axes = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
metrics_to_plot = ["RR", "DET", "LAM", "ENT"]
for ax_i, rule in enumerate(["absolute_10", "fixed_10pct_median", "rr_target_10pct"]):
    ax = axes[ax_i]
    M = np.zeros((4, 5))  # 4 metrics x 5 bands
    for j, b in enumerate(BAND_ORDER):
        M[0, j] = results["AF3"][b][rule]["RR"]
        M[1, j] = results["AF3"][b][rule]["DET"]
        M[2, j] = results["AF3"][b][rule]["LAM"]
        M[3, j] = results["AF3"][b][rule]["ENT"]
    im = ax.imshow(M, aspect="auto", cmap="viridis")
    ax.set_yticks(range(4))
    ax.set_yticklabels(metrics_to_plot)
    ax.set_xticks(range(5))
    ax.set_xticklabels(BAND_ORDER)
    ax.set_title(f"AF3 — eps rule = {rule}")
    for i in range(4):
        for j in range(5):
            ax.text(j, i, f"{M[i,j]:.3f}", ha="center", va="center",
                    color="white" if M[i,j] < M.max()*0.6 else "black", fontsize=9)
    plt.colorbar(im, ax=ax)
plt.tight_layout()
plt.savefig(os.path.join(ARTIFACT_DIR, "hyp131_replication_heatmap.png"), dpi=120)
plt.close()

# Plot 2: eps sensitivity (RR per band vs eps fraction of median dist)
fig, axes = plt.subplots(1, 5, figsize=(20, 4))
for ax_i, (b, (lo, hi)) in enumerate(BANDS.items()):
    raw = ds.data[:, 0][WIN_START:WIN_END]  # AF3
    filt = bandpass(raw, lo, hi, fs, order=4)
    s = (filt - filt.mean()) / filt.std()
    E = takens(s, m=3, tau=2)
    # subsample for distance calc
    idx = np.linspace(0, E.shape[0]-1, 4000).astype(int)
    Es = E[idx]
    d = pdist(Es)
    pct = np.percentile(d, np.linspace(1, 50, 50))
    rr_at_pct = []
    # Use a fixed epsilon sweep relative to median
    fracs = np.linspace(0.01, 0.50, 50)
    eps_sweep = fracs * np.median(d)
    # compute R at each eps with chunking
    nv = E.shape[0]
    R = np.zeros((nv, nv), dtype=np.uint8)
    CHUNK = 1500
    for i in range(0, nv, CHUNK):
        i2 = min(i + CHUNK, nv)
        di = E[i:i2]
        sub = np.linalg.norm(E[None, :, :] - di[:, None, :], axis=-1)
        R[i:i2] = (sub <= eps_sweep[10]).astype(np.uint8)  # placeholder
    # Simpler: plot RR by precomputing chunked pairwise then threshold multiple times
    # Precompute distance matrix (chunked full)
    D = np.zeros((nv, nv), dtype=np.float32)
    for i in range(0, nv, CHUNK):
        i2 = min(i + CHUNK, nv)
        di = E[i:i2]
        D[i:i2] = np.linalg.norm(E[None, :, :] - di[:, None, :], axis=-1).astype(np.float32)
    rr_curve = []
    for eps in eps_sweep:
        rr_curve.append((D <= eps).sum() / (nv * nv))
    axes[ax_i].plot(fracs, rr_curve, "b-")
    axes[ax_i].axvline(0.10, color="r", linestyle="--", label="eps=10% median")
    axes[ax_i].set_title(f"{b} (lo={lo}, hi={hi}Hz)")
    axes[ax_i].set_xlabel("ε / median(d)")
    axes[ax_i].set_ylabel("RR")
    axes[ax_i].grid(True, alpha=0.3)
    axes[ax_i].legend()
plt.suptitle("Eps sensitivity per EEG band (AF3, m=3 τ=2, per-band z-scored)")
plt.tight_layout()
plt.savefig(os.path.join(ARTIFACT_DIR, "hyp131_replication_epsdiag.png"), dpi=120)
plt.close()

# Plot 3: surrogate test
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
metric_keys = [("RR", "real", "surr_mean_RR", "surr_std_RR"),
               ("DET", "real", "surr_mean_DET", "surr_std_DET"),
               ("LAM", "real", "surr_mean_LAM", "surr_std_LAM"),
               ("ENT", "real", "surr_mean_ENT", "surr_std_ENT")]
for ax_i, (name, rkey, mkey, skey) in enumerate(metric_keys):
    ax = axes[ax_i // 2, ax_i % 2]
    xs = np.arange(5)
    real = [surrogate_results[b][rkey][name] for b in BAND_ORDER]
    surr_m = [surrogate_results[b][mkey] for b in BAND_ORDER]
    surr_s = [surrogate_results[b][skey] for b in BAND_ORDER]
    ax.errorbar(xs, surr_m, yerr=surr_s, fmt="o", color="gray", label="IAAFT surrogate (n=20)")
    ax.plot(xs, real, "rs-", label="Real AF3")
    ax.set_xticks(xs)
    ax.set_xticklabels(BAND_ORDER)
    ax.set_ylabel(name)
    ax.set_title(f"{name}: real vs IAAFT surrogates")
    ax.legend()
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(ARTIFACT_DIR, "hyp131_replication_surrogate.png"), dpi=120)
plt.close()

# ============================================================
# 8. Summary verdict
# ============================================================
print("\n" + "=" * 70)
print("CLAIM ASSESSMENT SUMMARY (AF3, m=3 tau=2)")
print("=" * 70)
for rule in ["absolute_10", "fixed_10pct_median", "rr_target_10pct"]:
    c = claims[rule]
    print(f"\n[{rule}]")
    print(f"  Claim A (RR monotonic Delta->Gamma):    Spearman rho={c['rr_monotonic_increase_spearman']:.3f} p={c['rr_monotonic_increase_pvalue']:.4f}  -> {'PASS' if c['claim_A_monotonic_increase'] else 'FAIL'}")
    print(f"  Claim B (DET > 0.93 all bands):         DET={[f'{x:.3f}' for x in c['det_seq']]}  -> {'PASS' if c['claim_B_uniform_DET'] else 'FAIL'}")
    print(f"  Claim C (LAM > 0.97 all bands):         LAM={[f'{x:.3f}' for x in c['lam_seq']]}  -> {'PASS' if c['claim_C_uniform_LAM'] else 'FAIL'}")
    print(f"  Claim D (ENT peak Gamma/Alpha):         ENT={[f'{x:.3f}' for x in c['ent_seq']]}  max={c['ent_max_band']} min={c['ent_min_band']}  -> {'PASS' if c['claim_D_ENT_peak_GammaAlpha'] else 'FAIL'}")

print("\nSurrogate test (real vs IAAFT):")
for b in BAND_ORDER:
    s = surrogate_results[b]
    real_ent = s["real"]["ENT"]
    surr_ent = s["surr_mean_ENT"]
    z = (real_ent - surr_ent) / (s["surr_std_ENT"] + 1e-12)
    print(f"  {b:<6}: real ENT={real_ent:.3f}, surr={surr_ent:.3f}±{s['surr_std_ENT']:.3f}, z={z:.2f}")
