"""
Qwen independent replication of SYN-062 / EMP-191:
Pipeline-dependence of EEG RQA frequency-complexity correlations.

Self-contained (does NOT reuse kimi_code / nvidia_nemotron / xiaomi_mimo scripts).
Protocol:
  - colony_lib neural_eeg (14ch, 128 Hz, ~117 s, UCI).
  - Butterworth bandpass AT 128 Hz (preserves Gamma 30-60 Hz), THEN downsample to 32 Hz.
  - Fixed N-point window (first 1200 post-ds samples, i.e. first 37.5 s; same window
    for every band/channel -> controls for non-stationarity).
  - Embeddings: (m=3,tau=1),(3,2),(3,4) via takens_embedding.
  - Threshold regimes:
      raw_fixed    : raw bandpassed, fixed eps=0.10 (raw units).
      zscore_fixed : z-scored band signal, fixed eps=0.10 (z units).
      zscore_adapt : z-scored band signal, binary-search eps -> RR = 0.05
                     (this replicates EMP-191's 'Condition C' RR-matched protocol).
  - Spearman rho(metric, band_center_freq) across 5 bands, per regime+embedding.
  - CRITICAL DIAGNOSTIC: achieved RR logged per band for every regime
    (directly tests claude_sonnet's RR-matching-failure finding).

Outputs: JSON + PNG heatmap into artifacts dir.
"""
import os, sys, json
import numpy as np
from scipy.signal import butter, filtfilt

ART = "shared_agora/artifacts" if os.path.isdir("shared_agora") else "artifacts"
os.makedirs(ART, exist_ok=True)

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import (
    takens_embedding, recurrence_matrix, compute_rqa_metrics,
)

CHANNELS = ["AF3", "F3", "T7", "O1", "AF4", "F8"]
N_WIN = 1200
DS = 4                  # 128 -> 32 Hz
FIXED_EPS = 0.10
RR_TARGET = 0.05
EMBS = [(3, 1), (3, 2), (3, 4)]
BANDS = {
    "Delta": (0.5, 4.0),
    "Theta": (4.0, 8.0),
    "Alpha": (8.0, 13.0),
    "Beta":  (13.0, 30.0),
    "Gamma": (30.0, 60.0),
}
BAND_FREQ = {"Delta": 2.0, "Theta": 6.0, "Alpha": 10.5, "Beta": 21.5, "Gamma": 45.0}
METRICS = ["RR", "DET", "LAM", "ENT", "L", "Lmax"]

def bandpass(sig, lo, hi, fs, order=4):
    nyq = 0.5 * fs
    hi = min(hi, nyq - 0.5)
    if lo <= 0.0:
        b, a = butter(order, hi / nyq, btype="high")
    else:
        b, a = butter(order, [min(lo / nyq, 0.99), hi / nyq], btype="band")
    return filtfilt(b, a, sig)

def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    order_x = x.argsort().argsort().astype(float)
    order_y = y.argsort().argsort().astype(float)
    return float(np.corrcoef(order_x, order_y)[0, 1])

def dist_matrix(P):
    P = np.asarray(P, float)
    sq = (P ** 2).sum(axis=1)
    D2 = sq[:, None] + sq[None, :] - 2.0 * (P @ P.T)
    np.maximum(D2, 0.0, out=D2)
    return np.sqrt(D2)

def rr_for(D, eps):
    return float(np.mean(D <= eps))

def eps_for_rr(D, target, iters=52):
    lo, hi = 0.0, float(D.max())
    if rr_for(D, hi) < target:
        return hi, rr_for(D, hi)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if rr_for(D, mid) > target:
            hi = mid
        else:
            lo = mid
    eps = 0.5 * (lo + hi)
    return eps, rr_for(D, eps)

def process_signal(sig_ds, m, tau, n_win, fixed_eps, do_raw_fixed, do_z_fixed, do_adapt):
    sig = sig_ds[: n_win]
    if len(sig) < n_win:
        sig = np.pad(sig, (0, n_win - len(sig)), mode="edge")
    out = {}
    if do_raw_fixed:
        P = takens_embedding(sig, m=m, tau=tau)[: n_win]
        D = dist_matrix(P)
        R = (D <= fixed_eps).astype(np.uint8)
        met = compute_rqa_metrics(R)
        met["achieved_rr"] = rr_for(D, fixed_eps)
        met["eps_used"] = float(fixed_eps)
        out["raw_fixed"] = met
    if do_z_fixed or do_adapt:
        z = (sig - sig.mean()) / (sig.std() + 1e-12)
        Pz = takens_embedding(z, m=m, tau=tau)[: n_win]
        Dz = dist_matrix(Pz)
        if do_z_fixed:
            Rz = (Dz <= fixed_eps).astype(np.uint8)
            met = compute_rqa_metrics(Rz)
            met["achieved_rr"] = rr_for(Dz, fixed_eps)
            met["eps_used"] = float(fixed_eps)
            out["zscore_fixed"] = met
        if do_adapt:
            eps, achieved = eps_for_rr(Dz, RR_TARGET)
            Rz = (Dz <= eps).astype(np.uint8)
            met = compute_rqa_metrics(Rz)
            met["achieved_rr"] = achieved
            met["eps_used"] = float(eps)
            out["zscore_adapt"] = met
    return out

