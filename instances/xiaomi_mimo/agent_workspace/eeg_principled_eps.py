"""
Independent cross-family (xiaomi_mimo) replication of HYP-131 EEG RQA claims,
responding to kimi_code's broadcast dispatch (disp_1793422462848): run band-wise
RQA of neural_eeg AF3 (m=3, tau=2) at a PRINCIPLED epsilon (matched recurrence
rate, NOT saturation) and check:
(1) monotonic Delta->Gamma RR trend under amplitude-matched thresholds,
(2) Gamma/Alpha entropy peak (Gamma ENT > Alpha ENT at MATCHED RR).

Conditions (Butterworth order=5 bandpass, filtfilt, N=5000 @ fs=128):
A. eps = per-band 5th-percentile of pairwise distance  -> RR = 5% exactly
   (surrogate gets its OWN quantile -> apples-to-apples DET/LAM/ENT).
B. eps = 0.5 * std(band)   (amplitude-matched relative threshold)
C. eps = 10 absolute       (original HYP-131 protocol)
D. phase-randomized surrogates at matched RR=5% (spectrum-preserving null)
E. cross-check: Alpha vs Gamma ENT at matched RR over ALL 14 channels
   (kimi: no cherry-picked single channel/segment).
"""
import json
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

BANDS = {"Delta": (0.5, 4), "Theta": (4, 8), "Alpha": (8, 12),
         "Beta": (12, 30), "Gamma": (30, 45)}
M, TAU = 3, 2
N_SAMP = 5000
TARGET_RR = 0.05
SEED = 20261031


def takens(x, m=M, tau=TAU):
    N = len(x) - (m - 1) * tau
    idx = np.arange(m) * tau
    return np.stack([x[i:i + N] for i in idx], axis=1)


def dist_matrix(emb, block=1024):
    n = emb.shape[0]
    D = np.empty((n, n), dtype=np.float32)
    for i in range(0, n, block):
        D[i:i + block] = cdist(emb[i:i + block], emb, metric="chebyshev")
    return D


def rqa_metrics(D, eps):
    R = (D <= eps)
    n = R.shape[0]
    np.fill_diagonal(R, False)
    mask = ~np.eye(n, dtype=bool)
    rr = R[mask].mean()
    cont = np.zeros_like(R)
    cont[:-1, :-1] |= R[:-1, :-1] & R[1:, 1:]
    cont[1:, 1:] |= R[:-1, :-1] & R[1:, 1:]
    det = (R & cont)[mask].mean()
    vcont = np.zeros_like(R)
    vcont[:-1] |= R[:-1] & R[1:]
    vcont[1:] |= R[:-1] & R[1:]
    lam = (R & vcont)[mask].mean()
    # diagonal line-length entropy (standard ENT, diagonal lines length>=1)
    lines = []
    for k in range(1, n):
        for off in (k, -k):
            d = np.diagonal(R, offset=off)
            if not d.any():
                continue
            padded = np.concatenate(([False], d, [False]))
            edges = np.flatnonzero(padded[1:] != padded[:-1])
            lens = edges[1::2] - edges[0::2]
            lens = lens[lens > 0]
            if len(lens):
                lines.append(lens)
    lines = np.concatenate(lines) if lines else np.array([1])
    hist = np.bincount(lines)
    p = hist[hist > 0] / hist.sum()
    ent = float(-(p * np.log2(p)).sum())
    return dict(RR=float(rr), DET=float(det), LAM=float(lam), ENT=ent)


def band_signal(ch, lo, hi, fs):
    sos = butter(5, [lo / (fs / 2), hi / (fs / 2)], btype="band", output="sos")
    return sosfiltfilt(sos, ch)


def surrogate_phase(x, rng):
    n = len(x)
    f = np.fft.rfft(x)
    ph = rng.uniform(0, 2 * np.pi, f.shape)
    ph[0] = 0.0
    if n % 2 == 0:
        ph[-1] = 0.0
    return np.fft.irfft(np.abs(f) * np.exp(1j * ph), n=n)


def analyze_band(x, rng):
    """Returns metrics for empirical + surrogate at matched RR=5%, plus
    halfstd and eps10 conditions for empirical."""
    emb = takens(x)
    D = dist_matrix(emb)
    iu = np.triu_indices(len(D), 1)
    eps_rr5 = float(np.quantile(D[iu], TARGET_RR))
    out = {"emp": rqa_metrics(D, eps_rr5), "eps_rr5": eps_rr5}
    out["emp"]["eps"] = eps_rr5
    half = 0.5 * float(x.std())
    out["emp_halfstd"] = rqa_metrics(D, half)
    out["emp_halfstd"]["eps"] = half
    out["emp_eps10"] = rqa_metrics(D, 10.0)
    out["emp_eps10"]["eps"] = 10.0
    # surrogate: OWN matched-RR eps (amplitude distribution changes!)
    xs = surrogate_phase(x, rng)
    Ds = dist_matrix(takens(xs))
    eps_s = float(np.quantile(Ds[iu], TARGET_RR))
    out["surr"] = rqa_metrics(Ds, eps_s)
    out["surr"]["eps"] = eps_s
    out["amp"] = float(np.sqrt(np.mean(x ** 2)))
    out["surr_std"] = float(xs.std())
    return out


