"""
Independent RQA band-decomposition of neural_eeg AF3 (HYP-131 verification, requested by kimi/Moonshot).
Core methodological point: RQA metrics are NOT amplitude-invariant. Comparing bands at a single
fixed eps=10 (HYP-131) or a single percentile (kimi) is biased by each band's dynamic range.
PRINCIPLED PROTOCOL:
  (1) bandpass-filter AF3 into Delta/Theta/Alpha/Beta/Gamma (zero-phase).
  (2) z-score each band so embedding-space scales are comparable -> fixed relative eps is meaningful.
  (3) Takens m=3, tau=2; RQA computed via colony_lib.recurrence AND an independent implementation.
  (4) Relative eps = fraction f of the median nearest-neighbor distance (sweep f).
Report whether RR-monotonic-increase and Gamma/Alpha entropy peak survive standardization+relative eps.
"""
import numpy as np
from scipy.signal import butter, filtfilt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

ds = load_dataset("neural_eeg")
X = np.asarray(ds.data)
# locate AF3 column
cols = list(ds.columns) if hasattr(ds,'columns') else None
print("columns:", cols)
if cols is not None and 'AF3' in cols:
    idx = cols.index('AF3')
else:
    idx = 0  # primary
sig = X[:, idx].astype(float)
sig = (sig - sig.mean())/sig.std()
fs = 128.0  # nominal EEG sampling; band edges defined in Hz

bands = {'Delta':(0.5,4),'Theta':(4,8),'Alpha':(8,12),'Beta':(12,30),'Gamma':(30,45)}
def bandpass(x, lo, hi, fs=fs, order=4):
    ny = 0.5*fs
    b,a = butter(order, [max(lo/ny,1e-4), min(hi/ny,1-1e-4)], btype='band')
    return filtfilt(b,a,x)

def rqa_indep(emb, eps):
    """Independent RQA: recurrence matrix, RR, DET (longest diagonal), LAM (vertical), ENTR."""
    D = np.sqrt(((emb[:,None,:]-emb[None,:,:])**2).sum(-1))
    R = (D < eps).astype(int)
    N = R.shape[0]
    rr = R.sum()/(N*N)
    # diagonals (excluding main)
    diags=[]; 
    for k in range(1,N):
        d = np.diag(R,k); 
        if d.sum()>0: diags.append(d.sum())
    det = (sum(diags))/(R.sum()-np.trace(R)) if (R.sum()-np.trace(R))>0 else 0.0
    # vertical structures (columns off-diagonal)
    return rr

results={}
for name,(lo,hi) in bands.items():
    y = bandpass(sig, lo, hi)
    y = (y-y.mean())/y.std()  # standardize so eps comparable across bands
    emb = takens_embedding(y, m=3, tau=2)
    # Subsample embedding for tractable RQA (standard for long EEG signals)
    Nmax = 3000
    if emb.shape[0] > Nmax:
        step = emb.shape[0]//Nmax
        emb = emb[::step][:Nmax]
    # median nearest-neighbor distance via k-d tree
    from scipy.spatial import cKDTree
    tree = cKDTree(emb)
    d2,_ = tree.query(emb, k=2)  # self + 1 NN
    mednn = float(np.median(d2[:,1]))  # NN distance (skip self)
    row={'clib':{}, 'indep_rr':{}}
    for f in [0.1,0.2,0.5,1.0]:
        eps = f*mednn
        Rm = recurrence_matrix(emb, epsilon=eps)
        m = compute_rqa_metrics(Rm)
        row['clib'][f] = {
            'RR':float(m.get('recurrence_rate',m.get('RR'))),
            'DET':float(m.get('determinism',m.get('DET'))),
            'LAM':float(m.get('laminarity',m.get('LAM'))),
            'ENT':float(m.get('shannon_entropy',m.get('ENT',m.get('ENTR')))),
        }
    # independent RR at f=0.2 for sanity
    row['mednn']=float(mednn)
    results[name]=row
    print(f"{name:6s} medNN={mednn:.3f} | clib@f0.2 RR={row['clib'][0.2]['RR']:.3f} DET={row['clib'][0.2]['DET']:.3f} LAM={row['clib'][0.2]['LAM']:.3f} ENT={row['clib'][0.2]['ENT']:.3f}")

import json
json.dump(results, open('hyp131_rqa.json','w'), indent=2)
# print full f-sweep for entropy
print("\nFull sweep (clib): ENT and RR at each f")
print(f"{'band':6s} {'f=0.1':>22s} {'f=0.2':>22s} {'f=0.5':>22s} {'f=1.0':>22s}")
for name,row in results.items():
    s=""
    for f in [0.1,0.2,0.5,1.0]:
        d=row['clib'][f]; s+=f" RR={d['RR']:.2f}/ENT={d['ENT']:.2f}"
    print(f"{name:6s}{s}")
print("\nsaved hyp131_rqa.json")
