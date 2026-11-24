"""
EMP-253 Synthetic-Ground-Truth Stress Test (VECTORIZED)
=======================================================
Author: minimax_m3 (The Empiricists)
Date: 2026-11-24

Optimization: target_RR ~= percentile of pairwise distances (no brentq).
For random Gaussian embeddings, P(D < eps) = target_RR iff eps ~ the target_RR quantile.
"""

import json
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from pathlib import Path

# ============================================================================
# Synthetic system generators (vectorized)
# ============================================================================

def generate_lorenz(N=4096, dt=0.01, sigma=10.0, rho=28.0, beta_frac=8.0/3.0,
                     seed=42, transient=1000):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(3) * 0.1
    traj = np.zeros((N + transient, 3))
    for i in range(N + transient):
        dx = sigma * (x[1] - x[0])
        dy = x[0] * (rho - x[2]) - x[1]
        dz = x[0] * x[1] - beta_frac * x[2]
        x = x + dt * np.array([dx, dy, dz])
        traj[i] = x
    return traj[transient:, 0]


def generate_ar1(N=4096, alpha=0.9, sigma=1.0, seed=43):
    rng = np.random.default_rng(seed)
    eps = rng.standard_normal(N) * sigma
    x = np.zeros(N)
    for i in range(1, N):
        x[i] = alpha * x[i - 1] + eps[i] * np.sqrt(1 - alpha ** 2)
    return x


def generate_white(N=4096, sigma=1.0, seed=44):
    return np.random.default_rng(seed).standard_normal(N) * sigma


def generate_fractal_noise(N=4096, alpha=1.0, seed=45):
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(N)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(N)
    freqs[0] = freqs[1]
    fft = fft / (freqs ** (alpha / 2))
    return np.fft.irfft(fft, N)


zscore = lambda x: (x - x.mean()) / x.std()


def bandpass(x, fs, lo, hi, order=4):
    nyq = fs / 2
    if lo <= 0:
        b, a = butter(order, hi / nyq, btype='low')
    elif hi >= nyq:
        b, a = butter(order, lo / nyq, btype='high')
    else:
        b, a = butter(order, [lo / nyq, hi / nyq], btype='band')
    return filtfilt(b, a, x)


# ============================================================================
# Takens + RQA (vectorized where possible)
# ============================================================================

def takens_embed(x, m=3, tau=2):
    N = len(x) - (m - 1) * tau
    if N <= 0:
        return np.zeros((0, m))
    return np.column_stack([x[i * tau:i * tau + N] for i in range(m)])


def pairwise_dists_condensed(pts):
    """Returns condensed distance vector (scipy.pdist style)."""
    if len(pts) < 2:
        return np.array([])
    from scipy.spatial.distance import pdist
    return pdist(pts, metric='euclidean')


def R_from_eps(D_condensed, n, eps):
    """Build recurrence matrix (n,n) from condensed distances given eps."""
    from scipy.spatial.distance import squareform
    if len(D_condensed) == 0:
        return np.zeros((n, n), dtype=np.uint8)
    D = squareform(D_condensed)
    return (D <= eps).astype(np.uint8)


def rqa_entropy_diagonal(R):
    n = len(R)
    if n < 3:
        return 0.0
    diag_lens = []
    for k in range(-(n - 1), n):
        d = np.diag(R, k)
        if len(d) == 0:
            continue
        cur = 1
        for i in range(1, len(d)):
            if d[i] == 1 and d[i - 1] == 1:
                cur += 1
            else:
                if cur >= 2:
                    diag_lens.append(cur)
                cur = int(d[i])
        if cur >= 2:
            diag_lens.append(cur)
    if not diag_lens:
        return 0.0
    counts, _ = np.histogram(diag_lens, bins=np.arange(2, max(diag_lens) + 2))
    counts = counts[counts > 0]
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


def ft_surrogate(x, seed=99):
    rng = np.random.default_rng(seed)
    fft = np.fft.rfft(x)
    phase = rng.uniform(0, 2 * np.pi, len(fft))
    phase[0] = 0
    new_fft = np.abs(fft) * np.exp(1j * phase)
    if len(new_fft) > 1:
        new_fft[-1] = np.abs(new_fft[-1])
    return np.fft.irfft(new_fft, len(x))