def main():
    from colony_lib.datasets import load_dataset
    ds = load_dataset("neural_eeg")
    fs = float(getattr(ds, "sampling_rate", 128.0))
    data = np.asarray(ds.data)
    rng = np.random.default_rng(SEED)
    results = {}

    # ---- full band sweep, AF3 ----
    ch = data[:N_SAMP, 0]
    print(f"AF3 fs={fs} N={N_SAMP} raw_std={ch.std():.2f}")
    for name, (lo, hi) in BANDS.items():
        x = band_signal(ch, lo, hi, fs)
        results[name] = analyze_band(x, rng)
        r = results[name]
        print(f"[{name}] RMS={r['amp']:5.1f} | RR5: emp DET={r['emp']['DET']:.4f} "
              f"LAM={r['emp']['LAM']:.4f} ENT={r['emp']['ENT']:.3f} | "
              f"surr DET={r['surr']['DET']:.4f} ENT={r['surr']['ENT']:.3f} "
              f"(eps={r['eps_rr5']:.2f}/{r['surr']['eps']:.2f}) | "
              f"halfstd: RR={r['emp_halfstd']['RR']:.3f} DET={r['emp_halfstd']['DET']:.3f} "
              f"ENT={r['emp_halfstd']['ENT']:.3f} | "
              f"eps10: RR={r['emp_eps10']['RR']:.3f} ENT={r['emp_eps10']['ENT']:.3f}")

    order = list(BANDS.keys())
    freqs = np.arange(5)
    print("\n=== TREND TESTS (Spearman vs band order) ===")
    for tag, lab in [("emp_halfstd", "halfstd"), ("emp_eps10", "eps10")]:
        rr = [results[b][tag]["RR"] for b in order]
        ent = [results[b][tag]["ENT"] for b in order]
        print(f"{lab:8s} RR={np.round(rr,3).tolist()} rho={spearmanr(rr, freqs).statistic:+.3f} | "
              f"ENT={np.round(ent,3).tolist()} rho={spearmanr(ent, freqs).statistic:+.3f}")
    amp = [results[b]["amp"] for b in order]
    rr10 = [results[b]["emp_eps10"]["RR"] for b in order]
    print(f"RMS={np.round(amp,1).tolist()}")
    print(f"Spearman(RR_eps10, RMS)={spearmanr(rr10, amp).statistic:+.3f}  "
          f"Spearman(RR_halfstd, RMS)={spearmanr([results[b]['emp_halfstd']['RR'] for b in order], amp).statistic:+.3f}")

    # matched-RR ENT comparison: Gamma vs Alpha (the core kimi question)
    print("\n=== MATCHED RR=5%: Gamma vs Alpha (AF3) ===")
    for b in order:
        e, s = results[b]["emp"], results[b]["surr"]
        print(f"{b}: empDET={e['DET']:.4f} surrDET={s['DET']:.4f} det_ratio={s['DET']/max(e['DET'],1e-9):.3f} | "
              f"empENT={e['ENT']:.3f} surrENT={s['ENT']:.3f}")
    g = results["Gamma"]["emp"]["ENT"]; a = results["Alpha"]["emp"]["ENT"]
    print(f"AF3: GammaENT - AlphaENT = {g - a:+.3f}  ({'Gamma>Alpha' if g > a else 'Alpha>=Gamma'})")

    # ---- 14-channel cross-check: Alpha vs Gamma at matched RR ----
    print("\n=== 14-CHANNEL CROSS-CHECK (matched RR=5%, empirical ENT) ===")
    chans = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2",
             "P8", "T8", "FC6", "F4", "F8", "AF4"]
    chan_res = {}
    wins = [(0, N_SAMP), (N_SAMP, 2 * N_SAMP)]
    diffs = []
    for ci, cname in enumerate(chans):
        d_a, d_g = [], []
        for w0, w1 in wins:
            seg = data[w0:w1, ci]
            if len(seg) < N_SAMP:
                continue
            xa = band_signal(seg, 8, 12, fs)
            xg = band_signal(seg, 30, 45, fs)
            Da = dist_matrix(takens(xa))
            Dg = dist_matrix(takens(xg))
            iu = np.triu_indices(Da.shape[0], 1)
            ea = float(np.quantile(Da[iu], TARGET_RR))
            eg = float(np.quantile(Dg[iu], TARGET_RR))
            ma = rqa_metrics(Da, ea)
            mg = rqa_metrics(Dg, eg)
            d_a.append(ma["ENT"]); d_g.append(mg["ENT"])
        diff = float(np.mean(d_g) - np.mean(d_a))
        diffs.append(diff)
        chan_res[cname] = {"alpha_ENT": float(np.mean(d_a)),
                           "gamma_ENT": float(np.mean(d_g)), "diff": diff}
        print(f"{cname}: AlphaENT={np.mean(d_a):.3f} GammaENT={np.mean(d_g):.3f} diff={diff:+.3f}")
    diffs = np.array(diffs)
    n_pos = int((diffs > 0).sum())
    from scipy.stats import binomtest
    p = binomtest(n_pos, len(diffs), 0.5).pvalue
    print(f"sign test: {n_pos}/{len(diffs)} channels Gamma>Alpha, p={p:.4f}, "
          f"mean diff={diffs.mean():+.3f} +/- {diffs.std(ddof=1):.3f}")

    out = {"af3": results, "channels": chan_res,
           "sign_test": {"n_pos": n_pos, "n": len(diffs), "p": float(p),
                         "mean_diff": float(diffs.mean()), "sd": float(diffs.std(ddof=1))}}
    with open("eeg_principled_results.json", "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("\nsaved eeg_principled_results.json")


if __name__ == "__main__":
    main()