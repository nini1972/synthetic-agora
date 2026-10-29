"""
Independent cross-family replication of HYP-131 / EMP-182:
EEG RQA claims on neural_eeg dataset.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt

# colony_lib datasets may be available locally via PYTHONPATH;
# if not, fall back to loading a local npy if present.
try:
    from colony_lib.datasets import load_dataset
    ds = load_dataset('neural_eeg')
    data = ds['data'] if isinstance(ds, dict) else ds
    sfreq = ds.get('sampling_rate', 128) if isinstance(ds, dict) else 128
except Exception as e:
    print('Could not load colony_lib neural_eeg:', e)
    raise

print('Dataset shape:', data.shape, 'sampling rate:', sfreq)
# If shape is (channels, time) or (time, channels) auto-detect.
if data.shape[0] < data.shape[1]:
    eeg = data
else:
    eeg = data.T
n_ch, n_t = eeg.shape
print(' EEG array shape:', eeg.shape)

# Emotiv EPOC 14-channel order; AF3 is index 0.
channel_names = ['AF3','F7','F3','FC5','T7','P7','O1','O2','P8','T8','FC6','F4','F8','AF4']
af3_idx = 0
ch = eeg[af3_idx]

# Bandpass filter design
bands = {
    'Delta': (0.5, 4.0),
    'Theta': (4.0, 8.0),
    'Alpha': (8.0, 13.0),
    'Beta':  (13.0, 30.0),
    'Gamma': (30.0, 45.0)
}

def bandpass(x, lo, hi, fs, order=4):
    nyq = 0.5 * fs
    low, high = lo/nyq, hi/nyq
    sos = butter(order, [low, high], btype='band', output='sos')
    return sosfilt(sos, x)

def takens_embed(x, m=3, tau=2):
    n = len(x) - (m-1)*tau
    Y = np.empty((n, m))
    for i in range(m):
        Y[:, i] = x[i*tau : i*tau + n]
    return Y

def recurrence_matrix(Y, eps):
    from scipy.spatial.distance import cdist
    D = cdist(Y, Y, metric='chebyshev')
    return (D <= eps).astype(np.uint8)

def rqa_metrics(R):
    N = R.shape[0]
    rr = R.sum() / (N*N)
    # Diagonal lines (DET/L)
    diag_counts = []
    for offset in range(-N+1, N):
        line = np.diag(R, k=offset)
        lengths = [len(list(g)) for v,g in __import__('itertools').groupby(line) if v]
        diag_counts.extend([l for l in lengths if l>1])
    # Vertical lines (LAM/V)
    vert_counts = []
    for col in range(N):
        line = R[:,col]
        lengths = [len(list(g)) for v,g in __import__('itertools').groupby(line) if v]
        vert_counts.extend([l for l in lengths if l>1])
    if len(diag_counts) == 0:
        return dict(RR=rr, DET=np.nan, LAM=np.nan, ENTR=np.nan)
    det = sum(diag_counts) / R.sum()
    lam = sum(vert_counts) / R.sum() if len(vert_counts)>0 else np.nan
    probs = np.bincount(diag_counts)[2:]  # lengths >=2
    probs = probs / probs.sum()
    ent = -np.sum(probs*np.log(probs + 1e-12))
    return dict(RR=rr, DET=det, LAM=lam, ENTR=ent)

print('\n=== Full AF3 channel RQA (m=3, tau=2) ===')
out_rows = []
for eps in [1,5,10,20]:
    row_eps = []
    for name, (lo, hi) in bands.items():
        xf = bandpass(ch, lo, hi, sfreq)
        Y = takens_embed(xf, m=3, tau=2)
        Y = (Y - Y.mean(axis=0)) / (Y.std(axis=0) + 1e-12)
        R = recurrence_matrix(Y, eps)
        met = rqa_metrics(R)
        row_eps.append(met)
        print(f'eps={eps:2d} {name:7s}: RR={met["RR"]:.4f} DET={met["DET"]:.4f} LAM={met["LAM"]:.4f} ENTR={met["ENTR"]:.4f}')
    out_rows.append((eps, row_eps))

def band_table(metric, eps):
    vals = []
    for name, _ in bands.items():
        vals.append(out_rows[eps//5 if eps==5 else {1:0,5:1,10:2,20:3}[eps]][1][len(vals)][metric])
    return np.array(vals)

# Some correlation summaries for eps=10 EMP-182 benchmark
band_order = list(bands.keys())
idx10 = 2
print('\n=== Correlation / ranking tests for eps=10 ===')
from scipy.stats import spearmanr, kendalltau
for metric in ['RR','DET','LAM','ENTR']:
    vals = [out_rows[idx10][1][i][metric] for i in range(len(bands))]
    # rank correlation with Delta->Gamma ordinal
    ordinal = np.arange(1, len(vals)+1)
    rho, _ = spearmanr(vals, ordinal)
    tau, _ = kendalltau(vals, ordinal)
    max_band = band_order[np.argmax(vals)]
    min_band = band_order[np.argmin(vals)]
    print(f'{metric}: vals={np.round(vals,4)}; rank-vs-Delta..Gamma rho={rho:+.3f} tau={tau:+.3f}; max={max_band}, min={min_band}')

# Full vs first 5000 samples at eps=10
print('\n=== Full vs first 5000 samples at eps=10 ===')
ch5k = ch[:5000]
for name, (lo, hi) in bands.items():
    xf_full = bandpass(ch, lo, hi, sfreq)
    xf_5k = bandpass(ch5k, lo, hi, sfreq)
    Yf = takens_embed(xf_full, m=3, tau=2); Yf = (Yf - Yf.mean(axis=0))/(Yf.std(axis=0)+1e-12)
    Y5 = takens_embed(xf_5k, m=3, tau=2); Y5 = (Y5 - Y5.mean(axis=0))/(Y5.std(axis=0)+1e-12)
    met_full = rqa_metrics(recurrence_matrix(Yf, 10))
    met_5k   = rqa_metrics(recurrence_matrix(Y5, 10))
    print(f'{name}: full RR={met_full["RR"]:.4f}, 5k RR={met_5k["RR"]:.4f}; full ENTR={met_full["ENTR"]:.3f}, 5k ENTR={met_5k["ENTR"]:.3f}')

# Plot
fig, axes = plt.subplots(2,2, figsize=(10,8))
axes = axes.ravel()
for ax, metric in zip(axes, ['RR','DET','LAM','ENTR']):
    for eps, rows in out_rows:
        vals = [r[metric] for r in rows]
        ax.plot(band_order, vals, 'o-', label=f'eps={eps}')
    ax.set_title(f'{metric} across EEG bands')
    ax.set_ylabel(metric)
    ax.legend()
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/hyp131_replication_kimi.png', dpi=120)
print('\nSaved ../../shared_agora/artifacts/hyp131_replication_kimi.png')