# ============================================================================
# Experiment
# ============================================================================

BANDS = [
    ("Delta",  0.5,  4.0),
    ("Theta",  4.0,  8.0),
    ("Alpha",  8.0, 13.0),
    ("Beta",  13.0, 30.0),
    ("Gamma", 30.0, 64.0),
]
FS = 128.0
N_CHANNELS = 14
WINDOW = 4096
EPS_FIXED = 0.3
TARGET_RR_MATCHED = 0.05


def run_system(system_name, generator, n_ch=14):
    print(f"\n=== System: {system_name} ===")
    raw_signals = [zscore(generator(seed=42 + c)) for c in range(n_ch)]
    rows = []

    for c in range(n_ch):
        x = raw_signals[c]
        for bname, lo, hi in BANDS:
            xb = zscore(bandpass(x, FS, lo, hi))
            # fixed-eps protocol
            emb_f = takens_embed(xb, m=3, tau=2)
            n_emb = len(emb_f)
            D_f = pairwise_dists_condensed(emb_f)
            R_f = R_from_eps(D_f, n_emb, EPS_FIXED)
            rr_f = float(R_f.sum()) / R_f.size if R_f.size else 0.0
            ent_f = rqa_entropy_diagonal(R_f)
            # matched-RR protocol: use TARGET_RR_MATCHED-quantile of pairwise dists
            if len(D_f) > 0:
                eps_m = float(np.quantile(D_f, TARGET_RR_MATCHED))
            else:
                eps_m = 0.1
            R_m = R_from_eps(D_f, n_emb, eps_m)
            rr_m = float(R_m.sum()) / R_m.size if R_m.size else 0.0
            ent_m = rqa_entropy_diagonal(R_m)
            # FT surrogate
            xb_surr = zscore(ft_surrogate(xb, seed=100 + c))
            emb_s = takens_embed(xb_surr, m=3, tau=2)
            D_s = pairwise_dists_condensed(emb_s)
            R_s = R_from_eps(D_s, len(emb_s), EPS_FIXED)
            ent_s = rqa_entropy_diagonal(R_s)

            rows.append({
                "system": system_name,
                "channel": c,
                "band": bname,
                "band_idx": [b[0] for b in BANDS].index(bname),
                "rr_fixed": rr_f,
                "ent_fixed": ent_f,
                "rr_matched": rr_m,
                "ent_matched": ent_m,
                "eps_matched": eps_m,
                "ent_surrogate_fixed": ent_s,
            })

    summary = {"system": system_name, "channels": {}}
    for c in range(n_ch):
        c_rows = [r for r in rows if r["channel"] == c]
        idx = np.array([r["band_idx"] for r in c_rows])
        ent_f = np.array([r["ent_fixed"] for r in c_rows])
        ent_m = np.array([r["ent_matched"] for r in c_rows])
        ent_s = np.array([r["ent_surrogate_fixed"] for r in c_rows])
        rr_f = np.array([r["rr_fixed"] for r in c_rows])
        max_rr = float(rr_f.max())
        rho_f, _ = spearmanr(idx, ent_f)
        rho_m, _ = spearmanr(idx, ent_m)
        rho_s, _ = spearmanr(idx, ent_s)
        gap_real_surr = float(np.mean(ent_f - ent_s))
        summary["channels"][c] = {
            "rho_fixed": float(rho_f) if not np.isnan(rho_f) else 0.0,
            "rho_matched": float(rho_m) if not np.isnan(rho_m) else 0.0,
            "rho_surrogate_fixed": float(rho_s) if not np.isnan(rho_s) else 0.0,
            "max_rr_fixed": max_rr,
            "gap_real_minus_surrogate": gap_real_surr,
            "saturation_flag": bool(max_rr > 0.90),
            "rr_per_band": rr_f.tolist(),
            "ent_per_band_fixed": ent_f.tolist(),
            "ent_per_band_matched": ent_m.tolist(),
            "ent_per_band_surrogate": ent_s.tolist(),
        }
    return summary, rows


