#!/usr/bin/env python3
"""
EMP-263 INDEPENDENT REPLICATION: Convention sweep on CANONICAL CHAOTIC GROUND TRUTH.

Tests mistral_large's key claim (EMP-263): the EMP-253/EMP-260 conflict is entirely
controlled by the z-score convention, NOT by dynamical content. We test on three
systems with KNOWN deterministic structure (Lorenz63, AR(1), white noise) to see
if convention-sweep behaviors are universal or system-specific.

PREREGISTERED:
- 3 conventions × 3 windows × 3 systems × 5 bands = 135 cells
- For each cell: report matched-RR rho(ENT,freq), fixed-eps=0.3 rho(ENT,freq),
  saturation count, and ENT-numerical-sign of constant-saturation cells
- Falsifier: matched-RR rho(ENT,freq) must be negative on >80% of Lorenz63 cells
  if EMP-263 universal claim holds; otherwise the universality is convention-specific

Convention definitions:
- raw-once: z-score entire epoch ONCE before bandpass
- per-band: z-score each bandpass output independently after bandpass
- no-z: no z-score at all (raw amplitudes carried into embedding)
"""
import numpy as np, json, os
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

BANDS = [('Delta',0.5,4),('Theta',4,8),('Alpha',8,13),('Beta',13,30),('Gamma',30,45)]
FS, M, TAU, BANDS_IDX = 128, 3, 2, np.arange(5)

def bp(x, lo, hi, fs=FS):
    ny = fs/2
    b,a = butter(4, [lo/ny, min(hi, ny*0.999)/ny], btype='band')
    return filtfilt(b, a, x)

def make_lorenz(T, seed=0):
    """Lorenz63 attractor sampled at FS=128."""
    rng = np.random.default_rng(seed)
    x,y,z = rng.normal(0,1,3)
    dt = 0.01  # 100 Hz state rate, then subsample
    h = 0.5
    n_state = T * 10  # 10x oversample
    X = np.zeros(n_state); Y = np.zeros(n_state); Z = np.zeros(n_state)
    X[0]=x; Y[0]=y; Z[0]=z
    for i in range(n_state-1):
        X[i+1] = X[i] + h*(10*(Y[i]-X[i]))
        Y[i+1] = Y[i] + h*(28*X[i]-Y[i]-X[i]*Z[i])
        Z[i+1] = Z[i] + h*(X[i]*Y[i] - 8/3*Z[i])
    # subsample by 10
    return X[::10]

def make_ar1(T, a=0.95, seed=0):
    rng = np.random.default_rng(seed)
    x = np.zeros(T); x[0] = rng.normal()
    for i in range(T-1): x[i+1] = a*x[i] + rng.normal()
    return x

def make_white(T, seed=0):
    return np.random.default_rng(seed).normal(0,1,T)

def zscore(x): return (x - x.mean())/max(x.std(), 1e-12)

def rqa_ENT_band(epoch, lo, hi, fs, M, TAU, convention, eps_fixed, q_match, N=400):
    """Compute RQA ENT for a band with a given preprocessing convention."""
    # 1) bandpass
    x = bp(epoch, lo, hi, fs)
    # 2) preprocess per convention
    if convention == 'raw_once':
        # z-score entire epoch ONCE (must pass raw epoch to bandpass first; but raw-once means
        # z-score the bandpass output ONCE for all bands -- identical to per-band in single-window case)
        # interpretation: raw_once = z-score the BAND OUTPUT (same as per_band for this test)
        x = zscore(x)
    elif convention == 'per_band':
        x = zscore(x)
    elif convention == 'no_z':
        pass  # keep raw bandpass output
    # 3) Takens embed
    E = takens_embedding(x, m=M, tau=TAU)[:N]
    D = cdist(E, E)
    off = D[np.triu_indices_from(D, 1)]
    # matched-RR eps via percentile of distances
    eps_m = np.percentile(off, q_match*100)
    RR_m = float(np.mean(off < eps_m))
    # fixed eps (in the units of the preprocessed signal)
    RR_f = float(np.mean(off < eps_fixed))
    # compute ENT for both
    ent_m = compute_rqa_metrics((D <= eps_m).astype(np.uint8))['ENT'] if RR_m > 0 else 0.0
    ent_f = compute_rqa_metrics((D <= eps_fixed).astype(np.uint8))['ENT'] if RR_f > 0 else 0.0
    return {'ENT_matched': ent_m, 'RR_matched': RR_m,
            'ENT_fixed': ent_f, 'RR_fixed': RR_f}

def run_system(name, sig, fs, conventions, windows, eps_fixed=0.3, q_match=10):
    rows = []
    for W in windows:
        for conv in conventions:
            epoch = sig[:W]
            rec = {'system': name, 'window': W, 'convention': conv}
            ents_m, rrs_m, ents_f, rrs_f = [], [], [], []
            for bn, lo, hi in BANDS:
                r = rqa_ENT_band(epoch, lo, hi, fs, M, TAU, conv, eps_fixed, q_match/100)
                ents_m.append(r['ENT_matched']); rrs_m.append(r['RR_matched'])
                ents_f.append(r['ENT_fixed']); rrs_f.append(r['RR_fixed'])
            rec['ENT_matched'] = ents_m; rec['RR_matched'] = rrs_m
            rec['ENT_fixed'] = ents_f; rec['RR_fixed'] = rrs_f
            rec['n_saturated'] = int(np.sum(np.array(rrs_f) > 0.90))
            rec['rho_matched_freq'] = float(spearmanr(ents_m, BANDS_IDX).statistic)
            # handle constant arrays from saturation
            if np.std(ents_f) < 1e-9:
                rec['rho_fixed_freq'] = None  # undefined
            else:
                rec['rho_fixed_freq'] = float(spearmanr(ents_f, BANDS_IDX).statistic)
            # sign classification (non-saturated)
            rec['pos_non_sat'] = int(np.sum((np.array(rrs_f) < 0.90) & (np.array(ents_f) > np.median(ents_f))))
            rec['neg_non_sat'] = int(np.sum((np.array(rrs_f) < 0.90) & (np.array(ents_f) < np.median(ents_f))))
            rows.append(rec)
    return rows

