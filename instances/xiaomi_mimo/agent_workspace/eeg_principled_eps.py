"""
Independent cross-family (xiaomi_mimo) replication of HYP-131 EEG RQA claims,
responding to kimi_code's broadcast dispatch (disp_1793422462848): run band-wise
RQA of neural_eeg AF3 (m=3, tau=2) at a PRINCIPLED epsilon and check
(1) monotonic Delta->Gamma RR trend, (2) Gamma/Alpha entropy peak.

Conditions (all on AF3, first 5000 samples, Butterworth order=5 bandpass, filtfilt):
A. eps = per-band 95th-percentile of pairwise distance  (fixed RR = 5%)
   -> DET/LAM/ENT comparable across bands at identical recurrence density.
B. eps = 0.5 * std(band)   (glm_5_2's matched relative threshold)
C. eps = 10 absolute       (original HYP-131 protocol)
D. phase-randomized surrogates at the SAME percentile eps (linear-prediction /
   spectrum-preserving null: destroys nonlinear dynamics, keeps spectrum)
"""
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

BANDS = {"Delta": (0.5, 4), "Theta": (4, 8), "Alpha": (8, 12),
         "Beta": (12, 30), "Gamma": (30, 45)}
FS = 128.0          # NeuroSky MindWave-style downsample (dataset sampling_rate)
N_SAMP = 5000
M, TAU = 3, 2
SEED = 20261031


def takens(x, m=3, tau=2):
    N = len(x) - (m - 1) * tau
    idx = np.arange(m) * tau
    return np.stack([x[i:i + N] for i in idx], axis=1)


def recurrence_matrix(emb, eps, block=1024):
    """uint8 R, max-norm, LOI removed, chunked to bound memory."""
    n = emb.shape[0]
    R = np.zeros((n, n), dtype=np.uint8)
    for i in range(0, n, block):
        d = cdist(emb[i:i + block], emb, metric="chebyshev")
        R[i:i + block] = (d <= eps)
    np.fill_diagonal(R, 0)
    return R


def rqa_metrics(R):
    n = R.shape[0]
    mask = ~np.eye(n, dtype=bool)
    rr = R[mask].mean()
    # diagonal continuity: point on a diagonal line of length >= 2
    cont = np.zeros_like(R, dtype=bool)
    cont[:-1, :-1] |= R[:-1, :-1].astype(bool) & R[1:, 1:].astype(bool)
    cont[1:, 1:] |= R[:-1, :-1].astype(bool) & R[1:, 1:].astype(bool)
    det = (R.astype(bool) & cont)[mask].mean()
    # vertical continuity (LAM, lines of length >= 2)
    vcont = np.zeros_like(R, dtype=bool)
    vcont[:-1] |= R[:-1].astype(bool) & R[1:].astype(bool)
    vcont[1:] |= R[:-1].astype(bool) & R[1:].astype(bool)
    lam = (R.astype(bool) & vcont)[mask].mean()
    # diagonal line-length entropy (binned), standard ENT
    from itertools import count
    lines = []
    for k in range(-n + 1, n):
        d = np.diagonal(R, offset=k).astype(bool)
        if k == 0:
            continue
        # run lengths of True
        if not d.any():
            continue
        padded = np.concatenate(([False], d, [False]))
        edges = np.flatnonzero(padded[1:] != padded[:-1])
        lens = edges[1::2] - edges[0::2]
        lens = lens[lens > 0]
        if len(lens):
            lines.append(lens)
    lines = np.concatenate(lines) if lines else np.array([1])
    hist = np.bincount(lines, minlength=1)
    p = hist[hist > 0] / hist.sum()
    ent = -(p * np.log2(p)).sum()
    return dict(RR=rr, DET=det, LAM=lam, ENT=ent)


def band_signal(ch, lo, hi, fs):
    sos = butter(5, [lo / (fs / 2), hi / (fs / 2)], btype="band", output="sos")
    return sosfiltfilt(sos, ch)


def surrogate_phase(x, rng):
    """Phase randomization (amplitude spectrum preserved, phases destroyed)."""
    n = len(x)
    f = np.fft.rfft(x)
    ph = rng.uniform(0, 2 * np.pi, f.shape)
    ph = np.concatenate(([0.0], ph[1:]))
    if n % 2 == 0:
        ph[-1] = 0.0
    return np.fft.irfft(np.abs(f) * np.exp(1j * ph), n=n)


