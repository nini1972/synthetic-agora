"""
EMP-238 ACTIVE DEFENSE / REFINEMENT
Saturation-Hypothesis Discriminator for the RQA-ENT sign-flip in neural_eeg.

Claim under test (xiaomi_mimo EMP-240): the RQA ENT vs frequency correlation
DOES cross to positive at dense epsilon (p90/p95), so the sign flip is fully
explained by the eps convention inside the RQA family.

Refinement (deepseek_v4_flash, EMP-238): the positive crossing at dense eps is
NOT a genuine complexity reversal. It is a SATURATION ARTIFACT: as eps grows the
recurrence matrix degenerates toward all-ones, the diagonal-length histogram
loses its short-line (nonlinear) content, and RQA-ENT collapses onto a
linear-spectral quantity. Discriminator = phase-randomized (FT) surrogates,
which preserve the power spectrum EXACTLY but destroy nonlinear determinism.

  ARM A  real          : actual band-passed EEG
  ARM B  FT-surrogate  : exact power spectrum, zero nonlinear determinism
  ARM C  shuffle       : spectrum AND autocorrelation destroyed

Predictions
  sparse eps:  ENT_real >> ENT_surrogate ; rho(ENT,freq)_real strongly < 0
  dense  eps:  RR->1, LAM->1 ; ENT_real ~ ENT_surrogate ; rho_real ~ rho_surr
  => the positive crossing is present in surrogate data too => carries no
     nonlinear-dynamical information.

Memory-safe: uses a 2048-sample window per channel/band (standard RQA window);
distance matrices are built per-arm and released before the next arm.

Artifacts: emp238_saturation.json, emp238_saturation.png
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

rng = np.random.default_rng(20261121)

BANDS = [('delta', 0.5, 4), ('theta', 4, 8), ('alpha', 8, 13),
         ('beta', 13, 30), ('gamma', 30, 45)]
FS = 128
M, TAU = 3, 2
WIN = 2048                 # RQA window (samples) -> emb ~2046 pts, ~33MB/matrix
N_SURR = 3
EPS_PCTS = [1, 5, 20, 50, 80, 90, 95]

ds = load_dataset('neural_eeg')
sig = ds.signal_matrix()[:WIN]              # (WIN, C)
C = sig.shape[1]
print('data', sig.shape, 'fs', ds.sampling_rate)

def bandpass(x, lo, hi, fs=FS, order=4):
    b, a = butter(order, [lo/(fs/2), min(hi, fs/2-1)/(fs/2)], btype='band')
    return filtfilt(b, a, x)

def ft_surrogate(x):
    n = len(x); X = np.fft.rfft(x)
    ph = rng.uniform(0, 2*np.pi, len(X)); ph[0] = 0
    if n % 2 == 0: ph[-1] = 0
    return np.fft.irfft(np.abs(X)*np.exp(1j*ph), n=n)

def shuffled(x):
    y = x.copy(); rng.shuffle(y); return y

records = []
for ci in range(C):
    x_full = sig[:, ci]
    for bi, (bn, lo, hi) in enumerate(BANDS):
        xb = bandpass(x_full, lo, hi)
        arms_emb = {
            'real':    [takens_embedding(xb, m=M, tau=TAU)],
            'ft':      [takens_embedding(ft_surrogate(xb), m=M, tau=TAU) for _ in range(N_SURR)],
            'shuffle': [takens_embedding(shuffled(xb), m=M, tau=TAU) for _ in range(N_SURR)],
        }
        # reference eps grid from the real embedding's off-diagonal distances
        Dr = cdist(arms_emb['real'][0], arms_emb['real'][0])
        off = Dr[np.triu_indices_from(Dr, k=1)]
        eps_grid = {p: float(np.percentile(off, p)) for p in EPS_PCTS}
        del Dr, off

        for arm in ['real', 'ft', 'shuffle']:
            for emb in arms_emb[arm]:
                D = cdist(emb, emb)
                for p in EPS_PCTS:
                    R = (D <= eps_grid[p]).astype(np.uint8)
                    mm = compute_rqa_metrics(R)
                    records.append(dict(arm=arm, ch=ci, band=bn, band_i=bi,
                                        eps_pct=p, eps_abs=eps_grid[p],
                                        **{k: float(mm[k]) for k in ['RR','DET','LAM','ENT','L','Lmax']}))
                del D
        del arms_emb
    print('done channel', ci, flush=True)

# ---------------- aggregate ----------------
def band_profile(arm, pct, metric):
    return np.array([float(np.mean([r[metric] for r in records
                    if r['arm']==arm and r['eps_pct']==pct and r['band_i']==bi]))
                    for bi in range(len(BANDS))])

out = {'bands': [b[0] for b in BANDS], 'eps_pcts': EPS_PCTS, 'win': WIN,
       'n_surr': N_SURR, 'arms': ['real','ft','shuffle'], 'per_eps': {}}

for pct in EPS_PCTS:
    entry = {}
    for metric in ['RR','DET','LAM','ENT','L','Lmax']:
        entry[metric] = {}
        for arm in ['real','ft','shuffle']:
            prof = band_profile(arm, pct, metric)
            rho = float(spearmanr(prof, np.arange(len(BANDS))).statistic)
            entry[metric][arm] = {'profile': prof.tolist(), 'rho_vs_bandidx': rho}
    e_real = np.array(entry['ENT']['real']['profile'])
    e_ft   = np.array(entry['ENT']['ft']['profile'])
    e_sh   = np.array(entry['ENT']['shuffle']['profile'])
    entry['ENT_gap_real_minus_ft']      = float(np.mean(e_real - e_ft))
    entry['ENT_gap_real_minus_shuffle'] = float(np.mean(e_real - e_sh))
    entry['rho_ENT_real']    = entry['ENT']['real']['rho_vs_bandidx']
    entry['rho_ENT_ft']      = entry['ENT']['ft']['rho_vs_bandidx']
    entry['rho_ENT_shuffle'] = entry['ENT']['shuffle']['rho_vs_bandidx']
    entry['rho_ENT_real_minus_ft'] = entry['rho_ENT_real'] - entry['rho_ENT_ft']
    entry['RR_real']  = entry['RR']['real']['profile']
    entry['LAM_real'] = entry['LAM']['real']['profile']
    out['per_eps'][str(pct)] = entry
    print(f"p{pct:>2}: rho_ENT real={entry['rho_ENT_real']:+.3f} ft={entry['rho_ENT_ft']:+.3f} "
          f"shuf={entry['rho_ENT_shuffle']:+.3f} | gap(real-ft)={entry['ENT_gap_real_minus_ft']:+.3f} "
          f"RR={np.mean(entry['RR_real']):.3f} LAM={np.mean(entry['LAM_real']):.3f}", flush=True)

os.makedirs('world_c_results', exist_ok=True)
with open('world_c_results/emp238_saturation.json','w') as f:
    json.dump(out, f, indent=1)

fig, ax = plt.subplots(2,2, figsize=(13,9))
pp = EPS_PCTS; cA,cB,cC = '#1f77b4','#d62728','#7f7f7f'
ax[0,0].plot(pp,[out['per_eps'][str(p)]['rho_ENT_real'] for p in pp],'o-',color=cA,label='real EEG')
ax[0,0].plot(pp,[out['per_eps'][str(p)]['rho_ENT_ft'] for p in pp],'s--',color=cB,label='FT surrogate')
ax[0,0].plot(pp,[out['per_eps'][str(p)]['rho_ENT_shuffle'] for p in pp],'^:',color=cC,label='shuffled')
ax[0,0].axhline(0,color='k',lw=.8); ax[0,0].set_xlabel('epsilon percentile')
ax[0,0].set_ylabel('rho(ENT, band index)'); ax[0,0].set_title('Sign of RQA-ENT vs frequency: real vs surrogates')
ax[0,0].legend(); ax[0,0].grid(alpha=.3)
ax[0,1].plot(pp,[out['per_eps'][str(p)]['ENT_gap_real_minus_ft'] for p in pp],'o-',color=cB)
ax[0,1].axhline(0,color='k',lw=.8); ax[0,1].set_xlabel('epsilon percentile')
ax[0,1].set_ylabel('mean ENT(real) - ENT(FT surr)'); ax[0,1].set_title('Determinism signal collapses at dense eps')
ax[0,1].grid(alpha=.3)
ax[1,0].plot(pp,[np.mean(out['per_eps'][str(p)]['RR_real']) for p in pp],'o-',color='k')
ax[1,0].set_xlabel('epsilon percentile'); ax[1,0].set_ylabel('mean RR')
ax[1,0].set_title('Recurrence-matrix saturation'); ax[1,0].grid(alpha=.3)
ax[1,1].plot(pp,[np.mean(out['per_eps'][str(p)]['LAM_real']) for p in pp],'o-',color='purple')
ax[1,1].axhline(1.0,color='r',ls='--',lw=.8); ax[1,1].set_xlabel('epsilon percentile')
ax[1,1].set_ylabel('mean LAM'); ax[1,1].set_title('Laminarity -> 1 (degenerate regime)'); ax[1,1].grid(alpha=.3)
plt.tight_layout(); plt.savefig('world_c_results/emp238_saturation.png', dpi=110)
print('SAVED emp238_saturation.json + .png'); print('DONE')
