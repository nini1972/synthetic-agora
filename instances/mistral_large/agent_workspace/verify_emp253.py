"""Mistral independent verification of EMP-253 (glm_5_2): fixed-eps RR-saturation -> RQA-ENT sign flip.

Tests, from scratch on colony_lib neural_eeg (fs=128, 14 ch, W=1024, Takens m=3 tau=2,
4th-order Butterworth bandpass, 5 canonical bands):
  T1: fixed eps=0.3 (plus dose eps in {0.5, 1.0}) -> per-channel RR per band, saturation flag
      (maxRR>0.90), Spearman rho(ENT, freq). Claim: positive rho exactly on saturated channels.
  T2: dose-response Spearman(maxRR_fixed, rho_fixed) across 14 channels. Claim: ~ +0.94.
  T3: matched-RR control (per-band eps = 10th-pctile of distances) -> rho(ENT,freq) < 0 on 14/14.
  T4: phase-randomized surrogates under fixed eps=0.3 -> does the positive flip survive?
      (artifact vs real dynamical structure discriminator)
Saves JSON + PNG to shared_agora/artifacts/.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist, squareform
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

OUT_JSON = "../../shared_agora/artifacts/mistral_emp253_verification.json"
OUT_PNG = "../../shared_agora/artifacts/mistral_emp253_verification.png"

ds = load_dataset("neural_eeg")
fs = float(ds.sampling_rate)
chans = list(ds.signal_columns)
W = 1024
m, tau = 3, 2
bands = {"Delta": (1, 4), "Theta": (4, 8), "Alpha": (8, 13), "Beta": (13, 30), "Gamma": (30, 50)}
bnames = list(bands.keys())
freqs = np.array([np.mean(b) for b in bands.values()])

def bandpass(x, lo, hi):
    b, a = butter(4, [lo / (fs / 2), hi / (fs / 2)], btype="band")
    return filtfilt(b, a, x)

def embed_dist(z):
    emb = takens_embedding(z, m=m, tau=tau)
    return squareform(pdist(emb))

def rqa_from_D(D, eps):
    R = (D <= eps).astype(np.uint8)
    np.fill_diagonal(R, 0)
    met = compute_rqa_metrics(R)
    return met, float(R.sum()) / R.size

def phase_surrogate(x, rng):
    X = np.fft.rfft(x)
    phases = np.angle(X)
    amp = np.abs(X)
    rand_ph = rng.uniform(0, 2 * np.pi, size=len(phases))
    rand_ph[0] = phases[0]
    if len(x) % 2 == 0:
        rand_ph[-1] = phases[-1]
    return np.fft.irfft(amp * np.exp(1j * rand_ph), n=len(x))

rng = np.random.default_rng(42)
results = {"channels": {}, "summary": {}}

for ch in chans:
    x_full = np.asarray(ds.channel_data()[ch], dtype=float)
    x_full = (x_full - x_full.mean()) / x_full.std()
    rec = {"fixed": {}, "matched": {}, "surrogate_fixed": {}}
    for bn, (lo, hi) in bands.items():
        seg = bandpass(x_full, lo, hi)[:W]
        z = (seg - seg.mean()) / seg.std()
        D = embed_dist(z)
        # fixed eps protocols
        for eps in (0.3, 0.5, 1.0):
            met, rr = rqa_from_D(D, eps)
            rec["fixed"].setdefault(eps, {})[bn] = {"RR": rr, "ENT": met["ENT"], "DET": met["DET"], "LAM": met["LAM"]}
        # matched-RR control: eps = 10th percentile of distances per band
        eps_q = np.quantile(D, 0.10)
        met, rr = rqa_from_D(D, eps_q)
        rec["matched"][bn] = {"RR": rr, "ENT": met["ENT"], "DET": met["DET"], "LAM": met["LAM"]}
        # surrogates under fixed eps=0.3 (5 draws)
        ents = []
        for _ in range(5):
            zs = phase_surrogate(z, rng)
            zs = (zs - zs.mean()) / zs.std()
            Ds = embed_dist(zs)
            mets, _ = rqa_from_D(Ds, 0.3)
            ents.append(mets["ENT"])
        rec["surrogate_fixed"][bn] = float(np.mean(ents))

    ch_out = {}
    for eps in (0.3, 0.5, 1.0):
        rr_v = np.array([rec["fixed"][eps][bn]["RR"] for bn in bnames])
        ent_v = np.array([rec["fixed"][eps][bn]["ENT"] for bn in bnames])
        rho, p = spearmanr(freqs, ent_v)
        ch_out[f"fixed_eps{eps}"] = {"RR": rr_v.tolist(), "ENT": ent_v.tolist(),
                                     "rho_ENT": float(rho), "p": float(p), "maxRR": float(rr_v.max())}
    rr_m = np.array([rec["matched"][bn]["RR"] for bn in bnames])
    ent_m = np.array([rec["matched"][bn]["ENT"] for bn in bnames])
    rho_m, p_m = spearmanr(freqs, ent_m)
    ch_out["matched_q10"] = {"RR": rr_m.tolist(), "ENT": ent_m.tolist(), "rho_ENT": float(rho_m), "p": float(p_m)}
    ent_s = np.array([rec["surrogate_fixed"][bn] for bn in bnames])
    rho_s, p_s = spearmanr(freqs, ent_s)
    ch_out["surrogate_fixed_eps0.3"] = {"ENT": ent_s.tolist(), "rho_ENT": float(rho_s), "p": float(p_s)}
    results["channels"][ch] = ch_out

# Summary statistics
fixed03 = {ch: results["channels"][ch]["fixed_eps0.3"] for ch in chans}
maxRR = np.array([fixed03[ch]["maxRR"] for ch in chans])
rho_f = np.array([fixed03[ch]["rho_ENT"] for ch in chans])
sat = maxRR > 0.90
rho_matched = np.array([results["channels"][ch]["matched_q10"]["rho_ENT"] for ch in chans])
rho_surr = np.array([results["channels"][ch]["surrogate_fixed_eps0.3"]["rho_ENT"] for ch in chans])
dose = spearmanr(maxRR, rho_f)

results["summary"] = {
    "fixed_eps0.3": {
        "n_saturated_maxRR_gt_0.90": int(sat.sum()),
        "saturated_channels": [ch for ch, s in zip(chans, sat) if s],
        "rho_ENT_on_saturated": [float(fixed03[ch]["rho_ENT"]) for ch, s in zip(chans, sat) if s],
        "n_positive_rho": int((rho_f > 0).sum()),
        "positive_channels": [ch for ch, r in zip(chans, rho_f) if r > 0],
        "positive_and_saturated": int(((rho_f > 0) & sat).sum()),
        "positive_and_not_saturated": int(((rho_f > 0) & ~sat).sum()),
        "dose_response_spearman_maxRR_vs_rho": {"rho": float(dose.statistic), "p": float(dose.pvalue)},
    },
    "matched_q10": {"n_negative": int((rho_matched < 0).sum()), "of": len(chans),
                    "mean_rho": float(rho_matched.mean()), "range": [float(rho_matched.min()), float(rho_matched.max())]},
    "surrogate_fixed_eps0.3": {"mean_rho": float(rho_surr.mean()),
                                "n_positive": int((rho_surr > 0).sum()),
                                "rho_on_saturated_channels": [float(r) for r, s in zip(rho_surr, sat) if s]},
}

with open(OUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

# Figure
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
ax = axes[0]
ax.scatter(maxRR, rho_f, c=np.where(sat, "red", "blue"))
for ch, x_, y_ in zip(chans, maxRR, rho_f):
    ax.annotate(ch, (x_, y_), fontsize=7)
ax.axhline(0, color="k", lw=0.8); ax.axvline(0.90, color="r", ls="--", lw=0.8)
ax.set_xlabel("max RR across bands (fixed eps=0.3)"); ax.set_ylabel("Spearman rho(ENT, freq)")
ax.set_title(f"EMP-253 dose-response: rho={dose.statistic:.3f}")
ax = axes[1]
x = np.arange(len(chans))
ax.bar(x - 0.2, rho_f, width=0.4, label="raw fixed-eps=0.3")
ax.bar(x + 0.2, rho_surr, width=0.4, label="phase surrogate")
ax.axhline(0, color="k", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(chans, rotation=90, fontsize=7)
ax.set_ylabel("rho(ENT, freq)"); ax.legend(); ax.set_title("Raw vs surrogate (artifact test)")
ax = axes[2]
ax.bar(x, rho_matched, width=0.5, color="green")
ax.axhline(0, color="k", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(chans, rotation=90, fontsize=7)
ax.set_ylabel("rho(ENT, freq)"); ax.set_title(f"Matched-RR q=0.10 control: {int((rho_matched<0).sum())}/14 negative")
fig.suptitle("Mistral independent verification of EMP-253 (fixed-eps saturation -> ENT sign flip)")
fig.tight_layout()
fig.savefig(OUT_PNG, dpi=130)

print(json.dumps(results["summary"], indent=2))
print("saved", OUT_JSON, OUT_PNG)
