import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Load results
with open('thomas_eoc_results.json', 'r') as f:
    res = json.load(f)

fig = plt.figure(figsize=(18, 28))
gs = GridSpec(6, 1, figure=fig, hspace=0.35)
b = np.array(res['b'])
lam1 = np.array(res['lam1'])
lam1_std = np.array(res['lam1_std'])

# Panel 1: Lyapunov Exponent
ax1 = fig.add_subplot(gs[0])
ax1.fill_between(b, lam1 - lam1_std, lam1 + lam1_std, alpha=0.3, color='gray')
ax1.plot(b, lam1, 'ko-', ms=3, lw=1.5, label='lambda1 mean +/- std (2 seeds)')
ax1.axhline(0, color='red', ls='--', lw=2, label='lambda1=0 (edge)')
ax1.axvline(0.208, color='green', ls=':', lw=2, label='b_c=0.208 (DOSSIER_002)')
for i in range(len(b)-1):
    color = 'red' if lam1[i] > 0.01 else ('blue' if lam1[i] < -0.01 else 'green')
    ax1.axvspan(b[i], b[i+1], alpha=0.05, color=color)
ax1.set_xlabel('Dissipation parameter b', fontsize=12)
ax1.set_ylabel('Largest Lyapunov Exponent', fontsize=12)
ax1.set_title('Panel 1: Lyapunov Exponent (Ground Truth)\nRed=chaotic, Blue=stable, Green=marginal', fontsize=13)
ax1.legend(fontsize=10)
ax1.set_ylim([-0.15, 0.3])

# Panel 2: Full Lyapunov Spectrum
ax2 = fig.add_subplot(gs[1])
lams = np.array(res['lam1_spec'])
for k in range(3):
    ax2.plot(b, lams[:, k], 'o-', ms=2, lw=1, label=f'lambda_{k+1}')
ax2.axhline(0, color='red', ls='--', alpha=0.5)
ax2.axvline(0.208, color='green', ls=':', alpha=0.5)
ax2.set_xlabel('b', fontsize=12)
ax2.set_ylabel('Lyapunov Exponents', fontsize=12)
ax2.set_title('Panel 2: Full Lyapunov Spectrum (all 3 exponents)', fontsize=13)
ax2.legend(fontsize=10)

# Panel 3: Block Entropies
ax3 = fig.add_subplot(gs[2])
for key, lbl, col in [('H1','H(1)','#e74c3c'),('H2','H(2)','#e67e22'),
                       ('H4','H(4)','#27ae60'),('H6','H(6)','#2980b9'),('H8','H(8)','#8e44ad')]:
    ax3.plot(b, np.array(res[key]), 'o-', color=col, ms=3, lw=1.5, label=lbl)
ax3.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax3.set_xlabel('b', fontsize=12)
ax3.set_ylabel('Block Entropy (bits)', fontsize=12)
ax3.set_title('Panel 3: Block Entropy at Multiple Block Sizes\n(DOSSIER_002 claims H peaks near b_c)', fontsize=13)
ax3.legend(ncol=3, fontsize=9)

# Panel 4: LZ Complexity
ax4 = fig.add_subplot(gs[3])
ax4.plot(b, np.array(res['lz_norm']), 'o-', color='#e74c3c', ms=3, lw=1.5, label='Normalized LZ')
ax4.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax4.set_xlabel('b', fontsize=12)
ax4.set_ylabel('Normalized LZ Complexity', fontsize=12)
ax4.set_title('Panel 4: Lempel-Ziv Complexity\n(EMP-035 claims LZ peaks at LOW b)', fontsize=13)
ax4.legend(fontsize=10)

# Panel 5: Permutation Entropy
ax5 = fig.add_subplot(gs[4])
ax5.plot(b, np.array(res['pe']), 'o-', color='#8e44ad', ms=3, lw=1.5, label='Perm Entropy')
ax5.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax5.set_xlabel('b', fontsize=12)
ax5.set_ylabel('Normalized Permutation Entropy', fontsize=12)
ax5.set_title('Panel 5: Permutation Entropy (order=4)', fontsize=13)
ax5.legend(fontsize=10)

# Panel 6: All metrics overlaid (normalized)
ax6 = fig.add_subplot(gs[5])
norm_lam = (lam1 - lam1.min()) / (lam1.max() - lam1.min() + 1e-10)
norm_lz = (np.array(res['lz_norm']) - min(res['lz_norm'])) / (max(res['lz_norm']) - min(res['lz_norm']) + 1e-10)
norm_pe = (np.array(res['pe']) - min(res['pe'])) / (max(res['pe']) - min(res['pe']) + 1e-10)
norm_H4 = (np.array(res['H4']) - min(res['H4'])) / (max(res['H4']) - min(res['H4']) + 1e-10)

ax6.plot(b, norm_lam, 'k-', lw=2, label='lambda1 (norm)')
ax6.plot(b, norm_lz, 'r-', lw=2, label='LZ norm')
ax6.plot(b, norm_pe, 'purple', lw=2, label='Perm Entropy')
ax6.plot(b, norm_H4, 'g-', lw=2, label='H(4)')
ax6.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax6.axvspan(0.15, 0.25, alpha=0.1, color='green')
ax6.set_xlabel('b', fontsize=12)
ax6.set_ylabel('Normalized Value', fontsize=12)
ax6.set_title('Panel 6: All Metrics Overlaid (Normalized)', fontsize=13)
ax6.legend(fontsize=10)

plt.suptitle('EMP-043: Thomas Attractor Edge-of-Chaos Resolution\nResolving DOSSIER_002 vs EMP-035/EMP-040', fontsize=16, y=0.98)
plt.savefig('thomas_eoc_resolution.png', dpi=150, bbox_inches='tight')
print("Saved: thomas_eoc_resolution.png")
plt.close()
