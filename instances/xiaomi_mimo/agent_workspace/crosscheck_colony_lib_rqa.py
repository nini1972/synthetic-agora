"""
Cross-validation of the hand-rolled RQA in eeg_principled_eps.py against
colony_lib.recurrence (independent implementation) — rules out an ENT/DET bug
in my own metrics code. Also re-tests the core kimi_code questions:
  (1) monotonic Delta->Gamma RR trend at matched RR / amplitude-matched eps
  (2) Gamma vs Alpha entropy at MATCHED recurrence rate
using colony_lib's takens_embedding + recurrence_matrix + compute_rqa_metrics.
"""
import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.stats import spearmanr, binomtest
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

BANDS = {"Delta": (0.5, 4), "Theta": (4, 8), "Alpha": (8, 12),
         "Beta": (12, 30), "Gamma": (30, 45)}
M, TAU, N, TARGET_RR = 3, 2, 5000, 0.05
CHANS = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2",
         "P8", "T8", "FC6", "F4", "F8", "AF4"]


def band_signal(ch, lo, hi, fs):
    sos = butter(5, [lo / (fs / 2), hi / (fs / 2)], btype="band", output="sos")
    return sosfiltfilt(sos, ch)


def matched_rr_metrics(x):
    emb = takens_embedding(x, m=M, tau=TAU)
    D = np.max(np.abs(emb[:, None, :] - emb[None, :, :]), axis=-1)
    iu = np.triu_indices(len(D), 1)
    eps = float(np.quantile(D[iu], TARGET_RR))
    R = recurrence_matrix(emb, epsilon=eps)
    m = dict(compute_rqa_metrics(R))
    m["eps"] = eps
    m["RR"] = float(np.mean(R[~np.eye(len(R), dtype=bool)]))
    return m


def main():
    ds = load_dataset("neural_eeg")
    fs = float(getattr(ds, "sampling_rate", 128.0))
    data = np.asarray(ds.data)
    res = {}

    print("=== colony_lib RQA, matched RR=5%, AF3 ===")
    for name, (lo, hi) in BANDS.items():
        x = band_signal(data[:N, 0], lo, hi, fs)
        m = matched_rr_metrics(x)
        res[name] = m
        print(f"{name}: RR={m['RR']:.4f} DET={m.get('DET', float('nan')):.4f} "
              f"LAM={m.get('LAM', float('nan')):.4f} ENT={m.get('ENT', float('nan')):.3f} "
              f"(keys={sorted(m.keys())})")

    order = list(BANDS)
    ent = [res[b].get("ENT", np.nan) for b in order]
    det = [res[b].get("DET", np.nan) for b in order]
    print(f"ENT trend rho={spearmanr(ent, np.arange(5)).statistic:+.3f}: {np.round(ent,3).tolist()}")
    print(f"DET trend rho={spearmanr(det, np.arange(5)).statistic:+.3f}: {np.round(det,3).tolist()}")
    print(f"GammaENT - AlphaENT = {ent[4]-ent[2]:+.3f}")

    print("\n=== 14-channel Alpha vs Gamma, matched RR=5% (colony_lib metrics) ===")
    diffs = []
    for ci, cn in enumerate(CHANS):
        a_list, g_list = [], []
        for w0 in (0, N):
            seg = data[w0:w0 + N, ci]
            if len(seg) < N:
                continue
            ma = matched_rr_metrics(band_signal(seg, 8, 12, fs))
            mg = matched_rr_metrics(band_signal(seg, 30, 45, fs))
            a_list.append(ma.get("ENT", np.nan))
            g_list.append(mg.get("ENT", np.nan))
        d = float(np.nanmean(g_list) - np.nanmean(a_list))
        diffs.append(d)
        print(f"{cn}: AlphaENT={np.nanmean(a_list):.3f} GammaENT={np.nanmean(g_list):.3f} diff={d:+.3f}")
    diffs = np.array(diffs)
    n_pos = int((diffs > 0).sum())
    p = binomtest(n_pos, len(diffs), 0.5).pvalue
    print(f"sign test: {n_pos}/{len(diffs)} Gamma>Alpha, p={p:.4f}, mean={diffs.mean():+.3f}+/-{diffs.std(ddof=1):.3f}")

    np.save("crosscheck_colony_lib.npy", np.array(1, dtype=int))
    import json
    json.dump({"af3": res, "channel_diffs": diffs.tolist(),
               "sign": {"n_pos": n_pos, "p": float(p)}},
              open("crosscheck_colony_lib.json", "w"), indent=1, default=float)
    print("saved crosscheck_colony_lib.json")


if __name__ == "__main__":
    main()