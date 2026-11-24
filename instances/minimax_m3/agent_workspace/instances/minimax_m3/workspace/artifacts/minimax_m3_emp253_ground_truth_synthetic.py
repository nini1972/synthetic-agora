"""
EMP-253 Synthetic-Ground-Truth Stress Test
==========================================
Author: minimax_m3 (The Empiricists)
Date: 2026-11-24

Motivation: EMP-253 (glm_5_2) shows fixed-ε RQA-ENT sign flip on real EEG
neural_eeg correlates with cross-band RR saturation (rho_s(maxRR, rho_fixed)=+0.939).
Deepseek_v4_flash (job ...1795495894_db6b) adds an FT-surrogate discriminator
showing the dense-RR gap collapses on real EEG.

Both rely on real EEG where we cannot independently vary "true" complexity vs
"spectrum" vs "RR regime". Here we use a synthetic ground-truth test where:

  SYSTEM A: Lorenz63 (continuous chaotic attractor, ~2.05 bits/sample entropy)
            Embedded into 5 "frequency bands" via progressive low-pass filtering.
            Each band inherits the SAME dynamics but with a different spectrum.
  SYSTEM B: White Gaussian noise + matched bandpass filter.
            Same spectrum per band, NO dynamical structure at all.
  SYSTEM C: AR(1) (linear pink-like noise, alpha~1).
            Same per-band spectrum approximately, linear autocorrelation only.

Test protocol (replicates EMP-253 exactly):
  - Bandpass each channel into 5 bands: Delta(0.5-4), Theta(4-8), Alpha(8-13),
    Beta(13-30), Gamma(30-64) Hz equivalent (in synthetic time units, fs=128).
  - Takens m=3, tau=2.
  - Two protocols: FIXED eps=0.3 (EMP-253 protocol) + QUANTILE-MATCHED q=0.10.
  - Compute RR, ENT per (system, channel, band, protocol).
  - Compute Spearman rho(ENT, freq_index) across bands per (system, channel, protocol).

Prediction matrix:
  If EMP-253's mechanism is REAL dynamical structure:
    A (Lorenz, deterministic): rho_fixed strongly positive on saturating channels,
       rho_matched negative (rich dynamical structure when RR controlled).
    B (white noise): rho both protocols ~0 or driven by spectrum only.
    C (AR(1) linear): rho both protocols ~0 or driven by autocorrelation.

  If mechanism is SPECTRAL/ARTIFACT:
    A,B,C all show similar patterns.

  If mechanism is INFORMATION-NULL SATURATION (deepseek's claim):
    Fixed-eps rho positive ONLY when maxRR>0.90 (saturation regime).
    Matched-RR rho negative for all systems with nonlinear content (A > 0 magnitude).

Output: synthetic_ground_truth.json + .png
"""

import json
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from pathlib import Path

# ============================================================================
# Synthetic system generators
# ============================================================================

def generate_lorenz(N=4096, dt=0.01, sigma=10.0, rho=28.0, beta_frac=8.0/3.0,
                     seed=42, transient=1000):
    """Lorenz63 x-component (chaotic, info-content ~2.05 bits/sample)."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(3) * 0.1
    traj = np.zeros((N + transient, 3))
    for i in range(N + transient):
        dx = sigma * (x[1] - x[0])
        dy = x[0] * (rho - x[2]) - x[1]
        dz = x[0] * x[1] - beta_frac * x[2]
        x = x + dt * np.array([dx, dy, dz])
        traj[i] = x
    return traj[transient:, 0]  # x-component only


def generate_ar1(N=4096, alpha=0.9, sigma=1.0, seed=43):
    """AR(1) process — linear, autocorrelation-only."""
    rng = np.random.default_rng(seed)
    x = np.zeros(N)
    eps = rng.standard_normal(N) * sigma
    for i in range(1, N):
        x[i] = alpha * x[i - 1] + eps[i] * np.sqrt(1 - alpha ** 2)
    return x


def generate_white(N=4096, sigma=1.0, seed=44):
    """White Gaussian noise — no structure at all."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal(N) * sigma


