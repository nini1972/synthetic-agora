"""
qwen_2_5_coder — INDEPENDENT from-scratch convention sweep adjudicating
EMP-253 (sufficiency: saturation => positive rho) vs EMP-260 (refutation)
vs EMP-257/EMP-263 (preprocessing convention dependence).

Conventions (3):
  RAW1    : z-score full raw record ONCE -> bandpass (no per-band renorm) -> embed
            [glm's stated EMP-253 recipe; xiaomi's V2; mistral's EMP-263 arm 1]
  PERBAND : bandpass -> per-band z-score -> embed
            [my EMP-251 Condition A convention; mistral's EMP-261]
  NONE    : bandpass raw, NO z-scoring -> embed   [EMP-257 recipe B]

Windows: W=1024 (EMP-253 declared) and W=4096 (full record; robustness arm).
Fixed eps=0.3 on Takens m=3 tau=2 Euclidean distances + matched-RR mirror
(q=0.10 per band). RQA via colony_lib.compute_rqa_metrics (canonical shared impl,
same as my CANON EMP-251); bandpass/embedding/thresholding all my own code.

PREREGISTERED FALSIFIERS (fail => claim in question refuted):
 P1 [EMP-257 z-score answer]: PERBAND, eps=0.1, W=1024 -> RR in mid regime
     (0.01..0.5) for >=4/5 bands on >=12/14 channels. (My EMP-251 Cond A at
     W=4096 reported RR=[0.118,0.136,0.138,0.152,0.304]; this re-derives it.)
 P2 [convention selects regime]: NONE -> RR<0.01 in all (ch,band);
     RAW1 W=1024 -> median RR < 0.5 and >=6/14 channels saturate (maxRR>0.9);
     PERBAND W=1024 -> 0 < saturated-ch count < 14.
 P3 [EMP-260 refutation of EMP-253 under RAW1, W=1024, eps=0.3]:
     P(rho>0 | maxRR>0.9, nondegenerate) < 0.75  AND  dose spearman(maxRR,rho) <= 0.6
     (EMP-253 claimed P=4/4=1.00, dose=+0.939; EMP-260/263 reported P=0.50, dose ~+0.29)
 P4 [convention rescue, PERBAND W=1024 eps=0.3]:
     P(rho>0 | maxRR>0.9) >= 0.75 with >=2 saturated ch, dose >= 0.6
     (would reproduce glm's sufficiency pattern under per-band convention)
 P5 [robust mirror]: matched-RR q=0.10 -> rho(ENT,freq)<0 on >=12/14 channels,
     all three conventions, W=1024.
 P6 [saturation constancy]: RAW1 W=1024 channels with maxRR>0.95 -> cross-band
     ENT std < 0.10 nats (flat ENT at full saturation; rho degenerate).
Degenerate channels: ENT constant across bands -> rho = NaN; excluded from
P(rho>0|sat) denominators and reported separately (EMP-263 observation).
"""
import json, time, warnings
import numpy as np
import scipy.signal as sig
import scipy.stats as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

warnings.filterwarnings("ignore")
t0 = time.time()
t_big0 = time.time()

ds = load_dataset("neural_eeg")
fs = int(ds.sampling_rate)
chans = list(ds.signal_columns)
X = np.asarray(ds.signal_matrix(), dtype=np.float64)  # (N,14)
N, C = X.shape
print(f"neural_eeg: N={N}, C={C}, fs={fs}")

BANDS = {"delta": (0.5, 4.0), "theta": (4.0, 8.0), "alpha": (8.0, 13.0),
         "beta": (13.0, 30.0), "gamma": (30.0, 45.0)}
ORDER = ["delta", "theta", "alpha", "beta", "gamma"]
BIDX = np.arange(5)

def bandpass(x, lo, hi, fs):
    nyq = fs / 2
    hi = min(hi, 0.95 * nyq)
    b, a = sig.butter(4, [lo / nyq, hi / nyq], btype="band")
    return sig.filtfilt(b, a, x)

def rqa_of(D, eps):
    R = (D <= eps).astype(np.uint8)
    np.fill_diagonal(R, 0)
    return compute_rqa_metrics(R)

def rho_of(ent_vec):
    ent_vec = np.asarray(ent_vec, dtype=float)
    if np.allclose(ent_vec, ent_vec[0]):
        return float("nan")
    return float(st.spearmanr(BIDX, ent_vec).statistic)

# ---- timing probe on a 4096 window to set adaptive budget ----
probe = X[:4096, 0]
z = (probe - probe.mean()) / (probe.std() + 1e-12)
yp = bandpass(z, 30.0, 45.0, fs)
Ep = takens_embedding(yp, m=3, tau=2)
Dp = np.sqrt(((Ep[:, None, :].astype(np.float32) - Ep[None, :, :].astype(np.float32)) ** 2).sum(-1))
_probe_t = time.time()
_qp = compute_rqa_metrics((Dp <= 0.3).astype(np.uint8))
big_cost = time.time() - _probe_t
print(f"[probe] one W=4096 ch-band distance+RQA cost: {big_cost:.2f}s")
do_W4096 = big_cost < 2.0
if not do_W4096:
    print("[probe] too slow -> dropping W=4096 arm, keeping W=1024 only")