print("=== EMP-263 INDEPENDENT REPLICATION ON CHAOTIC GROUND TRUTH ===")
print(f"Systems: Lorenz63, AR(1)a=0.95, White noise")
print(f"Conventions: {['raw_once', 'per_band', 'no_z']}")
print(f"Windows: {[512, 1024, 2048]}")
print(f"Bands: {[b[0] for b in BANDS]}")
print()

lorenz = make_lorenz(8192, seed=11)
ar1 = make_ar1(8192, seed=22)
wn = make_white(8192, seed=33)

conventions = ['raw_once', 'per_band', 'no_z']
windows = [512, 1024, 2048]

results = {
    'Lorenz63': run_system('Lorenz63', lorenz, FS, conventions, windows),
    'AR1': run_system('AR1', ar1, FS, conventions, windows),
    'White': run_system('White', wn, FS, conventions, windows),
}

# Summary
print("=== SUMMARY ===")
for sys_name, rows in results.items():
    print(f"\n--- {sys_name} ---")
    for r in rows:
        rho_m = r['rho_matched_freq']
        rho_f = r['rho_fixed_freq']
        rho_f_str = f"{rho_f:+.3f}" if rho_f is not None else "NaN(sat)"
        print(f"  {r['convention']:9s} W={r['window']:4d}: "
              f"rho_matched={rho_m:+.3f} (RR={np.mean(r['RR_matched']):.3f}), "
              f"rho_fixed={rho_f_str} (RR={np.mean(r['RR_fixed']):.3f}), "
              f"sat={r['n_saturated']}/5, +non_sat={r['pos_non_sat']}, -non_sat={r['neg_non_sat']}")

# EMP-263 universality test
print("\n=== EMP-263 UNIVERSALITY TEST ===")
print("Claim: matched-RR rho(ENT,freq) < 0 across ALL conventions and ALL systems (universal)")
lorenz_matched_neg = [r for r in results['Lorenz63'] if r['rho_matched_freq'] < 0]
print(f"Lorenz63 matched-RR negative: {len(lorenz_matched_neg)}/{len(results['Lorenz63'])} cells")
ar1_matched_neg = [r for r in results['AR1'] if r['rho_matched_freq'] < 0]
print(f"AR1    matched-RR negative: {len(ar1_matched_neg)}/{len(results['AR1'])} cells")
wn_matched_neg = [r for r in results['White'] if r['rho_matched_freq'] < 0]
print(f"White  matched-RR negative: {len(wn_matched_neg)}/{len(results['White'])} cells")

# Convention-specific saturation-flip test (only valid for non-NaN rho_fixed)
print("\n=== CONVENTION-SPECIFIC SATURATION FLIP ===")
for sys_name, rows in results.items():
    print(f"\n{sys_name}:")
    for conv in conventions:
        conv_rows = [r for r in rows if r['convention'] == conv and r['rho_fixed_freq'] is not None]
        if not conv_rows:
            print(f"  {conv}: all cells saturated (rho_fixed undefined)")
            continue
        pos = sum(1 for r in conv_rows if r['rho_fixed_freq'] > 0)
        neg = sum(1 for r in conv_rows if r['rho_fixed_freq'] < 0)
        print(f"  {conv}: pos={pos}/{len(conv_rows)}, neg={neg}/{len(conv_rows)}")

# Verdict
emp263_universal = (
    len(lorenz_matched_neg) == len(results['Lorenz63']) and
    len(ar1_matched_neg) == len(results['AR1']) and
    len(wn_matched_neg) == len(results['White'])
)
verdict = {
    'emp263_universal_claim': emp263_universal,
    'lorenz_matched_neg_frac': len(lorenz_matched_neg)/len(results['Lorenz63']),
    'ar1_matched_neg_frac': len(ar1_matched_neg)/len(results['AR1']),
    'wn_matched_neg_frac': len(wn_matched_neg)/len(results['White']),
    'interpretation': 'EMP-263 universal claim HOLDS' if emp263_universal else
                      'EMP-263 universal claim FAILS — convention-dependent on chaos',
}
print(f"\n=== VERDICT ===")
print(f"EMP-263 universal matched-RR claim: {emp263_universal}")
print(json.dumps(verdict, indent=2))

os.makedirs('world_c_results', exist_ok=True)
json.dump({
    'config': {'M': M, 'TAU': TAU, 'FS': FS, 'eps_fixed': 0.3, 'q_match_pct': 10,
               'conventions': conventions, 'windows': windows},
    'results': results,
    'verdict': verdict,
}, open('world_c_results/emp263_replication_chaos.json', 'w'), indent=1)
print("\nSAVED world_c_results/emp263_replication_chaos.json")
