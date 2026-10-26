"""
ADJUDICATION of the EMP-166 (deepseek, adversarial) vs EMP-167/173 (qwen) conflict.

Disputed claim (deepseek FINDING 1): "the dominant frequency of the spatial-mean (macro)
mode is f=0.5000 (Nyquist) for essentially EVERY (r,eps) probed, including controls well
outside the claimed window."

qwen (EMP-167/173) counter-claim: f_peak is 0.5000 ONLY inside the locked basin and
collapses to ~0.278 / 0.42-0.49 in the surrounding chaos, so the macro mode IS
discriminating.

We settle it with an independent fine scan: robust windowed FFT dominant frequency of the
spatial mean + lag-2 time autocorr A2 + time-lag-2 structural variance d2 + a spatial
lag-2 two-site variance d2s (candidate 'Delta_2'). Report the fraction of the plane with
f_peak~0.5 and its geometry, plus the fraction with d2s < 0.006.

L=64, T=1000, trans=400, 1 seed (macro behavior is seed-robust; long series for clean FFT).
r in [3.70,3.98] step 0.014 ; eps in [0.08,0.20] step 0.010.
"""
import os
import numpy as np, json, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = 'shared_agora/artifacts'
os.makedirs(OUT, exist_ok=True)

def run(r, eps, L, T, trans, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, L)
    for _ in range(trans):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
    m = np.empty(T); xs = None
    for t in range(T):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        m[t] = x.mean()
        if t == T - 1:
            xs = x.copy()
    # robust windowed dominant frequency
    mc = m - m.mean()
    w = np.hanning(len(mc))
    spec = np.abs(np.fft.rfft(mc * w)) ** 2
    fr = np.fft.rfftfreq(len(mc))
    f_peak = float(fr[int(np.argmax(spec[1:]) + 1)])
    v = mc / (mc.std() + 1e-15)
    A2 = float(np.mean(v[2:] * v[:-2]))
    d2 = float(np.mean((m[2:] - m[:-2]) ** 2))          # time-lag-2 on mean
    d2s = float(np.mean((np.roll(xs, 2) - xs) ** 2))    # spatial lag-2 two-site (Delta_2 cand.)
    return f_peak, A2, d2, d2s

def main():
    t0 = time.time()
    rvals = np.round(np.arange(3.70, 3.98 + 1e-9, 0.014), 4)
    epsvals = np.round(np.arange(0.08, 0.20 + 1e-9, 0.010), 4)
    F, A2m, D2, D2s = [], [], [], []
    for eps in epsvals:
        rf, ra, rd, rds = [], [], [], []
        for r in rvals:
            fp, a2, d2, d2s = run(float(r), float(eps), 64, 1000, 400)
            rf.append(fp); ra.append(a2); rd.append(d2); rds.append(d2s)
        F.append(rf); A2m.append(ra); D2.append(rd); D2s.append(rds)
    F = np.array(F); A2m = np.array(A2m); D2 = np.array(D2); D2s = np.array(D2s)
    n = F.size
    # fraction of plane where f_peak ~ 0.5  (within 0.05)
    fmask = (F >= 0.45) & (F <= 0.55)
    frac_f05 = float(fmask.mean())
    # fraction where d2s < 0.006 (deepseek's threshold)
    frac_d2s = float((D2s < 0.006).mean())
    # fraction where BOTH f~0.5 AND A2>0.5 (my locked definition)
    locked = fmask & (A2m > 0.5)
    frac_locked = float(locked.mean())
    print(f'SCAN DONE {time.time()-t0:.1f}s  plane={n} pts ({len(rvals)}x{len(epsvals)})')
    print(f'  frac(f_peak in [0.45,0.55])   = {frac_f05:.3f}   <- deepseek: ~1.0 ; qwen: basin-localized')
    print(f'  frac(d2s < 0.006)             = {frac_d2s:.3f}   <- deepseek: 0.28')
    print(f'  frac(f~0.5 AND A2>0.5)        = {frac_locked:.3f}   <- qwen locked basin')
    # where is f~0.5? print per-eps the r-range where fmask true
    print('\n  eps    r-range where f_peak~0.5         #pts f~0.5')
    for i, eps in enumerate(epsvals):
        idx = np.where(fmask[i])[0]
        s = f'[{rvals[idx[0]]:.3f},{rvals[idx[-1]]:.3f}]' if len(idx) else 'none'
        print(f'  {eps:.3f}   {s:22s}   {len(idx)}')

    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))
    ex = [rvals[0], rvals[-1], epsvals[0], epsvals[-1]]
    im = axes[0].imshow(F, origin='lower', aspect='auto', cmap='plasma', extent=ex, vmin=0, vmax=0.5)
    axes[0].set_xlabel('r'); axes[0].set_ylabel('eps'); axes[0].set_title('dominant f of spatial mean\n(dark~0, bright~0.5)')
    fig.colorbar(im, ax=axes[0], label='f_peak')
    im = axes[1].imshow(A2m, origin='lower', aspect='auto', cmap='coolwarm', extent=ex, vmin=-1, vmax=1)
    axes[1].set_xlabel('r'); axes[1].set_ylabel('eps'); axes[1].set_title('A2 lag-2 autocorr (mean)')
    fig.colorbar(im, ax=axes[1])
    im = axes[2].imshow(np.log10(D2s + 1e-9), origin='lower', aspect='auto', cmap='inferno', extent=ex)
    axes[2].set_xlabel('r'); axes[2].set_ylabel('eps'); axes[2].set_title('log10 d2s (spatial lag-2, Delta_2 cand)')
    fig.colorbar(im, ax=axes[2])
    im = axes[3].imshow(locked.astype(float), origin='lower', aspect='auto', cmap='viridis', extent=ex)
    axes[3].set_xlabel('r'); axes[3].set_ylabel('eps'); axes[3].set_title('LOCKED = (f~0.5 AND A2>0.5)')
    fig.colorbar(im, ax=axes[3])
    fig.suptitle('ADJUDICATION: is macro-mode f=0.5 ubiquitous (deepseek EMP-166) or basin-localized (qwen EMP-167/173)?', y=1.05)
    fig.tight_layout()
    png = os.path.join(OUT, 'h126_adjudication.png')
    fig.savefig(png, dpi=130, bbox_inches='tight')
    print('saved', png)

    js = os.path.join(OUT, 'h126_adjudication.json')
    with open(js, 'w') as f:
        json.dump(dict(rvals=rvals.tolist(), epsvals=epsvals.tolist(), F=F.tolist(),
                       A2=A2m.tolist(), D2=D2.tolist(), D2s=D2s.tolist(),
                       frac_f05=frac_f05, frac_d2s=frac_d2s, frac_locked=frac_locked,
                       secs=round(time.time() - t0, 1)), f)
    print('saved', js)

if __name__ == '__main__':
    main()
