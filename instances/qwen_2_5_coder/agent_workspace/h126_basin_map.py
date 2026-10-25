"""
EMP-167 defense / refinement: full (r,eps) basin map of the f=0.5000 P2-lock basin.
Question: at which eps does the basin extend, and what are its r-boundaries r_left(eps),
r_right(eps)?  We map LOCK PROBABILITY P3 = (#seeds in {0,1,2} that lock) / 3, where a seed
'locks' iff A2 (lag-2 autocorr of spatial mean) > 0.5 AND f_peak in [0.45,0.55].
L=32, T=1000, trans=400. r in [3.78,3.98] step 0.0025; eps in [0.100,0.160] step 0.003.
"""
import numpy as np, json, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def cml_lock(r, eps, L, T, trans, seed):
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
    f_peak = freqs[int(np.argmax(spec[1:]) + 1)]
    v = mc / (mc.std() + 1e-15)
    A2 = float(np.mean(v[2:] * v[:-2]))
    d2 = float(np.mean((m[2:] - m[:-2])**2))
    lock = (A2 > 0.5) and (0.45 <= f_peak <= 0.55)
    return lock, A2, f_peak, d2

if __name__ == '__main__':
    t0 = time.time()
    rvals = np.round(np.arange(3.78, 3.98 + 1e-9, 0.0025), 4)
    epsvals = np.round(np.arange(0.100, 0.160 + 1e-9, 0.003), 4)
    rows = []
    for eps in epsvals:
        row = []
        for r in rvals:
            locks = 0
            A2s, fps, d2s = [], [], []
            for seed in (0, 1, 2):
                lk, A2, fp, d2 = cml_lock(float(r), float(eps), 32, 1000, 400, seed)
                locks += int(lk); A2s.append(A2); fps.append(fp); d2s.append(d2)
            row.append(dict(p3=locks/3, A2=float(np.median(A2s)),
                            fp=float(np.median(fps)), d2=float(np.median(d2s))))
        rows.append(row)
    P3 = np.array([[row_['p3'] for row_ in rows]])[0].T if False else np.array([[r_['p3'] for r_ in row] for row in rows])  # eps x r
    A2m = np.array([[r_['A2'] for r_ in row] for row in rows])
    D2m = np.array([[r_['d2'] for r_ in row] for row in rows])
    print(f'scan done in {time.time()-t0:.1f}s; grid {P3.shape} (eps x r)')

    # boundary extraction: r_right(eps) = max r with P3>=2/3 (connected from interior);
    # r_left(eps) = min r with P3>=2/3
    print('\n  eps   P3>=2/3 span          P3=1 span           right-edge detail (P3 values near edge)')
    summary = []
    for i, eps in enumerate(epsvals):
        p = P3[i]
        idx = np.where(p >= 0.667)[0]
        idx1 = np.where(p == 1.0)[0]
        span = f'[{rvals[idx[0]]:.4f},{rvals[idx[-1]]:.4f}]' if len(idx) else 'none'
        span1 = f'[{rvals[idx1[0]]:.4f},{rvals[idx1[-1]]:.4f}]' if len(idx1) else 'none'
        summary.append(dict(eps=float(eps), span23=span, span1=span1))
        # edge detail: last few columns
        edge = ' '.join(f'{rvals[j]:.3f}:{p[j]:.0f}' for j in range(max(0,len(p)-8), len(p)))
        print(f'  {eps:.3f}  {span:26s}  {span1:26s}  {edge}')

    # plot: heatmap of P3 + contours; overlay d2
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    ax = axes[0]
    im = ax.imshow(P3.T, origin='lower', aspect='auto', cmap='viridis',
                   extent=[rvals[0], rvals[-1], epsvals[0], epsvals[-1]])
    ax.contour(rvals, epsvals, P3.T, levels=[0.1667, 0.5, 0.8333], colors='red', linewidths=1.2)
    ax.set_xlabel('r'); ax.set_ylabel('eps'); ax.set_title('P2-lock seed fraction (3 seeds)\ncontours: 1/3, 2/3, 1')
    fig.colorbar(im, ax=ax)
    im = axes[1].imshow(A2m.T, origin='lower', aspect='auto', cmap='coolwarm',
                        extent=[rvals[0], rvals[-1], epsvals[0], epsvals[-1]], vmin=-1, vmax=1)
    axes[1].set_xlabel('r'); axes[1].set_ylabel('eps'); axes[1].set_title('median A2 (lag-2 autocorr)')
    fig.colorbar(im, ax=axes[1])
    im = axes[2].imshow(np.log10(D2m + 1e-9).T, origin='lower', aspect='auto', cmap='inferno',
                        extent=[rvals[0], rvals[-1], epsvals[0], epsvals[-1]])
    axes[2].set_xlabel('r'); axes[2].set_ylabel('eps'); axes[2].set_title('median log10 d2 (lag-2 struct var)')
    fig.colorbar(im, ax=axes[2])
    fig.suptitle('EMP-167 basin map: f=0.5000 P2-lock basin in (r,eps), L=32, 3 seeds', y=1.02)
    fig.tight_layout()
    fig.savefig('h126_basin_map.png', dpi=130, bbox_inches='tight')
    print('saved h126_basin_map.png')

    out = dict(rvals=rvals.tolist(), epsvals=epsvals.tolist(),
               P3=P3.tolist(), A2=A2m.tolist(), D2=D2m.tolist(), summary=summary,
               secs=round(time.time()-t0, 1))
    with open('h126_basin_map.json', 'w') as f:
        json.dump(out, f)
    print('saved h126_basin_map.json')
