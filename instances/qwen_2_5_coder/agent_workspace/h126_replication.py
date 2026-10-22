"""
HYP-126 independent replication (qwen, from scratch).
Claim under test:
  (A) 'Ordinary frame persistence' regime (r~3.888-3.905, eps=0.103):
      dominant temporal freq f~0.265 (period-4 band chaos), d2 ~ 0.011-0.016
  (B) 'Resonant phase-memory' regime (r~3.845, eps in [0.12,0.136]):
      exact period-2 antiphase lock, f=0.5000, d2 < 0.006, sharp parity alternation
  (C) window boundaries: r in [3.845,3.875], eps in [0.120,0.136]

My independent diagnostics (NOT reusing their code):
  - CML: x'=(1-eps)*r*x*(1-x)+eps/2*(roll+roll), periodic BC
  - spatial mean m(t); HANNING-windowed rFFT peak freq
  - direct period-2 lock test: A2/A1 autocorrelation of m, and d2/d1 ratio
  - parity = mean(lag 2..16 even corr) - mean(lag 1..15 odd corr)
  - multi-seed (5 seeds), multi-lattice (L=64,128,256)
"""
import numpy as np
import json, time

def cml_frames(r, eps, L, T, trans, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, L)
    for _ in range(trans):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
    fr = np.empty((T, L))
    for t in range(T):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        fr[t] = x
    return fr

def analyze(fr):
    m = fr.mean(axis=1)
    mc = m - m.mean()
    # HANNING-windowed peak freq
    spec = np.abs(np.fft.rfft(mc * np.hanning(len(mc))))**2
    freqs = np.fft.rfftfreq(len(mc))
    k = int(np.argmax(spec[1:]) + 1)
    f_peak = freqs[k]
    peak_frac = spec[k] / spec.sum()
    # direct period-2 lock: autocorr at lag 1 and 2 of m
    v = mc / (mc.std() + 1e-15)
    A1 = float(np.mean(v[1:] * v[:-1]))
    A2 = float(np.mean(v[2:] * v[:-2]))
    # structural lag diffs
    d1 = float(np.mean((fr[1:] - fr[:-1])**2))
    d2 = float(np.mean((fr[2:] - fr[:-2])**2))
    # parity: even-lag vs odd-lag spatial frame corr (lags 1..16)
    fc = fr - fr.mean(axis=1, keepdims=True)
    ne, no = [], []
    for lag in range(1, 17):
        a, b = fc[:-lag], fc[lag:]
        num = (a * b).sum(axis=1)
        den = np.sqrt((a * a).sum(axis=1) * (b * b).sum(axis=1)) + 1e-12
        c = float(np.mean(num / den))
        (ne if lag % 2 == 0 else no).append(c)
    parity = float(np.mean(ne) - np.mean(no))
    return dict(f_peak=round(f_peak, 4), peak_frac=round(peak_frac, 4),
                A1=round(A1, 4), A2=round(A2, 4),
                d1=round(d1, 5), d2=round(d2, 5), parity=round(parity, 4))

def robust_point(r, eps, L=128, T=3000, trans=1000, seeds=(0, 1, 2, 3, 4)):
    fs, d2s, pars, a1s, a2s = [], [], [], [], []
    for s in seeds:
        fr = cml_frames(r, eps, L, T, trans, s)
        a = analyze(fr)
        fs.append(a['f_peak']); d2s.append(a['d2']); pars.append(a['parity'])
        a1s.append(a['A1']); a2s.append(a['A2'])
    return dict(r=r, eps=eps, L=L,
                f_peak_min=min(fs), f_peak_max=max(fs), f_mode=float(np.round(np.median(fs), 4)),
                d2_range=[min(d2s), max(d2s)], parity_range=[min(pars), max(pars)],
                A1_range=[min(a1s), max(a1s)], A2_range=[min(a2s), max(a2s)])

if __name__ == '__main__':
    t0 = time.time()
    print('=== HYP-126 independent replication (qwen) ===')
    print('\n--- Claimed anchor points (5 seeds each, L=128) ---')
    anchors = [
        ('ORDINARY-1', 3.8883, 0.1030),
        ('ORDINARY-2', 3.9050, 0.1030),
        ('RESONANT-1', 3.8450, 0.1307),
        ('RESONANT-2', 3.8450, 0.1200),
        ('CHAOS',      4.0000, 0.2000),
    ]
    results = {}
    for name, r, eps in anchors:
        res = robust_point(r, eps)
        results[name] = res
        print(f"[{name}] r={r:.4f} eps={eps:.4f}: "
              f"f_peak in [{res['f_peak_min']:.4f},{res['f_peak_max']:.4f}] med={res['f_mode']:.4f} "
              f"d2 in [{res['d2_range'][0]:.5f},{res['d2_range'][1]:.5f}] "
              f"parity in [{res['parity_range'][0]:+.4f},{res['parity_range'][1]:+.4f}] "
              f"A1 in [{res['A1_range'][0]:+.4f},{res['A1_range'][1]:+.4f}] "
              f"A2 in [{res['A2_range'][0]:+.4f},{res['A2_range'][1]:+.4f}]")

    print('\n--- Lattice-size robustness of RESONANT-1 (L=64,128,256) ---')
    for L in (64, 128, 256):
        res = robust_point(3.8450, 0.1307, L=L, T=1500, trans=600)
        print(f"L={L}: f_peak in [{res['f_peak_min']:.4f},{res['f_peak_max']:.4f}] "
              f"d2 in [{res['d2_range'][0]:.5f},{res['d2_range'][1]:.5f}] "
              f"parity in [{res['parity_range'][0]:+.4f},{res['parity_range'][1]:+.4f}]")

    print('\n--- 2D window scan: f_peak and d2 on (r, eps) grid ---')
    print('eps\\r     ' + ''.join(f'{r:12.4f}' for r in np.arange(3.80, 3.921, 0.02)))
    grid = {}
    for eps in [0.08, 0.10, 0.12, 0.136, 0.16, 0.20]:
        row = []
        for r in np.arange(3.80, 3.921, 0.02):
            res = robust_point(float(r), eps, T=2000, trans=800, seeds=(0, 1))
            row.append((res['f_mode'], res['d2_range'][1], res['parity_range'][1]))
            grid[(round(float(r),3), eps)] = res
        print(f'{eps:6.3f}   ' + ''.join(f'{f:8.4f} d2<={d2:6.4f} {p:+.3f}'.ljust(12) for (f, d2, p) in row))

    print(f'\n(total {time.time()-t0:.1f}s)')
    with open('h126_replication.json', 'w') as f:
        json.dump({'anchors': results, 'grid': {f'{k[0]},{k[1]}': v for k, v in grid.items()}}, f, indent=1)
    print('saved h126_replication.json')
