"""
World C job: multi-channel EEG RQA threshold/norm sweep.
Tests robustness of EMP-200 (matched-RR entropy decrease with frequency) and
reproduces SYN-064 sign-flip phenomenon across recurrence thresholds.
"""
import os, json, time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import spearmanr

from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

fs = 128.0
bands = [('Delta',0.5,4.0), ('Theta',4.0,8.0), ('Alpha',8.0,13.0),
         ('Beta',13.0,30.0), ('Gamma',30.0,45.0)]
band_centers = np.array([0.5*(l+h) for _,l,h in bands])
thresholds = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.80, 0.90]
norms = ['euclidean', 'chebyshev']
max_points = 3000

print('Loading dataset...')
ds = load_dataset('neural_eeg')
channels = list(ds.keys())
print('Channels:', channels)

records = []
start = time.time()
for ch_idx, ch in enumerate(channels):
    sig = ds[ch][:4096].astype(float)
    sig = sig - np.mean(sig)
    # pre-filter per band once
    filt = {}
    for name, low, high in bands:
        sos = signal.butter(4, [low, high], btype='band', output='sos', fs=fs)
        f = signal.sosfiltfilt(sos, sig)
        f = f - np.mean(f)
        f = f / (np.std(f) + 1e-12)
        filt[name] = f
    for norm in norms:
        for thr in thresholds:
            # accumulate band metrics
            det_v, lam_v, ent_v, rr_v = [], [], [], []
            for name, _, _ in bands:
                emb = takens_embedding(filt[name], m=3, tau=2)
                R = recurrence_matrix(emb, metric=norm, target_rr=thr, max_points=max_points)
                m = compute_rqa_metrics(R, min_diag_len=2, min_vert_len=2)
                det_v.append(m['DET']); lam_v.append(m['LAM']); ent_v.append(m['ENT']); rr_v.append(m['RR'])
            det_rho, _ = spearmanr(band_centers, det_v)
            lam_rho, _ = spearmanr(band_centers, lam_v)
            ent_rho, _ = spearmanr(band_centers, ent_v)
            ent_gamma_lt_alpha = int(ent_v[-1] < ent_v[-2])
            rec = {
                'channel': ch, 'norm': norm, 'target_rr': thr,
                'mean_actual_rr': float(np.mean(rr_v)),
                'DET_rho': float(det_rho), 'LAM_rho': float(lam_rho), 'ENT_rho': float(ent_rho),
                'ENT_gamma_lt_alpha': ent_gamma_lt_alpha,
                'DET_values': list(map(float, det_v)),
                'LAM_values': list(map(float, lam_v)),
                'ENT_values': list(map(float, ent_v)),
            }
            records.append(rec)
            print(f'{ch} {norm} rr={thr:.2f} DET_rho={det_rho:+.3f} LAM_rho={lam_rho:+.3f} ENT_rho={ent_rho:+.3f}')
print('Elapsed:', time.time()-start)

# Save CSV-like JSON
out_dir = 'world_c_results'
os.makedirs(out_dir, exist_ok=True)
json_path = os.path.join(out_dir, 'eeg_rqa_threshold_sweep.json')
with open(json_path,'w') as f:
    json.dump(records, f, indent=2)

# Aggregate summary
summary = []
for norm in norms:
    for thr in thresholds:
        subset = [r for r in records if r['norm']==norm and r['target_rr']==thr]
        det_neg = np.mean([r['DET_rho']<0 for r in subset])
        lam_neg = np.mean([r['LAM_rho']<0 for r in subset])
        ent_neg = np.mean([r['ENT_rho']<0 for r in subset])
        summary.append({
            'norm': norm, 'target_rr': thr,
            'frac_DET_rho_negative': float(det_neg),
            'frac_LAM_rho_negative': float(lam_neg),
            'frac_ENT_rho_negative': float(ent_neg),
            'mean_DET_rho': float(np.mean([r['DET_rho'] for r in subset])),
            'mean_LAM_rho': float(np.mean([r['LAM_rho'] for r in subset])),
            'mean_ENT_rho': float(np.mean([r['ENT_rho'] for r in subset])),
        })
sum_path = os.path.join(out_dir, 'eeg_rqa_threshold_summary.json')
with open(sum_path,'w') as f:
    json.dump(summary, f, indent=2)

# Plot aggregate mean rho vs threshold
fig, ax = plt.subplots(figsize=(8,5))
for norm in norms:
    s = [x for x in summary if x['norm']==norm]
    xs = [x['target_rr'] for x in s]
    ax.plot(xs, [x['mean_DET_rho'] for x in s], 'o-', label=f'DET {norm}')
    ax.plot(xs, [x['mean_LAM_rho'] for x in s], 's--', label=f'LAM {norm}')
    ax.plot(xs, [x['mean_ENT_rho'] for x in s], '^:', label=f'ENT {norm}')
ax.axhline(0, color='k', lw=0.5, ls='--')
ax.set_xscale('log')
ax.set_xlabel('Target recurrence rate RR')
ax.set_ylabel('Mean Spearman rho(freq, metric) over channels')
ax.set_title('EEG band-frequency RQA metric correlations vs recurrence threshold')
ax.legend(ncol=2, fontsize=8)
plt.tight_layout()
fig_path = os.path.join(out_dir, 'eeg_rqa_threshold_sweep.png')
plt.savefig(fig_path, dpi=150)

# Also plot fraction of channels with negative rho
fig2, ax2 = plt.subplots(figsize=(8,5))
for norm in norms:
    s = [x for x in summary if x['norm']==norm]
    xs = [x['target_rr'] for x in s]
    ax2.plot(xs, [x['frac_DET_rho_negative'] for x in s], 'o-', label=f'DET {norm}')
    ax2.plot(xs, [x['frac_LAM_rho_negative'] for x in s], 's--', label=f'LAM {norm}')
    ax2.plot(xs, [x['frac_ENT_rho_negative'] for x in s], '^:', label=f'ENT {norm}')
ax2.set_xscale('log')
ax2.set_xlabel('Target recurrence rate RR')
ax2.set_ylabel('Fraction of channels with rho(freq, metric) < 0')
ax2.set_title('Robustness of negative band-frequency correlations')
ax2.legend(ncol=2, fontsize=8)
plt.tight_layout()
fig2_path = os.path.join(out_dir, 'eeg_rqa_threshold_fractions.png')
plt.savefig(fig2_path, dpi=150)

print('Saved', json_path, sum_path, fig_path, fig2_path)
