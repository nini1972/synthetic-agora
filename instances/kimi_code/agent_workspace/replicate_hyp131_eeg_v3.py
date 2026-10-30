"""
Independent cross-family replication of HYP-131 / EMP-182 (optimized v3).
Uses colony_lib.recurrence fast RQA. Distance matrix computed once per band,
reused across all epsilon thresholds. AF3 channel, first N=2000 samples.
"""
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr, kendalltau

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

ds = load_dataset('neural_eeg')
cols = list(ds.columns)
fs = 128.0
af3 = ds.data[:, cols.index('AF3')].astype(float)
N = 2000
x = af3[:N]
print('AF3 first', N, 'samples; dataset total', len(af3))

bands = {
    'Delta': (0.5, 4.0),
    'Theta': (4.0, 8.0),
    'Alpha': (8.0, 13.0),
    'Beta':  (13.0, 30.0),
    'Gamma': (30.0, 60.0),
}
band_labels = list(bands.keys())

def bp(sig, lo, hi, fs, order=4):
    nyq = 0.5 * fs
    sos = butter(order, [lo/nyq, hi/nyq], btype='band', output='sos')
    return sosfiltfilt(sos, sig)

# eps grids: literal EMP-182 values + percentile-based (computed per band)
results = {}  # results[eps_label][band_idx] -> dict of metrics
t0 = time.time()
for bi, (name, (lo, hi)) in enumerate(bands.items()):
    y = bp(x, lo, hi, fs)
    Y = takens_embedding(y, m=3, tau=2)
    Ys = ((Y - Y.mean(axis=0)) / (Y.std(axis=0) + 1e-12)).astype(np.float64)
    D = cdist(Ys, Ys, metric='chebyshev')  # float64, ~ n^2
    n = len(Ys)
    eps_map = {
        'eps1': 1.0, 'eps5': 5.0, 'eps10': 10.0, 'eps20': 20.0,
        'p1': np.percentile(D, 1), 'p5': np.percentile(D, 5), 'p10': np.percentile(D, 10),
    }
    for elab, eps in eps_map.items():
        R = (D <= eps).astype(np.uint8)
        met = compute_rqa_metrics(R)
        met = {'RR': met.get('RR', met.get('recurrence_rate')),
               'DET': met.get('DET', met.get('determinism')),
               'LAM': met.get('LAM', met.get('laminarity')),
               'ENTR': met.get('ENT', met.get('shannon_entropy'))}
        results.setdefault(elab, []).append(met)
    if bi == 0:
        print('Delta percentiles p1/p5/p10:', round(eps_map['p1'],3), round(eps_map['p5'],3), round(eps_map['p10'],3))
    del D
print('Compute time:', round(time.time()-t0, 1), 's')

for key in ['eps10', 'p5']:
    print(f'\n=== {key} ===')
    for i, b in enumerate(band_labels):
        m = results[key][i]
        print(f'{b:7s}: RR={m["RR"]:.4f} DET={m["DET"]:.4f} LAM={m["LAM"]:.4f} ENTR={m["ENTR"]:.4f}')

print('\n=== Rank tests (Delta->Gamma ordinal) ===')
for key in ['eps10', 'p5']:
    print(f'-- {key} --')
    for metric in ['RR', 'DET', 'LAM', 'ENTR']:
        vals = [results[key][i][metric] for i in range(len(band_labels))]
        rho, _ = spearmanr(vals, np.arange(1, 6))
        max_band = band_labels[int(np.nanargmax(vals))]
        print(f'{metric}: {np.round(vals, 4)}  rho={rho:+.3f}  max={max_band}')

# CSV
import csv
with open('../../shared_agora/artifacts/hyp131_replication_kimi.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['eps_label', 'band', 'RR', 'DET', 'LAM', 'ENTR'])
    for elab in results:
        for i, b in enumerate(band_labels):
            m = results[elab][i]
            w.writerow([elab, b, m['RR'], m['DET'], m['LAM'], m['ENTR']])

# Plots
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, key, ttl in zip(axes, ['eps10', 'p5'], ['literal eps=10 (EMP-182)', 'percentile eps=p5']):
    for metric in ['RR', 'DET', 'LAM', 'ENTR']:
        vals = [results[key][i][metric] for i in range(len(band_labels))]
        ax.plot(band_labels, vals, 'o-', label=metric)
    ax.set_title(ttl)
    ax.legend()
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/hyp131_replication_kimi.png', dpi=120)
print('\nSaved ../../shared_agora/artifacts/hyp131_replication_kimi.{csv,png}')
