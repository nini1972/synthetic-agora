import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
import json, os
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

# Load EEG (AF3 / channel 0)
path = '../../shared_agora/artifacts/neural_eeg.npz'
if os.path.exists(path):
    d = np.load(path); ch = d['data'][:4096, 0]; fs = float(d['sampling_rate'])
else:
    d = load_dataset('neural_eeg'); ch = d.data[:4096, 0]; fs = d.sampling_rate

bands = {'Delta':(1,3), 'Theta':(4,7), 'Alpha':(8,12), 'Beta':(13,30), 'Gamma':(31,44)}
centers = np.array([2.25, 6.0, 10.0, 21.0, 37.5])
band_names = list(bands.keys())

def bp(x, lo, hi, fs):
    sos = butter(4, [lo/(fs/2), hi/(fs/2)], btype='band', output='sos')
    return sosfiltfilt(sos, x)

def measure(emb, eps):
    R = recurrence_matrix(emb, epsilon=eps)
    m = compute_rqa_metrics(R)
    return float(m['RR']), float(m['DET']), float(m['LAM']), float(m['ENT'])

def eps_for_RR(emb, target=0.05, n_samp=1500):
    n_samp = min(n_samp, emb.shape[0])
    idx = np.random.choice(emb.shape[0], n_samp, replace=False)
    D2 = np.sum((emb[idx][:,None,:]-emb[idx][None,:,:])**2, axis=2)
    triu = np.triu_indices(n_samp, k=1)
    dists = np.sqrt(D2[triu])
    return float(np.percentile(dists, target*100))

results_raw = {}
results_std = {}
for name,(lo,hi) in bands.items():
    x = bp(ch, lo, hi, fs)
    raw_emb = takens_embedding(x, m=3, tau=2)
    z = (x-x.mean())/(x.std()+1e-12)
    std_emb = takens_embedding(z, m=3, tau=2)
    # raw fixed eps=10
    rr, det, lam, ent = measure(raw_emb, 10.0)
    # standardized fixed eps=10
    rrS, detS, lamS, entS = measure(std_emb, 10.0)
    # standardized fixed RR=0.05
    epsR = eps_for_RR(std_emb, target=0.05)
    rrR, detR, lamR, entR = measure(std_emb, epsR)
    results_raw[name] = {'RR':rr,'DET':det,'LAM':lam,'ENT':ent,'rms_uv':float(np.sqrt(np.mean(x**2)))}
    results_std[name] = {'fixed_eps10':{'RR':rrS,'DET':detS,'LAM':lamS,'ENT':entS},
                         'fixed_RR05':{'RR':rrR,'DET':detR,'LAM':lamR,'ENT':entR,'eps':epsR}}

raw_RR = np.array([results_raw[n]['RR'] for n in band_names])
raw_ENT = np.array([results_raw[n]['ENT'] for n in band_names])
std_RR = np.array([results_std[n]['fixed_eps10']['RR'] for n in band_names])
std_ENT = np.array([results_std[n]['fixed_eps10']['ENT'] for n in band_names])
matched_ENT = np.array([results_std[n]['fixed_RR05']['ENT'] for n in band_names])

import scipy.stats as stats
res = {
    'raw_fixed_eps10':{n:results_raw[n] for n in band_names},
    'std_fixed_eps10': {n:results_std[n]['fixed_eps10'] for n in band_names},
    'std_fixed_RR05': {n:results_std[n]['fixed_RR05'] for n in band_names},
    'spearman_rho_vs_frequency': {
        'raw_RR': float(stats.spearmanr(centers, raw_RR)[0]),
        'raw_ENT': float(stats.spearmanr(centers, raw_ENT)[0]),
        'std_RR_fixed10': float(stats.spearmanr(centers, std_RR)[0]),
        'std_ENT_fixed10': float(stats.spearmanr(centers, std_ENT)[0]),
        'std_ENT_matchedRR05': float(stats.spearmanr(centers, matched_ENT)[0])
    }
}
with open('../../shared_agora/artifacts/hyp131_threshold_confound_kimi.json','w') as f:
    json.dump(res, f, indent=2)

fig, axs = plt.subplots(2,3,figsize=(13,7))
def panel(ax, vals, title, ylab):
    ax.plot(centers, vals, 'o-')
    ax.set_xticks(centers); ax.set_xticklabels(band_names, rotation=20)
    ax.set_title(title); ax.set_ylabel(ylab)
panel(axs[0,0], raw_RR, 'Raw signals: RR @ fixed eps=10', 'RR')
panel(axs[1,0], raw_ENT, 'Raw signals: ENT @ fixed eps=10', 'ENT')
panel(axs[0,1], std_RR, 'Z-scored: RR @ fixed eps=10', 'RR')
panel(axs[1,1], std_ENT, 'Z-scored: ENT @ fixed eps=10', 'ENT')
panel(axs[0,2], matched_ENT, 'Z-scored: ENT @ matched RR≈5%', 'ENT')
panel(axs[1,2], std_RR, 'Z-scored: RR @ fixed eps=10', 'RR')
plt.tight_layout(); plt.savefig('../../shared_agora/artifacts/hyp131_threshold_confound_kimi.png', dpi=150)
print(json.dumps(res['spearman_rho_vs_frequency'], indent=2))
