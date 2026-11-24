import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
import json, warnings, time, os
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import recurrence_matrix, compute_rqa_metrics

warnings.filterwarnings('ignore')
np.random.seed(42)

ds = load_dataset('neural_eeg')
fs = ds.sampling_rate
X = ds.signal_matrix()  # (N, 14)
channels = ds.signal_columns
n_ch = X.shape[1]

bands = {
    'Delta': (1, 4),
    'Theta': (4, 8),
    'Alpha': (8, 13),
    'Beta':  (13, 30),
    'Gamma': (30, 50),
}
freq_centers = np.array([2.5, 6.0, 10.5, 21.5, 40.0])
RR_targets = [0.01, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.70, 0.90]
norms = ['chebyshev', 'euclidean']
m, tau = 3, 1
N = 1500

def bandpass(x, fs, lo, hi):
    sos = signal.butter(4, [lo, hi], btype='band', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x)

def takens_embed(x, m, tau):
    idx = np.arange(0, m*tau, tau)
    N = len(x) - (m-1)*tau
    return np.array([x[i:i+m*tau:tau] for i in range(N)])

# Precompute filtered signals per channel/band
print('Filtering...')
filtered = np.empty((N, n_ch, len(bands)))
for c in range(n_ch):
    for b, (name, (lo, hi)) in enumerate(bands.items()):
        xf = bandpass(X[:, c], fs, lo, hi)
        filtered[:, c, b] = xf[:N]

results = []
start_all = time.time()
for norm_name in norms:
    metric = norm_name
    for rr_target in RR_targets:
        t0 = time.time()
        rhos = []
        for c in range(n_ch):
            ent_vals = []
            det_vals = []
            lam_vals = []
            rr_actual = []
            for b, name in enumerate(bands.keys()):
                x = filtered[:, c, b]
                emb = takens_embed(x, m, tau)
                D = cdist(emb, emb, metric=metric)
                eps = np.percentile(D[np.isfinite(D)], rr_target*100)
                R = recurrence_matrix(emb, epsilon=eps, norm=metric)
                # ensure binary uint8
                if R.dtype != np.uint8:
                    R = (R > 0).astype(np.uint8)
                mets = compute_rqa_metrics(R)
                ent_vals.append(mets['ENT'])
                det_vals.append(mets['DET'])
                lam_vals.append(mets['LAM'])
                rr_actual.append(mets['RR'])
            rho_ent, _ = spearmanr(freq_centers, ent_vals)
            rho_det, _ = spearmanr(freq_centers, det_vals)
            rho_lam, _ = spearmanr(freq_centers, lam_vals)
            rhos.append({
                'channel': channels[c],
                'rho_ENT': float(rho_ent),
                'rho_DET': float(rho_det),
                'rho_LAM': float(rho_lam),
                'ENT': [float(v) for v in ent_vals],
                'DET': [float(v) for v in det_vals],
                'LAM': [float(v) for v in lam_vals],
                'RR_actual': [float(v) for v in rr_actual],
            })
        mean_rho_ent = float(np.mean([r['rho_ENT'] for r in rhos]))
        frac_neg = float(np.mean([r['rho_ENT'] < 0 for r in rhos]))
        gamma_lt_alpha = float(np.mean([r['ENT'][-1] < r['ENT'][2] for r in rhos]))
        results.append({
            'norm': norm_name,
            'RR_target': rr_target,
            'mean_rho_ENT': mean_rho_ent,
            'std_rho_ENT': float(np.std([r['rho_ENT'] for r in rhos])),
            'frac_negative_ENT': frac_neg,
            'frac_Gamma_lt_Alpha': gamma_lt_alpha,
            'per_channel': rhos,
        })
        print(f'{norm_name} RR={rr_target:.2f}: mean rho_ENT={mean_rho_ent:.3f}, frac_neg={frac_neg:.2f}, gamma<alpha={gamma_lt_alpha:.2f}, time={time.time()-t0:.1f}s')

print(f'Total time {time.time()-start_all:.1f}s')

# Summary JSON
with open('replicate_emp250_kimi.json', 'w') as f:
    json.dump({
        'm': m, 'tau': tau, 'N': N, 'fs': fs,
        'bands': list(bands.keys()),
        'freq_centers': freq_centers.tolist(),
        'RR_targets': RR_targets,
        'norms': norms,
        'results': results,
    }, f, indent=2)

# Plot
fig, axes = plt.subplots(1, 2, figsize=(12,5))
for ax, norm_name in zip(axes, norms):
    sub = [r for r in results if r['norm']==norm_name]
    rr = [r['RR_target'] for r in sub]
    ent_mean = [r['mean_rho_ENT'] for r in sub]
    ent_std = [r['std_rho_ENT'] for r in sub]
    frac_neg = [r['frac_negative_ENT'] for r in sub]
    ax.errorbar(rr, ent_mean, yerr=ent_std, marker='o', capsize=4, label='mean ρ(ENT,freq)')
    ax.plot(rr, frac_neg, marker='s', linestyle='--', label='frac ρ(ENT,freq)<0')
    ax.axhline(0, color='k', linewidth=0.8)
    ax.set_xscale('log')
    ax.set_xlabel('target RR')
    ax.set_ylabel('Spearman ρ / fraction')
    ax.set_title(f'{norm_name} norm')
    ax.set_ylim(-1.1, 1.1)
    ax.legend()
    ax.grid(True, which='both', ls=':')
fig.suptitle('Matched-RR sweep replication of EMP-250 (neural_eeg, N=1500, m=3, τ=1)')
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/emp250_replication_kimi.png', dpi=150)
plt.close()
print('Saved artifact ../../shared_agora/artifacts/emp250_replication_kimi.png')
