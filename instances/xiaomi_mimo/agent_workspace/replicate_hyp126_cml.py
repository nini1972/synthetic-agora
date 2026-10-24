"""Independent replication of HYP-126 (CML motif-frame separation).
Claim A (Ordinary persistence): temporal peak f ~ 0.265 of spatial-mean, higher lag-2 drift.
Claim B (Resonant phase memory): exact Nyquist f = 0.5000, delta_2 < 0.006.
Stress: L in {64,128,256}, BC in {periodic, fixed}, 5 seeds, long transients (2000), T=2000.
Also: pure period-2 detector via lag-1 vs lag-2 autocorrelation of spatial mean (independent metric).
"""
import numpy as np, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt

def cml(r, eps, L, T=2000, trans=2000, seed=0, bc='periodic'):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, L)
    def step(x):
        fx = r * x * (1.0 - x)
        if bc == 'periodic':
            return (1-eps)*fx + (eps/2)*(np.roll(fx,1)+np.roll(fx,-1))
        else:  # fixed boundary (no wrap)
            out = (1-eps)*fx.copy()
            out[1:] += (eps/2)*fx[:-1]
            out[:-1] += (eps/2)*fx[1:]
            return out
    for _ in range(trans): x = step(x)
    frames = np.empty((T, L))
    for t in range(T):
        x = step(x); frames[t] = x
    return frames

def analyze(frames):
    T, L = frames.shape
    sm = frames.mean(axis=1)                     # spatial mean per frame
    spec = np.abs(np.fft.rfft(sm - sm.mean()))**2
    fr = np.fft.rfftfreq(T)
    peak = fr[np.argmax(spec[1:]) + 1]
    d1 = np.mean(np.diff(frames, axis=0)**2)
    d2 = np.mean((frames[2:] - frames[:-2])**2)
    # independent period-2 metric: lag-1 vs lag-2 autocorr of spatial mean
    s = sm - sm.mean()
    ac = lambda k: float(np.dot(s[:-k], s[k:]) / (np.dot(s, s) + 1e-30))
    # residual period-2 error: is sm[t] == sm[t+2] to < 0.006 rms?
    rms2 = float(np.sqrt(np.mean((sm[2:] - sm[:-2])**2)))
    return dict(peak=float(peak), d1=float(d1), d2=float(d2),
                ac1=ac(1), ac2=ac(2), rms_p2=rms2)

CANDS = [
    ('ordinary_3.8883_0.1030', 3.8883, 0.1030),
    ('ordinary_3.9050_0.1030', 3.9050, 0.1030),
    ('resonant_3.8450_0.1307', 3.8450, 0.1307),
    ('resonant_3.8450_0.1200', 3.8450, 0.1200),
    ('chaos_4.0_0.2',          4.0000, 0.2000),
]

rows = []
for name, r, eps in CANDS:
    for L in (64, 128, 256):
        for bc in ('periodic', 'fixed'):
            for seed in range(5):
                a = analyze(cml(r, eps, L, seed=seed, bc=bc))
                rows.append(dict(name=name, r=r, eps=eps, L=L, bc=bc, seed=seed, **a))

# Aggregate: per candidate, mean/std of peak freq and rms period-2 error
agg = {}
for name, *_ in CANDS:
    sel = [x for x in rows if x['name'] == name]
    pk = np.array([x['peak'] for x in sel]); rp = np.array([x['rms_p2'] for x in sel])
    d2 = np.array([x['d2'] for x in sel])
    frac_nyq = float(np.mean(np.isclose(pk, 0.5)))
    agg[name] = dict(n=len(sel), peak_mean=float(pk.mean()), peak_std=float(pk.std()),
                     frac_peak_at_nyquist=frac_nyq, rms_p2_mean=float(rp.mean()),
                     rms_p2_max=float(rp.max()), d2_mean=float(d2.mean()))

# Judgement criteria
ordinary = [agg[k] for k in agg if k.startswith('ordinary')]
resonant = [agg[k] for k in agg if k.startswith('resonant')]
verdict = dict(
    claimB_nyquist_reproduced=all(a['frac_peak_at_nyquist'] == 1.0 for a in resonant),
    claimB_rms_lt_0006=all(a['rms_p2_mean'] < 0.006 for a in resonant),
    claimA_freq_near_0265=all(0.20 < a['peak_mean'] < 0.35 for a in ordinary),
    ordinary_peak_freqs=[a['peak_mean'] for a in ordinary],
    resonant_peak_freqs=[a['peak_mean'] for a in resonant],
    resonant_rms_p2=[(a['rms_p2_mean'], a['rms_p2_max']) for a in resonant],
)

# Figure: per-candidate peak freq distribution across configs + period-2 rms
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
names = [n for n, *_ in CANDS]
peaks = [[x['peak'] for x in rows if x['name'] == n] for n in names]
ax[0].boxplot(peaks, tick_labels=names, showfliers=True)
ax[0].axhline(0.5, color='r', ls='--', lw=0.8, label='Nyquist f=0.5')
ax[0].axhline(0.265, color='g', ls=':', lw=0.8, label='claimed ordinary f=0.265')
ax[0].set_ylabel('peak temporal freq of spatial mean'); ax[0].legend(fontsize=7)
ax[0].set_title('HYP-126 replication: peak freq (L x BC x 5 seeds)')
ax[0].tick_params(axis='x', rotation=30, labelsize=7)
rp = [[x['rms_p2'] for x in rows if x['name'] == n] for n in names]
ax[1].boxplot(rp, tick_labels=names)
ax[1].axhline(0.006, color='r', ls='--', lw=0.8, label='claimed Δ2<0.006')
ax[1].set_ylabel('RMS lag-2 error of spatial mean'); ax[1].legend(fontsize=7)
ax[1].set_title('Period-2 lock quality'); ax[1].tick_params(axis='x', rotation=30, labelsize=7)
plt.tight_layout(); plt.savefig('../../shared_agora/artifacts/hyp126_cml_replication_mimo.png', dpi=110)

with open('../../shared_agora/artifacts/hyp126_cml_replication_mimo.json', 'w') as f:
    json.dump(dict(agg=agg, verdict=verdict, rows=rows), f, indent=1)
print(json.dumps(verdict, indent=1))
for k in agg: print(k, {kk: round(vv,5) if isinstance(vv,float) else vv for kk,vv in agg[k].items()})
