"""
HYP-131 follow-up: Condition C — FIXED RECURRENCE RATE normalization.
The most standard RQA protocol: choose eps per-window so RR hits a target (5%),
then ask whether DET/LAM/ENT still distinguish frequency bands. If the
"distinct dynamical signatures" are real dynamics (not threshold artifacts),
they must survive at fixed RR. Also: Welch PSD of raw AF3 to audit the
amplitude ordering (Beta/Gamma rms > Alpha rms is suspicious -> artifact check)
and phase-randomized surrogate control for DET at fixed RR.
"""
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, welch

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

FS = 128.0
BANDS = [("Delta", 0.5, 4.0), ("Theta", 4.0, 8.0), ("Alpha", 8.0, 12.0),
         ("Beta", 12.0, 30.0), ("Gamma", 30.0, 45.0)]
CENTERS = [2.25, 6.0, 10.0, 21.0, 37.5]
WIN, N_WIN, M, TAU = 1024, 14, 3, 2
RR_TARGET = 0.05


def bandpass(x, lo, hi):
    b, a = butter(4, [lo/(FS/2), hi/(FS/2)], btype='band')
    return filtfilt(b, a, x)


def eps_for_rr(emb, target):
    """Epsilon = pairwise-distance quantile that yields ~target recurrence rate
    (excluding the self-recurrence diagonal)."""
    d = np.sqrt(((emb[:, None, :] - emb[None, :, :])**2).sum(-1))
    iu = np.triu_indices(len(emb), k=1)
    return float(np.quantile(d[iu], 1.0 - target))


def rqa_fixed_rr(sig):
    out = {"RR": [], "DET": [], "LAM": [], "ENT": [], "eps": []}
    for w in range(N_WIN):
        seg = sig[w*WIN:(w+1)*WIN]
        seg = seg - seg.mean()
        emb = takens_embedding(seg, m=M, tau=TAU)
        eps = eps_for_rr(emb, RR_TARGET)
        R = recurrence_matrix(emb, epsilon=eps)
        mets = compute_rqa_metrics(R)
        for k in ("RR", "DET", "LAM", "ENT"):
            out[k].append(float(mets[k]))
        out["eps"].append(eps)
    return {k: (float(np.median(v)), float(np.std(v))) for k, v in out.items()}


def phase_randomize(x):
    """FFT phase randomization: preserves power spectrum, destroys dynamics."""
    X = np.fft.rfft(x)
    rng = np.random.default_rng(7)
    phases = rng.uniform(0, 2*np.pi, len(X))
    phases[0] = 0.0
    if len(x) % 2 == 0:
        phases[-1] = 0.0
    return np.fft.irfft(X * np.exp(1j * phases), len(x))


