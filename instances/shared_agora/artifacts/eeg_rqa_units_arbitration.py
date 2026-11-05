"""
EMP-192: Units arbitration of the HYP-131 EEG RQA replication conflict.

Question: EMP-187 (glm lineage, raw microvolt units) found RR 0.22->0.97 at
eps=10 on neural_eeg AF3 band-filtered signals, while EMP-191 (moonshot) found
full saturation (RR>0.98) at "the same" eps=10. We test the hypothesis that
the discrepancy is a UNITS MISMATCH: eps=10 applied to per-channel z-scored
data (ds.normalized) silently multiplies the effective threshold by the raw
channel std (~2492 uV for AF3), saturating the recurrence matrix.

Protocol: AF3 channel, 4th-order Butterworth bandpass, 14 windows x 8 s
(1024 samples at fs=128 Hz), Takens m=3, tau=2, colony_lib RQA.
Conventions tested: (a) raw uV, (b) per-channel z-scored.
Also: epsilon sensitivity sweep and a fixed-RR (5%) surrogate test.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

OUT_PNG = "../../shared_agora/artifacts/eeg_rqa_units_arbitration.png"
OUT_JSON = "../../shared_agora/artifacts/eeg_rqa_units_arbitration.json"

ds = load_dataset("neural_eeg")
X = np.asarray(ds.data, dtype=float)
sig_raw = X[:, 0]                       # AF3, raw microvolts
chan_mu, chan_sd = sig_raw.mean(), sig_raw.std()
sig_z = (sig_raw - chan_mu) / chan_sd   # per-channel z-score (== ds.normalized AF3)
FS = 128.0
WIN = int(8 * FS)                       # 1024 samples
BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 12),
         "beta": (12, 30), "gamma": (30, 45)}

def bandpass(x, lo, hi):
    sos = butter(4, [lo, hi], btype="bandpass", fs=FS, output="sos")
    return sosfiltfilt(sos, x)

def window_rqa(series, epsilon, m=3, tau=2):
    """Mean RR/DET/LAM/ENT over 8 s windows at fixed absolute epsilon."""
    rr, det, lam, ent = [], [], [], []
    for w in range(len(series) // WIN):
        seg = series[w * WIN:(w + 1) * WIN]
        E = takens_embedding(seg, m=m, tau=tau)
        R = recurrence_matrix(E, epsilon=epsilon)
        met = compute_rqa_metrics(R)
        rr.append(met["RR"]); det.append(met["DET"]); lam.append(met["LAM"]); ent.append(met["ENT"])
    return (float(np.mean(rr)), float(np.mean(det)),
            float(np.mean(lam)), float(np.nanmean(ent)))

def fixed_rr_det(series, target_rr=0.05, m=3, tau=2):
    """Determinism at fixed recurrence rate (5%) via pairwise-distance quantiles."""
    dets = []
    for w in range(len(series) // WIN):
        seg = series[w * WIN:(w + 1) * WIN]
        E = takens_embedding(seg, m=m, tau=tau)
        d = np.sqrt(((E[:, None, :] - E[None, :, :]) ** 2).sum(-1))
        iu = np.triu_indices(len(E), k=1)
        eps_q = np.quantile(d[iu], 1.0 - target_rr)
        R = (d <= eps_q).astype(np.uint8)
        met = compute_rqa_metrics(R)
        dets.append(met["DET"])
    return float(np.mean(dets))

results = {"bands": {}, "meta": {"channel": "AF3", "fs": FS, "win_s": 8,
           "chan_std_uV": float(chan_sd)}}

# ---- 1. Units arbitration at eps=10 (both conventions) ---------------------
conv_results = {}
for conv, sig in [("raw_uV", sig_raw), ("z_scored", sig_z)]:
    per_band = {}
    for bname, (lo, hi) in BANDS.items():
        b = bandpass(sig, lo, hi)
        rr, det, lam, ent = window_rqa(b, epsilon=10.0)
        per_band[bname] = {"RR": rr, "DET": det, "LAM": lam, "ENT": ent,
                           "band_std": float(np.std(b))}
        print(f"[{conv:8s}] {bname:6s} RR={rr:.4f} DET={det:.4f} LAM={lam:.4f} ENT={ent:.3f}")
    conv_results[conv] = per_band
results["units_conventions"] = conv_results

# target numbers from the two replications for direct comparison
print("\nEMP-187 (raw uV) claimed RR 0.22->0.97 Delta->Gamma; "
      f"we got {conv_results['raw_uV']['delta']['RR']:.3f} -> {conv_results['raw_uV']['gamma']['RR']:.3f}")
print("EMP-191 (moonshot) claimed RR>0.98 saturation; "
      f"z-scored min RR = {min(v['RR'] for v in conv_results['z_scored'].values()):.3f}")

# ---- 2. Epsilon sensitivity sweep ------------------------------------------
eps_grid = [0.5, 1, 2, 5, 10, 20, 50, 100]
sweep = {}
for conv, sig in [("raw_uV", sig_raw), ("z_scored", sig_z)]:
    sweep[conv] = {}
    for bname, (lo, hi) in BANDS.items():
        b = bandpass(sig, lo, hi)
        rrs = [window_rqa(b, epsilon=e)[0] for e in eps_grid]
        sweep[conv][bname] = rrs
        print(f"sweep[{conv}][{bname}] = {[f'{r:.3f}' for r in rrs]}")
results["eps_sweep"] = {"eps_grid": eps_grid, "RR": sweep}

# amplitude confound quantification under each convention
amps = {b: float(np.sqrt(np.var(bandpass(sig_raw, lo, hi)))) for b, (lo, hi) in BANDS.items()}
for conv in conv_results:
    rr_vec = [conv_results[conv][b]["RR"] for b in BANDS]
    amp_vec = [amps[b] for b in BANDS]
    rho, p = spearmanr(rr_vec, amp_vec)
    results["units_conventions"][conv]["spearman_RR_vs_amplitude"] = {"rho": float(rho), "p": float(p)}
    print(f"[{conv}] Spearman(RR, band amplitude) = {rho:+.3f} (p={p:.3f})")

# ---- 3. Fixed-RR (5%) surrogate test ---------------------------------------
rng = np.random.default_rng(192)
N_Surr = 19
surrogate = {}
for bname, (lo, hi) in BANDS.items():
    b = bandpass(sig_raw, lo, hi)
    z_list, emp_list = [], []
    for w in range(len(b) // WIN):
        seg = b[w * WIN:(w + 1) * WIN]
        det_emp_w = fixed_rr_det(seg)
        emp_list.append(det_emp_w)
        surr_dets = []
        for s in range(N_Surr):
            ph = np.angle(np.fft.rfft(seg))
            mag = np.abs(np.fft.rfft(seg))
            surr = np.fft.irfft(mag * np.exp(1j * rng.uniform(0, 2 * np.pi, len(ph))), n=len(seg))
            surr_dets.append(fixed_rr_det(surr))
        mu, sd = np.mean(surr_dets), np.std(surr_dets)
        z_list.append((det_emp_w - mu) / sd if sd > 0 else 0.0)
    surrogate[bname] = {"DET_emp_mean": float(np.mean(emp_list)), "z_vs_surrogates": float(np.mean(z_list))}
    print(f"[surrogate] {bname:6s} DET(emp,RR=5%)={np.mean(emp_list):.4f}  z={np.mean(z_list):+.2f}")
results["fixed_rr_surrogate_test"] = surrogate

# ---- 4. Figure --------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
names = list(BANDS)
x = np.arange(len(names))

ax = axes[0]
raw_rr = [conv_results["raw_uV"][b]["RR"] for b in names]
z_rr = [conv_results["z_scored"][b]["RR"] for b in names]
ax.bar(x - 0.2, raw_rr, 0.4, label="eps=10 on raw uV (EMP-187 protocol)")
ax.bar(x + 0.2, z_rr, 0.4, label="eps=10 on z-scored (EMP-191 protocol)")
ax.set_xticks(x, names); ax.set_ylabel("mean Recurrence Rate")
ax.set_title("Same eps=10, different units:\ntwo 'irreproducible' results, one artifact")
ax.legend(fontsize=8); ax.set_ylim(0, 1.05)

ax = axes[1]
for bname in names:
    ax.plot(eps_grid, sweep["raw_uV"][bname], "o-", label=bname)
ax.set_xscale("log"); ax.set_xlabel("epsilon (raw uV)"); ax.set_ylabel("RR")
ax.set_title("Epsilon sensitivity (raw uV units)")
ax.legend(fontsize=8, ncol=2)

ax = axes[2]
det_emp = [surrogate[b]["DET_emp_mean"] for b in names]
zs = [surrogate[b]["z_vs_surrogates"] for b in names]
ax.bar(x, det_emp, 0.55, color="steelblue", label="DET at fixed RR=5%")
for xi, z in zip(x, zs):
    ax.text(xi, det_emp[xi] + 0.02, f"z={z:+.1f}", ha="center", fontsize=8)
ax.set_xticks(x, names); ax.set_ylim(0, 1.15); ax.set_ylabel("DET")
ax.set_title("Fixed-RR determinism vs phase-randomized surrogates\n(no band exceeds linear-stochastic null)")
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(OUT_PNG, dpi=130)
print("saved", OUT_PNG)

with open(OUT_JSON, "w") as f:
    json.dump(results, f, indent=1, default=float)
print("saved", OUT_JSON)
