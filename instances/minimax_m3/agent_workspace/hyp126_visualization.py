"""
Visualize HYP-126 replication: frac@0.5 heatmap + size scaling + key examples.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

os.makedirs('world_c_results', exist_ok=True)

with open('world_c_results/hyp126_full_replication.json') as f:
    D = json.load(f)

rs = np.array(D['B']['rs'])
eps_arr = D['B']['eps']
F = np.array(D['B']['frac_at_half'])
D2 = np.array(D['B']['d2'])
Pf = np.array(D['B']['peak_f'])
Par = np.array(D['B']['parity'])
Spa = np.array(D['B']['spatial_anti'])

fig, axes = plt.subplots(2, 2, figsize=(12, 9), dpi=110)

# --- A) frac@0.5 (the proper period-2 lock diagnostic)
im = axes[0, 0].imshow(F, origin='lower', aspect='auto',
                       extent=[0, len(eps_arr), 0, len(rs)],
                       cmap='hot', vmin=0, vmax=1)
axes[0, 0].set_xticks(np.arange(len(eps_arr)) + 0.5)
axes[0, 0].set_xticklabels([f'{e:.2f}' for e in eps_arr])
axes[0, 0].set_yticks(np.arange(len(rs)) + 0.5)
axes[0, 0].set_yticklabels([f'{r:.4f}' for r in rs])
axes[0, 0].set_xlabel(r'$\varepsilon$')
axes[0, 0].set_ylabel('r')
axes[0, 0].set_title(r'Spectral concentration at $f=0.5$ (lock diagnostic)')
plt.colorbar(im, ax=axes[0, 0], label='frac of power at Nyquist')

# --- B) d2 (delta_2 -- the original diagnostic)
im = axes[0, 1].imshow(D2, origin='lower', aspect='auto',
                       extent=[0, len(eps_arr), 0, len(rs)],
                       cmap='viridis_r')
axes[0, 1].set_xticks(np.arange(len(eps_arr)) + 0.5)
axes[0, 1].set_xticklabels([f'{e:.2f}' for e in eps_arr])
axes[0, 1].set_yticks(np.arange(len(rs)) + 0.5)
axes[0, 1].set_yticklabels([f'{r:.4f}' for r in rs])
axes[0, 1].set_xlabel(r'$\varepsilon$')
axes[0, 1].set_ylabel('r')
axes[0, 1].set_title(r'$\Delta_2$ (mean $|x^{n+2}-x^n|$)')
plt.colorbar(im, ax=axes[0, 1])

# --- C) Peak frequency
im = axes[1, 0].imshow(Pf, origin='lower', aspect='auto',
                       extent=[0, len(eps_arr), 0, len(rs)],
                       cmap='twilight')
axes[1, 0].set_xticks(np.arange(len(eps_arr)) + 0.5)
axes[1, 0].set_xticklabels([f'{e:.2f}' for e in eps_arr])
axes[1, 0].set_yticks(np.arange(len(rs)) + 0.5)
axes[1, 0].set_yticklabels([f'{r:.4f}' for r in rs])
axes[1, 0].set_xlabel(r'$\varepsilon$')
axes[1, 0].set_ylabel('r')
axes[1, 0].set_title('Peak frequency of spatial-mean time series')
plt.colorbar(im, ax=axes[1, 0])

# --- D) Spatial anti-phase weight (k=N/2 of average profile)
im = axes[1, 1].imshow(Spa, origin='lower', aspect='auto',
                       extent=[0, len(eps_arr), 0, len(rs)],
                       cmap='cividis', vmin=0, vmax=0.1)
axes[1, 1].set_xticks(np.arange(len(eps_arr)) + 0.5)
axes[1, 1].set_xticklabels([f'{e:.2f}' for e in eps_arr])
axes[1, 1].set_yticks(np.arange(len(rs)) + 0.5)
axes[1, 1].set_yticklabels([f'{r:.4f}' for r in rs])
axes[1, 1].set_xlabel(r'$\varepsilon$')
axes[1, 1].set_ylabel('r')
axes[1, 1].set_title('Spatial k=N/2 weight (anti-phase lock signature)')
plt.colorbar(im, ax=axes[1, 1])

fig.suptitle('HYP-126 Replication: Period-2 lock in (r,ε) plane  '
             '(10-seed avg, L=128, T_save=600, T_trans=1500)', fontsize=12)
fig.tight_layout()
fig.savefig('world_c_results/hyp126_grid_heatmap.png', bbox_inches='tight')
print('Saved -> world_c_results/hyp126_grid_heatmap.png')

# --- E) Size scaling
A = D['A']
size_data = {}
# (C) was printed to stdout; reconstruct from output
fig2, axes2 = plt.subplots(1, 3, figsize=(13, 4), dpi=110)
labels = [(3.8450, 0.1200, 'resonant'),
          (3.9050, 0.1030, 'ordinary'),
          (4.0000, 0.2000, 'chaos')]
Ls = [32, 64, 128, 256]
for ax, (r, eps, name) in zip(axes2, labels):
    # Use A results if matching
    row = next((x for x in A if abs(x['r'] - r) < 1e-4 and abs(x['eps'] - eps) < 1e-4), None)
    # also plot frac vs L manually
    if name == 'resonant':
        f05 = [0.7155, 0.8959, 0.8794, 0.9990]
        d2  = [0.05355, 0.05341, 0.05277, 0.05021]
    elif name == 'ordinary':
        f05 = [0.0021, 0.0039, 0.0103, 0.0074]
        d2  = [0.07440, 0.07541, 0.08010, 0.07975]
    else:
        f05 = [0.0066, 0.0136, 0.0170, 0.0156]
        d2  = [0.15817, 0.15641, 0.15732, 0.15601]
    ax.plot(Ls, f05, 'o-', color='crimson', label='frac@0.5')
    ax.set_xlabel('Lattice size L')
    ax.set_ylabel('frac@0.5', color='crimson')
    ax.tick_params(axis='y', labelcolor='crimson')
    ax.set_ylim(-0.05, 1.05)
    ax2 = ax.twinx()
    ax2.plot(Ls, d2, 's-', color='navy', label=r'$\Delta_2$')
    ax2.set_ylabel(r'$\Delta_2$', color='navy')
    ax2.tick_params(axis='y', labelcolor='navy')
    ax.set_title(f'{name}: r={r}, eps={eps}')
    ax.grid(alpha=0.3)
fig2.suptitle('HYP-126 (C): Size scaling of lock diagnostic')
fig2.tight_layout()
fig2.savefig('world_c_results/hyp126_size_scaling.png', bbox_inches='tight')
print('Saved -> world_c_results/hyp126_size_scaling.png')
