import os, numpy as np, json, time
os.makedirs('../../shared_agora/artifacts', exist_ok=True)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr, pearsonr
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

t0 = time.time()
ds = load_dataset('neural_eeg')
fs = float(ds.fs)
data = np.asarray(ds.data)            # (14980, 15)
ch_idx = list(range(14))              # 14 EEG channels
print('fs', fs, 'data', data.shape)

bands = {'delta':(1,4),'theta':(4,8),'alpha':(8,13),'beta':(13,30),'gamma':(30,45)}
band_freq = {'delta':2.5,'theta':6.0,'alpha':10.5,'beta':21.5,'gamma':37.5}
band_order = ['delta','theta','alpha','beta','gamma']

def bandpass(x, lo, hi, fs, order=4):
    nyq = 0.5*fs
    lo = max(0.1, lo)/nyq
    hi = min(hi, fs/2-1)/nyq
    b,a = butter(order, [lo, hi], btype='band')
    return filtfilt(b,a,x)

def acf_first_min(x, maxlag=200):
    x = x - x.mean(); n=len(x)
    acf = np.correlate(x, x, mode='full')[n-1:]/ (x.var()*n + 1e-12)
    lag = int(min(maxlag, n//4))
    seg = acf[:lag]
    for i in range(1, len(seg)-1):
        if seg[i] < seg[i-1] and seg[i] <= seg[i+1]:
            return max(1, i)
    return max(1, int(np.argmin(np.abs(seg - 1/np.e))))

def rqa_matched(sig, target_rr=0.05, m=5, tau=None):
    if tau is None:
        tau = acf_first_min(sig); tau = max(1, min(tau, 20))
    emb = takens_embedding(sig, m=m, tau=tau)
    D = cdist(emb, emb)
    iu = np.triu_indices(len(emb), k=1)
    dvals = D[iu]
    # CORRECT: to get ~target_rr fraction below epsilon, use target_rr-th percentile
    eps = float(np.percentile(dvals, target_rr*100))
    R = recurrence_matrix(emb, epsilon=eps)
    mdict = compute_rqa_metrics(R)
    return mdict, eps, tau, len(emb)

seg_len = 2048
m_fixed = 5
target_rr = 0.05

# results[band] = list of ENT across channels
res_ent = {b: [] for b in band_order}
res_det = {b: [] for b in band_order}
res_lam = {b: [] for b in band_order}
res_rr  = {b: [] for b in band_order}
meta_rows = []
for ch in ch_idx:
    sig0 = data[:seg_len, ch]
    for b in band_order:
        lo,hi = bands[b]
        filt = bandpass(sig0, lo, hi, fs)
        try:
            md, eps, tau, L = rqa_matched(filt, target_rr=target_rr, m=m_fixed)
            ent = md.get('shannon_entropy', np.nan)
            det = md.get('determinism', np.nan)
            lam = md.get('laminarity', np.nan)
            rr  = md.get('RR', np.nan)
            res_ent[b].append(ent); res_det[b].append(det); res_lam[b].append(lam); res_rr[b].append(rr)
            meta_rows.append((ch,b,tau,eps,L,ent,det,lam,rr))
        except Exception as e:
            print('ERR ch%d %s: %s'%(ch,b,repr(e)[:80]))
            res_ent[b].append(np.nan); res_det[b].append(np.nan); res_lam[b].append(np.nan); res_rr[b].append(np.nan)

mean_ent = {b: float(np.nanmean(res_ent[b])) for b in band_order}
mean_det = {b: float(np.nanmean(res_det[b])) for b in band_order}
mean_lam = {b: float(np.nanmean(res_lam[b])) for b in band_order}

freqs = np.array([band_freq[b] for b in band_order])
ents  = np.array([mean_ent[b] for b in band_order])
dets  = np.array([mean_det[b] for b in band_order])
lams  = np.array([mean_lam[b] for b in band_order])

rho_ent, p_ent = spearmanr(freqs, ents)
rho_ent_p, p_ent_p = pearsonr(freqs, ents)
rho_det, p_det = spearmanr(freqs, dets)
rho_lam, p_lam = spearmanr(freqs, lams)

print('=== mean RQA per band (matched RR=%.2f, m=%d) ==='%(target_rr, m_fixed))
for b in band_order:
    print('%-6s f=%.1f ENT=%.3f DET=%.3f LAM=%.3f'%(b, band_freq[b], mean_ent[b], mean_det[b], mean_lam[b]))
print('rho(ENT,freq) Spearman=%.3f (p=%.2e) Pearson=%.3f'%(rho_ent,p_ent,rho_ent_p))
print('rho(DET,freq) Spearman=%.3f (p=%.2e)'%(rho_det,p_det))
print('rho(LAM,freq) Spearman=%.3f (p=%.2e)'%(rho_lam,p_lam))
decr = all(ents[i] >= ents[i+1] for i in range(len(ents)-1))
print('ENT monotonically decreasing across bands?', decr)

# Plot
plt.figure(figsize=(8,5))
plt.plot(freqs, ents, 'o-', label='ENT (shannon)')
ax2 = plt.gca().twinx()
ax2.plot(freqs, dets, 's--', color='orange', label='DET')
plt.xlabel('Band center frequency (Hz)'); plt.ylabel('Mean RQA ENT')
ax2.set_ylabel('Mean RQA DET')
plt.title('EEG RQA vs Band Freq (matched RR=%.2f, m=%d)\nrho_ENT=%.2f'%(target_rr,m_fixed,rho_ent))
plt.savefig('../../shared_agora/artifacts/eeg_rqa_definitive.png', dpi=130); plt.close()

out = {
  'config': {'seg_len':seg_len,'m':m_fixed,'target_rr':target_rr,'fs':fs},
  'mean_ent':mean_ent,'mean_det':mean_det,'mean_lam':mean_lam,
  'rho_ent_spearman':float(rho_ent),'p_ent':float(p_ent),'rho_ent_pearson':float(rho_ent_p),
  'rho_det_spearman':float(rho_det),'rho_lam_spearman':float(rho_lam),
  'mono_decreasing_ent':bool(decr),'elapsed_s':time.time()-t0
}
with open('../../shared_agora/artifacts/eeg_rqa_definitive.json','w') as f:
    json.dump(out, f, indent=2)
print('elapsed %.1fs'%(time.time()-t0))
