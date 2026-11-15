import os, numpy as np, json, time
os.makedirs('artifacts', exist_ok=True)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr, pearsonr
from scipy.spatial.distance import cdist
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

print('--- loading neural_eeg ---')
ds = load_dataset('neural_eeg')
fs = float(ds.fs)
data = np.asarray(ds.data)            # (14980, 15)
cols = ds.columns                      # last is eyeDetection
ch_idx = list(range(14))               # 14 EEG channels
print('fs', fs, 'data', data.shape, 'cols', cols[:14])

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

def matched_rr(emb, target_rr=0.05):
    D = cdist(emb, emb)
    iu = np.triu_indices(len(emb), k=1)
    dvals = D[iu]
    eps = float(np.percentile(dvals, (1-target_rr)*100))
    R = recurrence_matrix(emb, epsilon=eps)
    m = compute_rqa_metrics(R)
    return m, eps

# ---- VALIDATION RUN (1 channel, 1 band) ----
print('--- validation: ch0 delta ---')
seg_len = 2048
sig0 = data[:seg_len, 0]
filt = bandpass(sig0, 1, 4, fs)
tau = acf_first_min(filt); tau = max(1, min(tau, 20))
print('tau', tau)
emb = takens_embedding(filt, m=5, tau=tau)
print('emb shape', emb.shape)
met, eps = matched_rr(emb, 0.05)
print('RQA keys:', list(met.keys()))
print('ENT', met.get('shannon_entropy'), 'RR', met.get('RR'), 'DET', met.get('determinism'), 'LAM', met.get('laminarity'))
print('VALIDATION OK')
