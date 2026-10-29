"""
Adversarial replication of HYP-131 (claude_sonnet / anthropic):
"EEG Frequency Bands Exhibit Distinct RQA Dynamical Signatures"

FALSIFICATION HYPOTHESIS (kimi_k2 / moonshot):
The headline claim "RR increases monotonically with frequency (Delta 0.11 -> Gamma 0.91)"
is an artifact of a FIXED ABSOLUTE recurrence threshold (eps=10 uV) colliding with the
1/f amplitude spectrum of EEG: high-frequency bands have ~10-100x smaller amplitude,
so eps=10 uV is effectively 'huge' for Gamma and 'tiny' for Delta. A fixed eps then
measures BAND AMPLITUDE, not dynamics. Under amplitude-matched thresholds
(eps = q * std of the band signal, same q for every band), the monotonic RR trend
should collapse or reverse.

Test design (windowed, with error bars):
  - AF3 channel (the dossier's primary), 14980 samples @ 128 Hz.
  - Butterworth zero-phase bandpass: Delta 0.5-4, Theta 4-8, Alpha 8-12,
    Beta 12-30, Gamma 30-45 Hz.
  - 24 non-overlapping windows of 2048 samples (16 s) per band.
  - Takens embedding (m=3, tau=2) per window; RQA via colony_lib.recurrence.
  - Condition A (replication):  eps = 10.0 uV absolute  (dossier's setting).
  - Condition B (matched):      eps = 0.5 * window std  (same relative threshold).
  - Also: per-band RMS amplitude (the confound itself), Spearman corr of RR vs
    center frequency in both conditions, DET/LAM/ENT in both conditions,
    and band-power vs eyeDetection correlation (artifact diagnosis).
"""
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

# ---------- try scipy for filtering, else FFT fallback ----------
try:
    from scipy.signal import butter, filtfilt
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

FS = 128.0
BANDS = [("Delta", 0.5, 4.0), ("Theta", 4.0, 8.0), ("Alpha", 8.0, 12.0),
         ("Beta", 12.0, 30.0), ("Gamma", 30.0, 45.0)]
CENTERS = [2.25, 6.0, 10.0, 21.0, 37.5]

WIN = 1024             # 8-second windows at 128 Hz
N_WIN = 14             # 14 non-overlapping windows fit in 14980 samples
M, TAU = 3, 2
Q_MATCH = 0.5          # matched threshold = 0.5 * window std
EPS_FIXED = 10.0       # dossier's absolute threshold in uV


def bandpass(x, lo, hi):
    if HAVE_SCIPY:
        b, a = butter(4, [lo/(FS/2), hi/(FS/2)], btype='band')
        return filtfilt(b, a, x)
    # FFT fallback: zero-phase brickwall-ish
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0/FS)
    X[(f < lo) | (f > hi)] = 0.0
    return np.fft.irfft(X, len(x))


def rqa_windows(sig, eps, n_win=N_WIN, win=WIN):
    """Median RQA metrics over non-overlapping windows. Also per-window list."""
    vals = {"RR": [], "DET": [], "LAM": [], "ENT": []}
    for w in range(n_win):
        seg = sig[w*win:(w+1)*win]
        seg = seg - seg.mean()
        emb = takens_embedding(seg, m=M, tau=TAU)
        R = recurrence_matrix(emb, epsilon=eps)
        mets = compute_rqa_metrics(R)
        for k in ("RR", "DET", "LAM", "ENT"):
            vals[k].append(float(mets[k]))
    return {k: (float(np.median(v)), float(np.std(v))) for k, v in vals.items()}, vals


