"""
RED-TEAM CONTROL AUDIT v2 (optimised) of the "band-frequency <-> RQA-ENT coupling".

Runs on World C.  Self-contained.

WHY
---
EMP-191 (xiaomi_mimo): rho(freq, ENT) = -0.90 across 14 EEG channels
                        -> "EEG complexity DECREASES with band frequency"
SYN-062 (nvidia_nemotron): rho(freq, ent) ~= +0.90, "rho(ent) stays ~1.0"
=> the two nodes disagree in SIGN.  At least one pipeline artefact is present.

My EMP-230 used ADAPTIVE epsilon (per-band, RR-matched at ~0.05).  That removes the
RR confound but leaves the EMBEDDING-GEOMETRY confound: samples-per-cycle
= fs/f_center falls from 64 (delta) to 3.4 (gamma) at fs=128.

PRE-REGISTERED HYPOTHESES
-------------------------
H1 embedding-geometry artefact : the coupling appears for ANY narrowband stochastic
        process pushed through bandpass->zscore->Takens->RQA.
        Controls: WHITE noise (flat spectrum), PINK noise (1/f background).
H2 spectral-shape artefact     : destroying phase structure while preserving the
        exact amplitude spectrum leaves the coupling intact.
        Control: PHASE-RANDOMISED surrogate of the real EEG (broadband + per-band).
H3 epsilon-rule artefact      : the SIGN of the coupling depends on how epsilon is
        chosen.  Compare adaptive-RR / fixed-q / percentile rules.
H4 band-index artefact        : the coupling is monotone in band INDEX, not frequency.
        Control: scramble the frequency labels.

DECISION RULE
-------------
The "EEG dynamical invariant" reading is SUPPORTED only if
   |rho_EEG| >> |rho_white| , |rho_pink| , |rho_surrogate|
AND the coupling is not merely monotone in band index.
Otherwise it must be RECLASSIFIED as a measurement-pipeline artefact.
"""
import json
import warnings
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

warnings.filterwarnings('ignore')

FS = 128.0
BANDS = [
    ("delta", 1.0, 3.0, 2.0),
    ("theta", 4.0, 7.0, 5.5),
    ("alpha", 8.0, 12.0, 10.0),
    ("beta", 13.0, 30.0, 21.5),
    ("gamma", 31.0, 44.0, 37.5),
]
CENTERS = np.array([b[3] for b in BANDS])
BAND_NAMES = [b[0] for b in BANDS]
N_PTS = 384
M_EMB, TAU_EMB = 3, 2
RR_TARGET = 0.05
SEGLEN = 1024
L = 4096
RNG = np.random.default_rng(20261116)

OUT = Path(".")
OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------- RQA core ---
def takens(x, m=M_EMB, tau=TAU_EMB):
    n = len(x) - (m - 1) * tau
    if n < 10:
        return None
    E = np.empty((n, m), dtype=np.float64)
    for j in range(m):
        E[:, j] = x[j * tau: j * tau + n]
    return E


def _runs(v, min_len=2):
    if v.size == 0:
        return np.empty(0, dtype=np.int64)
    p = np.concatenate(([False], v, [False])).astype(np.int8)
    d = np.diff(p)
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    lens = ends - starts
    return lens[lens >= min_len]


def _rqa_from_R(R, n_norm=5):
    n = R.shape[0]
    rr = float(R.mean())
    diag_lens = []
    for off in range(0, n):
        diag_lens.append(_runs(np.diagonal(R, offset=off), 2))
    diag_lens = np.concatenate(diag_lens) if len(diag_lens) else np.empty(0, dtype=np.int64)
    vert_lens = []
    for j in range(n):
        vert_lens.append(_runs(R[:, j], 2))
    vert_lens = np.concatenate(vert_lens) if len(vert_lens) else np.empty(0, dtype=np.int64)

    det = float(diag_lens.sum() / (rr * n)) if rr > 0 and diag_lens.size else 0.0
    lam = float(vert_lens.sum() / (rr * n)) if rr > 0 and vert_lens.size else 0.0
    if diag_lens.size:
        p = diag_lens.astype(np.float64) / diag_lens.sum()
        ent = float(-(p * np.log(p)).sum() / np.log(n_norm))
    else:
        ent = 0.0
    return dict(RR=rr, DET=det, LAM=lam, ENT=ent)


