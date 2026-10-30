"""
Faithful replication of DOSSIER-159 with dossier parameters (m=3, tau=33, w=528).
Key insight: investigate dependence of Corr(|A|,DET) on Theiler window.
Uses colony_lib built-in recurrence primitives for clean RQA computation.
"""
import numpy as np
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

# Load dataset, extract sunspot column
ds = load_dataset('solar_sunspots')
print(f"Dataset columns: {ds.columns}, shape: {ds.data.shape}", flush=True)
ssn = ds.data[:, 3].astype(float)
print(f"Length: {len(ssn)}, missing-indicator (-1) count: {(ssn < 0).sum()}", flush=True)

# Dossier params
m = 3
tau = 33
w = 528

# Sweep windows
step = 66  # 5.5 yr step (overlap ~87%)
starts = list(range(0, len(ssn) - w, step))
print(f"Number of sliding windows: {len(starts)}", flush=True)

theiler_regimes = {
    'Theiler=0': 0,
    'Theiler=12': 12,
    'Theiler=33 (tau)': 33,
    'Theiler=64': 64,
    'Theiler=128 (Schwabe)': 128,
}

results = {label: {'DET': [], 'LAM': [], 'RR': [], 'ENT': [], 'amp': [], 'L': [], 'start': []}
           for label in theiler_regimes}

for i0 in starts:
    seg = ssn[i0: i0 + w]
    # skip if too many missing indicators
    if (seg < 0).sum() > 0.1 * w:
        continue
    seg = np.where(seg < 0, np.nanmean(seg[seg >= 0]), seg)
    amp = float(np.std(seg))

    # Embedding
    X = takens_embedding(seg, m=m, tau=tau)
    print(f"  window i0={i0} amp={amp:.1f} embedded shape {X.shape}", flush=True)

    # Pick eps as 10% quantile of pairwise distances (sample-based)
    rng = np.random.RandomState(42)
    sample_idx = rng.choice(X.shape[0], size=min(800, X.shape[0]), replace=False)
    Xs = X[sample_idx]
    # Compute pairwise distances in chunks to avoid memory blowup
    from scipy.spatial.distance import pdist
    Pd = pdist(Xs)
    eps = float(np.quantile(Pd, 0.10))

    for label, theiler in theiler_regimes.items():
        try:
            R = recurrence_matrix(X, epsilon=eps, theiler=theiler)
            metrics = compute_rqa_metrics(R)
            results[label]['DET'].append(float(metrics['DET']))
            results[label]['LAM'].append(float(metrics['LAM']))
            results[label]['RR'].append(float(metrics['RR']))
            results[label]['ENT'].append(float(metrics['ENT']))
            results[label]['L'].append(float(metrics['L']))
            results[label]['amp'].append(amp)
            results[label]['start'].append(i0)
        except Exception as e:
            print(f"WARN theiler={theiler} i0={i0}: {e}", flush=True)

print("\n=== DOSSIER-159 amplitude-RQA correlation replication ===", flush=True)
print(f"{'Regime':<35} {'Corr(A,DET)':<14} {'Corr(A,LAM)':<14} {'mean DET':<10} {'mean LAM':<10}", flush=True)
for label in theiler_regimes:
    DET = np.array(results[label]['DET'])
    LAM = np.array(results[label]['LAM'])
    amp = np.array(results[label]['amp'])
    if len(DET) < 5:
        print(f"{label:<35} (insufficient samples: {len(DET)})", flush=True)
        continue
    corr_det = np.corrcoef(amp, DET)[0, 1]
    corr_lam = np.corrcoef(amp, LAM)[0, 1]
    print(f"{label:<35} {corr_det:>+10.4f}     {corr_lam:>+10.4f}     {np.mean(DET):.4f}     {np.mean(LAM):.4f}", flush=True)

# Save plot
fig, axes = plt.subplots(2, 2, figsize=(11, 9))
axes = axes.flat
for ax, metric_name in zip(axes, ['DET', 'LAM', 'RR', 'ENT']):
    for label in theiler_regimes:
        ax.scatter(results[label]['amp'], results[label][metric_name], label=label, alpha=0.7, s=22)
    ax.set_xlabel('Window amplitude (std-dev)')
    ax.set_ylabel(metric_name)
    ax.set_title(f'|A| vs {metric_name}')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
plt.suptitle("DOSSIER-159 replication: amplitude-RQA correlations across Theiler regimes\n"
             "DOSSIER-159 claim (with unspecified Theiler): Corr(|A|,DET) = -0.77 (global) / -0.46 (local)")
plt.tight_layout()
plt.savefig('shared_agora/artifacts/solar_dossier159_replication.png', dpi=120)
print("\nFigure saved to shared_agora/artifacts/solar_dossier159_replication.png", flush=True)

# Save JSON
out = {label: {k: list(map(float, v)) for k, v in results[label].items()}
       for label in theiler_regimes}
with open('shared_agora/artifacts/solar_dossier159_replication.json', 'w') as f:
    json.dump(out, f, indent=2)
print("JSON saved to shared_agora/artifacts/solar_dossier159_replication.json", flush=True)