systems = [
    ("Lorenz63_chaotic", lambda seed: generate_lorenz(N=WINDOW, seed=seed)),
    ("AR1_linear",       lambda seed: generate_ar1(N=WINDOW, seed=seed)),
    ("White_noise",      lambda seed: generate_white(N=WINDOW, seed=seed)),
    ("Fractal_pink",     lambda seed: generate_fractal_noise(N=WINDOW, alpha=1.0, seed=seed)),
]

all_results = {}
all_rows = []
for name, gen in systems:
    s, r = run_system(name, gen, n_ch=N_CHANNELS)
    all_results[name] = s
    all_rows.extend(r)


# Dose-response
maxrr_list, rhof_list, sys_labels = [], [], []
for name, s in all_results.items():
    for c, d in s["channels"].items():
        maxrr_list.append(d["max_rr_fixed"])
        rhof_list.append(d["rho_fixed"])
        sys_labels.append(name)

maxrr_arr = np.array(maxrr_list)
rhof_arr = np.array(rhof_list)
dose_pooled, _ = spearmanr(maxrr_arr, rhof_arr)

dose_per_system = {}
for name in all_results:
    mr = [d["max_rr_fixed"] for d in all_results[name]["channels"].values()]
    rf = [d["rho_fixed"] for d in all_results[name]["channels"].values()]
    d, _ = spearmanr(mr, rf)
    dose_per_system[name] = float(d)


def agg(name):
    s = all_results[name]
    rho_f = np.array([d["rho_fixed"] for d in s["channels"].values()])
    rho_m = np.array([d["rho_matched"] for d in s["channels"].values()])
    rho_s = np.array([d["rho_surrogate_fixed"] for d in s["channels"].values()])
    gaps = np.array([d["gap_real_minus_surrogate"] for d in s["channels"].values()])
    maxrr = np.array([d["max_rr_fixed"] for d in s["channels"].values()])
    sat_mask = maxrr > 0.90
    return {
        "rho_fixed_mean": float(rho_f.mean()),
        "rho_fixed_std": float(rho_f.std()),
        "rho_matched_mean": float(rho_m.mean()),
        "rho_matched_std": float(rho_m.std()),
        "rho_surrogate_fixed_mean": float(rho_s.mean()),
        "rho_surrogate_fixed_std": float(rho_s.std()),
        "gap_real_minus_surrogate_mean": float(gaps.mean()),
        "gap_real_minus_surrogate_std": float(gaps.std()),
        "max_rr_fixed_mean": float(maxrr.mean()),
        "max_rr_fixed_std": float(maxrr.std()),
        "n_channels_saturated": int(sat_mask.sum()),
        "rho_fixed_mean_on_saturated": float(rho_f[sat_mask].mean()) if sat_mask.any() else None,
        "rho_fixed_mean_on_nonsaturated": float(rho_f[~sat_mask].mean()) if (~sat_mask).any() else None,
    }


report = {
    "experiment": "EMP-253 ground-truth synthetic stress test v2 (minimax_m3)",
    "purpose": "Validate glm_5_2 EMP-253 saturation mechanism on systems with KNOWN complexity structure",
    "protocols": {
        "fixed_eps": {"eps": EPS_FIXED, "matches_emp253": True},
        "matched_rr": {"target_rr": TARGET_RR_MATCHED, "method": "quantile of pairwise dists",
                       "matches_emp253_mirror": True},
        "ft_surrogate": {"matches_deepseek_emp238_discriminator": True},
    },
    "per_system": {name: agg(name) for name in all_results},
    "dose_response_rho_maxrr_vs_rho_fixed": {
        "pooled_spearman": float(dose_pooled),
        "per_system_spearman": dose_per_system,
    },
    "systems": {
        "Lorenz63_chaotic": "deterministic chaotic, ~2.05 bits/sample entropy",
        "AR1_linear":       "linear pink-like, NO nonlinear determinism",
        "White_noise":      "no structure at all",
        "Fractal_pink":     "intermediate, long-range dependence",
    },
    "n_channels": N_CHANNELS,
    "window": WINDOW,
    "n_bands": len(BANDS),
}

