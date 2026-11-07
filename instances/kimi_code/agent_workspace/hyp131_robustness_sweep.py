#!/usr/bin/env python3
"""
Robustness sweep for HYP-131 / EMP-191.
Check whether the standardized matched-RR entropy trend (ENT decreases with band
center frequency) is stable across m, tau, norm, EEG channel, filter order, and noise.
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import spearmanr
import sys
import os

sys.path.insert(0, os.path.expanduser('~/colony_lib'))
from colony_lib.datasets import load_dataset

def bandpass(x, fs, lo, hi, order=4):
    sos = signal.butter(order, [lo, hi], btype='band', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x)

def embed(x, m, tau):
    N = len(x) - (m - 1) * tau
    return np.array([x[i:i + N] for i in range(0, m * tau, tau)]).T

def recurrence_matrix(Y, eps, norm):
    if norm == 'chebyshev':
        D = np.max(np.abs(Y[:, None, :] - Y[None, :, :]), axis=2)
    elif norm == 'euclidean':
        D = np.linalg.norm(Y[:, None, :] - Y[None, :, :], axis=2)
    else:
        raise ValueError(norm)
    return (D <= eps).astype(np.uint8)

def diag_line_dists(R):
    N = R.shape[0]
    # lengths of diagonal lines excluding main diagonal (LOI)
    lengths = []
    for k in range(1, N):
        cnt = 0
        for i in range(N - k):
            if R[i, i + k]:
                cnt += 1
            else:
                if cnt >= 2:
                    lengths.append(cnt)
                cnt = 0
        if cnt >= 2:
            lengths.append(cnt)
    return np.array(lengths)

def entropy_from_lengths(lengths):
    if len(lengths) == 0:
        return 0.0
    vals, counts = np.unique(lengths, return_counts=True)
    p = counts / counts.sum()
    return -np.sum(p * np.log2(p))

def compute_matched_values(x, fs, band, m, tau, eps_target, norm, order):
    y = bandpass(x, fs, band[0], band[1], order=order)
    # standardize embedded space
    y = (y - y.mean()) / y.std()
    Y = embed(y, m, tau)
    Y = (Y - Y.mean(axis=0)) / Y.std(axis=0)
    lo, hi = 1e-6, y.std() * 10
    target = eps_target
    for _ in range(30):
        mid = (lo + hi) / 2
        R = recurrence_matrix(Y, mid, norm)
        rr = (R.sum() - R.shape[0]) / (R.shape[0] * (R.shape[0] - 1))
        if rr < target:
            lo = mid
        else:
            hi = mid
    eps_final = (lo + hi) / 2
    R = recurrence_matrix(Y, eps_final, norm)
    lengths = diag_line_dists(R)
    ent = entropy_from_lengths(lengths)
    return eps_final, ent

BANDS = {
    'Delta': (1, 3),
    'Theta': (4, 7),
    'Alpha': (8, 12),
    'Beta': (13, 30),
    'Gamma': (31, 44),
}
FREQ_CTR = {'Delta': 2.0, 'Theta': 5.5, 'Alpha': 10.0, 'Beta': 21.5, 'Gamma': 37.5}

def run_sweep():
    ds = load_dataset('neural_eeg')
    print('Dataset keys:', list(ds.keys()))
    fs = ds['fs']
    channels = [c for c in ds['channel_names'] if c in ds] or ['channel_0']
    if 'data' in ds:
        data = ds['data']
        channels = list(range(data.shape[1]))
    results = []
    configs = []
    for channel in [0, 1, 2, 3]:
        x = data[:4096, channel] if channel < data.shape[1] else None
        if x is None:
            continue
        for noise_std in [0.0, 0.1, 0.2]:
            xn = x + np.random.normal(0, noise_std, size=x.shape)
            for order in [4, 6]:
                for norm in ['chebyshev', 'euclidean']:
                    for m in [3, 4]:
                        for tau in [1, 2, 3]:
                            ents = {}
                            for name, band in BANDS.items():
                                _, ent = compute_matched_values(xn, fs, band, m, tau, 0.05, norm, order)
                                ents[name] = ent
                            freqs = [FREQ_CTR[n] for n in BANDS]
                            vals = [ents[n] for n in BANDS]
                            rho, _ = spearmanr(freqs, vals)
                            configs.append({'channel': channel, 'noise_std': noise_std, 'filter_order': order, 'norm': norm, 'm': m, 'tau': tau})
                            results.append({'ents': ents, 'rho': rho})
                            print(f"ch{channel} noise{noise_std} ord{order} {norm} m{m} tau{tau}: rho={rho:.3f}")
    return configs, results

if __name__ == '__main__':
    np.random.seed(42)
    configs, results = run_sweep()
    rhos = [r['rho'] for r in results]
    print(f"\nRobustness sweep: rho mean={np.mean(rhos):.3f} min={np.min(rhos):.3f} max={np.max(rhos):.3f} frac_negative={np.mean(np.array(rhos) < 0):.2f}")
    out = {'configs': configs, 'results': results, 'summary': {'mean_rho': float(np.mean(rhos)), 'min_rho': float(np.min(rhos)), 'max_rho': float(np.max(rhos)), 'fraction_negative': float(np.mean(np.array(rhos) < 0))}}
    with open('hyp131_robustness_sweep.json', 'w') as f:
        json.dump(out, f, indent=2)
    # histogram
    plt.figure(figsize=(6, 4))
    plt.hist(rhos, bins=20, edgecolor='k')
    plt.axvline(0, color='r', ls='--')
    plt.xlabel('Spearman rho(ENT vs frequency) at matched RR=5%')
    plt.ylabel('count')
    plt.title('HYP-131 robustness sweep over m/tau/norm/channel/order/noise')
    plt.tight_layout()
    plt.savefig('hyp131_robustness_sweep.png')
    print('saved hyp131_robustness_sweep.json and .png')
