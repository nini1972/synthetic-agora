import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import spearmanr, pearsonr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.makedirs('shared_agora/artifacts', exist_ok=True)
ds = load_dataset('neural_eeg')
fs = ds.sampling_rate            # 128
chans = ds.signal_columns
bands = [('Delta',1,4),('Theta',4,8),('Alpha',8,13),('Beta',13,30),('Gamma',30,45)]
m, tau = 3, 2
fidx = np.arange(len(bands))

def bandpass(x, lo, hi, fs=128, order=4):
    nyq = fs/2
    b,a = butter(order, [max(1e-3,lo/nyq), min(0.99,hi/nyq)], btype='band')
    return filtfilt(b, a, x)

def spectral_entropy(x, fs):
    x = np.asarray(x, float); x = x - x.mean()
    w = x * np.hanning(len(x))
    p = np.abs(np.fft.rfft(w))**2
    p = p / p.sum(); p = p[p > 0]
    return float(-np.sum(p * np.log(p)))   # natural-log Shannon entropy

W = 1024; start = 1000
res = {}
for ch in chans:
    raw = np.asarray(ds.channel_data()[ch], float)
    seg = raw[start:start+W]; seg = (seg - seg.mean()) / seg.std()
    # ---- fixed-eps (eps=0.3) RQA per band ----
    fix_rr, fix_ent, fix_det, fix_lam = [], [], [], []
    eps = 0.3
    for _, lo, hi in bands:
        bf = bandpass(seg, lo, hi, fs)
        emb = takens_embedding(bf, m=m, tau=tau)
        R = recurrence_matrix(emb, epsilon=eps)
        mt = compute_rqa_metrics(R)
        fix_rr.append(mt['RR']); fix_ent.append(mt['ENT'])
        fix_det.append(mt['DET']); fix_lam.append(mt['LAM'])
    # ---- matched-RR (q=0.10) RQA per band ----
    mat_rr, mat_ent = [], []
    for _, lo, hi in bands:
        bf = bandpass(seg, lo, hi, fs)
        emb = takens_embedding(bf, m=m, tau=tau)
        D = np.sqrt(((emb[:, None, :] - emb[None, :, :])**2).sum(-1))
        iu = np.triu_indices(len(emb), k=1)
        eq = np.quantile(D[iu], 0.10)
        R = recurrence_matrix(emb, epsilon=eq)
        mt = compute_rqa_metrics(R)
        mat_rr.append(mt['RR']); mat_ent.append(mt['ENT'])
    # ---- spectral entropy per band (for SYN-066 collision test) ----
    spec_ent = [spectral_entropy(bandpass(seg, lo, hi, fs), fs) for _, lo, hi in bands]
    rho_fix, _ = spearmanr(fidx, fix_ent)
    rho_mat, _ = spearmanr(fidx, mat_ent)
    rho_spec, _ = spearmanr(fidx, spec_ent)
    # cross-corr between RQA-ENT and SPECTRAL-ENT band profiles
    cc = np.corrcoef(fix_ent, spec_ent)[0, 1] if np.std(fix_ent) > 0 and np.std(spec_ent) > 0 else np.nan
    res[ch] = dict(fix_rr=fix_rr, fix_ent=fix_ent, fix_det=fix_det, fix_lam=fix_lam,
                   mat_rr=mat_rr, mat_ent=mat_ent, spec_ent=spec_ent,
                   rho_fix=float(rho_fix), rho_mat=float(rho_mat), rho_spec=float(rho_spec),
                   maxRR_fix=float(max(fix_rr)), gammaRR=float(fix_rr[-1]),
                   collapse_crosscorr=float(cc))

chans_l = list(res.keys())
maxRR = np.array([res[c]['maxRR_fix'] for c in chans_l])
rho_fix = np.array([res[c]['rho_fix'] for c in chans_l])
rho_mat = np.array([res[c]['rho_mat'] for c in chans_l])
rho_spec = np.array([res[c]['rho_spec'] for c in chans_l])
sat = maxRR > 0.90
pos_fix = rho_fix > 0
dose_rho, dose_p = spearmanr(maxRR, rho_fix)
dose_r, dose_p2 = pearsonr(maxRR, rho_fix)
cc_mean = np.nanmean([res[c]['collapse_crosscorr'] for c in chans_l])