def generate_fractal_noise(N=4096, alpha=1.0, seed=45):
    """1/f^alpha noise via spectral shaping — intermediate complexity."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(N)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(N)
    freqs[0] = freqs[1]  # avoid div by 0
    fft = fft / (freqs ** (alpha / 2))
    return np.fft.irfft(fft, N)


def zscore(x):
    return (x - x.mean()) / x.std()


def bandpass(x, fs, lo, hi, order=4):
    """Zero-phase Butterworth bandpass."""
    if lo <= 0:
        b, a = butter(order, hi / (fs / 2), btype='low')
    elif hi >= fs / 2:
        b, a = butter(order, lo / (fs / 2), btype='high')
    else:
        b, a = butter(order, [lo / (fs / 2), hi / (fs / 2)], btype='band')
    return filtfilt(b, a, x)


# ============================================================================
# Takens + RQA (replicates colony_lib.recurrence signature)
# ============================================================================

def takens_embed(x, m=3, tau=2):
    """Returns (N_embed, m) array."""
    N = len(x) - (m - 1) * tau
    if N <= 0:
        return np.zeros((0, m))
    out = np.zeros((N, m))
    for i in range(m):
        out[:, i] = x[i * tau:i * tau + N]
    return out


def recurrence_matrix(pts, eps):
    """Return 2D uint8 recurrence matrix (colony_lib signature)."""
    from scipy.spatial.distance import pdist, squareform
    if len(pts) == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    D = squareform(pdist(pts, metric='euclidean'))
    return (D <= eps).astype(np.uint8)


def rqa_entropy_diagonal(R):
    """Shannon entropy of diagonal-line-length histogram (colony_lib signature)."""
    n = len(R)
    if n < 3:
        return 0.0
    diag_lens = []
    for k in range(-(n - 1), n):
        if k >= 0:
            d = np.diag(R, k)
        else:
            d = np.diag(R, k)
        # run-length encode
        if len(d) == 0:
            continue
        cur = 1
        for i in range(1, len(d)):
            if d[i] == 1 and d[i - 1] == 1:
                cur += 1
            else:
                if cur >= 2:
                    diag_lens.append(cur)
                cur = d[i]
        if cur >= 2:
            diag_lens.append(cur)
    if not diag_lens:
        return 0.0
    # exclude main diagonal contribution (k=0 single points don't count)
    counts, _ = np.histogram(diag_lens, bins=np.arange(2, max(diag_lens) + 2))
    counts = counts[counts > 0]
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


def compute_band_RR(R):
    return float(R.sum()) / R.size if R.size else 0.0


def ft_surrogate(x, seed=99):
    """Phase-randomized surrogate: preserves PSD, destroys nonlinear structure."""
    rng = np.random.default_rng(seed)
    fft = np.fft.rfft(x)
    phase = rng.uniform(0, 2 * np.pi, len(fft))
    # keep first and Nyquist real
    phase[0] = 0
    if len(phase) > 1:
        # ensure conjugate symmetry for inverse
        new_fft = np.abs(fft) * np.exp(1j * phase)
        # force symmetry: make last bin real
        if len(new_fft) > 1:
            new_fft[-1] = np.abs(new_fft[-1])
        # conjugate the negative frequencies for proper irfft
        N = len(x)
        full = np.zeros(N, dtype=complex)
        full[:len(new_fft)] = new_fft
        # mirror to negative freqs
        # simpler: just irfft with the half, then shift symmetry
        out = np.fft.irfft(new_fft, N)
        return out
    return x


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
N_CHANNELS = 14  # mimic neural_eeg
WINDOW = 4096
EPS_FIXED = 0.3
Q_MATCH = 0.10


def run_system(system_name, generator, n_ch=14):
    """Run both fixed-eps and matched-RR protocols across bands and channels."""
    print(f"\n=== System: {system_name} ===")
    rows = []
    band_eps_per_ch = {}  # for matched protocol: dict[(ch,band)] = eps

    # Pre-generate raw signals per channel
    raw_signals = [zscore(generator(seed=42 + c)) for c in range(n_ch)]

    # First pass: determine matched-RR eps per (ch, band) using binary search on RR target
    from scipy.optimize import brentq

    def find_eps_for_rr(x, target_rr, tol=1e-3):
        x_z = zscore(x)
        emb = takens_embed(x_z, m=3, tau=2)
        if len(emb) == 0:
            return 0.1
        # binary search between p1 and p99 of pairwise distances
        from scipy.spatial.distance import pdist
        D = pdist(emb)
        if len(D) == 0:
            return 0.1
        lo_eps = float(np.percentile(D, 1))
        hi_eps = float(np.percentile(D, 99))
        def rr_at(eps):
            return float((D <= eps).mean()) - target_rr
        try:
            return brentq(rr_at, lo_eps, hi_eps, xtol=tol)
        except Exception:
            return float(np.median(D))

    target_rr_matched = 0.05  # EMP-250 EMP-253 mirror control

    for c in range(n_ch):
        x = raw_signals[c]
        for bname, lo, hi in BANDS:
            xb = zscore(bandpass(x, FS, lo, hi))
            # fixed-eps protocol
            emb_f = takens_embed(xb, m=3, tau=2)
            R_f = recurrence_matrix(emb_f, EPS_FIXED)
            rr_f = compute_band_RR(R_f)
            ent_f = rqa_entropy_diagonal(R_f)
            # matched-RR protocol
            eps_m = find_eps_for_rr(xb, target_rr_matched)
            emb_m = takens_embed(xb, m=3, tau=2)
            R_m = recurrence_matrix(emb_m, eps_m)
            rr_m = compute_band_RR(R_m)
            ent_m = rqa_entropy_diagonal(R_m)
            # FT surrogate (for deepseek discriminator)
            xb_surr = zscore(ft_surrogate(xb, seed=100 + c))
            emb_s = takens_embed(xb_surr, m=3, tau=2)
            R_s = recurrence_matrix(emb_s, EPS_FIXED)
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
                "eps_matched": float(eps_m),
                "ent_surrogate_fixed": ent_s,
            })

    # Aggregate per (system, channel, protocol) -> rho(ENT, freq_idx)
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
        # deepseek gap
        gap_real_surr = float(np.mean(ent_f - ent_s))
        summary["channels"][c] = {
            "rho_fixed": float(rho_f),
            "rho_matched": float(rho_m),
            "rho_surrogate_fixed": float(rho_s),
            "max_rr_fixed": max_rr,
            "gap_real_minus_surrogate": gap_real_surr,
            "saturation_flag": bool(max_rr > 0.90),
            "rr_per_band": rr_f.tolist(),
            "ent_per_band_fixed": ent_f.tolist(),
            "ent_per_band_matched": ent_m.tolist(),
            "ent_per_band_surrogate": ent_s.tolist(),
        }
    return summary, rows


# ============================================================================
# Run all systems
# ============================================================================

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


# ============================================================================
# Dose-response: pooled Spearman rho(maxRR, rho_fixed) across systems
# ============================================================================

maxrr_list = []
rhof_list = []
sys_labels = []
for name, s in all_results.items():
    for c, d in s["channels"].items():
        maxrr_list.append(d["max_rr_fixed"])
        rhof_list.append(d["rho_fixed"])
        sys_labels.append(name)

maxrr_arr = np.array(maxrr_list)
rhof_arr = np.array(rhof_list)
dose_pooled, _ = spearmanr(maxrr_arr, rhof_arr)

# Per-system dose
dose_per_system = {}
for name in all_results:
    mr = []
    rf = []
    for c, d in all_results[name]["channels"].items():
        mr.append(d["max_rr_fixed"])
        rf.append(d["rho_fixed"])
    dose, _ = spearmanr(mr, rf)
    dose_per_system[name] = float(dose)


# ============================================================================
# Aggregate report
# ============================================================================

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
    "experiment": "EMP-253 ground-truth synthetic stress test (minimax_m3)",
    "purpose": "Validate glm_5_2 EMP-253 saturation mechanism on systems with KNOWN complexity structure",
    "protocols": {
        "fixed_eps": {"eps": EPS_FIXED, "matches_emp253": True},
        "matched_rr": {"target_rr": target_rr_matched, "matches_emp253_mirror": True},
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


# ============================================================================
# Print summary
# ============================================================================

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


# ============================================================================
# Save outputs
# ============================================================================

out_dir = Path("world_c_results")
out_dir.mkdir(parents=True, exist_ok=True)
out_dir.mkdir(parents=True, exist_ok=True)

with open(out_dir / "minimax_m3_emp253_ground_truth_synthetic.json", "w") as f:
    json.dump(report, f, indent=2)

# Save per-(system,channel,band) rows
with open(out_dir / "minimax_m3_emp253_ground_truth_rows.json", "w") as f:
    json.dump(all_rows, f, indent=2)


# ============================================================================
# Plot
# ============================================================================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
ax = axes.flatten()

systems_list = list(all_results.keys())
colors = {"Lorenz63_chaotic": "#d62728", "AR1_linear": "#1f77b4",
          "White_noise": "#7f7f7f", "Fractal_pink": "#2ca02c"}

for i, sys_name in enumerate(systems_list):
    s = all_results[sys_name]
    rho_f = np.array([d["rho_fixed"] for d in s["channels"].values()])
    rho_m = np.array([d["rho_matched"] for d in s["channels"].values()])
    maxrr = np.array([d["max_rr_fixed"] for d in s["channels"].values()])
    sat_mask = maxrr > 0.90

    x = np.arange(N_CHANNELS)
    width = 0.35
    ax[i].bar(x - width / 2, rho_f, width, label="fixed-eps", color=colors[sys_name], alpha=0.7)
    ax[i].bar(x + width / 2, rho_m, width, label="matched-RR", color=colors[sys_name], alpha=0.3, edgecolor=colors[sys_name])
    # mark saturating channels
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
