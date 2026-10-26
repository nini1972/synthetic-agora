#!/usr/bin/env python3
"""
Empirical verification of the Frontier Instrument-Blindness Theorem (DOSSIER-154):
The parity_contrast(p) statistic for even p is structurally equal to
mean_even_lag(C) - mean_odd_lag(C), hence cannot distinguish period-2 from period-4.
World C / Synthetic Agora replication artifact.
"""
import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

np.random.seed(42)


def logistic_series(r, x0=0.5, length=10000, burn=2000):
    xs = np.empty(burn + length)
    xs[0] = x0
    for n in range(1, burn + length):
        xs[n] = r * xs[n-1] * (1 - xs[n-1])
    return xs[burn:]


def autocorr(ts, max_lag=60):
    """Pearson autocorrelation for lags 1..max_lag."""
    ts = np.asarray(ts)
    ts = ts - ts.mean()
    c0 = np.dot(ts, ts) / len(ts)
    out = np.empty(max_lag)
    for lag in range(1, max_lag+1):
        out[lag-1] = np.dot(ts[:-lag], ts[lag:]) / (len(ts)-lag) / c0
    return out


def parity_contrast(C, p, N=10):
    """Frontier definition: (1/N) sum_{k=1..N} [C(p*k) - C(p/2 + p*k)]."""
    idx1 = p * np.arange(1, N+1)
    idx2 = p//2 + p * np.arange(1, N+1)
    idx1 = idx1 - 1  # 0-based
    idx2 = idx2 - 1
    return C[idx1].mean() - C[idx2].mean()


def m4_index(C, max_lag_used=None):
    """New residue-class detector: (mean mod4==0 - mean mod4==2) / (mean mod4==0 + mean mod4==2)."""
    if max_lag_used is None:
        max_lag_used = len(C)
    vals0, vals2 = [], []
    for lag in range(1, max_lag_used+1):
        if lag % 4 == 0:
            vals0.append(C[lag-1])
        elif lag % 4 == 2:
            vals2.append(C[lag-1])
    return (np.mean(vals0) - np.mean(vals2)) / (np.mean(vals0) + np.mean(vals2))


# Build four signals
length = 20000
burn = 5000

r_p2 = 3.20       # genuine period-2 (logistic)
r_p4 = 3.50       # genuine period-4 window
r_canon = 3.865   # canonical regime from Frontier dossier

trajectories = {
    'period-2 logistic r=3.20': logistic_series(r_p2, length=length, burn=burn),
    'period-4 logistic r=3.50': logistic_series(r_p4, length=length, burn=burn),
    'canonical r=3.865': logistic_series(r_canon, length=length, burn=burn),
    'period-2 decoy square': np.tile([0.0, 1.0], length),
    'chaotic r=3.90': logistic_series(3.9, length=length, burn=burn),
    'shuffled canonical': np.random.permutation(logistic_series(r_canon, length=length, burn=burn)),
}

C_cache = {name: autocorr(ts, max_lag=120) for name, ts in trajectories.items()}

rows = []
for name, C in C_cache.items():
    pc2 = parity_contrast(C, 2)
    pc4 = parity_contrast(C, 4)
    pc6 = parity_contrast(C, 6)
    m4 = m4_index(C, max_lag_used=60)
    rows.append({
        'signal': name,
        'parity_contrast_p2': float(pc2),
        'parity_contrast_p4': float(pc4),
        'parity_contrast_p6': float(pc6),
        'm4_index': float(m4)
    })

# Save JSON
outdir = Path('../../shared_agora/artifacts/parity_blindness_demonstration')
outdir.mkdir(parents=True, exist_ok=True)
(outdir / 'audit_table.json').write_text(json.dumps(rows, indent=2))

print(json.dumps(rows, indent=2))

# Formal test: theorem predictions
C_p4 = C_cache['period-4 logistic r=3.50']
C_p2 = C_cache['period-2 logistic r=3.20']
C_decoy = C_cache['period-2 decoy square']
C_canon = C_cache['canonical r=3.865']

# Theorem: parity_contrast(p) = mean_even - mean_odd for any even p, tested for p=2,4,6
def even_minus_odd(C, max_lag=60):
    evens = [C[i] for i in range(1, max_lag+1) if i % 2 == 0]
    odds  = [C[i] for i in range(1, max_lag+1) if i % 2 == 1]
    return np.mean(evens) - np.mean(odds)

theorem_rows = []
for name, C in C_cache.items():
    baseline = even_minus_odd(C)
    theorem_rows.append({
        'signal': name,
        'even_minus_odd': float(baseline),
        'pc2_diff': float(parity_contrast(C, 2) - baseline),
        'pc4_diff': float(parity_contrast(C, 4) - baseline),
        'pc6_diff': float(parity_contrast(C, 6) - baseline),
    })
(outdir / 'theorem_check.json').write_text(json.dumps(theorem_rows, indent=2))
print("\nTheorem-check (pc(p) - [mean_even C - mean_odd C]):")
print(json.dumps(theorem_rows, indent=2))

# Linear-discrimination sanity: M4 separates true period-4 from decoy and nulls
fig, axs = plt.subplots(1, 2, figsize=(10, 4))
labels = [r['signal'] for r in rows]
pc4_vals = [r['parity_contrast_p4'] for r in rows]
m4_vals = [r['m4_index'] for r in rows]
axs[0].barh(range(len(labels)), pc4_vals, color='C0')
axs[0].set_yticks(range(len(labels)))
axs[0].set_yticklabels(labels)
axs[0].set_xlabel('parity_contrast(p=4)')
axs[0].set_title('Original metric (blind)')
axs[0].set_xlim(-0.1, 1.1)
axs[1].barh(range(len(labels)), m4_vals, color='C2')
axs[1].set_yticks(range(len(labels)))
axs[1].set_yticklabels(labels)
axs[1].set_xlabel('M4 corrected residue-class index')
axs[1].set_title('Residue-class detector')
axs[1].set_xlim(-0.05, 0.5)
plt.tight_layout()
fig.savefig(outdir / 'parity_blindness_comparison.png', dpi=150)
print(f"\nArtifacts saved to {outdir}")
