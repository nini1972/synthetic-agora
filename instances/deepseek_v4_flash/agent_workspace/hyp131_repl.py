import numpy as np
from scipy.signal import butter, filtfilt
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
from colony_lib.datasets import load_dataset

ds = load_dataset("neural_eeg")
X = np.asarray(ds.data, float)          # (14980, 15)
ch_names = ds.metadata["columns"]
fs = ds.sampling_rate
idx = ch_names.index("AF3")
sig = X[:, idx]
print("EEG shape:", X.shape, "AF3 idx", idx)
sig = np.asarray(sig, float)
print("signal len", len(sig), "fs", fs)
N = 3000            # use first 3000 samples (~23 s) for tractable RQA
sig = sig[:N]

bands = {"Delta":(0.5,4),"Theta":(4,8),"Alpha":(8,12),"Beta":(12,30),"Gamma":(30,45)}
def bandpass(s,lo,hi):
    ny=fs/2; hi=min(hi,ny*0.95)
    b,a=butter(4,[lo/ny,hi/ny],btype='band')
    return filtfilt(b,a,s)

def rqa(sig, eps_mode, eps_val, m=3, tau=2):
    s=(sig-sig.mean())/(sig.std()+1e-12)
    emb=takens_embedding(s, m=m, tau=tau)
    if eps_mode=="percentile":
        # pairwise distance percentile
        from scipy.spatial.distance import pdist
        d=pdist(emb[::3])
        eps=np.percentile(d, eps_val)
    else:
        eps=eps_val
    R=recurrence_matrix(emb, epsilon=eps)
    mtr=compute_rqa_metrics(R)
    return mtr, eps

print("\n=== eps=10 (dossier absolute) ===")
print(f"{'band':7s} {'RR':>7s} {'DET':>7s} {'LAM':>7s} {'ENT':>7s} {'eps':>7s}")
for name,(lo,hi) in bands.items():
    s=bandpass(sig,lo,hi)
    mtr,eps=rqa(s,"abs",10.0)
    print(f"{name:7s} {mtr['recurrence_rate']:7.3f} {mtr['determinism']:7.3f} {mtr['laminarity']:7.3f} {mtr['shannon_entropy']:7.3f} {eps:7.3f}")

print("\n=== eps=10th-percentile of pairwise distances (principled) ===")
print(f"{'band':7s} {'RR':>7s} {'DET':>7s} {'LAM':>7s} {'ENT':>7s} {'eps':>7s}")
rows=[]
for name,(lo,hi) in bands.items():
    s=bandpass(sig,lo,hi)
    mtr,eps=rqa(s,"percentile",10.0)
    rows.append((name,mtr))
    print(f"{name:7s} {mtr['recurrence_rate']:7.3f} {mtr['determinism']:7.3f} {mtr['laminarity']:7.3f} {mtr['shannon_entropy']:7.3f} {eps:7.3f}")

from scipy.stats import spearmanr
order=list(bands)
for key in ["recurrence_rate","determinism","laminarity","shannon_entropy"]:
    vals=[mtr[key] for _,mtr in rows]
    rho,p=spearmanr(range(len(vals)),vals)
    print(f"Spearman rho freq vs {key}: {rho:+.3f} (p={p:.4f})")
