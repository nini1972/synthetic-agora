"""
Definitive single-implementation test of HYP-131's three claims using ONLY
colony_lib RQA (standard DET/LAM/ENT conventions):
  A) eps=0.1 fixed (HYP-131's recipe)  -> does RR rise monotonically Delta->Gamma?
     and does Gamma exceed Alpha in ENT?
  B) amplitude-matched eps (each band scaled to unit std before eps search)
     -> is the RR monotonicity still there?
  C) matched RR=5% -> DET/LAM/ENT ordering; Alpha vs Gamma sign test over 14 chans.
"""
import json
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.stats import spearmanr, binomtest
from scipy.spatial.distance import cdist, pdist, squareform
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import compute_rqa_metrics

BANDS = {"Delta": (0.5, 4), "Theta": (4, 8), "Alpha": (8, 12),
         "Beta": (12, 30), "Gamma": (30, 45)}
M, TAU, N = 3, 2, 5000
CHANS = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2",
         "P8", "T8", "FC6", "F4", "F8", "AF4"]


def embed(x):
    idx = np.arange(M) * TAU
    NN = len(x) - (M - 1) * TAU
    return np.stack([x[i:i + NN] for i in idx], axis=1)


def rqa(emb, eps):
    D = squareform(pdist(emb, metric="chebyshev"))
    return compute_rqa_metrics(D <= eps)


def main():
    ds = load_dataset("neural_eeg")
    fs = float(getattr(ds, "sampling_rate", 128.0))
    data = np.asarray(ds.data)

    def band(ch, lo, hi, fs=None):
        sos = butter(5, [lo / (fs / 2), hi / (fs / 2)], btype="band", output="sos")
        return sosfiltfilt(sos, ch)

    out = {"A_fixed_eps": {}, "B_amp_matched": {}, "C_matched_rr": {}}

    # --- A) HYP-131 recipe ---
    for name, (lo, hi) in BANDS.items():
        emb = embed(band(data[:N, 0], lo, hi, fs))
        m = rqa(emb, 0.1)
        out["A_fixed_eps"][name] = {k: round(m[k], 4) for k in ("RR", "DET", "LAM", "ENT")}
    rrA = [out["A_fixed_eps"][b]["RR"] for b in BANDS]
    entA = [out["A_fixed_eps"][b]["ENT"] for b in BANDS]
    print("A fixed eps=0.1 RR :", np.round(rrA, 3).tolist(),
          f"rho={spearmanr(rrA, range(5)).statistic:+.3f}")
    print("A fixed eps=0.1 ENT:", np.round(entA, 3).tolist(),
          f"rho={spearmanr(entA, range(5)).statistic:+.3f}",
          f"Gamma-Alpha={entA[4]-entA[2]:+.3f}")

    # --- B) amplitude-matched: unit-std each band, eps scaled by 0.1*std ---
    for name, (lo, hi) in BANDS.items():
        x = band(data[:N, 0], lo, hi, fs)
        x = x / x.std()
        emb = embed(x)
        m = rqa(emb, 0.1)  # 0.1 of a standardized amplitude
        out["B_amp_matched"][name] = {k: round(m[k], 4) for k in ("RR", "DET", "LAM", "ENT")}
    rrB = [out["B_amp_matched"][b]["RR"] for b in BANDS]
    print("B amp-matched RR   :", np.round(rrB, 3).tolist(),
          f"rho={spearmanr(rrB, range(5)).statistic:+.3f}")

    # --- C) matched RR=5% ---
    def c_metrics(x):
        emb = embed(x)
        D = squareform(pdist(emb, metric="chebyshev"))
        iu = np.triu_indices(len(D), 1)
        eps = float(np.quantile(D[iu], 0.05))
        m = compute_rqa_metrics(D <= eps)
        m["RR_actual"] = float((D <= eps)[~np.eye(len(D), dtype=bool)].mean())
        return m

    for name, (lo, hi) in BANDS.items():
        m = c_metrics(band(data[:N, 0], lo, hi, fs))
        out["C_matched_rr"][name] = {k: round(float(m[k]), 4)
                                     for k in ("RR_actual", "DET", "LAM", "ENT")}
    detC = [out["C_matched_rr"][b]["DET"] for b in BANDS]
    lamC = [out["C_matched_rr"][b]["LAM"] for b in BANDS]
    entC = [out["C_matched_rr"][b]["ENT"] for b in BANDS]
    print("C matched-RR DET:", np.round(detC, 3).tolist(), f"rho={spearmanr(detC, range(5)).statistic:+.3f}")
    print("C matched-RR LAM:", np.round(lamC, 3).tolist(), f"rho={spearmanr(lamC, range(5)).statistic:+.3f}")
    print("C matched-RR ENT:", np.round(entC, 3).tolist(), f"rho={spearmanr(entC, range(5)).statistic:+.3f}")
    print(f"C Gamma-Alpha ENT = {entC[4]-entC[2]:+.3f}")

    diffs = []
    for ci, cn in enumerate(CHANS):
        seg = data[:N, ci]
        a = c_metrics(band(seg, 8, 12, fs))["ENT"]
        g = c_metrics(band(seg, 30, 45, fs))["ENT"]
        diffs.append(g - a)
    diffs = np.array(diffs)
    n_pos = int((diffs > 0).sum())
    p = binomtest(n_pos, len(diffs), 0.5).pvalue
    print(f"sign test Gamma>Alpha: {n_pos}/14 p={p:.5f} mean={diffs.mean():+.3f}+/-{diffs.std(ddof=1):.3f}")
    out["C_channel_diffs"] = {c: round(float(d), 3) for c, d in zip(CHANS, diffs)}
    out["sign_test"] = {"n_pos": int(n_pos), "p": float(p),
                        "mean": float(diffs.mean()), "sd": float(diffs.std(ddof=1))}

    json.dump(out, open("final_flip_test.json", "w"), indent=1)
    print("saved final_flip_test.json")


if __name__ == "__main__":
    main()