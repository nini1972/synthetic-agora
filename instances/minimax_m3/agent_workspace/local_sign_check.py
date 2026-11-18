"""
FAST LOCAL SIGN-CHECK:  which sign is rho(freq, ENT)?

Goal
----
Reproduce the EXACT condition used in EMP-191 (Condition C, RR-matched via adaptive
epsilon, neural_eeg 14 channels, fs=128, Takens m=3, tau=2) AND ask:

    1.  rho(freq, ENT)                -- the quantity everyone quotes
    2.  rho(ENT_diag, ENT_vert)        -- a POSSIBLE interpretation of SYN-062's
                                         "rho(ent_diag/ent_vert) stays positive"
    3.  rho(freq, ENT_diag)            -- diagonal-line-length entropy only
    4.  rho(freq, ENT_vert)            -- vertical-line-length entropy only
    5.  rho(freq, DET) / rho(freq, LAM)
    6.  per-band means with stderr

Output a JSON + a 1-page plot to local_sign_check/
"""
import json
from pathlib import Path
import warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

warnings.filterwarnings('ignore')

OUT = Path("local_sign_check")
OUT.mkdir(exist_ok=True)
SEGLEN = 1024
L = 4096
BANDS = [
    ("delta", 1.0, 3.0, 2.0),
    ("theta", 4.0, 7.0, 5.5),
    ("alpha", 8.0, 12.0, 10.0),
    ("beta", 13.0, 30.0, 21.5),
    ("gamma", 31.0, 44.0, 37.5),
]
CENTERS = np.array([b[3] for b in BANDS])
BAND_NAMES = [b[0] for b in BANDS]
FS = 128.0
M_EMB = 3
TAU_EMB = 2
N_PTS = 384
RR_TARGET = 0.05
EPS_MODES = ("adaptive", "fixed_q10", "pct5")
EEG_CH = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2", "P8",
          "T8", "FC6", "F4", "F8", "AF4"]


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


def _eps_from_D(D, mode, RR_TARGET=RR_TARGET):
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


def rqa_metrics(x, eps_mode):
    """Return ENT (combined, in normalised units), ENT_diag, ENT_vert, DET, LAM, RR."""
    E = takens(x)
    if E is None:
        return None
    if E.shape[0] > N_PTS:
        idx = np.linspace(0, E.shape[0] - 1, N_PTS).astype(int)
        E = E[idx]
    D = cdist(E, E)
    eps = _eps_from_D(D, eps_mode)
    R = (D <= eps).astype(np.int8)
    n = R.shape[0]
    rr = float(R.mean())

    diag_lens, vert_lens = [], []
    for off in range(n):
        diag_lens.append(_runs(np.diagonal(R, offset=off), 2))
    for j in range(n):
        vert_lens.append(_runs(R[:, j], 2))
    diag_lens = np.concatenate(diag_lens) if diag_lens else np.empty(0)
    vert_lens = np.concatenate(vert_lens) if vert_lens else np.empty(0)
    # trim out trivial 1-long runs already filtered
    diag_lens = diag_lens[diag_lens >= 2]
    vert_lens = vert_lens[vert_lens >= 2]

    det = float(diag_lens.sum() / (rr * n)) if rr > 0 and diag_lens.size else 0.0
    lam = float(vert_lens.sum() / (rr * n)) if rr > 0 and vert_lens.size else 0.0
    if diag_lens.size:
        p = diag_lens.astype(np.float64) / diag_lens.sum()
        ent_diag = float(-(p * np.log(p)).sum() / np.log(n))
    else:
        ent_diag = 0.0
    if vert_lens.size:
        p = vert_lens.astype(np.float64) / vert_lens.sum()
        ent_vert = float(-(p * np.log(p)).sum() / np.log(n))
    else:
        ent_vert = 0.0
    # combined ENT = entropy of diag+vert pooled (this matches colony_lib RQA convention)
    pooled = np.concatenate((diag_lens, vert_lens))
    if pooled.size:
        p = pooled.astype(np.float64) / pooled.sum()
        ent_combined = float(-(p * np.log(p)).sum() / np.log(n))
    else:
        ent_combined = 0.0
    return dict(RR=rr, DET=det, LAM=lam,
                ENT=ent_combined, ENT_diag=ent_diag, ENT_vert=ent_vert,
                eps=float(eps))


def bandpass(x, lo, hi, fs=FS, order=4):
    nyq = fs / 2.0
    sos = butter(order, [max(lo / nyq, 1e-4), min(hi / nyq, 0.999)], btype='band', output='sos')
    y = sosfiltfilt(sos, x)
    s = np.std(y)
    return (y - np.mean(y)) / s if s > 0 else y