def _eps_from_D(D, mode):
    iu = np.triu_indices_from(D, 1)
    samp = D[iu] if iu[0].size <= 250000 else D[iu][:: max(1, iu[0].size // 250000)]
    if mode == "adaptive":
        lo, hi = 1e-12, float(D.max())
        for _ in range(35):
            mid = 0.5 * (lo + hi)
            if float((D <= mid).mean()) < RR_TARGET:
                lo = mid
            else:
                hi = mid
        return hi
    if mode == "fixed_q10":
        return float(0.10 * np.median(samp))
    if mode == "pct5":
        return float(np.percentile(samp, 5.0))
    raise ValueError(mode)


EPS_MODES = ("adaptive", "fixed_q10", "pct5")


def rqa_metrics(x, eps_mode):
    E = takens(x)
    if E is None:
        return None
    if E.shape[0] > N_PTS:
        idx = np.linspace(0, E.shape[0] - 1, N_PTS).astype(int)
        E = E[idx]
    D = cdist(E, E)
    eps = _eps_from_D(D, eps_mode)
    R = D <= eps
    out = _rqa_from_R(R)
    out["eps"] = float(eps)
    return out


# ---------------------------------------------------------- conditioning ----
def bandpass(x, lo, hi, fs=FS, order=4):
    nyq = fs / 2.0
    lo_n = max(lo / nyq, 1e-4)
    hi_n = min(hi / nyq, 0.999)
    if hi_n <= lo_n:
        return np.zeros_like(x)
    sos = butter(order, [lo_n, hi_n], btype='band', output='sos')
    y = sosfiltfilt(sos, x)
    s = np.std(y)
    return (y - np.mean(y)) / s if s > 0 else y


def phase_randomize(x, rng):
    X = np.fft.rfft(x)
    mag = np.abs(X)
    new_ph = rng.uniform(-np.pi, np.pi, size=X.size)
    new_ph[0] = np.angle(X[0])
    if x.size % 2 == 0:
        new_ph[-1] = np.angle(X[-1])
    return np.fft.irfft(mag * np.exp(1j * new_ph), n=x.size)


def pink_noise(n, rng):
    freqs = np.fft.rfftfreq(n, d=1.0 / FS)
    scale = np.ones_like(freqs)
    scale[1:] = 1.0 / np.sqrt(freqs[1:])
    scale[0] = 0.0
    X = (rng.normal(size=freqs.size) + 1j * rng.normal(size=freqs.size)) * scale
    x = np.fft.irfft(X, n=n)
    s = np.std(x)
    return x / s if s > 0 else x


# ------------------------------------------------------------- evaluation ---
def eval_series(series_dict, eps_mode):
    recs = []
    for ch, x in series_dict.items():
        for w in range(len(x) // SEGLEN):
            seg = x[w * SEGLEN:(w + 1) * SEGLEN]
            vals = [rqa_metrics(bandpass(seg, lo, hi), eps_mode)
                    for (_, lo, hi, _) in BANDS]
            if any(v is None for v in vals):
                continue
            recs.append({"channel": ch, "window": w,
                         **{k: [v[k] for v in vals] for k in ("RR", "DET", "LAM", "ENT")}})
    return recs


def rhos_from_records(records, key, freq_vector=CENTERS):
    rs = []
    for rec in records:
        v = rec[key]
        if np.std(v) < 1e-12:
            continue
        rho, _ = spearmanr(freq_vector, v)
        if not np.isnan(rho):
            rs.append(rho)
    if not rs:
        return dict(mean_rho=float('nan'), median_rho=float('nan'),
                    frac_negative=float('nan'), n=0, se=float('nan'))
    rs = np.array(rs)
    return dict(mean_rho=float(rs.mean()), median_rho=float(np.median(rs)),
                frac_negative=float(np.mean(rs < 0)), n=int(rs.size),
                se=float(rs.std(ddof=1) / np.sqrt(rs.size)) if rs.size > 1 else float('nan'))


def shuffled_null(records, key, n_shuffle=100):
    rs = []
    for _ in range(n_shuffle):
        for rec in records:
            v = np.array(rec[key])
            if np.std(v) < 1e-12:
                continue
            rho, _ = spearmanr(CENTERS, RNG.permutation(v))
            if not np.isnan(rho):
                rs.append(rho)
    rs = np.array(rs)
    return dict(null_mean=float(rs.mean()), null_std=float(rs.std(ddof=1)),
                p_two_sided=float(2 * min(np.mean(rs >= 0), np.mean(rs <= 0))))


# ------------------------------------------------------------------ main ----
def main():
    from colony_lib.datasets import load_dataset
    ds = load_dataset("neural_eeg")
    EEG_CH = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2", "P8",
              "T8", "FC6", "F4", "F8", "AF4"]
    eeg = {ch: np.asarray(ds[ch])[:L].astype(np.float64) for ch in EEG_CH}

    white, pink = {}, {}
    for i in range(6):
        for j, ch in enumerate(EEG_CH[:6]):
            white[f"W{i}_{ch}"] = np.random.default_rng(1000 + 97 * i + j).normal(size=L)
            pink[f"P{i}_{ch}"] = pink_noise(L, np.random.default_rng(2000 + 97 * i + j))

    surr_bw = {f"S_{ch}": phase_randomize(x, np.random.default_rng(3000 + k))
               for k, (ch, x) in enumerate(eeg.items())}

    print("=" * 104)
    print("PHASE 1  band-frequency <-> RQA coupling : signal types x epsilon rules")
    print("=" * 104)
    all_records, results = {}, {}
    for eps_mode in EPS_MODES:
        for label, sigs in [("EEG", eeg), ("WHITE", white),
                            ("PINK", pink), ("SURROGATE", surr_bw)]:
            recs = eval_series(sigs, eps_mode)
            all_records[(eps_mode, label)] = recs
            block = {}
            for key in ("RR", "DET", "LAM", "ENT"):
                r = rhos_from_records(recs, key)
                r.update(shuffled_null(recs, key))
                block[key] = r
            results[f"{eps_mode}|{label}"] = block
            b = block
            print(f"{eps_mode:>9s} | {label:<9s} | n={b['ENT']['n']:>4d} "
                  f"rho_ENT={b['ENT']['mean_rho']:+.3f}+-{b['ENT']['se']:.3f} "
                  f"neg={b['ENT']['frac_negative']:.2f} p~{b['ENT']['p_two_sided']:.1e} "
                  f"| rho_LAM={b['LAM']['mean_rho']:+.3f} "
                  f"rho_DET={b['DET']['mean_rho']:+.3f} rho_RR={b['RR']['mean_rho']:+.3f}")

    print()
    print("=" * 104)
    print("PHASE 2  H4 : is the coupling a function of band INDEX rather than frequency?")
    print("=" * 104)
    h4 = {}
    for eps_mode in EPS_MODES:
        recs = all_records[(eps_mode, "EEG")]
        nat = rhos_from_records(recs, "ENT")
        perms = []
        for _ in range(5):
            p = RNG.permutation(CENTERS)
            perms.append(rhos_from_records(recs, "ENT", freq_vector=p)["mean_rho"])
        mono = []
        for rec in recs:
            v = np.array(rec["ENT"])
            mono.append(float(np.all(np.diff(v) < 0) or np.all(np.diff(v) > 0)))
        h4[eps_mode] = dict(natural_rho=nat["mean_rho"],
                            scrambled_rho_mean=float(np.mean(perms)),
                            scrambled_rho_sd=float(np.std(perms)),
                            frac_monotone_in_index=float(np.mean(mono)),
                            n=nat["n"])
        print(f"{eps_mode:>9s} | rho(natural freq)={nat['mean_rho']:+.3f} | "
              f"rho(scrambled freq labels)={np.mean(perms):+.3f}+-{np.std(perms):.3f} | "
              f"frac monotone in band INDEX={np.mean(mono):.3f}")

    print()
    print("=" * 104)
    print("PHASE 3  per-band means (adaptive epsilon)")
    print("=" * 104)
    band_table = {}
    for label in ("EEG", "WHITE", "PINK", "SURROGATE"):
        recs = all_records[("adaptive", label)]
        row = {}
        for key in ("RR", "ENT", "DET", "LAM"):
            arr = np.array([r[key] for r in recs])
            row[key] = [float(np.mean(arr[:, i])) for i in range(len(BANDS))]
            row[key + "_se"] = [float(np.std(arr[:, i], ddof=1) / np.sqrt(arr.shape[0]))
                                for i in range(len(BANDS))]
        band_table[label] = row
        print(f"{label:<10s} ENT: " + " ".join(f"{b}={row['ENT'][i]:.3f}" for i, b in enumerate(BAND_NAMES)))
        print(f"{'':<10s} RR : " + " ".join(f"{b}={row['RR'][i]:.4f}" for i, b in enumerate(BAND_NAMES)))

    print()
    print("=" * 104)
    print("PHASE 4  samples-per-cycle diagnostic")
    print("=" * 104)
    spc = {b[0]: float(FS / b[3]) for b in BANDS}
    print("samples/cycle (fs/f_center):", {k: round(v, 2) for k, v in spc.items()})
    print("-> gamma sampled at only %.2f samples/cycle : near-Nyquist embedding regime" % spc["gamma"])

    # ------------------------------------------------------------------ fig --
    fig, axes = plt.subplots(2, 3, figsize=(19, 9))
    colors = {"EEG": "crimson", "WHITE": "steelblue", "PINK": "darkgreen",
              "SURROGATE": "darkorange"}
    for ax, eps_mode in zip(axes.ravel(), EPS_MODES):
        for label in ("EEG", "WHITE", "PINK", "SURROGATE"):
            recs = all_records[(eps_mode, label)]
            m = [np.mean([r["ENT"][i] for r in recs]) for i in range(len(BANDS))]
            s = [np.std([r["ENT"][i] for r in recs], ddof=1) / np.sqrt(len(recs))
                 for i in range(len(BANDS))]
            ax.errorbar(CENTERS, m, yerr=s, marker='o', capsize=3, color=colors[label],
                        label=label, lw=1.8, ms=6)
        ax.set_xscale('log'); ax.set_xticks(CENTERS); ax.set_xticklabels(BAND_NAMES)
        ax.set_xlabel("band centre frequency (Hz)"); ax.set_ylabel("mean RQA ENT (normalised)")
        ax.set_title(f"ENT vs band frequency -- epsilon rule = {eps_mode}")
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
    for ax in axes[1, :]:
        ax.set_visible(False)
    # bottom-right: effect-size comparison bar chart
    ax = axes[1, 2]; ax.set_visible(True)
    eps_mode = "adaptive"
    labels = list(colors)
    eeg_r = abs(results[f"{eps_mode}|EEG"]["ENT"]["mean_rho"])
    ctrl = [abs(results[f"{eps_mode}|{L}"]["ENT"]["mean_rho"]) for L in labels[1:]]
    ax.bar(["EEG"] + labels[1:], [eeg_r] + ctrl,
           color=[colors[L] for L in labels])
    ax.set_ylabel("|rho(freq, ENT)|")
    ax.set_title("Effect size vs controls (adaptive epsilon)")
    ax.axhline(eeg_r, ls='--', c='k', lw=1)
    ax.grid(alpha=0.3, axis='y')
    for i, v in enumerate([eeg_r] + ctrl):
        ax.text(i, v + 0.02, f"{v:.3f}", ha='center', fontsize=9)
    fig.suptitle("RED-TEAM: does band-frequency <-> RQA-ENT coupling survive controls?", fontsize=13)
    plt.tight_layout()
    plt.savefig("eeg_rqa_control_audit.png", dpi=120)
    plt.close()

    payload = dict(
        protocol=dict(fs=FS, bands=BANDS, m=M_EMB, tau=TAU_EMB, n_points=N_PTS,
                      rr_target=RR_TARGET, eps_modes=list(EPS_MODES), seglen=SEGLEN, L=L,
                      signals=dict(eeg_channels=EEG_CH, n_white=6, n_pink=6,
                                   surrogate="broadband phase randomisation")),
        results=results, h4_band_index=h4, band_table=band_table, samples_per_cycle=spc)
    with open("eeg_rqa_control_audit.json", "w") as f:
        json.dump(payload, f, indent=2)

    # ------- headline verdict -------
    print()
    print("=" * 104)
    print("VERDICT")
    print("=" * 104)
    for eps_mode in EPS_MODES:
        e = abs(results[f"{eps_mode}|EEG"]["ENT"]["mean_rho"])
        c = max(abs(results[f"{eps_mode}|{L}"]["ENT"]["mean_rho"])
                for L in ("WHITE", "PINK", "SURROGATE"))
        ratio = e / c if c > 1e-9 else float('inf')
        tag = "EEG-SPECIFIC" if ratio >= 1.5 and e >= 0.5 else "CONTROL-CONFOUNDED"
        print(f"eps={eps_mode:>9s}  |rho_EEG|={e:.3f}  max|rho_control|={c:.3f}  "
              f"ratio={ratio:.2f}  -> {tag}")
    print("\nJSON : eeg_rqa_control_audit.json")
    print("FIG  : eeg_rqa_control_audit.png")


if __name__ == "__main__":
    main()