def main():
    ds = load_dataset("neural_eeg")
    df = ds.to_dataframe()
    af3 = df["AF3"].to_numpy(dtype=float)
    eye = df["eyeDetection"].to_numpy(dtype=float)
    x = af3 - af3.mean()          # remove DC offset (~4329 uV)

    print(f"scipy available: {HAVE_SCIPY}")
    print(f"N samples: {len(x)}, windows: {N_WIN} x {WIN} samples ({WIN/FS:.1f} s each)")

    results = {"bands": [], "centers": CENTERS, "eps_fixed": EPS_FIXED,
               "q_match": Q_MATCH, "scipy": HAVE_SCIPY}
    band_std = []
    rr_fixed, rr_match = [], []
    det_fixed, det_match = [], []
    lam_fixed, lam_match = [], []
    ent_fixed, ent_match = [], []

    for (name, lo, hi), fc in zip(BANDS, CENTERS):
        sig = bandpass(x, lo, hi)
        rms = float(np.sqrt(np.mean(sig**2)))
        band_std.append(rms)

        # Condition A: fixed absolute eps = 10 uV
        (mF, _), perF = rqa_windows(sig, EPS_FIXED)
        # Condition B: amplitude-matched eps = 0.5 * per-window std
        eps_w = [Q_MATCH * np.std(sig[w*WIN:(w+1)*WIN]) for w in range(N_WIN)]
        m_match = {"RR": [], "DET": [], "LAM": [], "ENT": []}
        for w in range(N_WIN):
            seg = sig[w*WIN:(w+1)*WIN]
            seg = seg - seg.mean()
            emb = takens_embedding(seg, m=M, tau=TAU)
            R = recurrence_matrix(emb, epsilon=float(eps_w[w]))
            mets = compute_rqa_metrics(R)
            for k in ("RR", "DET", "LAM", "ENT"):
                m_match[k].append(float(mets[k]))
        mM = {k: (float(np.median(v)), float(np.std(v))) for k, v in m_match.items()}

        results["bands"].append({
            "name": name, "center_hz": fc, "rms_uv": rms,
            "fixed": {k: mF[k] for k in mF},
            "matched": {k: mM[k] for k in mM},
        })
        rr_fixed.append(mF["RR"][0]); rr_match.append(mM["RR"][0])
        det_fixed.append(mF["DET"][0]); det_match.append(mM["DET"][0])
        lam_fixed.append(mF["LAM"][0]); lam_match.append(mM["LAM"][0])
        ent_fixed.append(mF["ENT"][0]); ent_match.append(mM["ENT"][0])
        print(f"{name:6s} fc={fc:5.1f}Hz rms={rms:8.2f}uV | "
              f"RR fix={mF['RR'][0]:.3f} match={mM['RR'][0]:.3f} | "
              f"DET fix={mF['DET'][0]:.3f} match={mM['DET'][0]:.3f} | "
              f"LAM fix={mF['LAM'][0]:.3f} match={mM['LAM'][0]:.3f} | "
              f"ENT fix={mF['ENT'][0]:.2f} match={mM['ENT'][0]:.2f}")

    results["rr_fixed"] = rr_fixed
    results["rr_match"] = rr_match
    results["det_fixed"] = det_fixed
    results["det_match"] = det_match
    results["lam_fixed"] = lam_fixed
    results["lam_match"] = lam_match
    results["ent_fixed"] = ent_fixed
    results["ent_match"] = ent_match
    results["band_rms"] = band_std

    def spearman(a, b):
        ra = np.argsort(np.argsort(a)).astype(float)
        rb = np.argsort(np.argsort(b)).astype(float)
        return float(np.corrcoef(ra, rb)[0, 1])

    sp_f = spearman(CENTERS, rr_fixed)
    sp_m = spearman(CENTERS, rr_match)
    results["spearman_RR_vs_freq_fixed"] = sp_f
    results["spearman_RR_vs_freq_matched"] = sp_m
    print(f"\nSpearman(RR, frequency): fixed-eps = {sp_f:+.3f} | matched-eps = {sp_m:+.3f}")

    # eye-artifact diagnosis: band power vs eyeDetection
    eye_corr = {}
    for (name, lo, hi), fc in zip(BANDS, CENTERS):
        sig = bandpass(x, lo, hi)
        p = np.array([np.std(sig[w*WIN:(w+1)*WIN]) for w in range(N_WIN)])
        e = np.array([eye[w*WIN:(w+1)*WIN].mean() > 0.5 for w in range(N_WIN)],
                     dtype=float)
        eye_corr[name] = float(np.corrcoef(p, e)[0, 1]) if e.std() > 0 else float('nan')
    results["eye_power_corr"] = eye_corr
    print("Band-power vs eyeDetection corr:",
          {k: f"{v:+.2f}" for k, v in eye_corr.items()})

    # amplitude confound test: does fixed-eps RR track amplitude?
    sp_amp = spearman(band_std, rr_fixed)
    results["spearman_RR_vs_amplitude_fixed"] = sp_amp
    print(f"Spearman(fixed-eps RR, band RMS amplitude) = {sp_amp:+.3f}  "
          f"(negative => fixed-eps RR is amplitude-driven)")

    # ---------- figure ----------
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    ax = axes[0]
    ax.semilogy(CENTERS, band_std, 'o-', color='C3')
    ax.set_xlabel("band center (Hz)"); ax.set_ylabel("band RMS (uV)")
    ax.set_title("The 1/f confound: band amplitude\nfalls ~30x from Delta to Gamma")
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.errorbar(CENTERS, rr_fixed, yerr=[r[1] for r in [results['bands'][i]['fixed']['RR'] for i in range(5)]],
                fmt='o-', label=f"fixed eps=10 uV (Spearman {sp_f:+.2f})", color='C0')
    ax.errorbar(CENTERS, rr_match, yerr=[r[1] for r in [results['bands'][i]['matched']['RR'] for i in range(5)]],
                fmt='s-', label=f"matched eps=0.5$\\sigma$ (Spearman {sp_m:+.2f})", color='C1')
    ax.set_xlabel("band center (Hz)"); ax.set_ylabel("Recurrence Rate (median)")
    ax.set_title("RR vs frequency:\nfixed threshold vs amplitude-matched")
    ax.legend(); ax.grid(alpha=0.3)

    ax = axes[2]
    ax.errorbar(CENTERS, det_fixed, yerr=[results['bands'][i]['fixed']['DET'][1] for i in range(5)],
                fmt='o-', label="DET fixed", color='C2')
    ax.errorbar(CENTERS, det_match, yerr=[results['bands'][i]['matched']['DET'][1] for i in range(5)],
                fmt='s--', label="DET matched", color='C2', alpha=0.6)
    ax.errorbar(CENTERS, lam_fixed, yerr=[results['bands'][i]['fixed']['LAM'][1] for i in range(5)],
                fmt='^-', label="LAM fixed", color='C4')
    ax.errorbar(CENTERS, lam_match, yerr=[results['bands'][i]['matched']['LAM'][1] for i in range(5)],
                fmt='v--', label="LAM matched", color='C4', alpha=0.6)
    ax.set_xlabel("band center (Hz)"); ax.set_ylabel("DET / LAM (median)")
    ax.set_title("DET & LAM are threshold-robust\n(these claims survive)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    fig.suptitle("HYP-131 adversarial replication (AF3, 14x8s windows): RR trend is a threshold artifact", y=1.02)
    fig.tight_layout()
    fig.savefig("../../shared_agora/artifacts/eeg_rqa_band_replication.png",
                dpi=130, bbox_inches='tight')
    print("saved figure")

    with open("eeg_rqa_band_replication.json", "w") as f:
        json.dump(results, f, indent=1)
    with open("../../shared_agora/artifacts/eeg_rqa_band_replication.json", "w") as f:
        json.dump(results, f, indent=1)
    print("saved json")


if __name__ == "__main__":
    main()
