import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

try:
    from colony_lib.datasets import load_dataset
    ds = load_dataset('neural_eeg')
    data = ds['data']
    fs = float(ds.get('sampling_rate', 128))
    ch_names = ds.get('channel_names', None)
except Exception as e:
    print('colony_lib load failed:', e)
    fallback = '../../shared_agora/world_c/datasets/neural_eeg.npz'
    ds = np.load(fallback)
    data = ds['data']
    fs = float(ds.get('sampling_rate', np.array([128]))[0])
    ch_names = ds.get('channel_names', None)

if ch_names is not None:
    ch_names = list(ch_names)
    idx = ch_names.index('AF3') if 'AF3' in ch_names else 0
else:
    idx = 0

x_full = data[:, idx] if data.ndim > 1 else data
fs = int(fs)
N_total = 14 * fs * 8
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
    b, a = butter(order, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, x)

def takens(x, m=3, tau=2):
    N = len(x) - (m-1)*tau
    idx = np.arange(N)[:, None] + np.arange(0, m*tau, tau)[None, :]
    return x[idx]

def cheb_dist(emb):
    return np.max(np.abs(emb[:, None, :] - emb[None, :, :]), axis=2)

def rqa(D, eps, lmin=2):
    R = (D <= eps).astype(np.uint8)
    N = R.shape[0]
    RR = R.sum() / (N*N)
    # diagonal line length distribution, excluding main diagonal
    line_counts = {}
    for k in range(1, N):
        diag = np.concatenate(([0], np.diag(R, k), [0]))
        dif = np.diff(diag)
        starts = np.where(dif == 1)[0]
        ends = np.where(dif == -1)[0]
        for s, e in zip(starts, ends):
            L = e - s
            line_counts[L] = line_counts.get(L, 0) + 1
    total_pts = sum(l*c for l, c in line_counts.items())
    long_pts = sum(l*c for l, c in line_counts.items() if l >= lmin)
    DET = long_pts / total_pts if total_pts > 0 else 0.0
    if line_counts:
        counts = np.array(list(line_counts.values()), dtype=float)
        counts = counts[counts > 0]
        p = counts / counts.sum()
        ENT = -np.sum(p * np.log(p))
    else:
        ENT = 0.0
    return RR, DET, ENT

methods = ['fixed_10uV', 'rel_0.5std', 'matched_RR5']
records = {m: {'RR': [], 'DET': [], 'ENT': []} for m in methods}
amplitudes = {b: [] for b in bands}

for w in windows:
    for name, (lo, hi) in bands.items():
        y = bandpass(w, lo, hi, fs)
        amplitudes[name].append(np.sqrt(np.mean(y**2)))
        emb = takens(y, m=3, tau=2)
        D = cheb_dist(emb)
        # fixed threshold 10 microvolts
        rr, det, ent = rqa(D, 10.0)
        records['fixed_10uV']['RR'].append(rr)
        records['fixed_10uV']['DET'].append(det)
        records['fixed_10uV']['ENT'].append(ent)
        # relative threshold 0.5 * std of the filtered signal
        eps_rel = 0.5 * np.std(y)
        rr, det, ent = rqa(D, eps_rel)
        records['rel_0.5std']['RR'].append(rr)
        records['rel_0.5std']['DET'].append(det)
        records['rel_0.5std']['ENT'].append(ent)
        # matched recurrence rate ~5%
        eps5 = np.percentile(D, 95)
        rr, det, ent = rqa(D, eps5)
        records['matched_RR5']['RR'].append(rr)
        records['matched_RR5']['DET'].append(det)
        records['matched_RR5']['ENT'].append(ent)

summary = {}
for m in methods:
    for qty in ['RR', 'DET', 'ENT']:
        arr = np.array(records[m][qty]).reshape(len(windows), len(bands))
        mean = arr.mean(axis=0)
        rho, p = spearmanr(freq_reps, mean)
        per_win_rho = []
        for i in range(len(windows)):
            try:
                per_win_rho.append(spearmanr(freq_reps, arr[i])[0])
            except Exception:
                per_win_rho.append(np.nan)
        per_win_rho = np.array(per_win_rho)
        summary[f"{m}_{qty}"] = {
            'mean_per_band': mean.tolist(),
            'Spearman_rho': float(rho),
            'Spearman_p': float(p),
            'fraction_windows_rho_negative': float(np.nanmean(per_win_rho < 0)) if len(per_win_rho)>0 else None,
            'median_window_rho': float(np.nanmedian(per_win_rho))
        }

# amplitude-confound check
amp_mean = np.array([np.mean(amplitudes[b]) for b in bands])
rho_amp_rr_fixed, p_amp = spearmanr(amp_mean,
    np.array(records['fixed_10uV']['RR']).reshape(len(windows), len(bands)).mean(axis=0))
summary['amplitude_RMS_per_band_uV'] = amp_mean.tolist()
summary['amplitude_RR_fixed_Spearman'] = float(rho_amp_rr_fixed)

print(json.dumps(summary, indent=2))

fig, axes = plt.subplots(3, 3, figsize=(12, 10), sharex=False, sharey=False)
for i, qty in enumerate(['RR', 'DET', 'ENT']):
    for j, m in enumerate(methods):
        ax = axes[i, j]
        key = f"{m}_{qty}"
        arr = np.array(records[m][qty]).reshape(len(windows), len(bands))
        ax.plot(freq_reps, arr.T, color='gray', alpha=0.25)
        ax.plot(freq_reps, arr.mean(axis=0), 'o-', color='red', lw=2)
        ax.set_xlabel('Band frequency (Hz)')
        ax.set_ylabel(qty)
        ax.set_title(f"{m} | {qty}\nρ={summary[key]['Spearman_rho']:.2f}")
        ax.set_xscale('log')
plt.tight_layout()
out_png = '../../shared_agora/artifacts/emp187_kimi_replication_v2.png'
plt.savefig(out_png, dpi=150)

out_json = '../../shared_agora/artifacts/emp187_kimi_replication_v2.json'
with open(out_json, 'w') as f:
    json.dump(summary, f, indent=2)
print('Saved', out_png, out_json)
