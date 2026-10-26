"""
EMP-167 active defense / refinement: full (r,eps) basin map of the f=0.5000 P2-lock basin.

Question: over which eps does the resonant P2-lock basin extend, and what are its
r-boundaries r_left(eps), r_right(eps)? We map LOCK FRACTION P3 = (#locking seeds)/3,
where a seed 'locks' iff A2 (lag-2 autocorr of spatial mean) > 0.5 AND f_peak in [0.45,0.55].

Fast grid for in-turn completion: L=32, T=400, trans=200, 3 seeds.
  r   in [3.78, 3.98] step 0.008  (26 values)
  eps in [0.100,0.160] step 0.008 (8 values)
"""
import os
import numpy as np, json, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = 'shared_agora/artifacts'
os.makedirs(OUT, exist_ok=True)

def cml_metrics(r, eps, L, T, trans, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, L)
    for _ in range(trans):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
    m = np.empty(T)
    for t in range(T):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        m[t] = x.mean()
    mc = m - m.mean()
    spec = np.abs(np.fft.rfft(mc * np.hanning(len(mc))))**2
    freqs = np.fft.rfftfreq(len(mc))
    f_peak = float(freqs[int(np.argmax(spec[1:]) + 1)])
    v = mc / (mc.std() + 1e-15)
    A2 = float(np.mean(v[2:] * v[:-2]))
    d2 = float(np.mean((m[2:] - m[:-2])**2))
    lock = (A2 > 0.5) and (0.45 <= f_peak <= 0.55)
    return lock, A2, f_peak, d2

def main():
    t0 = time.time()
    rvals = np.round(np.arange(3.78, 3.98 + 1e-9, 0.008), 4)
    epsvals = np.round(np.arange(0.100, 0.160 + 1e-9, 0.008), 4)
    P3, A2m, D2m = [], [], []
    for eps in epsvals:
        rowP, rowA, rowD = [], [], []
        for r in rvals:
            lk = 0
            A2s, fps, d2s = [], [], []
            for seed in (0, 1, 2):
                l, A2, fp, d2 = cml_metrics(float(r), float(eps), 32, 400, 200, seed)
                lk += int(l); A2s.append(A2); fps.append(fp); d2s.append(d2)
            rowP.append(lk / 3)
            rowA.append(float(np.median(A2s)))
            rowD.append(float(np.median(d2s)))
        P3.append(rowP); A2m.append(rowA); D2m.append(rowD)
    P3 = np.array(P3)   # (n_eps, n_r)
    A2m = np.array(A2m)
    D2m = np.array(D2m)
    print(f'GRID DONE in {time.time()-t0:.1f}s  shape(P3)={P3.shape} (eps x r)')

    print('\n  eps    P3>=2/3 span            P3=1 span              A2(med)  d2(med)')
    summary = []
    for i, eps in enumerate(epsvals):
        p = P3[i]
        idx = np.where(p >= 0.667)[0]
        idx1 = np.where(p == 1.0)[0]
        span = f'[{rvals[idx[0]]:.4f},{rvals[idx[-1]]:.4f}]' if len(idx) else 'none'
        span1 = f'[{rvals[idx1[0]]:.4f},{rvals[idx1[-1]]:.4f}]' if len(idx1) else 'none'
        summary.append(dict(eps=float(eps), span23=span, span1=span1,
                            A2=float(np.median(A2m[i])), d2=float(np.median(D2m[i]))))
        print(f'  {eps:.3f}   {span:22s}   {span1:22s}   {np.median(A2m[i]):+.3f}   {np.median(D2m[i]):.5f}')

    # --- plot: three panels, all shape (n_eps, n_r), extent [r0,r1,eps0,eps1] ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ax = axes[0]
    im = ax.imshow(P3, origin='lower', aspect='auto', cmap='viridis',
                   extent=[rvals[0], rvals[-1], epsvals[0], epsvals[-1]])
    ax.contour(rvals, epsvals, P3, levels=[1/3, 2/3], colors=['orange', 'red'], linewidths=1.4)
    ax.set_xlabel('r'); ax.set_ylabel('eps')
    ax.set_title('P2-lock seed fraction (3 seeds)\ncontours at 1/3 (orange), 2/3 (red)')
    fig.colorbar(im, ax=ax, label='fraction locked')
    im = axes[1].imshow(A2m, origin='lower', aspect='auto', cmap='coolwarm',
                        extent=[rvals[0], rvals[-1], epsvals[0], epsvals[-1]], vmin=-1, vmax=1)
    axes[1].set_xlabel('r'); axes[1].set_ylabel('eps'); axes[1].set_title('median A2 (lag-2 autocorr of mean)')
    fig.colorbar(im, ax=axes[1])
    im = axes[2].imshow(np.log10(D2m + 1e-9), origin='lower', aspect='auto', cmap='inferno',
                        extent=[rvals[0], rvals[-1], epsvals[0], epsvals[-1]])
    axes[2].set_xlabel('r'); axes[2].set_ylabel('eps'); axes[2].set_title('median log10 d2 (lag-2 struct var)')
    fig.colorbar(im, ax=axes[2])
    fig.suptitle('EMP-167 basin map: f=0.5000 P2-lock basin in (r,eps); L=32, T=400, 3 seeds', y=1.04)
    fig.tight_layout()
    png = os.path.join(OUT, 'h126_basin_map.png')
    fig.savefig(png, dpi=130, bbox_inches='tight')
    print('saved', png)

    out = dict(rvals=rvals.tolist(), epsvals=epsvals.tolist(),
               P3=P3.tolist(), A2=A2m.tolist(), D2=D2m.tolist(), summary=summary,
               secs=round(time.time()-t0, 1))
    js = os.path.join(OUT, 'h126_basin_map.json')
    with open(js, 'w') as f:
        json.dump(out, f)
    print('saved', js)

if __name__ == '__main__':
    main()
