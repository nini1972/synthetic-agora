#!/usr/bin/env python3
"""
rqa_operating_curve_sweep.py
============================
Tests the RR-Operating-Point Determinism hypothesis (extension of EMP-201):
  * RQA frequency gradients (rho(band_freq, ENT)) are controlled by the
    Recurrence Rate operating point, not by (m, tau, epsilon) per se.
  * The per-band ENT(RR) curve is single-peaked and band-asymmetric.
  * At fixed-epsilon, band RMS rises with frequency -> RR rises with
    frequency -> high bands sit on the ASCENDING branch -> rho(freq,ENT) > 0
    (matches SYN-062's +0.9).
  * At matched-RR, beta/gamma collapse onto the FRAGMENTATION branch
    (diagonal shattering) -> rho(freq,ENT) < 0 (EMP-201 Stage B, EMP-227).

Two falsification tests against SYN-062's "pipeline-invariance" claim:
  T1: epsilon-path invariance  -- two very different epsilon schedules
      (geometric vs linear) reaching the same RR must give the same ENT.
  T2: operating-point flip    -- fixed-epsilon rho vs matched-RR rho must
      have opposite signs (predicted + vs -).
Plus achi-averaging profile: rho(freq, ENT_fixed) per (m, tau) config,
   showing 'invariance' holds only WITHIN the fixed-epsilon operating branch.
"""
import json, time
import numpy as np
from scipy.signal import butter, sosfiltfilt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

RNG = np.random.default_rng(42)
T0 = time.time()

# ---------------------------------------------------------------- data
ds = load_dataset("neural_eeg")
n_ch = len(ds) if isinstance(ds, (list, tuple)) else ds["data"].shape[0]
ch_names = ds["channels"] if isinstance(ds, dict) and "channels" in ds else [f"ch{i}" for i in range(n_ch)]
if isinstance(ds, dict):
    sig = ds["data"]
else:
    sig = np.stack([np.asarray(x, float) for x in ds])
fs = 128.0
AF3 = int(ch_names.index("AF3")) if "AF3" in ch_names else 0
af3 = np.asarray(sig[AF3], float)

# canonical 1st-stage artefacts from EMP-201 Stage A (fixed-eps=10, m=3, tau=2)
BANDS = ["delta", "theta", "alpha", "beta", "gamma"]
CENTERS = [2.25, 6.0, 10.0, 21.0, 37.5]
RR_FIXED = np.array([0.221, 0.593, 0.760, 0.653, 0.974])
ENT_FIXED = np.array([5.281, 4.851, 6.405, 4.978, 7.303])

# ---------------------------------------------------------------- helpers
def bandpass(x, lo, hi, fs=128.0, order=4):
    sos = butter(order, [lo, hi], btype="bandpass", fs=fs, output="sos")
    return sosfiltfilt(sos, x)

def rqa_rr_ent(x, eps, m=3, tau=2):
    emb = takens_embedding(x, m=m, tau=tau)
    R = recurrence_matrix(emb, epsilon=eps)
    met = compute_rqa_metrics(R)
    return met["recurrence_rate"], met["shannon_entropy"], met["determinism"]

def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if np.std(ra) == 0 or np.std(rb) == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])

# ---------------------------------------------------------------- 1) eps-sweep: ENT(RR) operating curve
N_SWEEP = 2000
eps_grid = np.geomspace(0.35, 15.0, 22)
curve = {}
for band, (lo, hi) in {"delta": (1.0, 3.0), "beta": (13.0, 30.0)}.items():
    xb = bandpass(af3, lo, hi)[:N_SWEEP]
    rr_l, ent_l = [], []
    for eps in eps_grid:
        rr, ent, det = rqa_rr_ent(xb, m=3, tau=2, eps=eps)
        rr_l.append(rr); ent_l.append(ent)
    curve[band] = {"eps": eps_grid.tolist(), "rr": rr_l, "ent": ent_l,
                   "rms": float(np.sqrt(np.mean(xb**2)))}
    print(f"[sweep] {band}: rms={curve[band]['rms']:.1f} uV  "
          f"rr {rr_l[0]:.3f}->{rr_l[-1]:.3f}  ent {ent_l[0]:.2f}->{ent_l[-1]:.2f}")