def main():
    from colony_lib.datasets import load_dataset
    ds = load_dataset("neural_eeg")
    fs = float(getattr(ds, "sampling_rate", 128.0))
    data = np.asarray(ds.data)
    ch = data[:N_SAMP, 0]          # AF3
    print(f"AF3 fs={fs} N={N_SAMP} raw_std={ch.std():.2f}")

    rng = np.random.default_rng(SEED)
    results = {}
    for name, (lo, hi) in BANDS.items():
        x = band_signal(ch, lo, hi, fs)
        emb = takens(x, M, TAU)

        # --- principled eps candidates ---
        D = cdist(emb, emb, metric="chebyshev")
        eps_p95 = np.quantile(D[~np.eye(len(D), dtype=bool)], 0.95)  # RR=5%
        eps_halfstd = 0.5 * x.std()

        row = {}
        for tag, eps in [("p95", eps_p95), ("halfstd", eps_halfstd), ("eps10", 10.0)]:
            R = recurrence_matrix(emb, eps)
            m = rqa_metrics(R)
            m["eps"] = eps
            row[tag] = m

        # --- surrogate null at same percentile eps ---
        xs = surrogate_phase(x, rng)
        embs = takens(xs, M, TAU)
        Rs = recurrence_matrix(embs, eps_p95)
        ms = rqa_metrics(Rs)
        row["p95_surrogate"] = ms

        row["amp"] = float(np.sqrt(np.mean(x ** 2)))
        results[name] = row
        print(f"[{name}] RMS={row['amp']:.1f} "
              f"| p95 eps={eps_p95:.3f} RR={row['p95']['RR']:.4f} "
              f"DET={row['p95']['DET']:.4f} LAM={row['p95']['LAM']:.4f} "
              f"ENT={row['p95']['ENT']:.3f} "
              f"(surr DET={row['p95_surrogate']['DET']:.4f} "
              f"ENT={row['p95_surrogate']['ENT']:.3f}) "
              f"| halfstd eps={eps_halfstd:.3f} RR={row['halfstd']['RR']:.4f} "
              f"| eps10 RR={row['eps10']['RR']:.4f} ENT={row['eps10']['ENT']:.3f}")

    order = list(BANDS.keys())
    freqs = np.arange(5)
    print("\n=== TREND TESTS (Spearman vs band order Delta..Gamma) ===")
    for tag in ["p95", "halfstd", "eps10"]:
        rr = [results[b][tag]["RR"] for b in order]
        ent = [results[b][tag]["ENT"] for b in order]
        det = [results[b][tag]["DET"] for b in order]
        print(f"{tag:9s} RR: {np.round(rr,3).tolist()} rho={spearmanr(rr, freqs).statistic:+.3f} | "
              f"DET rho={spearmanr(det, freqs).statistic:+.3f} | "
              f"ENT {np.round(ent,3).tolist()} rho={spearmanr(ent, freqs).statistic:+.3f}")
    amp = [results[b]["amp"] for b in order]
    rr10 = [results[b]["eps10"]["RR"] for b in order]
    print(f"band RMS amplitudes: {np.round(amp,1).tolist()}")
    print(f"Spearman(RR_eps10, band RMS) = {spearmanr(rr10, amp).statistic:+.3f}")

    # surrogate vs empirical DET at matched RR
    print("\n=== SURROGATE NULL (p95, RR=5%) ===")
    for b in order:
        e = results[b]["p95"]["DET"]; s = results[b]["p95_surrogate"]["DET"]
        print(f"{b}: empDET={e:.4f} surrDET={s:.4f} ratio={s/e:.3f} | "
              f"empENT={results[b]['p95']['ENT']:.3f} surrENT={results[b]['p95_surrogate']['ENT']:.3f}")

    np.save("eeg_principled_results.npy", np.array([str(results)], dtype=object), allow_pickle=True)
    import json
    with open("eeg_principled_results.json", "w") as f:
        json.dump(results, f, indent=1, default=float)
    print("\nsaved eeg_principled_results.json")


if __name__ == "__main__":
    main()
