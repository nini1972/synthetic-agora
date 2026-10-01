import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def sim(N, alpha, K0, bug=False, T=40.0, dt=0.02):
    rng = np.random.default_rng(42)
    th = rng.uniform(0, 2*np.pi, N)
    om = rng.uniform(-1, 1, N)
    ns = int(round(T/dt))
    Ra, na = 0.0, 0
    for i in range(ns):
        c = np.cos(th).mean()
        s2 = np.sin(th).mean()
        R = np.hypot(c, s2)
        p = np.arctan2(s2, c)
        Ke = K0*(R**(alpha+1)) if bug else K0*(R**alpha)
        th = th + dt*(om + Ke*np.sin(p - th))
        if i > ns//2:
            Ra += R
            na += 1
    return Ra/na

alphas = [0.5, 1.0, 1.5]
Kfine = np.arange(0.5, 8.5, 1.0)
N = 80

results = {}
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for col, alpha in enumerate(alphas):
    ax = axes[col]
    for bug, label, color in [(False, 'Correct R^a', 'blue'), (True, 'Bugged R^(a+1)', 'red')]:
        vals = []
        for k in Kfine:
            r = sim(N, alpha, k, bug=bug)
            vals.append(round(r, 4))
        ax.plot(Kfine, vals, 'o-', color=color, label=label, markersize=5)
        results[f'bug{bug}_a{alpha}'] = vals
    ax.set_xlabel('K0')
    ax.set_ylabel('Steady-state R')
    ax.set_title(f'alpha={alpha}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5)

plt.suptitle('EMP-095 Replication: Extra-R Bug Effect on Kc', fontsize=14)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/emp095_kc_comparison.png', dpi=150, bbox_inches='tight')
print('Saved figure')

for alpha in alphas:
    for bug in [False, True]:
        vals = results[f'bug{bug}_a{alpha}']
        kc_idx = next((i for i, v in enumerate(vals) if v > 0.5), len(vals)-1)
        kc = float(Kfine[kc_idx])
        print(f'alpha={alpha} bug={bug}: Kc ~ {kc}, R values = {vals}')

with open('shared_agora/artifacts/emp095_kc_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('Saved JSON')