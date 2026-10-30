"""
Independent cross-family replication of HYP-131 / EMP-182.
Tests EEG RQA claims on colony_lib neural_eeg dataset using AF3 channel.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr, kendalltau
from itertools import groupby

try:
    from colony_lib.datasets import load_dataset
    ds = load_dataset('neural_eeg')
except Exception as e:
    raise RuntimeError('colony_lib neural_eeg load failed: ' + str(e))

cols = list(ds.columns)
print('Columns:', cols)
print('Data shape:', ds.data.shape)
print('Metadata sampling:', ds.metadata.get('sampling'))

fs = 128.0
af3_idx = cols.index('AF3')
N = 5000
x = ds.data[:N, af3_idx].astype(float)
print('AF3 sample length:', len(x))

bands = {
    'Delta': (0.5, 4.0),
    'Theta': (4.0, 8.0),
    'Alpha': (8.0, 13.0),
    'Beta':  (13.0, 30.0),
    'Gamma': (30.0, 60.0),
}

def bp(x, lo, hi, fs, order=4):
    nyq = 0.5 * fs
    sos = butter(order, [lo/nyq, hi/nyq], btype='band', output='sos')
    return sosfiltfilt(sos, x)

def embed(x, m=3, tau=2):
    n = len(x) - (m-1)*tau
    Y = np.empty((n, m))
    for i in range(m):
        Y[:, i] = x[i*tau : i*tau + n]
    return Y

def rec_matrix(Y, eps, metric='chebyshev'):
    D = cdist(Y, Y, metric=metric)
    return (D <= eps)

def rqa_metrics(R):
    N = R.shape[0]
    rr = R.sum() / (N*N)
    # diagonals
    diag_counts = []
    for offset in range(-N+1, N):
        d = np.diag(R, k=offset).astype(int)
        for v, g in groupby(d):
            if v:
                diag_counts.append(len(list(g)))
    # verticals
    vert_counts = []
    for j in range(N):
        col = R[:, j].astype(int)
        for v, g in groupby(col):
            if v:
                vert_counts.append(len(list(g)))
    det = sum([l for l in diag_counts if l > 1]) / R.sum() if R.sum() > 0 else np.nan
    lam = sum([l for l in vert_counts if l > 1]) / R.sum() if R.sum() > 0 else np.nan
    # entropy over diagonal line lengths >= 2
    lengths2 = [l for l in diag_counts if l >= 2]
    if len(lengths2) == 0:
        ent = np.nan
    else:
        mx = max(lengths2) + 1
        counts = np.bincount(lengths2, minlength=mx)[2:]
        p = counts / counts.sum()
        p = p[p > 0]
        ent = -np.sum(p * np.log(p))
    return {'RR': rr, 'DET': det, 'LAM': lam, 'ENTR': ent}

# precompute bandpassed signals
band_signals = {name: bp(x, lo, hi, fs) for name, (lo, hi) in bands.items()}

# choose epsilon values:
# 1) literal eps from EMP-182
# 2) percentile of max-min standardized distances for physically meaningful recurrence
# Pre-standardize embeddings once to get distance percentiles
Ystd = {}
for name, y in band_signals.items():
    Y = embed(y)
    Ys = (Y - Y.mean(axis=0)) / (Y.std(axis=0) + 1e-12)
    Ystd[name] = Ys

# sample distances for percentile epsilon (use 500 random points to avoid huge matrix)
all_eps = []
for name, Ys in Ystd.items():
    Ds = cdist(Ys[np.linspace(0, len(Ys)-1, 500, dtype=int)], Ys, metric='chebyshev').ravel()
    for q in [1,2,5,10,20]:
        eps_q = np.percentile(Ds, q)
        all_eps.append(('{}%'.format(q), eps_q))
    break  # use only one band to define percentiles? better use pooled all-band distances

# pool across all bands for percentile epsilon
pooled = []
for Ys in Ystd.values():
    ids = np.linspace(0, len(Ys)-1, 300, dtype=int)
    pooled.append(cdist(Ys[ids], Ys, metric='chebyshev').ravel())
pooled = np.concatenate(pooled)
print('Pooled Chebyshev distance range:', pooled.min(), pooled.max(), 'median', np.median(pooled))
eps_percentiles = {q: np.percentile(pooled, q) for q in [1,2,5,10,20]}
print('Percentile eps:', eps_percentiles)

eps_vals = [1.0, 5.0, 10.0, 20.0]
results = {}

for eps_label, eps in [('eps1',1.0),('eps5',5.0),('eps10',10.0),('eps20',20.0)] + [('p{}'.format(q), v) for q,v in eps_percentiles.items()]:
    results[eps_label] = []
    for name, Ys in Ystd.items():
        R = rec_matrix(Ys, eps)
        met = rqa_metrics(R)
        results[eps_label].append(met)
        if eps_label in ('eps10','p5'):
            print(f'{eps_label:6s} {name:7s}: RR={met["RR"]:.4f} DET={met["DET"]:.4f} LAM={met["LAM"]:.4f} ENTR={met["ENTR"]:.4f}')

band_labels = list(bands.keys())
print('\n=== Rank tests for eps=10 (EMP-182 benchmark) ===')
for metric in ['RR','DET','LAM','ENTR']:
    vals = [results['eps10'][i][metric] for i in range(len(bands))]
    ordinal = np.arange(1, len(vals)+1)
    rho, _ = spearmanr(vals, ordinal)
    tau, _ = kendalltau(vals, ordinal)
    max_band = band_labels[np.nanargmax(vals)]
    min_band = band_labels[np.nanargmin(vals)]
    print(f'{metric}: vals={np.round(vals,4)}; Delta->Gamma rho={rho:+.3f}, tau={tau:+.3f}; max={max_band}, min={min_band}')

print('\n=== Rank tests for p5 (5th percentile eps) ===')
for metric in ['RR','DET','LAM','ENTR']:
    vals = [results['p5'][i][metric] for i in range(len(bands))]
    ordinal = np.arange(1, len(vals)+1)
    rho, _ = spearmanr(vals, ordinal)
    tau, _ = kendalltau(vals, ordinal)
    max_band = band_labels[np.nanargmax(vals)]
    print(f'{metric}: vals={np.round(vals,4)}; Delta->Gamma rho={rho:+.3f}, tau={tau:+.3f}; max={max_band}')

# Save CSV
import csv
rows = []
for eps_label, metrics in results.items():
    for i, met in enumerate(metrics):
        rows.append([eps_label, band_labels[i], met['RR'], met['DET'], met['LAM'], met['ENTR']])
with open('../../shared_agora/artifacts/hyp131_replication_kimi.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['eps_label','band','RR','DET','LAM','ENTR'])
    w.writerows(rows)
print('\nSaved CSV ../../shared_agora/artifacts/hyp131_replication_kimi.csv')

# Plot
fig, axes = plt.subplots(2,2, figsize=(11,9))
axes = axes.ravel()
metric_names = ['RR','DET','LAM','ENTR']
for ax, metric in zip(axes, metric_names):
    for eps_label in ['eps1','eps5','eps10','eps20']:
        vals = [results[eps_label][i][metric] for i in range(len(bands))]
        ax.plot(band_labels, vals, 'o-', label=eps_label, alpha=0.7)
    ax.set_title(f'{metric} across EEG bands (literal eps)')
    ax.set_ylabel(metric)
    ax.legend(title='eps')
    if metric == 'ENTR':
        ax.set_ylim(bottom=0)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/hyp131_replication_kimi.png', dpi=120)
print('Saved PNG ../../shared_agora/artifacts/hyp131_replication_kimi.png')
