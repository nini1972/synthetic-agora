import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
import json, os

# Load EEG
path = 'shared_agora/artifacts/neural_eeg.npz' if os.path.exists('shared_agora/artifacts/neural_eeg.npz') else '../../shared_agora/artifacts/neural_eeg.npz'
if not os.path.exists(path):
    from colony_lib.datasets import load_dataset
    d = load_dataset('neural_eeg')
    ch = d.data[:8192, 0]
    fs = d.sampling_rate
else:
    d = np.load(path)
    ch = d['data'][:8192, 0]
    fs = float(d['sampling_rate'])

# Band definitions
bands = {'Delta':(1,3), 'Theta':(4,7), 'Alpha':(8,12), 'Beta':(13,30), 'Gamma':(31,44)}
centers = np.array([2.25, 6.0, 10.0, 21.0, 37.5])

def bandpass(x, lo, hi, fs):
    nyq = fs/2
    sos = butter(4, [lo/nyq, hi/nyq], btype='band', output='sos')
    return sosfiltfilt(sos, x)

def embed(x, m=3, tau=2):
    N = len(x) - (m-1)*tau
    return np.vstack([x[i*tau : i*tau+N] for i in range(m)]).T

def rqa_metrics(emb, eps, min_diag=2, min_vert=2):
    N = emb.shape[0]
    D = np.sqrt(((emb[:,None,:] - emb[None,:,:])**2).sum(axis=2))
    R = (D <= eps).astype(np.uint8)
    rr = R.sum()/(N*N)
    # diagonals excluding main
    bd = np.zeros(N-1, dtype=int)
    for k in range(1, N):
        diag = np.diag(R, k)
        if diag.size==0: continue
        # lengths of runs of 1
        runs = []
        cur=0
        for v in diag:
            if v: cur+=1
            else:
                if cur>=min_diag: runs.append(cur)
                cur=0
        if cur>=min_diag: runs.append(cur)
        bd[k-1] = sum(runs)
    det = (R*np.tri(N,N,k=-1)).sum()  # number of recurrences below main diag
    if det<=0: return rr, 0., 0., 0.
    det = det/(R.sum()+1e-12)
    # laminarity verticals
    bv=np.zeros(N, dtype=int)
    for j in range(N):
        col=R[:,j]
        cur=0
        for v in col:
            if v: cur+=1
            else:
                if cur>=min_vert: bv[j]+=cur
                cur=0
        if cur>=min_vert: bv[j]+=cur
    lam = bv.sum()/(R.sum()+1e-12)
    # entropy of diagonal line distribution
    hist,bins=np.histogram(bd[bd>0], bins=np.arange(min_diag-0.5, bd.max()+1.5))
    p=hist/hist.sum()
    ent = -np.sum(p*np.log2(p+1e-12))
    return rr, det, lam, ent

raw = ch
out = {}
policies = ['fixed_eps=10', 'fixed_RR_0.05', 'pct_diameter_15']
for name,(lo,hi) in bands.items():
    x = bandpass(raw, lo, hi, fs)
    amp = np.sqrt(np.mean(x**2))
    # standardize for embedding? keep raw for fixed distance policy
    z = (x-x.mean())/x.std()
    emb = embed(z, 3, 2)
    diam = np.sqrt(((emb.max(axis=0)-emb.min(axis=0))**2).sum())
    # fixed eps 10
    rr, det, lam, ent = rqa_metrics(emb, 10.0)
    row = {'rms_uv': amp, 'diameter': diam, 'fixed_eps10':{'RR':rr,'DET':det,'LAM':lam,'ENT':ent}}
    # fixed RR ~0.05 by binary search eps
    loe, hie = 1e-6, 10*diam
    eps_rr = hie
    for _ in range(20):
        mid=(loe+hie)/2
        rr_mid,_,_,_ = rqa_metrics(emb, mid)
        if rr_mid>0.05: hie=mid
        else: loe=mid
        eps_rr=mid
    rr2,det2,lam2,ent2 = rqa_metrics(emb, eps_rr)
    row['fixed_RR05']={'RR':rr2,'DET':det2,'LAM':lam2,'ENT':ent2,'eps':eps_rr}
    # percentage of diameter fixed at 15%
    eps3 = 0.15*diam
    rr3,det3,lam3,ent3 = rqa_metrics(emb, eps3)
    row['pct_diam15']={'RR':rr3,'DET':det3,'LAM':lam3,'ENT':ent3,'eps':eps3}
    out[name]=row

# assemble
import scipy.stats as stats
rows=[]
for n in bands:
    r=out[n]
    rows.append([n, r['rms_uv'], r['diameter'],
                 r['fixed_eps10']['RR'], r['fixed_eps10']['ENT'],
                 r['fixed_RR05']['RR'], r['fixed_RR05']['ENT'],
                 r['pct_diam15']['RR'], r['pct_diam15']['ENT']])
rows=np.array(rows)

# Spearman vs center frequency for RR and ENT under each policy
def corr(vals):
    return stats.spearmanr(centers, vals.astype(float))[0]
c_rr10 = corr(rows[:,3]); c_ent10 = corr(rows[:,4])
c_rr05 = corr(rows[:,5]); c_ent05 = corr(rows[:,6])
c_rr15 = corr(rows[:,7]); c_ent15 = corr(rows[:,8])

# Save json
res={'band':{}, 'spearman_RR_ENT_vs_frequency': {'fixed_eps10': {'RR':c_rr10,'ENT':c_ent10},
                                                    'fixed_RR05': {'RR':c_rr05,'ENT':c_ent05},
                                                    'pct_diam15': {'RR':c_rr15,'ENT':c_ent15}}}
for i,n in enumerate(bands):
    res['band'][n] = {policies[0]: {'RR':float(rows[i,3]),'ENT':float(rows[i,4])},
                      policies[1]: {'RR':float(rows[i,5]),'ENT':float(rows[i,6])},
                      policies[2]: {'RR':float(rows[i,7]),'ENT':float(rows[i,8])}}
with open('hyp131_threshold_confound.json','w') as f:
    json.dump(res,f,indent=2)

fig,axs=plt.subplots(2,3,figsize=(12,7))
def plot_metric(ax, vals, title, ylab):
    ax.plot(centers, vals, marker='o')
    ax.set_xticks(centers)
    ax.set_xticklabels(list(bands.keys()), rotation=20)
    ax.set_title(title)
    ax.set_ylabel(ylab)
plot_metric(axs[0,0], rows[:,3].astype(float), 'RR fixed eps=10', 'RR')
plot_metric(axs[1,0], rows[:,4].astype(float), 'ENT fixed eps=10', 'ENT')
plot_metric(axs[0,1], rows[:,5].astype(float), 'RR fixed ~0.05', 'RR')
plot_metric(axs[1,1], rows[:,6].astype(float), 'ENT fixed ~0.05', 'ENT')
plot_metric(axs[0,2], rows[:,7].astype(float), 'RR 15% diameter', 'RR')
plot_metric(axs[1,2], rows[:,8].astype(float), 'ENT 15% diameter', 'ENT')
plt.tight_layout()
plt.savefig('hyp131_threshold_confound.png', dpi=150)

print(json.dumps(res, indent=2))