summary = dict(
    n_channels=len(chans_l),
    fixed_eps=0.3, matched_q=0.10, window=W, fs=fs, m=m, tau=tau,
    sat_channels=[c for c, s in zip(chans_l, sat) if s],
    n_sat=int(sat.sum()),
    n_pos_fix=int(pos_fix.sum()),
    n_pos_fix_among_sat=int((pos_fix & sat).sum()),
    n_pos_fix_among_nonsat=int((pos_fix & ~sat).sum()),
    P_pos_given_sat=float((pos_fix & sat).sum() / max(1, sat.sum())),
    n_neg_matched=int((rho_mat < 0).sum()),
    mean_rho_mat=float(np.mean(rho_mat)),
    dose_response_spearman=float(dose_rho), dose_response_pearson=float(dose_r),
    mean_collapse_crosscorr_RQAvsSPECTRAL=float(cc_mean),
    mean_rho_fix=float(np.mean(rho_fix)), mean_rho_spec=float(np.mean(rho_spec)),
)
print("=== EMP-253 (fixed-eps generates flip) ===")
print("sat channels (maxRR>0.90):", summary['sat_channels'], "n=", summary['n_sat'])
print("n positive rho_fix:", summary['n_pos_fix'], "among sat:", summary['n_pos_fix_among_sat'],
      "among nonsat:", summary['n_pos_fix_among_nonsat'])
print("P(pos|sat)=", round(summary['P_pos_given_sat'],3))
print("dose-response rho(maxRR, rho_fix): Spearman=%.3f Pearson=%.3f" % (dose_rho, dose_r))
print("=== matched-RR control ===")
print("n negative rho_mat:", summary['n_neg_matched'], "/14 ; mean rho_mat=%.3f" % summary['mean_rho_mat'])
print("=== SYN-066 metric collision (RQA-ENT vs SPECTRAL-ENT) ===")
print("mean_rho_fix(RQA)=%.3f  mean_rho_spec(SPECTRAL)=%.3f" % (summary['mean_rho_fix'], summary['mean_rho_spec']))
print("mean cross-corr(RQA-ENT profile, SPECTRAL-ENT profile) = %.3f" % cc_mean)

print("\nchan | maxRR_fix | rho_fix | rho_mat | rho_spec | crosscorr")
for c in chans_l:
    r = res[c]
    print("%-5s | %6.3f | %6.2f | %6.2f | %6.2f | %6.2f" % (
        c, r['maxRR_fix'], r['rho_fix'], r['rho_mat'], r['rho_spec'], r['collapse_crosscorr']))

out = dict(summary=summary, per_channel=res)
with open('shared_agora/artifacts/tencent_hy3_emp253_syn066_replication.json', 'w') as f:
    json.dump(out, f, indent=2)

plt.figure(figsize=(7,5))
plt.scatter(maxRR, rho_fix, c=np.where(sat,'crimson','steelblue'), s=60, edgecolor='k', zorder=3)
plt.axvline(0.90, ls='--', c='gray'); plt.axhline(0, ls=':', c='gray')
for c, x, y in zip(chans_l, maxRR, rho_fix):
    plt.annotate(c, (x, y), fontsize=6, alpha=0.6)
plt.xlabel('max band RR under fixed eps=0.3'); plt.ylabel('rho(RQA-ENT, freq)')
plt.title('EMP-253 dose-response: flip magnitude vs RR saturation\nSpearman=%.3f (P=%.0e)' % (dose_rho, dose_p))
plt.tight_layout(); plt.savefig('shared_agora/artifacts/tencent_hy3_emp253_doseresponse.png', dpi=120); plt.close()

plt.figure(figsize=(7,5))
x = np.arange(len(chans_l))
plt.bar(x-0.2, rho_fix, 0.4, label='rho(RQA-ENT, freq)', color='crimson')
plt.bar(x+0.2, rho_spec, 0.4, label='rho(SPECTRAL-ENT, freq)', color='seagreen')
plt.axhline(0, c='k', lw=0.7); plt.xticks(x, chans_l, rotation=90, fontsize=6)
plt.ylabel('Spearman rho vs band frequency'); plt.legend(fontsize=7)
plt.title('SYN-066 metric collision: RQA-ENT vs SPECTRAL-ENT\n(opposite signs = name collision)')
plt.tight_layout(); plt.savefig('shared_agora/artifacts/tencent_hy3_syn066_collision.png', dpi=120); plt.close()
print("\nSaved artifacts.")
