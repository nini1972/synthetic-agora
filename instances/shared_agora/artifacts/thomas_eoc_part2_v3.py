"""
EMP-043 Part 2: Fast Experiment (with FIXED LZ76)
"""
import sys, os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ── import Part 1 ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thomas_eoc_part1_v3 import *

print("Part 1 (v3) loaded. Starting experiment...")

# ── Parameters ──
dt = 0.05
T_transient = 250
T_measure = 300
bs = np.concatenate([np.linspace(0.05, 0.25, 9),
                     np.linspace(0.15, 0.26, 8),
                     np.linspace(0.26, 0.36, 5)])
bs = np.unique(np.round(bs, 3))
seeds_lyap = [42, 123]
seed_traj = 7

# ── Storage ──
res = dict(b=[], lam1=[], lam1_std=[], lam1_spec=[], H1=[], H2=[], H4=[], H6=[], H8=[],
           lz_raw=[], lz_norm=[], pe=[])

print("="*70)
print("EMP-043: Thomas Attractor - Edge-of-Chaos Resolution (v3 FIXED)")
print("Adjudicating DOSSIER_002 vs EMP-035/EMP-040")
print("="*70)

for idx, b in enumerate(bs):
    print(f"  b={b:.3f} ({idx+1}/{len(bs)})")
    
    # Lyapunov
    all_specs = [compute_lyapunov_spectrum(b, dt=0.02, T_transient=200, T_measure=600, seed=s) for s in seeds_lyap]
    lam1_vals = [sp[0] for sp in all_specs]
    mean_spec = np.mean(all_specs, axis=0)
    
    # Trajectory + symbolic dynamics
    rng = np.random.default_rng(seed_traj)
    state = rng.standard_normal(3) * 0.5
    for _ in range(int(T_transient/dt)):
        state = rk4_step(state, dt, b)
    n_m = int(T_measure/dt)
    traj = np.zeros((n_m, 3))
    for j in range(n_m):
        state = rk4_step(state, dt, b)
        traj[j] = state
    
    sym = symbolize(traj)
    
    res['b'].append(float(b))
    res['lam1'].append(float(mean_spec[0]))
    res['lam1_std'].append(float(np.std(lam1_vals)))
    res['lam1_spec'].append(mean_spec.tolist())
    
    for bs_, key in [(1,'H1'),(2,'H2'),(4,'H4'),(6,'H6'),(8,'H8')]:
        res[key].append(block_entropy(sym, bs_))
    
    lz = lz76(sym)
    lz_n = len(sym) / np.log2(len(sym))
    res['lz_raw'].append(int(lz))
    res['lz_norm'].append(float(lz / lz_n))
    res['pe'].append(perm_entropy(sym, order=4))

print("\nComputation done!")

with open('thomas_eoc_results_v3.json', 'w') as f:
    json.dump(res, f)
print("Results saved to thomas_eoc_results_v3.json")

# ── Summary ──
b_arr = np.array(res['b'])
lam_arr = np.array(res['lam1'])
lz_arr = np.array(res['lz_norm'])
pe_arr = np.array(res['pe'])
H4_arr = np.array(res['H4'])

# Edge-of-chaos region
eoc_mask = np.abs(lam_arr) < 0.01
if eoc_mask.any():
    eoc_b = b_arr[eoc_mask]
    print(f"\nEdge-of-chaos region (|lambda1| < 0.01): b in [{eoc_b.min():.3f}, {eoc_b.max():.3f}]")
print(f"DOSSIER_002 claimed b_c = 0.208")

# Peak locations
print(f"\nMetric peaks:")
print(f"  LZ complexity peak at b = {b_arr[np.argmax(lz_arr)]:.3f} (lambda1 = {lam_arr[np.argmax(lz_arr)]:.4f})")
print(f"  Permutation entropy peak at b = {b_arr[np.argmax(pe_arr)]:.3f} (lambda1 = {lam_arr[np.argmax(pe_arr)]:.4f})")
print(f"  Block entropy H(4) peak at b = {b_arr[np.argmax(H4_arr)]:.3f} (lambda1 = {lam_arr[np.argmax(H4_arr)]:.4f})")

# ── Visualization ──
fig = plt.figure(figsize=(18, 28))
gs = GridSpec(6, 1, figure=fig, hspace=0.35)

ax1 = fig.add_subplot(gs[0])
std_arr = np.array(res['lam1_std'])
ax1.fill_between(b_arr, lam_arr - std_arr, lam_arr + std_arr, alpha=0.3, color='gray')
ax1.plot(b_arr, lam_arr, 'ko-', ms=3, lw=1.5, label='lambda1 mean ± std (2 seeds)')
ax1.axhline(0, color='red', ls='--', lw=2, label='lambda1=0 (edge)')
ax1.axvline(0.208, color='green', ls=':', lw=2, label='b_c=0.208 (DOSSIER_002)')
for i in range(len(b_arr)-1):
    color = 'red' if lam_arr[i] > 0.01 else ('blue' if lam_arr[i] < -0.01 else 'green')
    ax1.axvspan(b_arr[i], b_arr[i+1], alpha=0.05, color=color)
