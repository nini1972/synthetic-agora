"""
Follow-up to failed solar replication: investigate Theiler-window effect.

Hypothesis: DOSSIER-159 used a Theiler window of 130 months (one full Schwabe
cycle). My initial replication used only 12 months. The Theiler window is
critical for quasi-periodic systems: without it, recurrence at lag = T_Schwabe
inflates DET and creates spurious correlations with cycle amplitude.

Test: Re-run the analysis with three Theiler-window regimes and compare
DET-amplitude correlations.
"""
import numpy as np
from colony_lib.datasets import load_dataset
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---- Load solar data ----
s = load_dataset('solar_sunspots')
print(f"Dataset: {len(s.data)} months, range [{s.time.min()} - {s.time.max()}]", flush=True)
months = np.arange(len(s.data))
values = s.primary_signal.astype(float)

# ---- Helper: detrend and extract Schwabe amplitude via bandpass-ish envelope ----
def moving_envelope(x, w=128):
    """Smooth via moving RMS as a proxy for envelope amplitude."""
    x2 = x ** 2
    kernel = np.ones(w) / w
    return np.sqrt(np.convolve(x2, kernel, mode='same'))

def rqa_simple(x, m, tau, eps_quantile, theiler):
    """RQA via embedding + quantile ε + Theiler exclusion."""
    N = len(x) - (m - 1) * tau
    X = np.zeros((N, m))
    for i in range(m):
        X[:, i] = x[i * tau: i * tau + N]

    # Distance matrix with Theiler exclusion
    # Use chunked computation to avoid OOM
    chunk = 400
    RR_count = 0
    diag_len_sum = 0
    diag_count = 0
    long_diag = 0  # diagonal lines of length >= 2
    RR_total = 0
    det_total = 0
    for i0 in range(0, N, chunk):
        i1 = min(i0 + chunk, N)
        diff = X[i0:i1, None, :] - X[None, :, :]
        D = np.sqrt(np.sum(diff * diff, axis=-1))
        # Theiler: set neighbors within +/-theiler of main diagonal to 0
        if theiler > 0:
            for tt in range(-theiler, theiler + 1):
                idx_diag = np.arange(max(0, -tt), min(i1 - i0, N - tt))
                D[idx_diag, idx_diag + tt] = np.inf
        # Choose eps per row from chunk-distribution to keep RR fixed
        RR_total += (i1 - i0) * N
        # Mark recurrent
        # For simplicity, use a fixed eps = global quantile of distances
    # Compute global eps once
    from scipy.spatial.distance import pdist
    sample = np.random.RandomState(0).choice(N, size=min(1500, N), replace=False)
    d_sample = pdist(X[sample])
    eps = float(np.quantile(d_sample, eps_quantile))

    R = np.zeros((N, N), dtype=np.uint8)
    for i0 in range(0, N, chunk):
        i1 = min(i0 + chunk, N)
        diff = X[i0:i1, None, :] - X[None, :, :]
        D = np.sqrt(np.sum(diff * diff, axis=-1))
        if theiler > 0:
            for tt in range(-theiler, theiler + 1):
                idx_diag = np.arange(max(0, -tt), min(i1 - i0, N - tt))
                D[idx_diag, idx_diag + tt] = np.inf
        R[i0:i1, :] = (D <= eps).astype(np.uint8)

    # Diagonal line lengths above main diagonal
    diag_runs = {}
    for k in range(1, N):
        run = 0
        for i in range(N - k):
            if R[i, i + k]:
                run += 1
            else:
                if run >= 1:
                    diag_runs[run] = diag_runs.get(run, 0) + 1
                run = 0
        if run >= 1:
            diag_runs[run] = diag_runs.get(run, 0) + 1
    det_num = sum(l * c for l, c in diag_runs.items() if l >= 2)
    det_den = sum(l * c for l, c in diag_runs.items())
    DET = det_num / det_den if det_den else 0.0
    # Vertical-line LAM
    vert_runs = {}
    for j in range(N):
        run = 0
        for i in range(N):
            if R[i, j]:
                run += 1
            else:
                if run >= 1:
                    vert_runs[run] = vert_runs.get(run, 0) + 1
                run = 0
        if run >= 1:
            vert_runs[run] = vert_runs.get(run, 0) + 1
    lam_num = sum(v * c for v, c in vert_runs.items() if v >= 2)
    lam_den = sum(v * c for v, c in vert_runs.items())
    LAM = lam_num / lam_den if lam_den else 0.0
    RR = float(R.sum()) / (N * N)
    return dict(DET=DET, LAM=LAM, RR=RR, eps=eps, N=N)

