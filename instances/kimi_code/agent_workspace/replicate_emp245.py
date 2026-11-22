import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import spearmanr
import json
import os

# colony_lib is available in workspace via world_c PYTHONPATH
try:
    from colony_lib.datasets import load_dataset
    from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
except Exception as e:
    raise RuntimeError(f"colony_lib import failed: {e}")

# Load EEG dataset
ds = load_dataset('neural_eeg')
fs = ds.sampling_rate
channels = ds.signal_columns
# Use AF3 (index 0 typically) and also pool all channels for robustness
ch_idx = channels.index('AF3') if 'AF3' in channels else 0

N = 4096  # use a longer segment than EMP-245 for robustness
raw_full = ds.signal_matrix()[:N, :]

bands = {
    'Delta': (0.5, 4.0),
    'Theta': (4.0, 8.0),
    'Alpha': (8.0, 13.0),
    'Beta': (13.0, 30.0),
    'Gamma': (30.0, 45.0),
}
band_centers = np.array([2.0, 6.0, 10.5, 21.5, 37.5])

def bandpass(x, lo, hi, fs, order=4):
    sos = signal.butter(order, [lo, hi], btype='band', fs=fs, output='sos')
    return signal.sosfiltfilt(sos, x)

def welch_spectral_entropy(x, fs, fmin=0.5, fmax=45.0):
    freqs, psd = signal.welch(x, fs=fs, nperseg=256, window='hann')
    mask = (freqs >= fmin) & (freqs <= fmax)
    p = psd[mask]
    p = p / p.sum()
    return -np.sum(p * np.log(p + 1e-12))

def rqa_matched(x, m=3, tau=2, percentile=5, norm='chebyshev'):
    emb = takens_embedding(x, m=m, tau=tau)
    # Pairwise distance matrix for percentile threshold
    if norm == 'chebyshev':
        from scipy.spatial.distance import cdist
        D = cdist(emb, emb, metric='chebyshev')
    else:
        from scipy.spatial.distance import cdist
        D = cdist(emb, emb, metric='euclidean')
    # exclude diagonal
    eps = np.percentile(D[np.triu_indices_from(D, k=1)], percentile)
    R = recurrence_matrix(emb, epsilon=eps)
    metrics = compute_rqa_metrics(R)
    rr = metrics['RR']
    det = metrics['DET']
    lam = metrics['LAM']
    ent = metrics['ENT']
    return rr, det, lam, ent, eps

def analyze_channel(x, label):
    x_z = (x - x.mean()) / x.std()
    results = {'label': label, 'band': list(bands.keys()), 'freq': band_centers.tolist()}
    rqa_ent = []
    det = []
    lam = []
    rr = []
    spec_ent = []
    for name, (lo, hi) in bands.items():
        xf = bandpass(x_z, lo, hi, fs)
        r, d, l, e, eps = rqa_matched(xf, percentile=5)
        rqa_ent.append(e); det.append(d); lam.append(l); rr.append(r)
        spec_ent.append(welch_spectral_entropy(xf, fs))
    results['RR'] = rr
    results['RQA_ENT'] = rqa_ent
    results['DET'] = det
    results['LAM'] = lam
    results['SPEC_ENT'] = spec_ent
    # correlations
    rho_rqa, _ = spearmanr(band_centers, rqa_ent)
    rho_det, _ = spearmanr(band_centers, det)
    rho_lam, _ = spearmanr(band_centers, lam)
    rho_spec, _ = spearmanr(band_centers, spec_ent)
    results['rho'] = {
        'RQA_ENT': float(rho_rqa),
        'DET': float(rho_det),
        'LAM': float(rho_lam),
        'SPEC_ENT': float(rho_spec),
        'cross_profile_corr': float(np.corrcoef(rqa_ent, spec_ent)[0,1])
    }
    return results

# Main analyses
reports = []
reports.append(analyze_channel(raw_full[:, ch_idx], f'AF3 (ch={ch_idx})'))

# Pooled channel mean (z-scored per channel then averaged) to test channel heterogeneity
x_pooled = np.zeros(N)
for c in range(raw_full.shape[1]):
    xc = raw_full[:, c]
    xc = (xc - xc.mean()) / xc.std()
    x_pooled += xc
x_pooled /= raw_full.shape[1]
reports.append(analyze_channel(x_pooled, '14-channel mean (z-scored/pooled)'))

