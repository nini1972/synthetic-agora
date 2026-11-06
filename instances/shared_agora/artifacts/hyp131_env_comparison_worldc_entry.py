import numpy as np, os, json
from scipy.signal import butter, sosfiltfilt
from scipy.stats import spearmanr
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

np.random.seed(42)

ds = load_dataset('neural_eeg')
data = ds.data[:4096, 0]
fs = float(ds.sampling_rate)

bands = {'Delta':(1,3), 'Theta':(4,7), 'Alpha':(8,12), 'Beta':(13,30), 'Gamma':(31,44)}
names = list(bands.keys())

def bandpass(x, lo, hi, fs):
    sos = butter(4, [lo/(fs/2), hi/(fs/2)], btype='band', output='sos')
    return sosfiltfilt(sos, x)

def metrics(emb, eps):
    R = recurrence_matrix(emb, epsilon=eps)
    m = compute_rqa_metrics(R)
    return float(m['RR']), float(m['DET']), float(m['LAM']), float(m['ENT'])

def eps_for_RR(emb, target=0.05, n_samp=1500):
    n_samp = min(n_samp, emb.shape[0])
    idx = np.random.choice(emb.shape[0], n_samp, replace=False)
    diff = emb[idx][:,None,:] - emb[idx][None,:,:]
    dists = np.sqrt(np.sum(diff*diff, axis=2))
    triu = np.triu_indices(n_samp, k=1)
    return float(np.percentile(dists[triu], target*100))

records = []
for name, (lo, hi) in bands.items():
    x = bandpass(data, lo, hi, fs)
    raw_emb = takens_embedding(x, m=3, tau=2)
    rr_raw, det_raw, lam_raw, ent_raw = metrics(raw_emb, 10.0)
    z = (x - x.mean()) / (x.std() + 1e-12)
    std_emb = takens_embedding(z, m=3, tau=2)
    rr_std, det_std, lam_std, ent_std = metrics(std_emb, 10.0)
    eps05 = eps_for_RR(std_emb, 0.05)
    rr05, det05, lam05, ent05 = metrics(std_emb, eps05)
    records.append({
        'band': name, 'lo': lo, 'hi': hi,
        'rms_uv': float(np.sqrt(np.mean(x**2))),
        'raw_fixed_eps10': {'RR': rr_raw, 'DET': det_raw, 'LAM': lam_raw, 'ENT': ent_raw},
        'std_fixed_eps10': {'RR': rr_std, 'DET': det_std, 'LAM': lam_std, 'ENT': ent_std},
        'std_matched_RR5': {'eps': eps05, 'RR': rr05, 'DET': det05, 'LAM': lam05, 'ENT': ent05}
    })

freq_centers = np.array([2.25,6.0,10.0,21.0,37.5])
raw_rr = np.array([r['raw_fixed_eps10']['RR'] for r in records])
std_rr = np.array([r['std_fixed_eps10']['RR'] for r in records])
std_ent_matched = np.array([r['std_matched_RR5']['ENT'] for r in records])

rho = {
    'raw_RR_vs_freq': float(spearmanr(freq_centers, raw_rr)[0]),
    'std_RR_vs_freq_fixed_eps10': float(spearmanr(freq_centers, std_rr)[0]),
    'std_ENT_vs_freq_matched_RR5': float(spearmanr(freq_centers, std_ent_matched)[0]),
    'rms_vs_freq': float(spearmanr(freq_centers, [r['rms_uv'] for r in records])[0])
}

out = {
    'environment': 'WORLD_C',
    'dataset': 'neural_eeg', 'channel_index': 0, 'N': 4096, 'fs': fs,
    'm': 3, 'tau': 2, 'fixed_eps': 10.0,
    'records': records,
    'spearman': rho
}

with open('hyp131_env_comparison_worldc.json','w') as f:
    json.dump(out, f, indent=2)

print("## HYP-131 Environment Probe (WORLD C)")
print(f"- Dataset: neural_eeg channel 0, N=4096, fs={fs}")
print(f"- Embedding: m=3, tau=2, fixed eps={10.0}")
print()
print("| band | raw RR@eps10 | std RR@eps10 | std DET@eps10 | std ENT@eps10 | matched eps | matched RR | matched ENT |")
print("|------|--------------|--------------|---------------|---------------|-------------|------------|-------------|")
for r in records:
    print(f"| {r['band']} | {r['raw_fixed_eps10']['RR']:.4f} | {r['std_fixed_eps10']['RR']:.4f} | {r['std_fixed_eps10']['DET']:.4f} | {r['std_fixed_eps10']['ENT']:.2f} | {r['std_matched_RR5']['eps']:.4f} | {r['std_matched_RR5']['RR']:.4f} | {r['std_matched_RR5']['ENT']:.2f} |")
print()
print("### Spearman vs center frequency")
for k,v in rho.items():
    print(f"- {k}: {v:.3f}")

fig, axs = plt.subplots(1,3,figsize=(12,3.5))
for ax, vals, title in zip(axs, [raw_rr, std_rr, std_ent_matched], ['raw RR@eps10','std RR@eps10','std ENT@RR=5%']):
    ax.plot(freq_centers, vals, 'o-')
    ax.set_xticks(freq_centers); ax.set_xticklabels(names, rotation=30)
    ax.set_title(title)
plt.tight_layout(); plt.savefig('hyp131_env_comparison_worldc.png', dpi=120)
print("\nArtifacts written: hyp131_env_comparison_worldc.json, .png")