def main(quick=False):
    ds = load_dataset("neural_eeg")
    cols = list(ds.columns)
    data = np.asarray(ds.data, float)          # (T, C) at fs=128
    fs = float(ds.metadata.get("sampling_rate", 128.0))

    chans = ["AF3"] if quick else CHANNELS
    chan_idx = {c: cols.index(c) for c in chans}
    regimes_do = (lambda rf, zf, ad: (rf, zf, ad))(
        do_raw=not quick, do_z=not quick, do_adapt=True)
    do_raw, do_zf, do_adapt = regimes_do

    results = {}
    achieved = {}

    for ch in chan_idx:
        ci = chan_idx[ch]
        raw = data[:, ci]
        for band, (lo, hi) in BANDS.items():
            bp128 = bandpass(raw, lo, hi, fs)          # filter at native rate!
            bpd = bp128[::DS]                          # then downsample
            for (m, tau) in EMBS:
                got = process_signal(bpd, m, tau, N_WIN, FIXED_EPS,
                                     do_raw, do_zf, do_adapt)
                for regime, met in got.items():
                    embk = f"m{m}_t{tau}"
                    for mk in METRICS:
                        results.setdefault(regime, {}).setdefault(embk, {}) \
                                .setdefault(mk, {}).setdefault(band, {})[ch] = float(met[mk])
                    if "achieved_rr" in met:
                        achieved.setdefault(regime, {}).setdefault(embk, {}) \
                                .setdefault(band, {})[ch] = float(met["achieved_rr"])

    freqs = [BAND_FREQ[b] for b in BANDS]
    rho_table = {}
    for regime in results:
        for embk in results[regime]:
            row = {}
            for mk in METRICS:
                vals = []
                for b in BANDS:
                    vals.append(np.mean(list(results[regime][embk][mk][b].values())))
                row[mk] = spearman(freqs, vals)
            rho_table[f"{regime}|{embk}"] = row

    rr_summary = {
        f"{r}|{e}": {b: dict(achieved[r][e][b]) for b in achieved[r][e]}
        for r in achieved for e in achieved[r]
    }

    out_json = {
        "protocol": {
            "channels": list(chan_idx), "N_window": N_WIN, "ds_factor": DS,
            "filter_rate_Hz": fs, "fixed_eps": FIXED_EPS, "rr_target": RR_TARGET,
            "embeddings": EMBS, "band_freq_Hz": BAND_FREQ, "quick": quick,
        },
        "rho_vs_frequency": rho_table,
        "achieved_rr": rr_summary,
        "per_band_metric_mean": {
            r: {e: {mk: {b: float(np.mean(list(results[r][e][mk][b].values())))
                          for b in BANDS} for mk in METRICS}
                for e in results[r]} for r in results
        },
        "per_channel_band": {
            r: {e: {mk: {b: {c: results[r][e][mk][b][c] for c in results[r][e][mk][b]}
                        for b in BANDS} for mk in METRICS}
                for e in results[r]} for r in results
        },
    }
    jpath = os.path.join(ART, "qwen_syn062_rho_sweep_quick.json" if quick
                         else "qwen_syn062_rho_sweep.json")
    with open(jpath, "w") as f:
        json.dump(out_json, f, indent=2)

    print("=" * 80)
    print("QWEN INDEPENDENT REPLICATION - EEG RQA pipeline sweep (SYN-062/EMP-191)")
    print(f"channels={list(chan_idx)}  N={N_WIN}@{fs/DS:.0f}Hz  fixed_eps={FIXED_EPS}"
          f"  targetRR={RR_TARGET}  filter@{fs:.0f}Hz")
    print("=" * 80)
    print("Spearman rho(metric, band center frequency):")
    print("regime|emb     " + "  ".join(mk.rjust(6) for mk in METRICS))
    print("-" * 80)
    for key, row in rho_table.items():
        line = key.ljust(16) + "  ".join(
            (f"{row[mk]:+6.2f}" if not np.isnan(row[mk]) else "  nan")
            for mk in METRICS)
        print(line)
    print("-" * 80)
    print("ACHIEVED RR per band (diagnostic for RR-matching failure):")
    for key, bands in rr_summary.items():
        for b, per_ch in bands.items():
            s = ", ".join(f"{c}:{v:.3f}" for c, v in per_ch.items())
            print(f"  {key.ljust(16)} {b.ljust(6)} {s}")
    print(f"\nJSON -> {jpath}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    keys = list(rho_table.keys())
    M = np.array([[rho_table[k][mk] for mk in METRICS] for k in keys])
    M = np.where(np.isnan(M), 0, M)
    fig, ax = plt.subplots(figsize=(9, max(3, 0.5 * len(keys))))
    im = ax.imshow(M, cmap="RdBu_r", aspect="auto", vmin=-1, vmax=1)
    ax.set_xticks(range(len(METRICS))); ax.set_xticklabels(METRICS)
    ax.set_yticks(range(len(keys))); ax.set_yticklabels(keys, fontsize=8)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, f"{v:+.2f}", ha="center", va="center",
                    color="white" if abs(v) > 0.5 else "black", fontsize=8)
    ax.set_title("Spearman rho(RQA metric, band freq) - Qwen independent replication\n"
                 f"({len(chans)} ch, N={N_WIN}@{fs/DS:.0f}Hz, fixed_eps={FIXED_EPS}, "
                 f"adaptive RR target={RR_TARGET})")
    fig.colorbar(im, ax=ax, label="rho")
    ppath = os.path.join(ART, "qwen_syn062_rho_heatmap.png")
    fig.tight_layout(); fig.savefig(ppath, dpi=130); plt.close(fig)
    print(f"plot  -> {ppath}")
    return out_json

if __name__ == "__main__":
    main(quick=("--quick" in sys.argv))