# Fixed epsilon=10 audit on z-scored AF3 (EMP-180-like)
xfixed = {}
x = raw_full[:, ch_idx]
x_z = (x - x.mean()) / x.std()
fixed_eps = 10.0
fixed_audit = {'label': 'fixed_eps=10_audit_zscored_AF3', 'band': list(bands.keys()),
               'RR_fix': [], 'DET_fix': [], 'LAM_fix': [], 'ENT_fix': [], 'amp_std': []}
for name, (lo, hi) in bands.items():
    xf = bandpass(x_z, lo, hi, fs)
    emb = takens_embedding(xf, m=3, tau=2)
    R = recurrence_matrix(emb, epsilon=fixed_eps)
    m = compute_rqa_metrics(R)
    fixed_audit['RR_fix'].append(m['RR']); fixed_audit['DET_fix'].append(m['DET'])
    fixed_audit['LAM_fix'].append(m['LAM']); fixed_audit['ENT_fix'].append(m['ENT'])
    fixed_audit['amp_std'].append(float(xf.std()))
reports.append(fixed_audit)

# Save JSON metrics
out_json = 'emp245_replication_kimi.json'
with open(out_json, 'w') as f:
    json.dump(reports, f, indent=2)

# Plot
fig, axes = plt.subplots(2, 2, figsize=(11, 9))
for rep in reports[:2]:
    ax = axes[0, 0]
    ax.plot(rep['freq'], rep['RQA_ENT'], marker='o', label=rep['label'])
    ax.set_xlabel('Band center frequency (Hz)')
    ax.set_ylabel('RQA ENT (matched RR~5%)')
    ax.set_title('RQA Shannon Entropy vs frequency')
    ax.legend()
for rep in reports[:2]:
    ax = axes[0, 1]
    ax.plot(rep['freq'], rep['SPEC_ENT'], marker='s', label=rep['label'])
    ax.set_xlabel('Band center frequency (Hz)')
    ax.set_ylabel('Spectral Shannon Entropy')
    ax.set_title('Spectral Entropy vs frequency')
    ax.legend()
for rep in reports[:2]:
    ax = axes[1, 0]
    ax.plot(rep['freq'], rep['DET'], marker='^', label=rep['label']+' DET')
    ax.plot(rep['freq'], rep['LAM'], marker='v', linestyle='--', label=rep['label']+' LAM')
    ax.set_xlabel('Band center frequency (Hz)')
    ax.set_ylabel('DET / LAM')
    ax.set_title('DET & LAM vs frequency')
    ax.legend(fontsize=7)
ax = axes[1, 1]
ax.bar(range(len(bands)), fixed_audit['RR_fix'], alpha=0.6, label='RR @ eps=10')
ax2 = ax.twinx()
ax2.plot(range(len(bands)), fixed_audit['amp_std'], color='red', marker='o', label='Band amp std')
ax.set_xticks(range(len(bands)))
ax.set_xticklabels(list(bands.keys()), rotation=30)
ax.set_ylabel('RR @ fixed eps=10')
ax2.set_ylabel('Band amplitude std (z-scored)')
ax.set_title('EMP-180 fixed-eps audit: saturation/amplitude confound')
fig.tight_layout()
artifact_path = '../../shared_agora/artifacts/emp245_replication_kimi.png'
os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
fig.savefig(artifact_path, dpi=150)
print('Artifact saved to', artifact_path)

# Print summary
for rep in reports[:2]:
    print('\n===', rep['label'], '===')
    print('rho(RQA_ENT, freq) =', rep['rho']['RQA_ENT'])
    print('rho(SPEC_ENT, freq)=', rep['rho']['SPEC_ENT'])
    print('rho(DET, freq)     =', rep['rho']['DET'])
    print('rho(LAM, freq)     =', rep['rho']['LAM'])
    print('cross-profile corr =', rep['rho']['cross_profile_corr'])
print('\n=== Fixed eps=10 audit (z-scored AF3) ===')
print('RR:', ['%.4f'%v for v in fixed_audit['RR_fix']])
print('DET:', ['%.4f'%v for v in fixed_audit['DET_fix']])
print('LAM:', ['%.4f'%v for v in fixed_audit['LAM_fix']])
print('ENT:', ['%.4f'%v for v in fixed_audit['ENT_fix']])
print('amp std:', ['%.3f'%v for v in fixed_audit['amp_std']])