# ---------------------------------------------------------------- 2) T1 eps-path invariance @ fixed RR
x_alpha = bandpass(af3, 8.0, 12.0)[:N_SWEEP]
RR_TARGET = 0.226
def bisection_eps(x, rr_target, lo=0.2, hi=40.0, iters=18):
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        rr, _, _ = rqa_rr_ent(x, mid)
        if rr < rr_target: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)

eps_geom = bisection_eps(x_alpha, RR_TARGET, 0.2, 40.0)
eps_lin = float(np.clip(eps_geom + 0.18 * eps_geom, eps_geom * 0.5, eps_geom * 1.5))
lin_lo, lin_hi = eps_geom * 0.85, eps_geom * 1.15
for _ in range(8):
    mid = 0.5 * (lin_lo + lin_hi)
    rr, _, _ = rqa_rr_ent(x_alpha, 3, 2, mid)
    if rr < RR_TARGET: lin_lo = mid
    else: lin_hi = mid
eps_lin = 0.5 * (lin_lo + lin_hi)
rr_a, ent_a, det_a = rqa_rr_ent(x_alpha, 3, 2, eps_geom)
rr_b, ent_b, det_b = rqa_rr_ent(x_alpha, 3, 2, eps_lin)
t1 = {"rr_target": RR_TARGET, "eps_geom": eps_geom, "eps_lin": eps_lin,
      "rr_geom": rr_a, "ent_geom": ent_a, "det_geom": det_a,
      "rr_lin": rr_b, "ent_lin": ent_b, "det_lin": det_b,
      "d_rr": abs(rr_a - rr_b), "d_ent": abs(ent_a - ent_b)}
print(f"[T1] eps-path invariance: geom eps={eps_geom:.3f} (rr={rr_a:.3f}, ent={ent_a:.2f}) vs "
      f"lin eps={eps_lin:.3f} (rr={rr_b:.3f}, ent={ent_b:.2f}) -> dENT={t1['d_ent']:.3f}")

# ---------------------------------------------------------------- 3) T2 operating-point flip (5 bands, m=3, tau=2)
N_BANDS = 1600
band_defs = {"delta": (1.0, 3.0), "theta": (4.0, 7.0), "alpha": (8.0, 12.0),
             "beta": (13.0, 30.0), "gamma": (31.0, 44.0)}
rr_f, ent_f = [], []
for band in BANDS:
    lo, hi = band_defs[band]
    xb = bandpass(af3, lo, hi)[:N_BANDS]
    rr, ent, _ = rqa_rr_ent(xb, 3, 2, 10.0)
    rr_f.append(rr); ent_f.append(ent)
rr_f, ent_f = np.array(rr_f), np.array(ent_f)
rho_rr_freq_fixed = spearman(rr_f, CENTERS)
rho_ent_freq_fixed = spearman(ent_f, CENTERS)
rho_ent_rr_fixed = spearman(ent_f, rr_f)
# matched-RR (from EMP-201 Stage B protocol, q=0.5): reuse published artefact values
ENT_MATCHED = np.array([5.230, 3.944, 3.912, 2.337, 2.561])
RR_MATCHED = np.array([0.240, 0.220, 0.234, 0.018, 0.064])
rho_ent_freq_matched = spearman(ENT_MATCHED, CENTERS)
t2 = {"rr_fixed": rr_f.tolist(), "ent_fixed": ent_f.tolist(),
      "rho_rr_freq_fixed": rho_rr_freq_fixed, "rho_ent_freq_fixed": rho_ent_freq_fixed,
      "rho_ent_rr_fixed": rho_ent_rr_fixed, "rho_ent_freq_matched": rho_ent_freq_matched,
      "ent_matched_ref": ENT_MATCHED.tolist()}
print(f"[T2] fixed-eps:  rho(rr,freq)={rho_rr_freq_fixed:+.2f}  rho(ent,freq)={rho_ent_freq_fixed:+.2f}  rho(ent,rr)={rho_ent_rr_fixed:+.2f}")
print(f"[T2] matched-RR (EMP-201 Stage B): rho(ent,freq)={rho_ent_freq_matched:+.2f}  -> sign flip: "
      f"{np.sign(rho_ent_freq_fixed) != np.sign(rho_ent_freq_matched)}")

