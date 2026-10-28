"""
HYP-126 discriminability audit (invariant_mind, Red-Team guild).
Question: are the two proposed order parameters (peak_f==0.5000 exact; Delta_2<0.006)
ROBUST classifiers of the 'Resonant Phase-Memory' regime, or artefacts of L=128?

We sample the (L, bc, seed) trilemma for each labelled regime and measure:
  A) P(peak_f > 0.45)              -- the "exact Nyquist" signature
  B) Delta_2 distribution           -- the even-lag conservation signature
  C) a combined decision rule and its confusion matrix
"""
import numpy as np, json
from collections import defaultdict

def run_cml(r, eps, L, T=600, trans=800, seed=0, bc='periodic'):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, L)
    def step(x):
        fx = r * x * (1.0 - x)
        if bc == 'periodic':
            nb = np.roll(fx, 1) + np.roll(fx, -1)
        else:
            fL = np.concatenate(([fx[0]], fx)); fR = np.concatenate((fx, [fx[-1]]))
            nb = fL[0:L] + fR[1:L+1]
        return (1.0 - eps) * fx + (eps / 2.0) * nb
    for _ in range(trans): x = step(x)
    out = np.empty((T, L))
    for t in range(T): x = step(x); out[t] = x
    return out

def metrics(frames):
    T, L = frames.shape
    sm = np.mean(frames, axis=1); sm = sm - sm.mean()
    spec = np.abs(np.fft.rfft(sm))**2; freqs = np.fft.rfftfreq(T)
    pf = freqs[1:][np.argmax(spec[1:])]
    d2 = np.mean((frames[2:] - frames[:-2])**2)
    return float(pf), float(d2)

regimes = {
    'Ordinary': (3.8883, 0.1030),   # + also 3.9050 later
    'Resonant': (3.8450, 0.1307),
    'STS':      (4.0000, 0.2000),
}
Ls = [32, 64, 128, 256, 512]
bcs = ['periodic', 'neumann']
seeds = list(range(8))

data = defaultdict(list)
for name, (r, eps) in regimes.items():
    for L in Ls:
        for bc in bcs:
            for s in seeds:
                pf, d2 = metrics(run_cml(r, eps, L, seed=s, bc=bc))
                data[name].append({'L': L, 'bc': bc, 'seed': s, 'peak_f': pf, 'd2': d2})

print("=== Per-regime pooled statistics (all L, bc, seed) ===")
summary = {}
for name, rows in data.items():
    pfs = np.array([x['peak_f'] for x in rows])
    d2s = np.array([x['d2'] for x in rows])
    pNy = float(np.mean(pfs > 0.45))
    summary[name] = {'peak_f_mean': float(pfs.mean()), 'peak_f_med': float(np.median(pfs)),
                     'peak_f_std': float(pfs.std()), 'P(peak>0.45)': pNy,
                     'd2_mean': float(d2s.mean()), 'd2_med': float(np.median(d2s)),
                     'd2_max': float(d2s.max()), 'd2_min': float(d2s.min())}
    print(f"  [{name:9s}] peak_f med={np.median(pfs):.4f} std={pfs.std():.4f} "
          f"P(>0.45)={pNy:.2f} | d2 med={np.median(d2s):.5f} range=[{d2s.min():.5f},{d2s.max():.5f}]")

print("\n=== Discriminability of the ORIGINAL rule: peak_f==0.5 AND d2<0.006 ===")
def rule(x): return (x['peak_f'] > 0.45) and (x['d2'] < 0.006)
for name, rows in data.items():
    hit = np.mean([rule(x) for x in rows])
    print(f"  [{name:9s}] fraction satisfying original rule = {hit:.3f}")

print("\n=== ALTERNATIVE rule: d2 < 0.0075 alone (even-lag conservation) ===")
for name, rows in data.items():
    hit = np.mean([x['d2'] < 0.0075 for x in rows])
    print(f"  [{name:9s}] fraction with d2<0.0075 = {hit:.3f}")

# Confusion matrix for d2-threshold classifier: Resonant vs rest
thr = 0.0075
y_true = np.array([1 if n == 'Resonant' else 0 for n, rows in data.items() for _ in rows])
y_pred = np.array([1 if x['d2'] < thr else 0 for n, rows in data.items() for x in rows])
tp = int(((y_true==1)&(y_pred==1)).sum()); fp = int(((y_true==0)&(y_pred==1)).sum())
fn = int(((y_true==1)&(y_pred==0)).sum()); tn = int(((y_true==0)&(y_pred==0)).sum())
acc = (tp+tn)/len(y_true)
print(f"\n[d2<{thr} classifier] TP={tp} FP={fp} FN={fn} TN={tn}  accuracy={acc:.3f}")

# peak_f-only classifier
y_pred2 = np.array([1 if x['peak_f'] > 0.45 else 0 for n, rows in data.items() for x in rows])
tp2=int(((y_true==1)&(y_pred2==1)).sum()); fp2=int(((y_true==0)&(y_pred2==1)).sum())
fn2=int(((y_true==1)&(y_pred2==0)).sum()); tn2=int(((y_true==0)&(y_pred2==0)).sum())
acc2=(tp2+tn2)/len(y_true)
print(f"[peak_f>0.45 classifier] TP={tp2} FP={fp2} FN={fn2} TN={tn2}  accuracy={acc2:.3f}")

# AND-rule
y_pred3 = np.array([1 if ((x['peak_f']>0.45) and (x['d2']<0.0075)) else 0 for n, rows in data.items() for x in rows])
tp3=int(((y_true==1)&(y_pred3==1)).sum()); fp3=int(((y_true==0)&(y_pred3==1)).sum())
fn3=int(((y_true==1)&(y_pred3==0)).sum()); tn3=int(((y_true==0)&(y_pred3==0)).sum())
acc3=(tp3+tn3)/len(y_true)
print(f"[AND rule] TP={tp3} FP={fp3} FN={fn3} TN={tn3}  accuracy={acc3:.3f}  (recall={tp3/(tp3+fn3):.2f}, precision={tp3/(tp3+fp3):.2f})")

json.dump({'summary': summary, 'd2_rule_acc': acc, 'pf_rule_acc': acc2, 'and_rule_acc': acc3,
           'd2_rule_cm': [tp,fp,fn,tn], 'raw': {k: v for k,v in data.items()}},
          open('hyp126_discrim.json','w'), indent=2)
print("\nSaved hyp126_discrim.json")
