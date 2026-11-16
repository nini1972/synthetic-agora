import os, numpy as np, json, time
os.makedirs('../../shared_agora/artifacts', exist_ok=True)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

ds = load_dataset('neural_eeg'); fs=float(ds.fs); data=np.asarray(ds.data)
bands={'delta':(1,4),'theta':(4,8),'alpha':(8,13),'beta':(13,30),'gamma':(30,45)}
bf={'delta':2.5,'theta':6.0,'alpha':10.5,'beta':21.5,'gamma':37.5}
order=['delta','theta','alpha','beta','gamma']
def bp(x,lo,hi):
    nyq=0.5*fs; lo=max(0.1,lo)/nyq; hi=min(hi,fs/2-1)/nyq
    b,a=butter(4,[lo,hi],btype='band'); return filtfilt(b,a,x)
def acf_fm(x,m=200):
    x=x-x.mean(); n=len(x)
    acf=np.correlate(x,x,mode='full')[n-1:]/(x.var()*n+1e-12)
    seg=acf[:int(min(m,n//4))]
    for i in range(1,len(seg)-1):
        if seg[i]<seg[i-1] and seg[i]<=seg[i+1]: return max(1,i)
    return max(1,int(np.argmin(np.abs(seg-1/np.e))))
def rqa_conv(sig,convention,m=5):
    tau=max(1,min(acf_fm(sig),20)); emb=takens_embedding(sig,m=m,tau=tau)
    D=cdist(emb,emb); iu=np.triu_indices(len(emb),k=1); dv=D[iu]
    # convention A (sparse): eps at 5th pct -> RR~0.05
    # convention B (dense):  eps at 95th pct -> RR~0.95
    eps=float(np.percentile(dv, 5 if convention=='A' else 95))
    R=recurrence_matrix(emb,epsilon=eps); md=compute_rqa_metrics(R)
    return md.get('shannon_entropy'), md.get('RR'), tau, len(emb)

seg=2048; chs=[0,6,13]
res={c:{b:[] for b in order} for c in ['A','B']}
for ch in chs:
    s0=data[:seg,ch]
    for b in order:
        fl=bp(s0,*bands[b])
        for c in ['A','B']:
            ent,rr,tau,L=rqa_conv(fl,c)
            res[c][b].append(ent)
menA={b:float(np.nanmean(res['A'][b])) for b in order}
menB={b:float(np.nanmean(res['B'][b])) for b in order}
f=np.array([bf[b] for b in order])
rA,_=spearmanr(f,[menA[b] for b in order])
rB,_=spearmanr(f,[menB[b] for b in order])
print('CONVENTION A (sparse RR~0.05) mean ENT per band:', {b:round(menA[b],3) for b in order})
print('CONVENTION B (dense  RR~0.95) mean ENT per band:', {b:round(menB[b],3) for b in order})
print('rho(ENT,freq) Convention A = %.3f'%rA)
print('rho(ENT,freq) Convention B = %.3f'%rB)
print('>>> SIGN FLIP UNDER THRESHOLD CONVENTION:', (rA*rB)<0)
plt.figure(figsize=(7,4))
plt.plot(f,[menA[b] for b in order],'o-',label='A: eps=p5 (RR~0.05)')
plt.plot(f,[menB[b] for b in order],'s--',label='B: eps=p95 (RR~0.95)')
plt.xlabel('Band freq (Hz)'); plt.ylabel('Mean ENT'); plt.legend()
plt.title('RQA ENT vs Band Freq: threshold-convention sign flip\nrhoA=%.2f  rhoB=%.2f'%(rA,rB))
plt.savefig('../../shared_agora/artifacts/eeg_rqa_threshold_test.png',dpi=130); plt.close()
json.dump({'menA':menA,'menB':menB,'rhoA':float(rA),'rhoB':float(rB),'sign_flip':bool((rA*rB)<0)},
          open('../../shared_agora/artifacts/eeg_rqa_threshold_test.json','w'),indent=2)
