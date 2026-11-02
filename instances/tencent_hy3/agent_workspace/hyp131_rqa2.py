"""HYP-131 verification: raw-amplitude artifact vs dynamical RQA signature.
Reuse one distance matrix per band for all eps thresholds (RR = CDF of distances)."""
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import pdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

ds = load_dataset("neural_eeg")
X = np.asarray(ds.data, float)
idx = list(ds.columns).index('AF3')
raw = X[:, idx]
fs = 128.0
bands = {'Delta':(0.5,4),'Theta':(4,8),'Alpha':(8,12),'Beta':(12,30),'Gamma':(30,45)}
def bp(x, lo, hi, fs=fs, order=4):
    ny=0.5*fs; b,a=butter(order,[max(lo/ny,1e-4),min(hi/ny,1-1e-4)],'band'); return filtfilt(b,a,x)
def rqa_from_D(D, eps):
    R=(D<eps).astype(np.uint8); m=compute_rqa_metrics(R)
    return {k:float(m.get(k,0.0)) for k in ['recurrence_rate','determinism','laminarity','shannon_entropy','DET','LAM','ENT']}

NM=3000; order=['Delta','Theta','Alpha','Beta','Gamma']
out={'A_raw_eps10':{}, 'B_std_k':{}, 'B_adaptive':{}}
for name,(lo,hi) in bands.items():
    y=bp(raw, lo, hi)
    embA=takens_embedding(y, m=3, tau=2)
    if embA.shape[0]>NM: embA=embA[::embA.shape[0]//NM][:NM]
    DA=pdist(embA)
    out['A_raw_eps10'][name]=rqa_from_D(DA,10.0)
    ys=(y-y.mean())/y.std()
    embB=takens_embedding(ys, m=3, tau=2)
    if embB.shape[0]>NM: embB=embB[::embB.shape[0]//NM][:NM]
    DB=pdist(embB); s=np.std(DB)
    out['B_std_k'][name]={}
    for k in [0.05,0.1,0.2]:
        out['B_std_k'][name][k]=rqa_from_D(DB,k*s)
    # adaptive: eps for RR~0.05 = 5th percentile of nonzero distances
    eps_ad=np.percentile(DA[DA>0],5)
    out['B_adaptive'][name]=rqa_from_D(DA,eps_ad); out['B_adaptive'][name]['_eps']=float(eps_ad); out['B_adaptive'][name]['_rr']=float(out['B_adaptive'][name]['recurrence_rate'])

print("=== Protocol A: HYP-131 EXACT (raw band, eps=10) ===")
print(f"{'band':6s} {'RR':>6s} {'DET':>6s} {'LAM':>6s} {'ENT':>6s}")
for n in order: m=out['A_raw_eps10'][n]; print(f"{n:6s} {m['recurrence_rate']:.3f} {m['determinism']:.3f} {m['laminarity']:.3f} {m['shannon_entropy']:.3f}")
rrA=[out['A_raw_eps10'][n]['recurrence_rate'] for n in order]
print("A monotonic RR Delta->Gamma?", all(rrA[i]<rrA[i+1] for i in range(len(rrA)-1)))
print("\n=== Protocol B1: standardized, eps=k*std(emb) ===")
for k in [0.05,0.1,0.2]:
    print(f"-- k={k} --  ", ' '.join(f"{n}:RR={out['B_std_k'][n][k]['recurrence_rate']:.2f}/ENT={out['B_std_k'][n][k]['shannon_entropy']:.2f}" for n in order))
print("\n=== Protocol B2: raw band, ADAPTIVE eps->RR=0.05 (compare DET/LAM/ENT at equal RR) ===")
print(f"{'band':6s} {'eps':>8s} {'RR':>6s} {'DET':>6s} {'LAM':>6s} {'ENT':>6s}")
for n in order: m=out['B_adaptive'][n]; print(f"{n:6s} {m['_eps']:.3f} {m['recurrence_rate']:.3f} {m['determinism']:.3f} {m['laminarity']:.3f} {m['shannon_entropy']:.3f}")
import json
json.dump(out, open('hyp131_rqa.json','w'), indent=2, default=float)
print("\nsaved hyp131_rqa.json")
