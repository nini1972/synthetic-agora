import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
import json, os
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

# Load EEG
path = 'shared_agora/artifacts/neural_eeg.npz' if os.path.exists('shared_agora/artifacts/neural_eeg.npz') else '../../shared_agora/artifacts/neural_eeg.npz'
if os.path.exists(path):
    d = np.load(path)
    ch = d['data'][:4096, 0]
    fs = float(d['sampling_rate'])
else:
    d = load_dataset('neural_eeg')
    ch = d.data[:4096, 0]
    fs = d.sampling_rate

bands = {'Delta':(1,3), 'Theta':(4,7), 'Alpha':(8,12), 'Beta':(13,30), 'Gamma':(31,44)}
centers = np.array([2.25, 6.0, 10.0, 21.0, 37.5])

def bandpass(x, lo, hi, fs):
    nyq = fs/2
    sos = butter(4, [lo/nyq, hi/nyq], btype='band', output='sos')
    return sosfiltfilt(sos, x)

def measure(emb, eps):
    R = recurrence_matrix(emb, epsilon=eps)
    m = compute_rqa_metrics(R)
    return float(m['RR']), float(m['DET']), float(m['LAM']), float(m['ENT'])

results = {}
for name,(lo,hi) in bands.items():
    x = bandpass(ch, lo, hi, fs)
    rms = float(np.sqrt(np.mean(x**2)))
    z = (x-x.mean())/(x.std()+1e-12)
    emb = takens_embedding(z, m=3, tau=2)
    # attractor diameter
    diams = np.sqrt(((emb.max(axis=0)-emb.min(axis=0))**2).sum())
    # fixed eps=10
    rr1,det1,lam1,ent1 = measure(emb, 10.0)
    # approx eps for RR=0.05 using random sample distances
    n_samp = min(1500, emb.shape[0])
    idx = np.random.choice(emb.shape[0], n_samp, replace=False)
    sample = emb[idx]
    D2 = np.sum((sample[:,None,:]-sample[None,:,:])**2, axis=2)
    # take off-diagonal
    triu = np.triu_indices(n_samp, k=1)
    dists = np.sqrt(D2[triu])
    eps_rr05 = float(np.percentile(dists, 5.0))
    rr2,det2,lam2,ent2 = measure(emb, eps_rr05)
    # pct diameter ~ eps such that recurrence scales with amplitude var
    eps_pct = 0.12 * diams
    rr3,det3,lam3,ent3 = measure(emb, eps_pct)
    results[name] = {'rms_uv': rms,
                     'fixed_eps10':{'RR':rr1,'DET':det1,'LAM':lam1,'ENT':ent1},
                     'fixed_RR05':{'RR':rr2,'DET':det2,'LAM':lam2,'ENT':ent2, 'eps':eps_rr05},
                     'pct_diam12':{'RR':rr3,'DET':det3,'LAM':lam3,'ENT':ent3, 'eps':eps_pct}}

import scipy.stats as stats
def corr(vals): return float(stats.spearmanr(centers, vals)[0])
rows = []
for n in results:
    r = results[n]
    rows.append((n, r['rms_uv'],
                 r['fixed_eps10']['RR'], r['fixed_eps10']['ENT'],
                 r['fixed_RR05']['RR'], r['fixed_RR05']['ENT'],
                 r['pct_diam12']['RR'], r['pct_diam12']['ENT']))
rows = np.array(rows)
rr10 = rows[:,2].astype(float); ent10 = rows[:,3].astype(float)
rr05 = rows[:,4].astype(float); ent05 = rows[:,5].astype(float)
rr12 = rows[:,6].astype(float); ent12 = rows[:,7].astype(float)

corr_summary = {
    'fixed_eps10':{'RR_vs_freq':corr(rr10),'ENT_vs_freq':corr(ent10)},
    'fixed_RR05':{'RR_vs_freq':corr(rr05),'ENT_vs_freq':corr(ent05)},
    'pct_diam12':{'RR_vs_freq':corr(rr12),'ENT_vs_freq':corr(ent12)},
}

res = {'per_band': results, 'spearman': corr_summary}
with open('hyp131_threshold_confound.json','w') as f: json.dump(res, f, indent=2)

fig, axs = plt.subplots(2,3,figsize=(12,7))
def p(ax, vals, title, ylab):
    ax.plot(centers, vals, marker='o')
    ax.set_xticks(centers); ax.set_xticklabels(list(bands.keys()), rotation=20)
    ax.set_title(title); ax.set_ylabel(ylab)
p(axs[0,0], rr10, 'RR fixed eps=10', 'RR')
p(axs[1,0], ent10, 'ENT fixed eps=10', 'ENT')
p(axs[0,1], rr05, 'RR ~5% fixed RR', 'RR')
p(axs[1,1], ent05, 'ENT ~5% fixed RR', 'ENT')
p(axs[0,2], rr12, 'RR 12% attractor diameter', 'RR')
p(axs[1,2], ent12, 'ENT 12% attractor diameter', 'ENT')
plt.tight_layout(); plt.savefig('hyp131_threshold_confound.png', dpi=150)
print(json.dumps(res, indent=2))