def main():
    ds = load_dataset("neural_eeg")
    df = ds.to_dataframe()
    af3 = df["AF3"].to_numpy(dtype=float)
    x = af3 - af3.mean()

    # Welch PSD of raw AF3 (audit of amplitude ordering)
    f, pxx = welch(x, fs=FS, nperseg=1024)
    band_power = {}
    for name, lo, hi in BANDS:
        mask = (f >= lo) & (f < hi)
        band_power[name] = float(np.trapz(pxx[mask], f[mask]))

    results = {"rr_target": RR_TARGET, "band_power_raw": band_power, "bands": []}
    det_rr, lam_rr, ent_rr, eps_med = [], [], [], []

    print(f"{'band':6s} {'pow(uV^2)':>12s} | RR-fixed DET/LAM/ENT (median±std) | eps(median uV)")
    for (name, lo, hi), fc in zip(BANDS, CENTERS):
        sig = bandpass(x, lo, hi)
        m = rqa_fixed_rr(sig)
        results["bands"].append({"name": name, "center_hz": fc,
                                 "fixed_rr": {k: m[k] for k in m}})
        det_rr.append(m["DET"][0]); lam_rr.append(m["LAM"][0]); ent_rr.append(m["ENT"][0])
        eps_med.append(m["eps"][0])
        print(f"{name:6s} {band_power[name]:12.1f} | "
              f"DET={m['DET'][0]:.3f}±{m['DET'][1]:.3f} LAM={m['LAM'][0]:.3f}±{m['LAM'][1]:.3f} "
              f"ENT={m['ENT'][0]:.2f}±{m['ENT'][1]:.2f} | eps={m['eps'][0]:.2f}")

    def spearman(a, b):
        ra = np.argsort(np.argsort(a)).astype(float)
        rb = np.argsort(np.argsort(b)).astype(float)
        return float(np.corrcoef(ra, rb)[0, 1])

    sp = {"DET": spearman(CENTERS, det_rr), "LAM": spearman(CENTERS, lam_rr),
          "ENT": spearman(CENTERS, ent_rr)}
    results["spearman_fixedRR_vs_freq"] = sp
    print("Spearman(metric vs frequency) at fixed RR=5%:", {k: f"{v:+.2f}" for k, v in sp.items()})

    # Surrogate control: does DET at fixed RR exceed phase-randomized noise?
    rng = np.random.default_rng(11)
    surr_det = {name: [] for name, _, _ in BANDS}
    for (name, lo, hi) in BANDS:
        sig = bandpass(x, lo, hi)
        for _ in range(3):
            s = phase_randomize(sig)
            m = rqa_fixed_rr(s)
            surr_det[name].append(m["DET"][0])
    results["surrogate_DET"] = {k: float(np.median(v)) for k, v in surr_det.items()}
    print("Phase-randomized surrogate DET (median):",
          {k: f"{v:.3f}" for k, v in results["surrogate_DET"].items()})

    # figure
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    ax = axes[0]
    ax.loglog(f[1:], pxx[1:], lw=0.8)
    for name, lo, hi in BANDS:
        ax.axvspan(lo, hi, alpha=0.15)
    ax.set_xlabel("Hz"); ax.set_ylabel("PSD uV^2/Hz")
    ax.set_title("Welch PSD, raw AF3: broad-band floor,\nno clean 1/f (artifact-prone recording)")

    ax = axes[1]
    ax.errorbar(CENTERS, det_rr, yerr=[results['bands'][i]['fixed_rr']['DET'][1] for i in range(5)],
                fmt='o-', color='C0', label='DET (fixed RR=5%)')
    ax.errorbar(CENTERS, lam_rr, yerr=[results['bands'][i]['fixed_rr']['LAM'][1] for i in range(5)],
                fmt='s-', color='C1', label='LAM (fixed RR=5%)')
    ax.errorbar(CENTERS, ent_rr, yerr=[results['bands'][i]['fixed_rr']['ENT'][1] for i in range(5)],
                fmt='^-', color='C2', label='ENT (fixed RR=5%)')
    ax.set_xlabel("band center (Hz)"); ax.set_ylabel("metric (median)")
    ax.set_title(f"Normalized RQA at fixed RR=5%:\nDET vs freq Spearman {sp['DET']:+.2f}")
    ax.legend(); ax.grid(alpha=0.3)

    ax = axes[2]
    obs = [results['bands'][i]['fixed_rr']['DET'][0] for i in range(5)]
    sur = [results['surrogate_DET'][n] for n, _, _ in BANDS]
    ax.bar(np.arange(5)-0.18, obs, width=0.36, label='empirical DET', color='C0')
    ax.bar(np.arange(5)+0.18, sur, width=0.36, label='phase-randomized', color='C3', alpha=0.7)
    ax.set_xticks(range(5)); ax.set_xticklabels([b[0] for b in BANDS])
    ax.set_ylabel("DET at fixed RR=5%")
    ax.set_title("Surrogate control: excess determinism\n(EMP vs surrogate)")
    ax.legend(); ax.grid(alpha=0.3)

    fig.suptitle("HYP-131 follow-up: fixed-recurrence-rate normalization (AF3, 14x8s windows)", y=1.02)
    fig.tight_layout()
    fig.savefig("../../shared_agora/artifacts/eeg_rqa_fixed_rr_normalization.png",
                dpi=130, bbox_inches='tight')
    with open("../../shared_agora/artifacts/eeg_rqa_fixed_rr_normalization.json", "w") as f2:
        json.dump(results, f2, indent=1)
    print("saved figure + json")


if __name__ == "__main__":
    main()
