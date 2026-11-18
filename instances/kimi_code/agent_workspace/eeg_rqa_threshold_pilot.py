"""
Pilot sweep: RQA frequency correlations as a function of recurrence threshold RR,
comparing Euclidean vs Chebyshev norms on EEG channel AF3.
Tests the sign-flip hypothesis raised by SYN-064 in #sanity-check.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import spearmanr
import json

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

fs = 128.0
bands = [
    ('Delta', 0.5, 4.0),
    ('Theta', 4.0, 8.0),
    ('Alpha', 8.0, 13.0),
    ('Beta', 13.0, 30.0),
    ('Gamma', 30.0, 45.0),
]
band_centers = [0.5*(l+h) for _,l,h in bands]

rrs = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.80, 0.90, 0.95]
metrics = ['DET','LAM','ENT']
norm_names = ['euclidean', 'chebyshev']

ds = load_dataset('neural_eeg')
sig = ds['AF3'][:4096].astype(float)
sig = sig - np.mean(sig)

# Pre-filter signals once per band
filtered = {}
for name, low, high in bands:
    sos = signal.butter(4, [low, high], btype='band', output='sos', fs=fs)
    f = signal.sosfiltfilt(sos, sig)
    f = f - np.mean(f)
    f = f / (np.std(f) + 1e-12)
    filtered[name] = f

records = []
for metric in norm_names:
    for rr in rrs:
        row = {'norm': metric, 'RR_threshold': rr}
        vals = {m: [] for m in metrics}
        for name, _, _ in bands:
            emb = takens_embedding(filtered[name], m=3, tau=2)
            R = recurrence_matrix(emb, metric=metric, target_rr=rr)
            q = compute_rqa_metrics(R, min_diag_len=2, min_vert_len=2)
            for m in metrics:
                vals[m].append(q[m])
        for m in metrics:
            rho, _ = spearmanr(band_centers, vals[m])
            row[m] = vals[m]
            row[m+'_rho'] = float(rho)
            # also compute ga_frac of ENT_Gamma < ENT_Alpha as in SYN-064
            if m == 'ENT':
                row['ENT_gamma_lt_alpha'] = float(int(vals[m][-1] < vals[m][-2]))
        records.append(row)
        print(metric, rr, {m: row[m+'_rho'] for m in metrics})

# Plot
fig, axes = plt.subplots(1, 3, figsize=(14,4))
for i, m in enumerate(metrics):
    ax = axes[i]
    for metric in norm_names:
        subset = [r for r in records if r['norm']==metric]
        x = [r['RR_threshold'] for r in subset]
        y = [r[m+'_rho'] for r in subset]
        ax.plot(x, y, 'o-', label=metric)
    ax.axhline(0, color='k', ls='--', lw=0.5)
    ax.set_xscale('log')
    ax.set_xlabel('Recurrence threshold RR')
    ax.set_ylabel(f'Spearman rho(freq, {m})')
    ax.set_title(f'{m} correlation vs threshold')
    ax.legend()
axes[0].set_ylim(-1.05, 1.05)
plt.tight_layout()
png_path = '../../shared_agora/artifacts/eeg_rqa_threshold_pilot_moonshot.png'
json_path = '../../shared_agora/artifacts/eeg_rqa_threshold_pilot_moonshot.json'
plt.savefig(png_path, dpi=150)
with open(json_path,'w') as f:
    json.dump(records, f, indent=2, default=lambda o: o.tolist() if hasattr(o,'tolist') else o)
print('saved', png_path, json_path)
