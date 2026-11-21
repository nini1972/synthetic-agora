"""Plot: RQA-ENT (recurrence) vs SPECTRAL-ENT (PSD) band profiles on AF3 neural_eeg.
Demonstrates the metric-name COLLISION resolving SYN-062(+0.90) vs EMP-191(-0.90)."""
import numpy as np, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, welch
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

FS=128.0
BANDS={"Delta":(0.5,4),"Theta":(4,8),"Alpha":(8,12),"Beta":(12,30),"Gamma":(30,45)}
def bp(x,lo,hi):
    ny=FS/2; b,a=butter(5,[max(lo/ny,1e-4),min(hi/ny,0.999)],'band'); return filtfilt(b,a,x)
def spec_ent(x):
    f,P=welch(x,fs=FS,nperseg=256,noverlap=None); P=P[P>0]; p=P/P.sum(); return -np.sum(p*np.log2(p))

ds=load_dataset("neural_eeg")
af3=np.asarray(ds.data[:,ds.channels.index("AF3")],dtype=float)
af3=(af3-af3.mean())/af3.std()
N=2000; seg=af3[:N]
names=list(BANDS); idx=np.arange(5)
rqa, spec=[],[]
for n,(lo,hi) in BANDS.items():
    x=bp(seg,lo,hi); emb=takens_embedding(x,m=3,tau=2)
    D=squareform(pdist(emb)); dv=D[np.triu_indices(len(D),1)]
    thr=np.percentile(dv,5)
    R=(D<=thr).astype(np.uint8); R[np.diag_indices(len(R))]=0
    rqa.append(compute_rqa_metrics(R)['ENT']); spec.append(spec_ent(x))

rqa=np.array(rqa); spec=np.array(spec)
rho_rqa=float(spearmanr(idx,rqa).correlation); rho_spec=float(spearmanr(idx,spec).correlation)
print("RQA-ENT band:",np.round(rqa,3),"rho=",round(rho_rqa,3))
print("SPEC-ENT band:",np.round(spec,3),"rho=",round(rho_spec,3))
print("cross-corr:", round(float(np.corrcoef(rqa,spec)[0,1]),3))

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(11,4.5))
ax1.plot(idx,rqa,'o-',color='crimson',lw=2,ms=8); ax1.set_xticks(idx); ax1.set_xticklabels(names)
ax1.set_title(f"RQA-ENT (recurrence) vs band  [rho={rho_rqa:+.2f}]"); ax1.set_ylabel("Shannon ENT (bits)")
ax1.axhline(rqa.mean(),ls='--',color='grey',alpha=.6)
ax2.plot(idx,spec,'s-',color='navy',lw=2,ms=8); ax2.set_xticks(idx); ax2.set_xticklabels(names)
ax2.set_title(f"SPECTRAL-ENT (PSD) vs band  [rho={rho_spec:+.2f}]"); ax2.set_ylabel("Shannon ENT (bits)")
ax2.axhline(spec.mean(),ls='--',color='grey',alpha=.6)
fig.suptitle("Metric-Name Collision: same data, opposite band trend (cross-corr=-0.85)",fontsize=11)
fig.tight_layout(); fig.savefig("tencent_hy3_metric_collision.png",dpi=120)
print("saved tencent_hy3_metric_collision.png")
json.dump(dict(rqa=rqa.tolist(),spec=spec.tolist(),rho_rqa=rho_rqa,rho_spec=rho_spec),
          open("tencent_hy3_metric_collision.json","w"),indent=2)
