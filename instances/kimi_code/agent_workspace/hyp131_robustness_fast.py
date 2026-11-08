#!/usr/bin/env python3
"""
Fast robustness sweep for EMP-191 (HYP-131).
Uses exact percentile thresholding for matched RR to avoid repeated O(N^2) operations.
"""
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

def bandpass(x, fs, lo, hi, order):
    sos = signal.butter(order, [lo, hi], btype='band', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x)

def embed(x, m, tau):
    N = len(x) - (m - 1) * tau
    return np.vstack([x[i:i + N] for i in range(0, m * tau, tau)]).T

def diag_line_dists(R):
    N = R.shape[0]
    lengths = []
    for k in range(1, N):
        cnt = 0
        diag = np.diag(R, k=k)
        for val in diag:
            if val:
                cnt += 1
            else:
                if cnt >= 2:
                    lengths.append(cnt)
                cnt = 0
        if cnt >= 2:
            lengths.append(cnt)
    return np.array(lengths, dtype=int)

def entropy_len(lengths):
    if len(lengths) == 0:
        return 0.0
    vals, counts = np.unique(lengths, return_counts=True)
    p = counts / counts.sum()
    return -np.sum(p * np.log2(p))

def metrics_for_band(x, fs, band, m, tau, norm, order, rr_target):
    y = bandpass(x, fs, band[0], band[1], order)
    y = (y - y.mean()) / y.std()
    Y = embed(y, m, tau)
    Y = (Y - Y.mean(axis=0)) / Y.std(axis=0)
    D = cdist(Y, Y, metric=norm)
    # upper triangular distances excluding diagonal
    triu = D[np.triu_indices_from(D, k=1)]
    eps = np.percentile(triu, 100.0 * rr_target)
    R = (D <= eps).astype(np.uint8)
    lengths = diag_line_dists(R)
    ent = entropy_len(lengths)
    return ent

def main():
    np.random.seed(42)
    ds = load_dataset('neural_eeg')
    fs = ds.sampling_rate
    channel = 'AF3'
    x_full = np.asarray(ds[channel], dtype=float)
    x = x_full[:4096]
    configs = []
    results = []
    for noise_std in [0.0, 0.1, 0.2, 0.5]:
        for order in [4, 6, 8]:
            for norm in ['chebyshev', 'euclidean']:
                for tau in [1, 2, 3]:
                    m = 3
                    xn = x + np.random.normal(0, noise_std, size=x.shape)
                    ents = {}
                    for name, band in BANDS.items():
                        ent = metrics_for_band(xn, fs, band, m, tau, norm, order, rr_target=0.05)
                        ents[name] = float(ent)
                    freqs = [FREQ_CTR[n] for n in BANDS]
                    vals = [ents[n] for n in BANDS]
                    rho, _ = spearmanr(freqs, vals)
                    configs.append({'channel': channel, 'noise_std': noise_std, 'filter_order': order, 'norm': norm, 'm': m, 'tau': tau})
                    results.append({'ents': ents, 'rho': float(rho)})
                    print(f"noise{noise_std:.1f} ord{order} {norm} tau{tau}: rho={rho:.3f}")
    rhos = np.array([r['rho'] for r in results])
    summary = {
        'mean_rho': float(np.mean(rhos)),
        'min_rho': float(np.min(rhos)),
        'max_rho': float(np.max(rhos)),
        'fraction_negative': float(np.mean(rhos < 0)),
    }
    out = {'configs': configs, 'results': results, 'summary': summary}
    with open('hyp131_robustness_fast.json', 'w') as f:
        json.dump(out, f, indent=2)
    plt.figure(figsize=(6, 4))
    plt.hist(rhos, bins=15, edgecolor='k', alpha=0.75)
    plt.axvline(0, color='r', ls='--', label='no trend')
    plt.xlabel(r'Spearman $\rho$(ENT vs frequency) at matched RR=5%')
    plt.ylabel('count')
    plt.title(f'Robustness sweep (AF3, m=3, orders 4/6/8, tau 1/2/3, noise 0-0.5)\n' f'$\\bar\\rho$={summary["mean_rho"]:.3f}, min={summary["min_rho"]:.3f}, max={summary["max_rho"]:.3f}, neg%={summary["fraction_negative"]:.1%}')
    plt.tight_layout()
    plt.savefig('hyp131_robustness_fast.png')
    print('saved hyp131_robustness_fast.json/.png')
    print('summary:', summary)

if __name__ == '__main__':
    main()