print("\n" + "=" * 78)
print("RESULTS")
print("=" * 78)
for sys_name in report["per_system"]:
    a = report["per_system"][sys_name]
    print(f"\n{sys_name}:")
    print(f"  rho_fixed            : {a['rho_fixed_mean']:+.3f} ± {a['rho_fixed_std']:.3f}")
    print(f"  rho_matched          : {a['rho_matched_mean']:+.3f} ± {a['rho_matched_std']:.3f}")
    print(f"  rho_surrogate_fixed  : {a['rho_surrogate_fixed_mean']:+.3f} ± {a['rho_surrogate_fixed_std']:.3f}")
    print(f"  gap(real - surr)     : {a['gap_real_minus_surrogate_mean']:+.3f} ± {a['gap_real_minus_surrogate_std']:.3f}")
    print(f"  maxRR_fixed          : {a['max_rr_fixed_mean']:.3f} ± {a['max_rr_fixed_std']:.3f}")
    print(f"  n_saturated(>0.90)   : {a['n_channels_saturated']}/{N_CHANNELS}")
    if a["rho_fixed_mean_on_saturated"] is not None:
        print(f"  rho_fixed|sat        : {a['rho_fixed_mean_on_saturated']:+.3f}")
        print(f"  rho_fixed|not sat    : {a['rho_fixed_mean_on_nonsaturated']:+.3f}")

print("\nDOSE-RESPONSE rho(maxRR, rho_fixed):")
print(f"  Pooled across all systems: {dose_pooled:+.3f}")
for sys_name, d in dose_per_system.items():
    print(f"  {sys_name:25s}: {d:+.3f}")

out_dir = Path("world_c_results")
out_dir.mkdir(parents=True, exist_ok=True)

with open(out_dir / "minimax_m3_emp253_ground_truth_synthetic.json", "w") as f:
    json.dump(report, f, indent=2)

with open(out_dir / "minimax_m3_emp253_ground_truth_rows.json", "w") as f:
    json.dump(all_rows, f, indent=2)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
ax = axes.flatten()

colors = {"Lorenz63_chaotic": "#d62728", "AR1_linear": "#1f77b4",
          "White_noise": "#7f7f7f", "Fractal_pink": "#2ca02c"}

for i, sys_name in enumerate(all_results):
    s = all_results[sys_name]
    rho_f = np.array([d["rho_fixed"] for d in s["channels"].values()])
    rho_m = np.array([d["rho_matched"] for d in s["channels"].values()])
    maxrr = np.array([d["max_rr_fixed"] for d in s["channels"].values()])
    sat_mask = maxrr > 0.90

    x = np.arange(N_CHANNELS)
    width = 0.35
    ax[i].bar(x - width / 2, rho_f, width, label="fixed-eps", color=colors[sys_name], alpha=0.7)
    ax[i].bar(x + width / 2, rho_m, width, label="matched-RR", color=colors[sys_name],
              alpha=0.3, edgecolor=colors[sys_name])
    for j in range(N_CHANNELS):
        if sat_mask[j]:
            ax[i].scatter([j], [1.1], marker='*', s=100, color='gold', edgecolor='black', zorder=10)
    ax[i].axhline(0, color='k', linewidth=0.5)
    ax[i].set_title(f"{sys_name}\nmaxRR={maxrr.mean():.2f}, n_sat={int(sat_mask.sum())}",
                     fontsize=10)
    ax[i].set_ylim(-1.2, 1.2)
    ax[i].set_xlabel("channel")
    ax[i].set_ylabel(r"$\rho$(ENT, freq_idx)")
    ax[i].legend(loc='upper right', fontsize=8)
    ax[i].grid(alpha=0.3)

plt.suptitle("EMP-253 Synthetic Ground-Truth Stress Test — "
             "rho(ENT,freq) per channel, fixed-eps vs matched-RR\n"
             "(gold stars = saturating channels with maxRR>0.90)",
             fontsize=11)
plt.tight_layout()
plt.savefig(out_dir / "minimax_m3_emp253_ground_truth_synthetic.png", dpi=120, bbox_inches='tight')
print(f"\nFigure: {out_dir / 'minimax_m3_emp253_ground_truth_synthetic.png'}")
print(f"Report: {out_dir / 'minimax_m3_emp253_ground_truth_synthetic.json'}")
print("\nDONE.")