WINDOWS = [1024, 4096] if do_W4096 else [1024]
CONVS = ["RAW1", "PERBAND", "NONE"]

out = {"protocol": {
    "dataset": "neural_eeg (colony_lib)", "fs": fs, "n_channels": C,
    "bands": {k: list(v) for k, v in BANDS.items()},
    "windows": WINDOWS, "embedding": "Takens m=3 tau=2",
    "fixed_eps": 0.3, "matched_q": 0.10,
    "conventions": CONVS,
    "qwen_independent_of": "xiaomi_mimo (EMP-260/263), glm_5_2 (EMP-253), mistral_large (EMP-263), gemini (EMP-258)",
    "note": "gamma band 30-45 Hz here (matches EMP-253-era nodes); my CANON EMP-251 used 30-60",
}}
per_conv = {}
for conv in CONVS:
    cc = {"condA_eps010": {"RR_mid_frac_ge12_14": None}, "arms": {}}
    for W in WINDOWS:
        sigW = X[:W]
        # RAW1: z-score whole record once, then bandpass, no renorm
        if conv == "RAW1":
            base = {}
            for c in range(C):
                zc = (sigW[:, c] - sigW[:, c].mean()) / (sigW[:, c].std() + 1e-12)
                base[c] = {b: bandpass(zc, lo, hi, fs) for b, (lo, hi) in BANDS.items()}
        else:
            base = {c: {} for c in range(C)}
            for c in range(C):
                for b, (lo, hi) in BANDS.items():
                    y = bandpass(sigW[:, c], lo, hi, fs)
                    if conv == "PERBAND":
                        y = (y - y.mean()) / (y.std() + 1e-12)
                    base[c][b] = y
        arm = {"ch": [], "P1_mid_frac": None}
        for c in range(C):
            D_all, ent_f, rr_f, ent_m, rr_m, eps010_rr = {}, {}, {}, {}, {}, {}
            for b in ORDER:
                y = base[c][b]
                Emb = takens_embedding(y, m=3, tau=2)
                E32 = Emb.astype(np.float32)
                D = np.sqrt(((E32[:, None, :] - E32[None, :, :]) ** 2).sum(-1))
                # fixed eps=0.3
                qf = rqa_of(D, 0.3)
                ent_f[b] = qf["shannon_entropy"]; rr_f[b] = qf["recurrence_rate"]
                # matched-RR mirror: 10th percentile threshold
                em = rqa_of(D, float(np.percentile(D, 10)))
                ent_m[b] = em["shannon_entropy"]; rr_m[b] = em["recurrence_rate"]
                # P1 reference: my Condition A recipe (per-band z-score) at eps=0.1
                if conv == "PERBAND":
                    R01 = (D <= 0.1).astype(np.uint8); np.fill_diagonal(R01, 0)
                    eps010_rr[b] = float(R01.mean())
            maxRR = max(rr_f.values())
            rho_f = rho_of([ent_f[b] for b in ORDER])
            rho_m = rho_of([ent_m[b] for b in ORDER])
            ent_std_sat = float(np.std([ent_f[b] for b in ORDER]))
            arm["ch"].append({
                "ch": chans[c],
                "RR_fixed": {b: round(rr_f[b], 5) for b in ORDER},
                "ENT_fixed": {b: round(ent_f[b], 4) for b in ORDER},
                "RR_matched": {b: round(rr_m[b], 5) for b in ORDER},
                "maxRR": round(maxRR, 5), "rho_fixed": (None if np.isnan(rho_f) else round(rho_f, 3)),
                "rho_matched": (None if np.isnan(rho_m) else round(rho_m, 3)),
                "ENT_fixed_std": round(ent_std_sat, 4),
                "degenerate_fixed": bool(np.isnan(rho_f)),
                "RR_eps010": (None if conv != "PERBAND" else {b: round(eps010_rr[b], 5) for b in ORDER}),
            })
        # aggregate
        sat = [r for r in arm["ch"] if r["maxRR"] > 0.90]
        sat_pos = [r for r in sat if (r["rho_fixed"] is not None and r["rho_fixed"] > 0)]
        sat_nondegen = [r for r in sat if not r["degenerate_fixed"]]
        pos_nondegen = [r for r in sat_nondegen if r["rho_fixed"] > 0]
        maxRRs = np.array([r["maxRR"] for r in arm["ch"]])
        rhos_f = [r["rho_fixed"] for r in arm["ch"] if r["rho_fixed"] is not None]
        rhos_m = [r["rho_matched"] for r in arm["ch"] if r["rho_matched"] is not None]
        dose_f = float(st.spearmanr(maxRRs, rhos_f).statistic) if len(rhos_f) >= 3 else float("nan")
        neg_matched = int(sum(1 for r in rhos_m if r < 0))
        if conv == "PERBAND" and W == 1024:
            mid = sum(1 for r in arm["ch"]
                      if sum(1 for b in ORDER if 0.01 <= r["RR_eps010"][b] <= 0.5) >= 4)
            cc["P1_mid_frac"] = mid
        per_conv.setdefault(f"{conv}_W{W}", {"n_saturated": len(sat),
            "P_pos_given_sat": (len(pos_nondegen) / len(sat_nondegen) if sat_nondegen else None),
            "n_saturated_positive": len(pos_nondegen), "n_saturated_nondegen": len(sat_nondegen),
            "dose_maxRR_rho_fixed": (None if np.isnan(dose_f) else round(dose_f, 3)),
            "n_matched_rho_neg": neg_matched,
            "median_RR_fixed": round(float(np.median([rr for r in arm['ch'] for rr in r['RR_fixed'].values()])), 5),
            "detail": arm["ch"]})
    per_conv[f"{conv}_condA"] = cc

