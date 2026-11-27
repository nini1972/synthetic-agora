import numpy as np
import warnings, json, time
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scipy import signal
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import compute_rqa_metrics
from colony_lib.persistence import StageTracker

# Load EEG data
raw = load_dataset('neural_eeg')
fs = raw.sampling_rate
X = raw.signal_matrix()  # (N, 14)
channels = raw.signal_columns
N = 1500
X = X[:N, :]

bands = {
    'Delta': (0.5, 4.0),
    'Theta': (4.0, 8.0),
    'Alpha': (8.0, 13.0),
    'Beta':  (13.0, 30.0),
    'Gamma': (30.0, 45.0),
}
RR_targets = [0.01, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.70, 0.90]
norms = ['chebyshev', 'euclidean']
m, tau = 3, 1


def bandpass(x, fs, lo, hi):
    sos = signal.butter(4, [lo, hi], btype='band', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x)


def embed(x, m, tau):
    n = len(x) - (m - 1) * tau
    return np.array([x[i:i + (m - 1) * tau + 1:tau] for i in range(n)])


# Precompute embeddings per channel/band
print('Precomputing embeddings...')
embeddings = {}
for ci, ch in enumerate(channels):
    x_raw = X[:, ci]
    for band_name, (lo, hi) in bands.items():
        x_filt = bandpass(x_raw, fs, lo, hi)
        embeddings[(ci, band_name)] = embed(x_filt, m, tau)

# Stage tracker for resumability
stage_name = 'emp250_replication_kimi_fast'
tracker = StageTracker(stage_name)
done = set(tracker.get_all_stages())
print(f'Done stages: {len(done)}')

total_start = time.time()
for ci, ch in enumerate(channels):
    for band_name in bands.keys():
        emb = embeddings[(ci, band_name)]
        n_embed = emb.shape[0]
        # Compute both norms once
        D_cheb = cdist(emb, emb, metric='chebyshev').astype(np.float32)
        D_euc = cdist(emb, emb, metric='euclidean').astype(np.float32)
        for norm, D in [('chebyshev', D_cheb), ('euclidean', D_euc)]:
            key = f'{ch}_{band_name}_{norm}'
            if key in done:
                print(f'SKIP {key}')
                continue
            flat = D[np.triu_indices_from(D, k=1)]
            group_results = []
            for RR_t in RR_targets:
                eps = np.percentile(flat, RR_t * 100).astype(np.float64)
                R = (D <= eps).astype(np.uint8)
                R = np.maximum(R, R.T)  # symmetrise
                met = compute_rqa_metrics(R)
                group_results.append({
                    'channel': ch,
                    'channel_idx': ci,
                    'band': band_name,
                    'norm': norm,
                    'RR_target': RR_t,
                    'RR_actual': float(met['RR']),
                    'DET': float(met['DET']),
                    'LAM': float(met['LAM']),
                    'ENT': float(met['ENT']),
                    'Lmax': float(met['Lmax']),
                    'eps': float(eps),
                    'n_embed': n_embed,
                })
            tracker.save_stage(key, group_results)
            print(f'DONE {key} in {time.time()-total_start:.1f}s total elapsed')

# Collect all results
all_results = []
for key in tracker.get_all_stages():
    all_results.extend(tracker.load_stage(key))

out_json = 'replicate_emp250_fast_results.json'
with open(out_json, 'w') as f:
    json.dump({'N': N, 'm': m, 'tau': tau, 'bands': bands, 'RR_targets': RR_targets,
               'norms': norms, 'channels': channels, 'results': all_results}, f, indent=2)

# Aggregate and plot
import pandas as pd
df = pd.DataFrame(all_results)
summary = df.groupby(['band', 'norm', 'RR_target']).agg(
    RR_actual=('RR_actual', 'median'),
    ENT_median=('ENT', 'median'),
    ENT_iqr=('ENT', lambda s: np.percentile(s, 75) - np.percentile(s, 25)),
    DET_median=('DET', 'median'),
    LAM_median=('LAM', 'median'),
).reset_index()

fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
colors = plt.cm.tab10(np.linspace(0, 1, len(bands)))
for ax, norm in zip(axes, norms):
    for band_name, color in zip(bands.keys(), colors):
        sub = summary[(summary['band'] == band_name) & (summary['norm'] == norm)].sort_values('RR_target')
        ax.plot(sub['RR_target'], sub['ENT_median'], marker='o', label=band_name, color=color)
        ax.fill_between(sub['RR_target'],
                        sub['ENT_median'] - 0.5 * sub['ENT_iqr'],
                        sub['ENT_median'] + 0.5 * sub['ENT_iqr'],
                        color=color, alpha=0.15)
    ax.set_xlabel('Target Recurrence Rate (RR)')
    ax.set_ylabel('Median RQA ENT across channels')
    ax.set_title(f'EMP-250 replication — {norm} norm')
    ax.set_xscale('log')
    ax.legend(title='Band')
    ax.grid(True, ls='--', alpha=0.4)
plt.tight_layout()
out_png = 'replicate_emp250_fast.png'
plt.savefig(out_png, dpi=150)
print(f'Saved {out_json} and {out_png}. Total elapsed {time.time()-total_start:.1f}s')
