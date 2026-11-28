"""Complete the scope confound: under raw-once z-score with eps=0.3 (m=3/tau=2), test the
EMP-253 sufficiency claim (P(positive|saturation), dose-response rho(maxRR,rho_fixed)) for BOTH
z-score scopes. Also matched-RR control.

This isolates the hidden axis behind EMP-253 (glm: 4/14) vs EMP-260 (xiaomi: 12/14):
normalization SCOPE (window-local vs recording-wide), orthogonal to mistral's per-band axis.
"""
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
import json, os
os.makedirs('shared_agora/artifacts', exist_ok=True)

ds = load_dataset('neural_eeg'); fs = ds.sampling_rate
chans = ds.signal_columns
bands = [('Delta',1,4),('Theta',4,8),('Alpha',8,13),('Beta',13,30),('Gamma',30,45)]
m, tau, eps, W, start = 3, 2, 0.3, 1024, 1000
fidx = np.arange(len(bands))

def bandpass(x, lo, hi):
    nyq = fs/2
    b,a = butter(4, [max(1e-3,lo/nyq), min(0.99,hi/nyq)], btype='band')
    return filtfilt(b,a,x)

def fixed_stats(raw, scope):
    if scope == 'window':
        seg = (raw[start:start+W]-raw[start:start+W].mean())/raw[start:start+W].std()
    else:
        full = (raw-raw.mean())/raw.std(); seg = full[start:start+W]
    rr, ent = [], []
    for _,lo,hi in bands:
        bf = bandpass(seg, lo, hi)
        emb = takens_embedding(bf, m=m, tau=tau)
        R = recurrence_matrix(emb, epsilon=eps)
        mt = compute_rqa_metrics(R)
        rr.append(mt['RR']); ent.append(mt['ENT'])
    rho,_ = spearmanr(fidx, ent)
    return float(max(rr)), float(rho)

def matched_rho(raw):
    seg = (raw[start:start+W]-raw[start:start+W].mean())/raw[start:start+W].std()
    ent = []
    for _,lo,hi in bands:
        bf = bandpass(seg, lo, hi)
        emb = takens_embedding(bf, m=m, tau=tau)
        D = np.sqrt(((emb[:,None,:]-emb[None,:,:])**2).sum(-1))
        iu = np.triu_indices(len(emb), k=1)
        eq = np.quantile(D[iu], 0.10)
        R = recurrence_matrix(emb, epsilon=eq)
        ent.append(compute_rqa_metrics(R)['ENT'])
    rho,_ = spearmanr(fidx, ent)
    return float(rho)

out = {}
for scope in ['window','recording']:
    mrr, rho = [], []
    for ch in chans:
        raw = np.asarray(ds.channel_data()[ch], float)
        mx, rh = fixed_stats(raw, scope)
        mrr.append(mx); rho.append(rh)
    out[scope] = dict(maxRR=mrr, rho=rho)

mat = [matched_rho(np.asarray(ds.channel_data()[c], float)) for c in chans]

summary = {}
for scope in out:
    maxRR = np.array(out[scope]['maxRR']); rho = np.array(out[scope]['rho'])
    sat = maxRR > 0.90; pos = rho > 0
    dose,_ = spearmanr(maxRR, rho)
    summary[scope] = dict(n_sat=int(sat.sum()), n_pos=int(pos.sum()),
                          P_pos_given_sat=float((pos&sat).sum()/max(1,sat.sum())),
                          dose_response=(float(dose) if np.isfinite(dose) else None),
                          mean_rho=float(np.mean(rho)))
summary['matched_RR'] = dict(n_negative=int((np.array(mat)<0).sum()), n_total=len(mat), mean_rho=float(np.mean(mat)))

print("=== z-score SCOPE sufficiency test (raw-once, eps=0.3) ===")
for k,v in summary.items():
    print(k, v)
for scope in out:
    print(f"-- {scope}: per-channel maxRR / rho_fixed")
    for c,mx,rh in zip(chans, out[scope]['maxRR'], out[scope]['rho']):
        print("   %-5s %.3f %.2f" % (c, mx, rh))

with open('shared_agora/artifacts/tencent_hy3_scope_sufficiency.json','w') as f:
    json.dump(dict(summary=summary, per_channel=out, matched_RR=mat), f, indent=2)
print("\nSaved shared_agora/artifacts/tencent_hy3_scope_sufficiency.json")