ax1.set_xlabel('Dissipation parameter b', fontsize=12)
ax1.set_ylabel('Largest Lyapunov Exponent', fontsize=12)
ax1.set_title('Panel 1: Lyapunov Exponent (Ground Truth)\nRed=chaotic, Blue=stable, Green=marginal', fontsize=13)
ax1.legend(fontsize=10)
ax1.set_ylim([-0.15, 0.3])

ax2 = fig.add_subplot(gs[1])
lams = np.array(res['lam1_spec'])
for k in range(3):
    ax2.plot(b_arr, lams[:, k], 'o-', ms=2, lw=1, label=f'lambda_{k+1}')
ax2.axhline(0, color='red', ls='--', alpha=0.5)
ax2.axvline(0.208, color='green', ls=':', alpha=0.5)
ax2.set_xlabel('b', fontsize=12)
ax2.set_ylabel('Lyapunov Exponents', fontsize=12)
ax2.set_title('Panel 2: Full Lyapunov Spectrum (all 3 exponents)', fontsize=13)
ax2.legend(fontsize=10)

ax3 = fig.add_subplot(gs[2])
for key, lbl, col in [('H1','H(1)','#e74c3c'),('H2','H(2)','#e67e22'),
                       ('H4','H(4)','#27ae60'),('H6','H(6)','#2980b9'),('H8','H(8)','#8e44ad')]:
    ax3.plot(b_arr, np.array(res[key]), 'o-', color=col, ms=3, lw=1.5, label=lbl)
ax3.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax3.set_xlabel('b', fontsize=12)
ax3.set_ylabel('Block Entropy (bits)', fontsize=12)
ax3.set_title('Panel 3: Block Entropy at Multiple Block Sizes\n(DOSSIER_002 claims H peaks near b_c)', fontsize=13)
ax3.legend(ncol=3, fontsize=9)

ax4 = fig.add_subplot(gs[3])
ax4.plot(b_arr, lz_arr, 'o-', color='#e74c3c', ms=3, lw=1.5, label='Normalized LZ (FIXED)')
ax4.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax4.set_xlabel('b', fontsize=12)
ax4.set_ylabel('Normalized LZ Complexity', fontsize=12)
ax4.set_title('Panel 4: Lempel-Ziv Complexity (FIXED LZ78)\n(EMP-035 claims LZ peaks at LOW b)', fontsize=13)
ax4.legend(fontsize=10)

ax5 = fig.add_subplot(gs[4])
ax5.plot(b_arr, pe_arr, 'o-', color='#8e44ad', ms=3, lw=1.5, label='Perm Entropy')
ax5.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax5.set_xlabel('b', fontsize=12)
ax5.set_ylabel('Normalized Permutation Entropy', fontsize=12)
ax5.set_title('Panel 5: Permutation Entropy (order=4)', fontsize=13)
ax5.legend(fontsize=10)

ax6 = fig.add_subplot(gs[5])
norm_lam = (lam_arr - lam_arr.min()) / (lam_arr.max() - lam_arr.min() + 1e-10)
norm_lz = (lz_arr - lz_arr.min()) / (lz_arr.max() - lz_arr.min() + 1e-10)
norm_pe = (pe_arr - pe_arr.min()) / (pe_arr.max() - pe_arr.min() + 1e-10)
norm_H4 = (H4_arr - H4_arr.min()) / (H4_arr.max() - H4_arr.min() + 1e-10)

ax6.plot(b_arr, norm_lam, 'k-', lw=2, label='lambda1 (norm)')
ax6.plot(b_arr, norm_lz, 'r-', lw=2, label='LZ norm')
ax6.plot(b_arr, norm_pe, 'purple', lw=2, label='Perm Entropy')
ax6.plot(b_arr, norm_H4, 'g-', lw=2, label='H(4)')
ax6.axvline(0.208, color='green', ls=':', lw=2, label='b_c')
ax6.axvspan(0.15, 0.25, alpha=0.1, color='green')
ax6.set_xlabel('b', fontsize=12)
ax6.set_ylabel('Normalized Value', fontsize=12)
ax6.set_title('Panel 6: All Metrics Overlaid (Normalized)', fontsize=13)
ax6.legend(fontsize=10)

plt.suptitle('EMP-043: Thomas Attractor Edge-of-Chaos Resolution\nResolving DOSSIER_002 vs EMP-035/EMP-040 (FIXED LZ76)', fontsize=16, y=0.98)
plt.savefig('thomas_eoc_resolution_v3.png', dpi=150, bbox_inches='tight')
print("\nSaved: thomas_eoc_resolution_v3.png")
plt.close()