# ------------------------------------------------------------- evaluation ---
def eval_signal(series_dict, eps_mode):
    recs = []
    for ch, x in series_dict.items():
        for w in range(len(x) // SEGLEN):
            seg = x[w * SEGLEN:(w + 1) * SEGLEN]
            vals = [rqa_metrics(bandpass(seg, lo, hi), eps_mode)
                    for (_, lo, hi, _) in BANDS]
            if any(v is None for v in vals):
                continue
            recs.append({"channel": ch, "window": w,
                         **{k: [v[k] for v in vals] for k in
                            ("RR", "DET", "LAM", "ENT", "ENT_diag", "ENT_vert")}})
    return recs


def rhos(records, key, freq=CENTERS):
    rs = []
    for rec in records:
        v = rec[key]
        if np.std(v) < 1e-12:
            continue
        rho, _ = spearmanr(freq, v)
        if not np.isnan(rho):
            rs.append(rho)
    rs = np.array(rs)
    return dict(mean=float(rs.mean()), se=float(rs.std(ddof=1) / np.sqrt(rs.size)),
                median=float(np.median(rs)), n=int(rs.size),
                frac_pos=float(np.mean(rs > 0)), frac_neg=float(np.mean(rs < 0))) if rs.size \
        else dict(mean=float('nan'), se=float('nan'), median=float('nan'), n=0,
                  frac_pos=float('nan'), frac_neg=float('nan'))


# ------------------------------------------------------------------ main ----
def main():
    import sys
    sys.path.insert(0, ".")
    from colony_lib.datasets import load_dataset
    ds = load_dataset("neural_eeg")
    eeg = {ch: np.asarray(ds[ch])[:L].astype(np.float64) for ch in EEG_CH}

    out = {}
    for eps_mode in EPS_MODES:
        recs = eval_signal(eeg, eps_mode)
        block = {key: rhos(recs, key) for key in
                 ("RR", "DET", "LAM", "ENT", "ENT_diag", "ENT_vert")}
        # special: correlation of ENT_diag with ENT_vert (within-pipeline) -
        # this matches a possible interpretation of SYN-062's notation
        within = []
        for rec in recs:
            ed, ev = np.array(rec["ENT_diag"]), np.array(rec["ENT_vert"])
            if np.std(ed) < 1e-12 or np.std(ev) < 1e-12:
                continue
            r, _ = spearmanr(ed, ev)
            if not np.isnan(r):
                within.append(r)
        within = np.array(within)
        block["ENT_diag_vs_ENT_vert_within"] = dict(
            mean=float(within.mean()), se=float(within.std(ddof=1) / np.sqrt(within.size)),
            n=int(within.size))
        # per-band means with stderr
        per_band = {}
        for key in ("RR", "ENT", "ENT_diag", "ENT_vert", "DET", "LAM"):
            arr = np.array([r[key] for r in recs])
            per_band[key] = dict(
                means=[float(np.mean(arr[:, i])) for i in range(len(BANDS))],
                ses=[float(np.std(arr[:, i], ddof=1) / np.sqrt(arr.shape[0]))
                     for i in range(len(BANDS))])
        block["per_band"] = per_band
        out[eps_mode] = block

        print(f"\n== eps = {eps_mode} ==")
        print(f"  n recs: {len(recs)}")
        print(f"  ENT per band:      " + "  ".join(f"{b}={per_band['ENT']['means'][i]:.3f}+-{per_band['ENT']['ses'][i]:.3f}"
                                                     for i, b in enumerate(BAND_NAMES)))
        print(f"  ENT_diag per band: " + "  ".join(f"{b}={per_band['ENT_diag']['means'][i]:.3f}"
                                                     for i, b in enumerate(BAND_NAMES)))
        print(f"  ENT_vert per band: " + "  ".join(f"{b}={per_band['ENT_vert']['means'][i]:.3f}"
                                                     for i, b in enumerate(BAND_NAMES)))
        print(f"  rho(freq, ENT)              = {block['ENT']['mean']:+.3f}+-{block['ENT']['se']:.3f}  "
              f"frac_neg={block['ENT']['frac_neg']:.2f}")
        print(f"  rho(freq, ENT_diag)         = {block['ENT_diag']['mean']:+.3f}+-{block['ENT_diag']['se']:.3f}  "
              f"frac_neg={block['ENT_diag']['frac_neg']:.2f}")
        print(f"  rho(freq, ENT_vert)         = {block['ENT_vert']['mean']:+.3f}+-{block['ENT_vert']['se']:.3f}  "
              f"frac_neg={block['ENT_vert']['frac_neg']:.2f}")
        print(f"  rho(ENT_diag, ENT_vert) [WITHIN] = {block['ENT_diag_vs_ENT_vert_within']['mean']:+.3f}")
        print(f"  rho(freq, DET)              = {block['DET']['mean']:+.3f}")
        print(f"  rho(freq, LAM)              = {block['LAM']['mean']:+.3f}")
        print(f"  rho(freq, RR)               = {block['RR']['mean']:+.3f}")

    with open(OUT / "local_sign_check.json", "w") as f:
        json.dump(out, f, indent=2)

    # ------- figure -------
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, eps_mode in zip(axes, EPS_MODES):
        for key, c in [("ENT", "crimson"), ("ENT_diag", "darkorange"),
                       ("ENT_vert", "steelblue"), ("DET", "darkgreen")]:
            pb = out[eps_mode]["per_band"][key]
            m = pb["means"]; s = pb["ses"]
            ax.errorbar(CENTERS, m, yerr=s, marker='o', capsize=3, label=key,
                        lw=1.8, ms=6)
        ax.set_xscale('log'); ax.set_xticks(CENTERS); ax.set_xticklabels(BAND_NAMES)
        ax.set_xlabel("band centre freq (Hz)"); ax.set_ylabel("RQA metric")
        ax.set_title(f"eps = {eps_mode}")
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("LOCAL SIGN CHECK: ENT / ENT_diag / ENT_vert / DET vs band frequency (neural_eeg, fs=128, RR-matched)", fontsize=12)
    plt.tight_layout()
    plt.savefig(OUT / "local_sign_check.png", dpi=120)
    plt.close()
    print("\nJSON:", OUT / "local_sign_check.json")
    print("FIG :", OUT / "local_sign_check.png")


if __name__ == "__main__":
    main()
