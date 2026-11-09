import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

# Load dataset using colony_lib if available, else fall back to local npy
try:
    from colony_lib.datasets import load_dataset
    ds = load_dataset('neural_eeg')
    # Expect keys: 'data', 'sampling_rate', 'channel_names' or similar
    data = ds['data']
    fs = float(ds.get('sampling_rate', 128))
    ch_names = ds.get('channel_names', None)
except Exception as e:
    print('colony_lib load failed:', e)
    # Try a known shared path as fallback
    fallback = '../../shared_agora/world_c/datasets/neural_eeg.npz'
    ds = np.load(fallback)
    data = ds['data']
    fs = float(ds.get('sampling_rate', np.array([128]))[0])
    ch_names = ds.get('channel_names', None)

# Identify AF3 channel
if ch_names is not None:
    ch_names = list(ch_names)
    if 'AF3' in ch_names:
        idx = ch_names.index('AF3')
    else:
        idx = 0
else:
    idx = 0

x_full = data[:, idx] if data.ndim > 1 else data
fs = int(fs)
N_total = 14 * fs * 8   # 14 windows of 8 seconds
x_full = x_full[:N_total]

bands = {
    'Delta': (1, 3),
    'Theta': (4, 7),
    'Alpha': (8, 12),
    'Beta': (13, 30),
    'Gamma': (31, 44),
}
freq_reps = np.array([2.0, 5.5, 10.0, 21.5, 37.5])

win_len = fs * 8
windows = [x_full[i*win_len:(i+1)*win_len] for i in range(14)]

def bandpass(x, low, high, fs, order=4):
    nyq = 0.5 * fs
    low, high = low/nyq, high/nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, x)

def takens(x, m=3, tau=2):
    N = len(x) - (m-1)*tau
    emb = np.empty((N, m))
    for i in range(m):
        emb[:, i] = x[i*tau:i*tau+N]
    return emb

def rqa_metrics(emb, eps):
    D = np.max(np.abs(emb[:, None, :] - emb[None, :, :]), axis=2)
    R = (D <= eps).astype(np.uint8)
    N = R.shape[0]
    # Recurrence rate
    RR = np.sum(R) / (N*N)
    # Diagonal line statistics (exclude main diagonal)
    line_counts = {}
    for k in range(1, N):
        diag = np.concatenate(([0], np.diag(R, k), [0]))
        dif = np.diff(diag)
        starts = np.where(dif == 1)[0]
        ends = np.where(dif == -1)[0]
        for s, e in zip(starts, ends):
            L = e - s
            line_counts[L] = line_counts.get(L, 0) + 1
    total_points = sum(l*count for l, count in line_counts.items())
    long_points = sum(l*count for l, count in line_counts.items() if l >= 2)
    DET = long_points / total_points if total_points > 0 else 0.0
    # Shannon entropy of line length distribution
    if line_counts:
        counts = np.array(list(line_counts.values()), dtype=float)
        counts = counts[counts > 0]
        p = counts / counts.sum()
        ENT = -np.sum(p * np.log(p))
    else:
        ENT = 0.0
    return RR, DET, ENT

methods = ['fixed_10uV', 'rel_0.5std', 'matched_RR5']
results = {m: {'RR': [], 'DET': [], 'ENT': []} for m in methods}

for w in windows:
    band_rr = {m: [] for m in methods}
    band_det = {m: [] for m in methods}
    band_ent = {m: [] for m in methods}
    for name, (lo, hi) in bands.items():
        y = bandpass(w, lo, hi, fs)
        emb = takens(y, m=3, tau=2)
        # fixed threshold 10 uV
        rr1, det1, ent1 = rqa_metrics(emb, 10.0)
        band_rr['fixed_10uV'].append(rr1)
        band_det['fixed_10uV'].append(det1)
        band_ent['fixed_10uV'].append(ent1)
        # relative threshold 0.5 std
        eps_rel = 0.5 * np.std(emb, axis=0).mean()  # mean std across dimensions
        rr2, det2, ent2 = rqa_metrics(emb, eps_rel)
        band_rr['rel_0.5std'].append(rr2)
        band_det['rel_0.5std'].append(det2)
        band_ent['rel_0.5std'].append(ent2)
        # matched RR ~5%
        D = np.max(np.abs(emb[:, None, :] - emb[None, :, :]), axis=2)
        eps5 = np.percentile(D, 95)
        rr3, det3, ent3 = rqa_metrics(emb, eps5)
        band_rr['matched_RR5'].append(rr3)
        band_det['matched_RR5'].append(det3)
        band_ent['matched_RR5'].append(ent3)
    for m in methods:
        results[m]['RR'].append(band_rr[m])
        results[m]['DET'].append(band_det[m])
        results[m]['ENT'].append(band_ent[m])

# Aggregate and compute Spearman
summary = {}
for m in methods:
    rr_arr = np.array(results[m]['RR'])  # (14,5)
    mean_rr = rr_arr.mean(axis=0)
    rho, p = spearmanr(freq_reps, mean_rr)
    summary[m] = {'mean_RR_per_band': mean_rr.tolist(),
                  'Spearman_rho': float(rho),
                  'Spearman_p': float(p),
                  'fraction_windows_rho_negative': float(np.mean([spearmanr(freq_reps, rr_arr[i])[0] < 0 for i in range(len(windows))]))}

print(json.dumps(summary, indent=2))

# Plot
fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)
for ax, m in zip(axes, methods):
    rr_mat = np.array(results[m]['RR'])
    ax.plot(freq_reps, rr_mat.T, color='gray', alpha=0.3)
    ax.plot(freq_reps, rr_mat.mean(axis=0), 'o-', color='red', lw=2)
    ax.set_xlabel('Band frequency (Hz)')
    ax.set_ylabel('RR')
    ax.set_title(f"{m}\nρ={summary[m]['Spearman_rho']:.2f}")
    ax.set_xscale('log')
plt.tight_layout()
out_png = '../../shared_agora/artifacts/emp187_kimi_replication.png'
plt.savefig(out_png, dpi=150)

out_json = '../../shared_agora/artifacts/emp187_kimi_replication.json'
with open(out_json, 'w') as f:
    json.dump(summary, f, indent=2)
print('Saved', out_png, out_json)
