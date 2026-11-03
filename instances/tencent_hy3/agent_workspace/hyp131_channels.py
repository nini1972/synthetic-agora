"""Multi-channel check: is RR(eps=10) monotonic in frequency band? (HYP-131 claim a)"""
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import pdist, squareform
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics
ds=load_dataset("neural_eeg"); X=np.asarray(ds.data,float); fs=128.0
bands=[('Delta',0.5,4),('Theta',4,8),('Alpha',8,12),('Beta',12,30),('Gamma',30,45)]
def bp(x,lo,hi,order=4):
    ny=0.5*fs; b,a=butter(order,[max(lo/ny,1e-4),min(hi/ny,1-1e-4)],'band'); return filtfilt(b,a,x)
NM=2500; chans=['AF3','F3','O1','T7','F4']
for ch in chans:
    idx=list(ds.columns).index(ch); raw=X[:,idx]
    RR=[]
    for nm,lo,hi in bands:
        y=bp(raw,lo,hi); emb=takens_embedding(y,m=3,tau=2)
        if emb.shape[0]>NM: emb=emb[::emb.shape[0]//NM][:NM]
        D=squareform(pdist(emb)); R=(D<10.0).astype(np.uint8)
        RR.append(compute_rqa_metrics(R)['recurrence_rate'])
    mono=all(RR[i]<RR[i+1] for i in range(len(RR)-1))
    vals=' '.join(f"{nm}{r:.2f}" for (nm,_,_),r in zip(bands,RR))
    print(f"{ch:4s} {vals}  monotonic? {mono}")
