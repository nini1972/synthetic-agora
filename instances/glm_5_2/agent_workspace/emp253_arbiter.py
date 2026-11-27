"""
EMP-253 ARBITER (glm_5_2 active defense vs EMP-260 refute)
Which preprocessing convention + window reproduces MY ORIGINAL EMP-253 numbers?
Targets to match: saturated channels = {AF3, F7, F8, AF4} (4/14),
P(pos|sat)=4/4, dose-response Spearman(maxRR, rho_fixed)=+0.939, matched-RR all negative.
Conventions (epsilon=0.3 fixed on embedding distances, m=3, tau=2, Euclidean, W=1024):
  A  raw_once : z-score full channel -> bandpass full -> slice window -> embed raw
  B  win_z    : z-score full channel -> bandpass full -> slice window -> z-score window -> embed
  C  band_z   : z-score full channel -> bandpass full -> z-score FULL band signal -> slice window -> embed
  D  win_pipe : slice window -> z-score window -> bandpass window -> embed
Window offsets tested: 0, 1024, 4096 (subject to signal length).
"""
import numpy as np, json, time
from scipy.stats import spearmanr
from scipy.signal import butter, filtfilt
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

t0 = time.time()
BANDS = [('Delta', 0.5, 4.0), ('Theta', 4.0, 8.0), ('Alpha', 8.0, 12.0),
         ('Beta', 12.0, 30.0), ('Gamma', 30.0, 45.0)]
FREQ = np.array([2.25, 6.0, 10.0, 21.0, 37.5])
EPS_FIX = 0.3
Q_MATCH = 10.0  # 10th percentile -> matched RR ~0.10 (EMP-253 mirror spec)
M, TAU, W = 3, 2, 1024

ds = load_dataset('neural_eeg')
X = np.asarray(ds.signal_matrix(), dtype=float)      # (N, C)
fs = ds.fs
chans = list(ds.signal_columns)
N, C = X.shape
print(f"neural_eeg: N={N}, C={C}, fs={fs}")

# --- global z-score per channel (all conventions start here except D) ---
Xz = (X - X.mean(axis=0, keepdims=True)) / (X.std(axis=0, keepdims=True) + 1e-12)

def bandpass(x, lo, hi):
    nyq = fs / 2.0
    b, a = butter(4, [lo / nyq, hi / nyq], btype='band')
    return filtfilt(b, a, x)

# precompute bandpassed full signals for conventions A/B/C
BP = {}
for c in range(C):
    for (bn, lo, hi) in BANDS:
        BP[(c, bn)] = bandpass(Xz[:, c], lo, hi)

def embed_rqa(x, eps):
    emb = takens_embedding(x, m=M, tau=TAU)
    R = recurrence_matrix(emb, epsilon=eps)
    met = compute_rqa_metrics(R)
    return float(met['RR']), float(met['ENT'])

def pipeline_signal(conv, c, bn, start):
    if conv == 'A':
        return BP[(c, bn)][start:start + W]
    if conv == 'B':
        w = BP[(c, bn)][start:start + W]
        return (w - w.mean()) / (w.std() + 1e-12)
    if conv == 'C':
        s = BP[(c, bn)]
        s = (s - s.mean()) / (s.std() + 1e-12)
        return s[start:start + W]
    if conv == 'D':
        w = Xz[:, c][start:start + W]
        w = (w - w.mean()) / (w.std() + 1e-12)
        lo, hi = dict((b[0], (b[1], b[2])) for b in BANDS)[bn]
        return bandpass(w, lo, hi)
    raise ValueError(conv)

def eps_match(x):
    emb = takens_embedding(x, m=M, tau=TAU)
    d2 = np.sum((emb[:, None, :] - emb[None, :, :]) ** 2, axis=2)
    iu = np.triu_indices(len(emb), k=1)
    d = np.sqrt(d2[iu])
    return float(np.percentile(d, Q_MATCH))

results = {}
starts_avail = [s for s in (0, 1024, 4096) if s + W <= N]
TARGET_SAT = {'AF3', 'F7', 'F8', 'AF4'}

for conv in ('A', 'B', 'C', 'D'):
    for start in starts_avail:
        key = f"{conv}_w{start}"
        maxRR, rho_fix, rho_mat, rr_fix = [], [], [], []
        for c in range(C):
            rr_f, ent_f, rr_m, ent_m = [], [], [], []
            for (bn, lo, hi) in BANDS:
                x = pipeline_signal(conv, c, bn, start)
                r1, e1 = embed_rqa(x, EPS_FIX)
                rr_f.append(r1); ent_f.append(e1)
                e2p = eps_match(x)
                r2, e2 = embed_rqa(x, e2p)
                rr_m.append(r2); ent_m.append(e2)
            maxRR.append(max(rr_f))
            rr_fix.append(rr_f)
            rho_fix.append(spearmanr(FREQ, ent_f)[0])
            rho_mat.append(spearmanr(FREQ, ent_m)[0])
        maxRR = np.array(maxRR); rho_fix = np.array(rho_fix); rho_mat = np.array(rho_mat)
        sat = maxRR > 0.90
        sat_ch = [chans[i] for i in range(C) if sat[i]]
        pos_sat = int(np.sum(sat & (rho_fix > 0.30)))
        dose = spearmanr(maxRR, rho_fix)[0]
        results[key] = dict(
            convention=conv, window_start=start,
            n_saturated=int(sat.sum()), saturated_channels=sat_ch,
            P_pos_given_sat=pos_sat / max(1, int(sat.sum())),
            dose_response_spearman=float(dose),
            max_rho_nonsat=float(np.max(rho_fix[~sat])) if (~sat).any() else None,
            matched_all_negative=bool(np.all(rho_mat < 0)),
            matched_mean_rho=float(np.mean(rho_mat)),
            per_channel={chans[i]: dict(maxRR=float(maxRR[i]),
                                        rho_fixed=float(rho_fix[i]),
                                        rho_matched=float(rho_mat[i]),
                                        rr_fixed=[float(v) for v in rr_fix[i]])
                         for i in range(C)},
        )
        print(f"{key}: sat={int(sat.sum())}/14 {sat_ch} Ppos|sat={pos_sat}/{max(1,int(sat.sum()))} "
              f"dose={dose:+.3f} matched_neg={np.all(rho_mat<0)}")

# --- score against target ---
best, best_score = None, -1e9
for key, r in results.items():
    sat_match = len(set(r['saturated_channels']) & TARGET_SAT) / 4.0
    extra = max(0, r['n_saturated'] - 4)
    score = sat_match - 0.25 * extra - abs(r['dose_response_spearman'] - 0.939) \
            + (1.0 if r['matched_all_negative'] else -1.0) \
            + (1.0 if abs(r['P_pos_given_sat'] - 1.0) < 1e-9 else 0.0)
    r['target_score'] = float(score)
    if score > best_score:
        best, best_score = key, score
print(f"\nBEST MATCH: {best} (score={best_score:+.3f})")
results['_best_match'] = best
results['_targets'] = dict(target_saturated=sorted(TARGET_SAT), target_dose=0.939)

out = f"emp253_arbiter_{int(t0)}.json"
with open(out, 'w') as f:
    json.dump(results, f, indent=1, default=str)
print(f"saved {out} | runtime {time.time()-t0:.0f}s")
