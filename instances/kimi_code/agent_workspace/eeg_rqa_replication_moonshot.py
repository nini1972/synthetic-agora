"""
Independent replication of EMP-180: RQA of human EEG across canonical frequency bands.
Uses colony_lib neural_eeg dataset, channel AF3, Butterworth bandpass filters,
Takens embedding (m=3, tau=2), and fixed recurrence rate RR=5%.
"""
import os
import json
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import spearmanr

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

ds = load_dataset('neural_eeg')
sig = ds['AF3'][:4096].astype(float)
sig = sig - np.mean(sig)

results = []
embeddings = {}
for name, low, high in bands:
    sos = signal.butter(4, [low, high], btype='band', analog=False, output='sos', fs=fs)
    filtered = signal.sosfiltfilt(sos, sig)
    filtered = filtered - np.mean(filtered)
    filtered = filtered / (np.std(filtered) + 1e-12)

    emb = takens_embedding(filtered, m=3, tau=2)
    R = recurrence_matrix(emb, metric='euclidean', target_rr=0.05)
    metrics = compute_rqa_metrics(R, min_diag_len=2, min_vert_len=2)
    embeddings[name] = emb
    results.append({
        'band': name,
        'low': low,
        'high': high,
        'RR': float(metrics['RR']),
        'DET': float(metrics['DET']),
        'LAM': float(metrics['LAM']),
        'ENT': float(metrics['ENT']),
        'L': float(metrics['L']),
        'Lmax': float(metrics['Lmax']),
    })
    print(name, metrics['RR'], metrics['DET'], metrics['LAM'], metrics['ENT'])

df = {r['band']: r for r in results}
centers = [0.5*(r['low']+r['high']) for r in results]
ENTs = [r['ENT'] for r in results]
rho, p = spearmanr(centers, ENTs)
print('Spearman rho(freq, ENT) =', rho, 'p =', p)

fig, axes = plt.subplots(2, 3, figsize=(12, 7))
axes = axes.ravel()
for idx, (name, low, high) in enumerate(bands):
    if idx < 5:
        ax = axes[idx]
        emb = embeddings[name]
        ax.plot(emb[:2000, 0], emb[:2000, 1], alpha=0.5, lw=0.5)
        ax.set_title(f'{name} embedding')
        ax.set_xlabel('x(t)')
        ax.set_ylabel('x(t+tau)')

ax = axes[5]
ax.plot([r['band'] for r in results], [r['DET'] for r in results], 'o-', label='DET')
ax.plot([r['band'] for r in results], [r['LAM'] for r in results], 's-', label='LAM')
ax.set_ylabel('DET / LAM')
ax.set_xlabel('Band')
ax.legend()
ax.set_title(f'ENT rho={rho:.3f} (p={p:.3g})')

plt.tight_layout()
png_path = '../../shared_agora/artifacts/eeg_rqa_replication_moonshot.png'
json_path = '../../shared_agora/artifacts/eeg_rqa_replication_moonshot.json'
plt.savefig(png_path, dpi=150)

with open(json_path, 'w') as f:
    json.dump({'bands': results, 'spearman_rho_freq_ent': rho, 'spearman_p': p}, f, indent=2)
print('saved', png_path, json_path)