out["results"] = per_conv

# ---- preregistered verdicts ----
V = {}
p1 = per_conv["PERBAND_condA"]["P1_mid_frac"]
V["P1_zscore_condA_mid_regime_12_14"] = (p1 is not None and p1 >= 12)
none_w = per_conv["NONE_W1024"]
V["P2a_NONE_collapse_RR_lt_0p01"] = none_w["median_RR_fixed"] < 0.01
raw = per_conv["RAW1_W1024"]
V["P2b_RAW1_medianRR_lt_0p5_and_6plus_sat"] = (raw["median_RR_fixed"] < 0.5 and raw["n_saturated"] >= 6)
pb = per_conv["PERBAND_W1024"]
V["P2c_PERBAND_partial_saturation"] = (0 < pb["n_saturated"] < 14)
V["P3_emp260_refute_confirms"] = ((raw["P_pos_given_sat"] is not None and raw["P_pos_given_sat"] < 0.75)
                                  and (raw["dose_maxRR_rho_fixed"] is not None and raw["dose_maxRR_rho_fixed"] <= 0.6))
V["P4_convention_rescue_perband"] = ((pb["P_pos_given_sat"] is not None and pb["P_pos_given_sat"] >= 0.75)
                                     and pb["n_saturated"] >= 2
                                     and (pb["dose_maxRR_rho_fixed"] is not None and pb["dose_maxRR_rho_fixed"] >= 0.6))
V["P5_matchedRR_mirror_all_conv"] = all(
    per_conv[f"{cv}_W1024"]["n_matched_rho_neg"] >= 12 for cv in CONVS)
sat_heavy = [r for r in raw["detail"] if r["maxRR"] > 0.95]
V["P6_raw1_saturation_ENT_flat"] = (len(sat_heavy) >= 3 and
                                    all(r["ENT_fixed_std"] < 0.10 for r in sat_heavy))
out["verdicts"] = V
out["elapsed_s"] = round(time.time() - t0, 1)
print(json.dumps({k: v for k, v in V.items()}, indent=2))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "detail"}
                  for k, v in per_conv.items() if "condA" not in k}, indent=2))

import os
outdir = "shared_agora/artifacts"
os.makedirs(outdir, exist_ok=True)
with open(os.path.join(outdir, "qwen_emp260_convention_sweep.json"), "w") as f:
    json.dump(out, f, indent=2)

# ---- figure: per-channel rho_fixed vs maxRR, 3 conventions, W=1024 ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
for ax, conv in zip(axes, CONVS):
    d = per_conv[f"{conv}_W1024"]["detail"]
    xs = [r["maxRR"] for r in d]
    ys = [r["rho_fixed"] if r["rho_fixed"] is not None else np.nan for r in d]
    ax.scatter(xs, ys, c=["crimson" if (y is not None and y > 0) else "navy" for y in ys], s=42, zorder=3)
    ax.axhline(0, color="k", lw=0.8); ax.axvline(0.90, color="gray", ls="--", lw=0.8)
    yy = [r["rho_matched"] for r in d if r["rho_matched"] is not None]
    ax.set_title(f"{conv}, eps=0.3, W=1024\nP(rho>0|sat)={per_conv[f'{conv}_W1024']['P_pos_given_sat']}, dose={per_conv[f'{conv}_W1024']['dose_maxRR_rho_fixed']}")
    ax.set_xlabel("maxRR (fixed eps)"); ax.set_ylabel("rho(ENT, band)")
    ax.set_ylim(-1.15, 1.15); ax.grid(alpha=0.3)
mirror_counts = "/".join(str(per_conv[cv + "_W1024"]["n_matched_rho_neg"]) for cv in CONVS)
fig.suptitle("qwen_2_5_coder independent convention sweep: EMP-253 sufficiency vs EMP-260 refutation "
             f"(matched-RR mirror negatives: {mirror_counts}/14 for RAW1/PERBAND/NONE)")
fig.tight_layout()
fig.savefig(os.path.join(outdir, "qwen_emp260_convention_sweep.png"), dpi=130)
print("saved artifacts:", os.path.join(outdir, "qwen_emp260_convention_sweep.json"),
      os.path.join(outdir, "qwen_emp260_convention_sweep.png"))
