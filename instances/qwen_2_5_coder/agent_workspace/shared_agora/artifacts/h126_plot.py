"""
Phase diagram of HYP-126 resonant (f=0.5) vs ordinary (f~0.25-0.27) CML window.
Plots the qwen 2D (r,eps) scan as three panels: dominant freq, d2 (max), parity.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

g = json.load(open('h126_replication.json'))['grid']
eps_vals = [0.08, 0.10, 0.12, 0.136, 0.16, 0.20]
r_vals = [3.80, 3.82, 3.84, 3.86, 3.88, 3.90, 3.92]

F = np.zeros((len(eps_vals), len(r_vals)))
D2 = np.zeros_like(F)
P = np.zeros_like(F)
for i, e in enumerate(eps_vals):
    for j, r in enumerate(r_vals):
        rec = g[f'{round(r, 3)},{e}']
        F[i, j] = rec['f_mode']
        D2[i, j] = rec['d2_range'][1]
        P[i, j] = rec['parity_range'][1]

fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
R, E = np.meshgrid(r_vals, eps_vals)

im0 = axes[0].pcolormesh(R, E, F, shading='auto', cmap='viridis', vmin=0, vmax=0.55)
for i in range(len(eps_vals)):
    for j in range(len(r_vals)):
        tag = 'P2' if F[i, j] > 0.45 else ('P4' if 0.20 < F[i, j] < 0.33 else ('SUB' if 0.33 <= F[i, j] <= 0.45 else 'DC'))
        axes[0].text(R[i, j], E[i, j], tag, ha='center', va='center',
                     fontsize=8, color='white', fontweight='bold')
cb0 = fig.colorbar(im0, ax=axes[0]); cb0.set_label('dominant freq (Nyq=0.5)')
axes[0].set_title('Dominant temporal freq (P2=resonant)')
axes[0].set_xlabel('r')

im1 = axes[1].pcolormesh(R, E, D2, shading='auto', cmap='magma', vmin=0, vmax=0.08)
cb1 = fig.colorbar(im1, ax=axes[1]); cb1.set_label('max d2 (lag-2 structural var)')
axes[1].set_title('d2 = mean||x(t+2)-x(t)||^2')
axes[1].set_xlabel('r')

im2 = axes[2].pcolormesh(R, E, P, shading='auto', cmap='coolwarm', vmin=0, vmax=2)
cb2 = fig.colorbar(im2, ax=axes[2]); cb2.set_label('parity = M_even - M_odd')
axes[2].set_title('parity (even-lag dominance)')
axes[2].set_xlabel('r')

# mark claimed window
from matplotlib.patches import Rectangle
ax0 = axes[0]
rect = Rectangle((3.845, 0.120), 0.030, 0.016, fill=False, edgecolor='cyan', lw=2, ls='--')
ax0.add_patch(rect)
ax0.text(3.86, 0.140, 'claimed\nwindow', color='cyan', fontsize=7, ha='center')

axes[0].set_ylabel('eps (coupling)')
fig.suptitle('HYP-126 CML phase diagram — qwen independent 2D (r,eps) scan (2 seeds/cell, L=128)', fontsize=12)
plt.tight_layout()
plt.savefig('h126_phase_diagram.png', dpi=130, bbox_inches='tight')
print('saved h126_phase_diagram.png')
print('F grid:\n', F.round(3))
