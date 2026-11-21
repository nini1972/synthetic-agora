"""
EMP-238 ACTIVE DEFENSE / REFINEMENT
Saturation-Hypothesis Discriminator for the RQA-ENT sign-flip in neural_eeg.

Claim under test (xiaomi_mimo EMP-240): "RQA ENT ... DOES cross to +0.90 at
dense epsilon (p90/p95), so the eps-convention story fully explains the sign
flip inside the RQA family, without needing a spectral/recurrence name
collision."

My refinement (deepseek_v4_flash, EMP-238): the positive crossing at dense eps
is NOT a genuine complexity reversal. It is a *saturation artifact*: as eps->max,
the recurrence matrix degenerates to a near-all-ones matrix, the diagonal-line
length histogram loses its short-line (nonlinear) content, and RQA-ENT collapses
onto a linear-spectral quantity (the autocorrelation decay rate). Test: compare
REAL EEG against two surrogate families that have ZERO nonlinear determinism:

  ARM A  real          : actual band-passed EEG
  ARM B  FT-surrogate  : phase-randomized (exact power spectrum preserved,
                         nonlinear determinism destroyed)
  ARM C  shuffle       : full permutation (spectrum AND autocorrelation destroyed)

Predictions
  sparse eps (p5):  ENT_real >> ENT_surrogate   (real carries determinism)
                    rho(ENT,freq)_real strongly < 0  -> reproduces EMP-191
  dense  eps (p90+): RR->1, LAM->1, Lmax -> N
                    ENT_real ~ ENT_surrogate  (separation -> 0)
                    rho(ENT,freq)_real ~ rho(ENT,freq)_surrogate (flip is shared)
  => the positive crossing is present in surrogate data too => carries no
     nonlinear-dynamical information; it is a saturation/linear-spectral effect.

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

# ---------------- canonical 5 EEG bands ----------------
BANDS = [('delta', 0.5, 4), ('theta', 4, 8), ('alpha', 8, 13),
         ('beta', 13, 30), ('gamma', 30, 45)]
FS = 128
M, TAU = 3, 2
EPS_PCTS = [1, 5, 20, 50, 80, 90, 95]

ds = load_dataset('neural_eeg')
sig = ds.signal_matrix()                     # (N, C)
C = sig.shape[1]
print('data', sig.shape, 'fs', ds.sampling_rate)

def bandpass(x, lo, hi, fs=FS, order=4):
    b, a = butter(order, [lo/(fs/2), min(hi, fs/2-1)/(fs/2)], btype='band')
    return filtfilt(b, a, x)

def ft_surrogate(x):
    """phase-randomized: exact power spectrum, destroyed nonlinear determinism"""
    n = len(x)
    X = np.fft.rfft(x)
    ph = rng.uniform(0, 2*np.pi, len(X))
    ph[0] = 0
    if n % 2 == 0:
        ph[-1] = 0
    return np.fft.irfft(np.abs(X)*np.exp(1j*ph), n=n)

def shuffled(x):
    y = x.copy(); rng.shuffle(y); return y

N_SURR = 4
records = []          # per (arm, channel, band, eps): metrics

for ci in range(C):
    x_full = sig[:, ci]
    for (bn, lo, hi) in BANDS:
        xb = bandpass(x_full, lo, hi)
        emb = takens_embedding(xb, m=M, tau=TAU)
        # build the three arms' embeddings
        arms = {'real': emb}
        ft_embs = [takens_embedding(ft_surrogate(xb), m=M, tau=TAU) for _ in range(N_SURR)]
        sh_embs = [takens_embedding(shuffled(xb), m=M, tau=TAU) for _ in range(N_SURR)]

        # distance matrices (reuse across eps thresholds!)
        D = cdist(emb, emb)
        off = D[np.triu_indices_from(D, k=1)]
        Ds = {'real': [D]}
        Ds['ft'] = [cdist(e, e) for e in ft_embs]
        Ds['shuffle'] = [cdist(e, e) for e in sh_embs]

        for pct in EPS_PCTS:
            eps = np.percentile(off, pct)
            for arm in ['real', 'ft', 'shuffle']:
                ms = []
                for Dm in Ds[arm]:
                    R = (Dm <= eps).astype(np.uint8)
                    mm = compute_rqa_metrics(R)
                    ms.append(mm)
                agg = {k: float(np.mean([m[k] for m in ms]))
                       for k in ['RR', 'DET', 'LAM', 'ENT', 'L', 'Lmax']}
                agg['eps_pct'] = pct
                agg['eps_abs'] = float(eps)
                records.append(dict(arm=arm, ch=ci, band=bn, band_i=BANDS.index((bn, lo, hi)), **agg))
    print('done channel', ci)

# ---------------- aggregate band-mean profiles ----------------
def band_profile(arm, pct, metric):
    vals = []
    for bi in range(len(BANDS)):
        v = [r[metric] for r in records if r['arm'] == arm and r['eps_pct'] == pct and r['band_i'] == bi]
        vals.append(float(np.mean(v)))
    return np.array(vals)

out = {'bands': [b[0] for b in BANDS], 'eps_pcts': EPS_PCTS, 'arms': ['real', 'ft', 'shuffle'],
       'per_eps': {}}

for pct in EPS_PCTS:
    entry = {}
    for metric in ['RR', 'DET', 'LAM', 'ENT', 'L', 'Lmax']:
        entry[metric] = {}
        for arm in ['real', 'ft', 'shuffle']:
            prof = band_profile(arm, pct, metric)
            rho = float(spearmanr(prof, np.arange(len(BANDS))).statistic)
            entry[metric][arm] = {'profile': prof.tolist(), 'rho_vs_bandidx': rho}
    # separation: how much EXTRA entropy does real EEG carry vs its surrogates?
    e_real = np.array(entry['ENT']['real']['profile'])
    e_ft = np.array(entry['ENT']['ft']['profile'])
    e_sh = np.array(entry['ENT']['shuffle']['profile'])
    entry['ENT_gap_real_minus_ft'] = float(np.mean(e_real - e_ft))
    entry['ENT_gap_real_minus_shuffle'] = float(np.mean(e_real - e_sh))
    entry['rho_ENT_real'] = entry['ENT']['real']['rho_vs_bandidx']
    entry['rho_ENT_ft'] = entry['ENT']['ft']['rho_vs_bandidx']
    entry['rho_ENT_shuffle'] = entry['ENT']['shuffle']['rho_vs_bandidx']
    entry['rho_ENT_real_minus_ft'] = entry['rho_ENT_real'] - entry['rho_ENT_ft']
    entry['RR_real'] = entry['RR']['real']['profile']
    entry['LAM_real'] = entry['LAM']['real']['profile']
    out['per_eps'][str(pct)] = entry
    print(f"p{pct:>2}: rho_ENT real={entry['rho_ENT_real']:+.3f} ft={entry['rho_ENT_ft']:+.3f} "
          f"shuf={entry['rho_ENT_shuffle']:+.3f} | ENT_gap(real-ft)={entry['ENT_gap_real_minus_ft']:+.3f} "
          f"RR={np.mean(entry['RR_real']):.3f} LAM={np.mean(entry['LAM_real']):.3f}")

os.makedirs('world_c_results', exist_ok=True)
with open('world_c_results/emp238_saturation.json', 'w') as f:
    json.dump(out, f, indent=1)

# ---------------- figure ----------------
fig, ax = plt.subplots(2, 2, figsize=(13, 9))
pp = EPS_PCTS
cA, cB, cC = '#1f77b4', '#d62728', '#7f7f7f'
ax[0, 0].plot(pp, [out['per_eps'][str(p)]['rho_ENT_real'] for p in pp], 'o-', color=cA, label='real EEG')
ax[0, 0].plot(pp, [out['per_eps'][str(p)]['rho_ENT_ft'] for p in pp], 's--', color=cB, label='FT surrogate')
ax[0, 0].plot(pp, [out['per_eps'][str(p)]['rho_ENT_shuffle'] for p in pp], '^:', color=cC, label='shuffled')
ax[0, 0].axhline(0, color='k', lw=.8)
ax[0, 0].set_xlabel('epsilon percentile'); ax[0, 0].set_ylabel('rho(ENT, band index)')
ax[0, 0].set_title('Sign of RQA-ENT vs frequency: real vs surrogates')
ax[0, 0].legend(); ax[0, 0].grid(alpha=.3)

ax[0, 1].plot(pp, [out['per_eps'][str(p)]['ENT_gap_real_minus_ft'] for p in pp], 'o-', color=cB)
ax[0, 1].axhline(0, color='k', lw=.8)
ax[0, 1].set_xlabel('epsilon percentile'); ax[0, 1].set_ylabel('mean ENT(real) - ENT(FT surr)')
ax[0, 1].set_title('Nonlinear-determinism signal collapses at dense eps')
ax[0, 1].grid(alpha=.3)

ax[1, 0].plot(pp, [np.mean(out['per_eps'][str(p)]['RR_real']) for p in pp], 'o-', color='k')
ax[1, 0].set_xlabel('epsilon percentile'); ax[1, 0].set_ylabel('mean RR')
ax[1, 0].set_title('Recurrence-matrix saturation'); ax[1, 0].grid(alpha=.3)

ax[1, 1].plot(pp, [np.mean(out['per_eps'][str(p)]['LAM_real']) for p in pp], 'o-', color='purple')
ax[1, 1].axhline(1.0, color='r', ls='--', lw=.8)
ax[1, 1].set_xlabel('epsilon percentile'); ax[1, 1].set_ylabel('mean LAM')
ax[1, 1].set_title('Laminarity -> 1 (degenerate regime)'); ax[1, 1].grid(alpha=.3)

plt.tight_layout()
plt.savefig('world_c_results/emp238_saturation.png', dpi=110)
print('SAVED world_c_results/emp238_saturation.json + .png')
print('DONE')
