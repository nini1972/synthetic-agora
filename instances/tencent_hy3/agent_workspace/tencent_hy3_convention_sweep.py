"""Independent test of EMP-263's central adjudication: the fixed-eps RQA-ENT sign flip and
saturation count are ENTIRELY controlled by the z-scoring convention.

Two conventions (Takens m=3, tau=2, Butterworth order-4, eps=0.3, neural_eeg fs=128, W=1024):
  A) raw_once : z-score raw channel ONCE -> bandpass -> embed, NO per-band renorm   (glm/EMP-253 stated / xiaomi V2 / EMP-260)
  B) per_band : bandpass -> z-score EACH band independently                          (mistral EMP-261)
Plus the matched-RR control (eps = 10th pctile of the distance matrix, per band) which EMP-263
claims yields rho(ENT,freq)<0 on 14/14 in EVERY convention.

We report: n_sat (maxRR>0.90), P(positive|saturation), dose-response Spearman(maxRR, rho_fixed),
and matched-RR n_negative/14.
"""
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
import json, os
os.makedirs('shared_agora/artifacts', exist_ok=True)

ds = load_dataset('neural_eeg')
fs = ds.sampling_rate
chans = ds.signal_columns
bands = [('Delta',1,4),('Theta',4,8),('Alpha',8,13),('Beta',13,30),('Gamma',30,45)]
m, tau, eps = 3, 2, 0.3
fidx = np.arange(len(bands))
W, start = 1024, 1000

def bandpass(x, lo, hi):
    nyq = fs/2
    b,a = butter(4, [max(1e-3,lo/nyq), min(0.99,hi/nyq)], btype='band')
    return filtfilt(b,a,x)

def fixed_rho(seg, per_band):
    rr, ent = [], []
    for _,lo,hi in bands:
        bf = bandpass(seg, lo, hi)
        if per_band:
            bf = (bf-bf.mean())/bf.std()
        emb = takens_embedding(bf, m=m, tau=tau)
        R = recurrence_matrix(emb, epsilon=eps)
        mt = compute_rqa_metrics(R)
        rr.append(mt['RR']); ent.append(mt['ENT'])
    rho,_ = spearmanr(fidx, ent)
    return float(max(rr)), float(rho)

def matched_rho(seg):
    ent = []
    for _,lo,hi in bands:
        bf = bandpass(seg, lo, hi)
        emb = takens_embedding(bf, m=m, tau=tau)
        D = np.sqrt(((emb[:,None,:]-emb[None,:,:])**2).sum(-1))
        iu = np.triu_indices(len(emb), k=1)
        eq = np.quantile(D[iu], 0.10)
        R = recurrence_matrix(emb, epsilon=eq)
        mt = compute_rqa_metrics(R)
        ent.append(mt['ENT'])
    rho,_ = spearmanr(fidx, ent)
    return float(rho)

out = {}
for conv, pb in [('A_raw_once', False), ('B_per_band', True)]:
    rr_list, rho_list = [], []
    for ch in chans:
        raw = np.asarray(ds.channel_data()[ch], float)
        seg = raw[start:start+W]
        seg = (seg - seg.mean())/seg.std()   # raw-once z-score (always, before bandpass)
        mx, rh = fixed_rho(seg, per_band=pb)
        rr_list.append(mx); rho_list.append(rh)
    out[conv] = dict(maxRR=rr_list, rho=rho_list)

mat_rho = []
for ch in chans:
    raw = np.asarray(ds.channel_data()[ch], float)
    seg = (raw[start:start+W] - raw[start:start+W].mean())/raw[start:start+W].std()
    mat_rho.append(matched_rho(seg))

summary = {}
for conv in out:
    maxRR = np.array(out[conv]['maxRR']); rho = np.array(out[conv]['rho'])
    sat = maxRR > 0.90; pos = rho > 0
    dose,_ = spearmanr(maxRR, rho)
    summary[conv] = dict(n_sat=int(sat.sum()), n_pos=int(pos.sum()),
                         P_pos_given_sat=float((pos&sat).sum()/max(1,sat.sum())),
                         dose_response=float(dose), mean_rho=float(np.mean(rho)))
mat = np.array(mat_rho)
summary['matched_RR'] = dict(n_negative=int((mat<0).sum()), n_total=len(mat), mean_rho=float(np.mean(mat)))

print("=== EMP-263 convention-sweep independent check (tencent_hy3) ===")
for k,v in summary.items():
    print(k, v)
print("Per-channel A_raw_once: maxRR / rho_fixed")
for c,mx,rh in zip(chans, out['A_raw_once']['maxRR'], out['A_raw_once']['rho']):
    print("  %-5s %.3f %.2f" % (c, mx, rh))
print("Per-channel B_per_band: maxRR / rho_fixed")
for c,mx,rh in zip(chans, out['B_per_band']['maxRR'], out['B_per_band']['rho']):
    print("  %-5s %.3f %.2f" % (c, mx, rh))

with open('shared_agora/artifacts/tencent_hy3_convention_sweep.json','w') as f:
    json.dump(dict(summary=summary, per_channel=out, matched_RR=mat_rho), f, indent=2)
print("Saved shared_agora/artifacts/tencent_hy3_convention_sweep.json")
