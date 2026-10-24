"""
Focused verification: does the f=0.5 resonant (period-2) CML window extend in r
beyond the claimed [3.845, 3.875] at eps in {0.12, 0.136}? 5 seeds, L=128.
Also probe the eps=0.136 low-r anomaly (SUB/DC) that appeared in the coarse grid.
"""
import numpy as np

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
    m = fr.mean(axis=1); mc = m - m.mean()
    spec = np.abs(np.fft.rfft(mc * np.hanning(len(mc))))**2
    freqs = np.fft.rfftfreq(len(mc))
    f_peak = freqs[int(np.argmax(spec[1:]) + 1)]
    v = mc / (mc.std() + 1e-15)
    A1 = float(np.mean(v[1:] * v[:-1])); A2 = float(np.mean(v[2:] * v[:-2]))
    d2 = float(np.mean((fr[2:] - fr[:-2])**2))
    fc = fr - fr.mean(axis=1, keepdims=True)
    ne, no = [], []
    for lag in range(1, 17):
        a, b = fc[:-lag], fc[lag:]
        c = float(np.mean((a*b).sum(1) / (np.sqrt((a*a).sum(1)*(b*b).sum(1)) + 1e-12)))
        (ne if lag % 2 == 0 else no).append(c)
    parity = float(np.mean(ne) - np.mean(no))
    return f_peak, A1, A2, d2, parity

def pt(r, eps, L=128, T=3000, trans=1000, seeds=(0,1,2,3,4)):
    out = [analyze(cml_frames(r, eps, L, T, trans, s)) for s in seeds]
    fp = [o[0] for o in out]; A2 = [o[2] for o in out]; d2 = [o[3] for o in out]
    return dict(f_min=min(fp), f_max=max(fp), f_mode=round(float(np.median(fp)),4),
                A2_range=[min(A2), max(A2)], d2_range=[min(d2), max(d2)])

if __name__ == '__main__':
    print('=== r-EXTENSION of resonant window, 5 seeds, L=128 ===')
    for eps in (0.120, 0.136):
        print(f'\n--- eps = {eps} ---')
        print('  r       f_peak      A2 (P2 lock)          d2(max)   verdict')
        for r in [3.80, 3.82, 3.845, 3.875, 3.888, 3.90, 3.92, 3.95, 3.98]:
            res = pt(float(r), eps)
            # P2 lock: strong anti-correlation A2>0 and f_peak=0.5
            verdict = 'P2' if (res['f_mode'] > 0.45 and res['A2_range'][1] > 0.3) else (
                      'ORD' if 0.20 < res['f_mode'] < 0.33 else 'SUB/other')
            print(f'  {r:5.3f}  [{res["f_min"]:.3f},{res["f_max"]:.3f}] med={res["f_mode"]:.3f}  '
                  f'[{res["A2_range"][0]:+.3f},{res["A2_range"][1]:+.3f}]  '
                  f'[{res["d2_range"][0]:.5f},{res["d2_range"][1]:.5f}]  {verdict}')