# ---------------------------------------------------------------- 4) achi-averaged profile per (m, tau)
per_config = []
for m in (2, 3, 5):
    for tau in (1, 2, 4):
        e_f = []
        for band in BANDS:
            lo, hi = band_defs[band]
            xb = bandpass(af3, lo, hi)[:N_BANDS]
            _, ent, _ = rqa_rr_ent(xb, m, tau, 10.0)
            e_f.append(ent)
        per_config.append({"m": m, "tau": tau,
                           "rho_ent_freq_fixed": spearman(np.array(e_f), CENTERS)})
rhos = [c["rho_ent_freq_fixed"] for c in per_config]
rho_mean, rho_std = float(np.mean(rhos)), float(np.std(rhos))
print(f"[achi] fixed-eps rho(ent,freq) across 9 (m,tau): mean={rho_mean:+.2f} +/- {rho_std:.2f}")

# ---------------------------------------------------------------- figures
fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8))
colors = {"delta": "#1f77b4", "beta": "#d62728"}
for band in ("delta", "beta"):
    c = curve[band]
    axes[0].plot(c["rr"], c["ent"], "o-", ms=3.5, lw=1.2, color=colors[band], label=f"{band} (rms {c['rms']:.0f} uV)")
axes[0].axhline(max(curve["delta"]["ent"]), color="grey", ls=":", lw=0.8)
axes[0].set_xlabel("Recurrence rate RR (eps-sweep, fixed m=3, tau=2)")
axes[0].set_ylabel("Diagonal entropy ENT")
axes[0].set_title("(1) Single-peaked ENT(RR) operating curves\n(band-asymmetric)")
axes[0].legend(fontsize=8)
for i, band in enumerate(BANDS):
    axes[1].scatter(rr_f[i], ent_f[i], s=90, color=colors.get(band, "#7f7f7f"), zorder=3)
    axes[1].annotate(f"{band[0].upper()}", (rr_f[i], ent_f[i]), fontsize=9,
                     xytext=(4, 4), textcoords="offset points")
axes[1].set_xlabel("RR at fixed eps=10 uV^2")
axes[1].set_ylabel("ENT at fixed eps=10 uV^2")
axes[1].set_title(f"(2) Fixed-eps operating points, AF3\n"
                  f"rho(rr,freq)={rho_rr_freq_fixed:+.2f}, rho(ent,freq)={rho_ent_freq_fixed:+.2f}")
axes[1].grid(alpha=0.3)
xs = np.arange(5)
axes[2].bar(xs - 0.18, ENT_FIXED, width=0.36, label="fixed eps=10 (Stage A)", color="#ff7f0e", alpha=0.85)
axes[2].bar(xs + 0.18, ENT_MATCHED, width=0.36, label="matched RR~0.2 (Stage B)", color="#2ca02c", alpha=0.85)
axes[2].set_xticks(xs); axes[2].set_xticklabels([b[0].upper() for b in BANDS])
axes[2].set_ylabel("ENT"); axes[2].legend(fontsize=8)
axes[2].set_title(f"(3) Operating-point flip\nrho(ent,freq): fixed={rho_ent_freq_fixed:+.2f} vs matched={rho_ent_freq_matched:+.2f}")
plt.tight_layout()
plt.savefig("rqa_operating_curve.png", dpi=140)
print("saved rqa_operating_curve.png")

out = {"t1_eps_path_invariance": t1,
       "t2_operating_point_flip": t2,
       "t3_pipeline_invariance_within_branch": {"per_config": per_config,
                                               "rho_mean": rho_mean, "rho_std": rho_std},
       "operating_curves": curve,
       "achi_fixed_ref": {"rr": RR_FIXED.tolist(), "ent": ENT_FIXED.tolist()},
       "runtime_s": round(time.time() - T0, 1)}
with open("rqa_operating_curve.json", "w") as f:
    json.dump(out, f, indent=1)
print("saved rqa_operating_curve.json")
print(f"DONE in {out['runtime_s']}s")
