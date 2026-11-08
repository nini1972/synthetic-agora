#!/usr/bin/env python3
"""Targeted robustness test for EMP-191: noise and norm variation."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import spearmanr
from scipy.spatial.distance import cdist
import sys, os

sys.path.insert(0, os.path.expanduser('~/colony_lib'))
from colony_lib.datasets import load_dataset

BANDS = {
    'Delta': (1, 3),
    'Theta': (4, 7),
    'Alpha': (8, 12),
    'Beta': (13, 30),
    'Gamma': (31, 44),
}
FREQ_CTR = {'Delta': 2.0, 'Theta': 5.5, 'Alpha': 10.0, 'Beta': 21.5, 'Gamma': 37.5}

def bandpass(x, fs, lo, hi, order=4):
    sos = signal.butter(order, [lo, hi], btype='band', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x)

def embed(x, m, tau):
    N = len(x) - (m - 1) * tau
    return np.vstack([x[i:i + N] for i in range(0, m * tau, tau)]).T

def diag_lengths(R):
    N = R.shape[0]
    lengths = []
    for k in range(1, N):
        diag = np.diag(R, k=k)
        run = 0
        for v in diag:
            if v:
                run += 1
            else:
                if run >= 2:
                    lengths.append(run)
                run = 0
        if run >= 2:
            lengths.append(run)
    return np.array(lengths, dtype=int)

def shannon_ent(lengths):
    if len(lengths) == 0:
        return 0.0
    vals, counts = np.unique(lengths, return_counts=True)
    p = counts / counts.sum()
    return -np.sum(p * np.log2(p + 1e-12))

def run_one(x, fs, band, norm, rr_target=0.05):
    y = bandpass(x, fs, band[0], band[1])
    y = (y - y.mean()) / y.std()
    Y = embed(y, m=3, tau=2)
    Y = (Y - Y.mean(axis=0)) / Y.std(axis=0)
    D = cdist(Y, Y, metric=norm)
    triu = D[np.triu_indices_from(D, k=1)]
    eps = np.percentile(triu, rr_target * 100.0)
    R = (D <= eps).astype(np.uint8)
    ent = shannon_ent(diag_lengths(R))
    return float(ent)

def main():
    np.random.seed(7)
    ds = load_dataset('neural_eeg')
    fs = ds.sampling_rate
    x = np.asarray(ds['AF3'], dtype=float)[:4096]
    configs, results = [], []
    for noise_std in [0.0, 0.2, 0.5]:
        for norm in ['chebyshev', 'euclidean']:
            xn = x + np.random.normal(0, noise_std, x.shape)
            ents = {}
            for name, band in BANDS.items():
                ents[name] = run_one(xn, fs, band, norm)
            freqs = [FREQ_CTR[n] for n in BANDS]
            vals = [ents[n] for n in BANDS]
            rho, pval = spearmanr(freqs, vals)
            configs.append({'noise_std': noise_std, 'norm': norm})
            results.append({'ents': ents, 'rho': float(rho), 'pvalue': float(pval)})
            print(f"noise={noise_std:.1f} norm={norm}: rho={rho:.3f} p={pval:.3g}")
    rhos = np.array([r['rho'] for r in results])
    summary = {
        'mean_rho': float(np.mean(rhos)),
        'min_rho': float(np.min(rhos)),
        'max_rho': float(np.max(rhos)),
        'fraction_negative': float(np.mean(rhos < 0)),
    }
    out = {'configs': configs, 'results': results, 'summary': summary}
    with open('hyp131_robustness_targeted.json', 'w') as f:
        json.dump(out, f, indent=2)
    # plot
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = {'Delta': '#1f77b4', 'Theta': '#2ca02c', 'Alpha': '#ff7f0e', 'Beta': '#d62728', 'Gamma': '#9467bd'}
    xtick = 0
    labels, pos = [], []
    for cfg, res in zip(configs, results):
        for i, name in enumerate(BANDS):
            ax.bar(xtick + i, res['ents'][name], color=colors[name], alpha=0.8)
        labels.append(f"σ={cfg['noise_std']:.1f}\n{cfg['norm'][:4]}")
        pos.append(xtick + 2)
        xtick += 6
    ax.set_xticks(pos)
    ax.set_xticklabels(labels)
    ax.set_ylabel('matched diagonal entropy ENT')
    ax.set_title('EMP-191 targeted robustness: ENT decreases with EEG band frequency')
    handles = [plt.Rectangle((0,0),1,1, color=colors[n]) for n in BANDS]
    ax.legend(handles, list(BANDS), loc='upper right')
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig('hyp131_robustness_targeted.png')
    print('saved hyp131_robustness_targeted.json/.png')
    print('summary:', summary)

if __name__ == '__main__':
    main()
