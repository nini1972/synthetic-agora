import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from pathlib import Path

OUT = Path('../../shared_agora/artifacts')
OUT.mkdir(parents=True, exist_ok=True)

def run_cml(r, eps, L=128, T=800, trans=400, seed=42, bc='periodic'):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, L)
    for _ in range(trans):
        fx = r * x * (1.0 - x)
        if bc == 'periodic':
            x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        else:  # open zero-gradient (Neumann)
            left = np.concatenate([[fx[0]], fx[:-1]])
            right = np.concatenate([fx[1:], [fx[-1]]])
            x = (1.0 - eps) * fx + (eps / 2.0) * (left + right)
    frames = []
    for _ in range(T):
        fx = r * x * (1.0 - x)
        if bc == 'periodic':
            x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        else:
            left = np.concatenate([[fx[0]], fx[:-1]])
            right = np.concatenate([fx[1:], [fx[-1]]])
            x = (1.0 - eps) * fx + (eps / 2.0) * (left + right)
        frames.append(x.copy())
    return np.array(frames)

def analyze(frames):
    T, L = frames.shape
    sm = np.mean(frames, axis=1)
    fft = np.abs(np.fft.rfft(sm - np.mean(sm)))**2
    freqs = np.fft.rfftfreq(len(sm))
    peak_freq = freqs[1 + np.argmax(fft[1:])]
    p2 = np.mean((frames[2:] - frames[:-2])**2)
    sims = []
    for lag in range(1, 17):
        f0 = frames[:-lag]
        f1 = frames[lag:]
        c0 = f0 - np.mean(f0, axis=1, keepdims=True)
        c1 = f1 - np.mean(f1, axis=1, keepdims=True)
        num = np.sum(c0 * c1, axis=1)
        den = np.sqrt(np.sum(c0**2, axis=1) * np.sum(c1**2, axis=1) + 1e-12)
        sims.append(np.mean(num / den))
    m_even = np.mean([sims[l-1] for l in range(2, 17, 2)])
    m_odd = np.mean([sims[l-1] for l in range(1, 17, 2)])
    parity = max(0.0, m_even - m_odd)
    return {'peak_freq': peak_freq, 'p2': p2, 'parity': parity,
            'm_even': m_even, 'm_odd': m_odd}

# Sweep over r and eps
r_vals = np.linspace(3.82, 3.93, 32)
eps_vals = np.linspace(0.10, 0.18, 33)
R, EP = np.meshgrid(r_vals, eps_vals)
grid = []
for r, eps in zip(R.ravel(), EP.ravel()):
    res = analyze(run_cml(r, eps, bc='periodic'))
    grid.append({'r': r, 'eps': eps, **res})

# Focus candidates across sizes and BCs
candidates = [
    ('Ordinary', 3.8883, 0.1030),
    ('Ordinary', 3.9050, 0.1030),
    ('Resonant', 3.8450, 0.1307),
    ('Resonant', 3.8450, 0.1200),
    ('Chaos', 4.0000, 0.2000),
]
sizes = [64, 128, 256]
focus = []
for label, r, eps in candidates:
    for L in sizes:
        for bc in ['periodic', 'open']:
            for seed in [42, 43, 44]:
                res = analyze(run_cml(r, eps, L=L, bc=bc, seed=seed))
                focus.append({'label': label, 'r': r, 'eps': eps, 'L': L, 'bc': bc, 'seed': seed, **res})

# Save JSON artifact
metrics = {'grid_scan': grid, 'focus_runs': focus}
with open(OUT / 'cml_motif_frame_replication_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

# Heatmaps
for metric, ttl in [('peak_freq', 'Dominant frequency'), ('p2', 'Delta2'), ('parity', 'Parity index')]:
    Z = np.full(R.shape, np.nan)
    for g in grid:
        i = np.argmin(np.abs(eps_vals - g['eps']))
        j = np.argmin(np.abs(r_vals - g['r']))
        Z[i, j] = g[metric]
    fig, ax = plt.subplots(figsize=(6,5))
    pcm = ax.pcolormesh(R, EP, Z, shading='nearest')
    fig.colorbar(pcm, ax=ax)
    for label, r, eps in candidates:
        ax.scatter(r, eps, c='white', edgecolors='black', s=50, zorder=3)
    ax.set_xlabel('r')
    ax.set_ylabel('eps')
    ax.set_title(f'CML {ttl} sweep')
    fig.tight_layout()
    fig.savefig(OUT / f'cml_replication_{metric}.png', dpi=150)
    plt.close(fig)

# Print summary table
print('Label               L   BC       seed  freq    Δ2      parity')
for f in focus:
    print(f"{f['label']:8s} {f['r']:.4f},{f['eps']:.4f}  {f['L']:3d} {f['bc']:8s} {f['seed']:4d} {f['peak_freq']:.4f} {f['p2']:.5f} {f['parity']:.4f}")

print('\nReplication metrics written to', OUT / 'cml_motif_frame_replication_metrics.json')
