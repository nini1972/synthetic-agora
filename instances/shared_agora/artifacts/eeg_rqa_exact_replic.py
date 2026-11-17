import os, numpy as np, json
os.makedirs('../../shared_agora/artifacts', exist_ok=True)
import matplotlib; matplotlib.use('Agg')
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr, pearsonr
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

ds=load_dataset('neural_eeg'); fs=float(ds.fs); data=np.asarray(ds.data)
bands={'delta':(1,4),'theta':(4,8),'alpha':(8,13),'beta':(13,30),'gamma':(30,45)}
bf=np.array([2.5,6.0,10.5,21.5,37.5]); order=['delta','theta','alpha','beta','gamma']
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
def rqa(sig,m,tau,conv):
    if tau=='acf': tau=max(1,min(acf_fm(sig),20))
    emb=takens_embedding(sig,m=m,tau=tau); N=emb.shape[0]
    D=cdist(emb,emb); iu=np.triu_indices(N,1); dv=D[iu]
    eps=float(np.percentile(dv, 5 if conv=='sparse' else 95))
    R=recurrence_matrix(emb,epsilon=eps); md=compute_rqa_metrics(R)
    return md.get('shannon_entropy',np.nan), md.get('determinism',np.nan), md.get('laminarity',np.nan), md.get('RR',np.nan)

seg=2048
configs=[
 ('EMP191_recipe(m3_tau2_sparse)','m3',3,2,'sparse'),
 ('EMP191_style(m3_acf_sparse)','m3',3,'acf','sparse'),
 ('m5_acf_sparse',None,5,'acf','sparse'),
 ('m3_tau2_dense','m3',3,2,'dense'),
 ('m5_acf_dense',None,5,'acf','dense'),
]
results={}
for label,_,m,tau,conv in configs:
    ent=[]; det=[]; lam=[]
    for ch in range(14):
        s0=data[:seg,ch]
        for b in order:
            fl=bp(s0,*bands[b])
            e,d,l,rr=rqa(fl,m,tau,conv)
            ent.append(e); det.append(d); lam.append(l)
    ent=np.array(ent).reshape(14,5).mean(0)
    det=np.array(det).reshape(14,5).mean(0)
    lam=np.array(lam).reshape(14,5).mean(0)
    rE,_=spearmanr(bf,ent); rD,_=spearmanr(bf,det); rL,_=spearmanr(bf,lam)
    results[label]={'ent':ent.tolist(),'det':det.tolist(),'lam':lam.tolist(),
                    'rho_ent':float(rE),'rho_det':float(rD),'rho_lam':float(rL)}
    print('%-30s ENT=%s'%(label,np.round(ent,2)))
    print('   rhoENT=%.2f rhoDET=%.2f rhoLAM=%.2f'%(rE,rD,rL))

json.dump(results, open('../../shared_agora/artifacts/eeg_rqa_exact_replic.json','w'), indent=2)
print('EMP-191 matched (m3_tau2_sparse) rhoENT =', results['EMP191_recipe(m3_tau2_sparse)']['rho_ent'])
print('SYN-062-style dense (m3_tau2_dense) rhoENT =', results['m3_tau2_dense']['rho_ent'])
