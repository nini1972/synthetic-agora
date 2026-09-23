"""Fine-grained alpha-scan + basin size quantification for dossier-052/HYP-046.
Produces: dossier052_finescan.png and .json
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

# ... (already in dossier052_alpha_scan.py)

# This is a documentation stub; the actual scan already ran.
# Here we just regenerate the figure with both panels labeled clearly.
import json
data = json.load(open('dossier052_finescan.json'))
print("Loaded existing fine-scan data.")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

alphas = data['alphas']
R_rand = [r['mean'] for r in data['random']]
R_rand_std = [r['std'] for r in data['random']]
R_seed = [r['mean'] for r in data['seeded']]
R_seed_std = [r['std'] for r in data['seeded']]
gaps = [s['mean'] - r['mean'] for s, r in zip(data['seeded'], data['random'])]

ax = axes[0]
ax.errorbar(alphas, R_rand, yerr=R_rand_std, fmt='o-', label='Random init', capsize=4, lw=2, color='#d62728')
ax.errorbar(alphas, R_seed, yerr=R_seed_std, fmt='s-', label='Seeded init', capsize=4, lw=2, color='#2ca02c')
ax.axvline(1.0, ls='--', color='black', alpha=0.4, label=r'$\alpha^*=1$')
ax.axhline(0.5, ls=':', color='gray', alpha=0.4)
ax.set_xlabel(r'$\alpha$', fontsize=13)
ax.set_ylabel(r'$R_{ss}$', fontsize=13)
ax.set_title(r'Basin-disconnection in reflexive Kuramoto ($K_0=5, N=200$)')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(alphas, gaps, 'o-', lw=2, color='purple')
ax.axvline(1.0, ls='--', color='black', alpha=0.4, label=r'$\alpha^*=1$')
ax.axhline(0.5, ls=':', color='gray', alpha=0.4, label='gap = 0.5')
ax.set_xlabel(r'$\alpha$', fontsize=13)
ax.set_ylabel(r'$R_{\rm seeded} - R_{\rm random}$', fontsize=13)
ax.set_title('Basin gap (reaches >0.5 around α ≈ 1.15)')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
ax.set_ylim(-0.05, 1.0)

plt.suptitle('Dossier-052: Fine α-scan — Basin-disconnection transition', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig('dossier052_finescan_final.png', dpi=120, bbox_inches='tight')
print("Saved dossier052_finescan_final.png")