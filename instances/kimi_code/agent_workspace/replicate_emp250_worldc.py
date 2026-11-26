import numpy as np
import warnings, json
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scipy import signal
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import compute_rqa_metrics

# Load EEG data
raw = load_dataset('neural_eeg')
fs = raw.sampling_rate
X = raw.signal_matrix()  # (N, 14)
channels = raw.signal_columns
N = 1500
X = X[:N, :]

# EEG bands (Hz) matching EMP-250
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


def make_symmetric(R):
    # Use upper triangle and mirror to avoid counting the LOI twice if present.
    return np.maximum(R, R.T)


results = []
print(f"Starting EMP-250 replication: {len(channels)} channels x {len(bands)} bands x {len(RR_targets)} RR targets x {len(norms)} norms")

for ci, ch in enumerate(channels):
    x_raw = X[:, ci]
    for band_name, (lo, hi) in bands.items():
        x_filt = bandpass(x_raw, fs, lo, hi)
        emb = embed(x_filt, m, tau)
        n_embed = emb.shape[0]
        for norm in norms:
            D = cdist(emb, emb, metric=norm)
            # One distance percentile sweep per (channel, band, norm)
            flat = D[np.triu_indices_from(D, k=1)]
            percs = np.linspace(0.0, 100.0, 2001)
            q = np.percentile(flat, percs)
            for RR_t in RR_targets:
                # Find epsilon that gives target RR
                rr_curve = np.array([np.mean(flat <= eps) for eps in q])
                # Handle exact target by interpolation on the percentile axis
                if RR_t <= rr_curve.min():
                    eps = q[0]
                elif RR_t >= rr_curve.max():
                    eps = q[-1]
                else:
                    idx = np.searchsorted(rr_curve, RR_t)
                    # linear interpolation between (q[idx-1], rr_curve[idx-1]) and (q[idx], rr_curve[idx])
                    x1, y1 = rr_curve[idx - 1], q[idx - 1]
                    x2, y2 = rr_curve[idx], q[idx]
                    if x2 == x1:
                        eps = y1
                    else:
                        eps = y1 + (RR_t - x1) * (y2 - y1) / (x2 - x1)
                R = (D <= eps).astype(np.uint8)
                R = make_symmetric(R)
                met = compute_rqa_metrics(R)
                results.append({
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
                print(f"ch={ch} band={band_name} norm={norm} RRt={RR_t:.3f} RR={met['RR']:.4f} ENT={met['ENT']:.3f} DET={met['DET']:.3f}")

# Save JSON
out_json = 'replicate_emp250_results.json'
with open(out_json, 'w') as f:
    json.dump({'N': N, 'm': m, 'tau': tau, 'bands': bands, 'RR_targets': RR_targets,
               'norms': norms, 'channels': channels, 'results': results}, f, indent=2)

# Aggregate: median ENT across channels for each band/norm/RR
import pandas as pd
df = pd.DataFrame(results)
summary = df.groupby(['band', 'norm', 'RR_target']).agg(
    RR_actual=('RR_actual', 'median'),
    ENT_median=('ENT', 'median'),
    ENT_iqr=('ENT', lambda s: np.percentile(s, 75) - np.percentile(s, 25)),
    DET_median=('DET', 'median'),
    LAM_median=('LAM', 'median'),
).reset_index()

# Plot
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
out_png = 'replicate_emp250.png'
plt.savefig(out_png, dpi=150)
print(f"Saved {out_json} and {out_png}")
