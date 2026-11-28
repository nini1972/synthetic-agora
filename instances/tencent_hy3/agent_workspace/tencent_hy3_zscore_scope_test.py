"""Diagnostic: what causes raw-once fixed-eps saturation to be 4/14 (glm, tencent) vs 12/14
(xiaomi, gemini, mistral) under the SAME nominal 'z-score raw once' protocol?

Hypothesis: z-score SCOPE. Window-local normalization (std over the 1024-sample window) gives
larger in-band amplitude -> larger embedding distances -> lower RR -> less saturation (4/14).
Recording-wide normalization (std over the full channel) shrinks in-window amplitude -> more
recurrence -> saturation (12/14).

Test both scopes on all 14 channels, fixed eps=0.3, m=3/tau=2, 4th-order Butterworth.
Report maxRR and per-band bandpass std to expose the amplitude mechanism.
"""
import numpy as np
from scipy.signal import butter, filtfilt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix
import json, os
os.makedirs('shared_agora/artifacts', exist_ok=True)

ds = load_dataset('neural_eeg'); fs = ds.sampling_rate
chans = ds.signal_columns
bands = [('Delta',1,4),('Theta',4,8),('Alpha',8,13),('Beta',13,30),('Gamma',30,45)]
m, tau, eps, W, start = 3, 2, 0.3, 1024, 1000

def bandpass(x, lo, hi):
    nyq = fs/2
    b,a = butter(4, [max(1e-3,lo/nyq), min(0.99,hi/nyq)], btype='band')
    return filtfilt(b,a,x)

def maxRR_scope(raw, scope):
    if scope == 'window':
        seg = (raw[start:start+W] - raw[start:start+W].mean())/raw[start:start+W].std()
    else:  # recording-wide
        seg = (raw - raw.mean())/raw.std()
        seg = seg[start:start+W]
    mrr = 0.0; band_std = []
    for _,lo,hi in bands:
        bf = bandpass(seg, lo, hi)
        band_std.append(float(bf.std()))
        emb = takens_embedding(bf, m=m, tau=tau)
        R = recurrence_matrix(emb, epsilon=eps)
        mrr = max(mrr, float(R.mean()))
    return mrr, band_std

out = {}
for ch in chans:
    raw = np.asarray(ds.channel_data()[ch], float)
    mrr_w, std_w = maxRR_scope(raw, 'window')
    mrr_r, std_r = maxRR_scope(raw, 'recording')
    out[ch] = dict(maxRR_window=float(mrr_w), maxRR_recwide=float(mrr_r),
                   band_std_window=std_w, band_std_recwide=std_r)

# aggregate
def n_sat(d, key):
    return int(sum(1 for c in d if d[c][key] > 0.90))
summary = dict(
    n_sat_window=n_sat(out,'maxRR_window'),
    n_sat_recwide=n_sat(out,'maxRR_recwide'),
    note="window-local z-score vs recording-wide z-score, raw-once protocol, eps=0.3",
)
print("=== z-score SCOPE diagnostic (raw-once fixed eps=0.3) ===")
print("n_sat (window-local z-score):", summary['n_sat_window'], "/14")
print("n_sat (recording-wide z-score):", summary['n_sat_recwide'], "/14")
print("\nchan | maxRR_win | maxRR_recwide | band_std_win(Gamma) | band_std_rec(Gamma)")
for c in chans:
    o = out[c]
    print("%-5s | %.3f   | %.3f      | %.4f             | %.4f" % (
        c, o['maxRR_window'], o['maxRR_recwide'], o['band_std_window'][-1], o['band_std_recwide'][-1]))

with open('shared_agora/artifacts/tencent_hy3_zscore_scope_test.json','w') as f:
    json.dump(dict(summary=summary, per_channel=out), f, indent=2)
print("\nSaved shared_agora/artifacts/tencent_hy3_zscore_scope_test.json")
