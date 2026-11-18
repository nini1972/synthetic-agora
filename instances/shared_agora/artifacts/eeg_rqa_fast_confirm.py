import os, numpy as np, json, time
os.makedirs('../../shared_agora/artifacts', exist_ok=True)
import matplotlib; matplotlib.use('Agg')
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
t0=time.time()
ds=load_dataset('neural_eeg'); fs=float(ds.fs); data=np.asarray(ds.data)
bands={'delta':(1,4),'theta':(4,8),'alpha':(8,13),'beta':(13,30),'gamma':(30,45)}
bf=np.array([2.5,6.0,10.5,21.5,37.5]); order=['delta','theta','alpha','beta','gamma']
def bp(x,lo,hi):
    nyq=0.5*fs; lo=max(0.1,lo)/nyq; hi=min(hi,fs/2-1)/nyq
    b,a=butter(4,[lo,hi],btype='band'); return filtfilt(b,a,x)
def rqa(sig,m,tau,conv):
    emb=takens_embedding(sig,m=m,tau=tau); N=emb.shape[0]
    D=cdist(emb,emb); iu=np.triu_indices(N,1); dv=D[iu]
    eps=float(np.percentile(dv, 5 if conv=='sparse' else 95))
    R=recurrence_matrix(emb,epsilon=eps); md=compute_rqa_metrics(R)
    return md.get('shannon_entropy',np.nan)
seg=1024; chs=[0,13]
for conv,lab in [('sparse','EMP191_m3t2_sparse'),('dense','SYN062_m3t2_dense')]:
    ent=np.zeros((len(chs),5))
    for ci,ch in enumerate(chs):
        s0=data[:seg,ch]
        for bi,b in enumerate(order):
            fl=bp(s0,*bands[b]); ent[ci,bi]=rqa(fl,3,2,conv)
    em=ent.mean(0); rE,_=spearmanr(bf,em)
    print('%-22s ENT=%s rho=%.2f'%(lab,np.round(em,2),rE))
print('%.1fs'%(time.time()-t0))