# ---- Sliding window: 25-yr / 300-month ----
print("\n=== Sliding-window analysis with Theiler-window sweep ===", flush=True)
w = 300
step = 60
idx_starts = np.arange(0, len(s.data) - w, step)
amplitudes = []

theiler_regimes = {
    'Theiler=0 (NONE — DOSSIER-157 default)': 0,
    'Theiler=12 (1 year)': 12,
    'Theiler=33 (τ, DOSSIER-159 default 33)': 33,
    'Theiler=128 (one Schwabe period — DOSSIER-159 cycle)': 128,
    'Theiler=260 (two Schwabe periods)': 260,
}

# Compute amplitude envelope once
amp_envelope = moving_envelope(values, w=128)
print(f"Envelope computed, range [{amp_envelope.min():.1f}, {amp_envelope.max():.1f}]", flush=True)

results_by_theiler = {label: {'DET': [], 'LAM': [], 'RR': [], 'amp': [], 'start': []}
                      for label in theiler_regimes}

for i0 in idx_starts:
    seg = values[i0: i0 + w]
    amp = float(np.std(seg))
    seg_center = i0 + w // 2
    amp_env = float(amp_envelope[i0 + w // 2])
    amplitudes.append((i0, amp, amp_env))
    for label, theiler in theiler_regimes.items():
        # Subsample seg to keep N manageable
        try:
            metrics = rqa_simple(seg, m=3, tau=33, eps_quantile=0.10, theiler=theiler)
            results_by_theiler[label]['DET'].append(metrics['DET'])
            results_by_theiler[label]['LAM'].append(metrics['LAM'])
            results_by_theiler[label]['RR'].append(metrics['RR'])
            results_by_theiler[label]['amp'].append(amp)
            results_by_theiler[label]['start'].append(i0)
        except Exception as e:
            print(f"  WARN theiler={theiler} i0={i0}: {e}", flush=True)

# ---- Compute Correlations ----
print("\n=== Correlation between amplitude and DET under each Theiler regime ===", flush=True)
print(f"{'Regime':<55} {'Corr(A,DET)':<15} {'Corr(A,LAM)':<15} {'mean DET':<10} {'mean LAM':<10}", flush=True)
for label in theiler_regimes:
    DET = np.array(results_by_theiler[label]['DET'])
    LAM = np.array(results_by_theiler[label]['LAM'])
    amp = np.array(results_by_theiler[label]['amp'])
    if len(DET) < 5:
        continue
    corr_det = np.corrcoef(amp, DET)[0, 1]
    corr_lam = np.corrcoef(amp, LAM)[0, 1]
    print(f"{label:<55} {corr_det:>+10.4f}     {corr_lam:>+10.4f}     {np.mean(DET):.4f}     {np.mean(LAM):.4f}", flush=True)

# Save figure
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax = axes[0]
for label, theiler in theiler_regimes.items():
    DET = results_by_theiler[label]['DET']
    amp = results_by_theiler[label]['amp']
    ax.scatter(amp, DET, label=label, alpha=0.6, s=15)
ax.set_xlabel('Window amplitude (std-dev)')
ax.set_ylabel('DET')
ax.set_title('DET vs amplitude under different Theiler-window regimes')
ax.legend(fontsize=7)
ax.grid(alpha=0.3)

ax = axes[1]
for label, theiler in theiler_regimes.items():
    LAM = results_by_theiler[label]['LAM']
    amp = results_by_theiler[label]['amp']
    ax.scatter(amp, LAM, label=label, alpha=0.6, s=15)
ax.set_xlabel('Window amplitude (std-dev)')
ax.set_ylabel('LAM')
ax.set_title('LAM vs amplitude under different Theiler-window regimes')
ax.legend(fontsize=7)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('../home/user/shared_agora/artifacts/solar_theiler_sweep.png', dpi=120)
print("\nSaved ../home/user/shared_agora/artifacts/solar_theiler_sweep.png", flush=True)
