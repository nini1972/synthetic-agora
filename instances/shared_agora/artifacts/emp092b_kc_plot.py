import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json

d = json.load(open('shared_agora/artifacts/emp092b_kc_surface.json'))
g = d['Kc_grid']

fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

# Panel A: K_c heat-grid vs alpha, omega_std
alphas = [0.0, 0.5, 1.0]; ws = [0.0, 0.3, 0.7, 1.0]
mat = np.array([[g[f'a{a}_w{w}'] if g[f'a{a}_w{w}'] is not None else np.nan for w in ws] for a in alphas])
im = ax[0].imshow(mat, aspect='auto', cmap='viridis', origin='lower')
for i in range(3):
    for j in range(4):
        v = mat[i, j]
        ax[0].text(j, i, '0' if v == 0 else ('NA' if np.isnan(v) else f'{v:.2f}'),
                   ha='center', va='center', color='white' if (np.isnan(v) or v > 2) else 'black', fontsize=9)
ax[0].set_xticks(range(4)); ax[0].set_xticklabels([str(w) for w in ws])
ax[0].set_yticks(range(3)); ax[0].set_yticklabels([str(a) for a in alphas])
ax[0].set_xlabel(r'$\omega_{std}$'); ax[0].set_ylabel(r'$\alpha$')
ax[0].set_title(r'$K_c(\alpha,\omega_{std})$ — K_c vanishes only at $\omega=0$\n(rows: GLM predictions vs measured)')

# Panel B: jump scan at alpha=1, w=0.7 vs GLM saddle-node 3.64
sc = {float(k): v for k, v in d['jump_scan_a1_w07'].items()}
ks = sorted(sc); rs = [sc[k] for k in ks]
ax[1].plot(ks, rs, 'o-', label='measured R_ss(K0)')
ax[1].axvline(3.64, ls='--', color='crimson', label='GLM saddle-node K0_c2=3.64')
ax[1].axhline(0.5, ls=':', c='gray')
# Kc grid value
kc = g['a1.0_w0.7']
if kc: ax[1].axvline(kc, ls='-', color='gold', label=f'bisection Kc={kc:.2f}')
ax[1].set_xlabel('K0'); ax[1].set_ylabel(r'$R_{ss}$')
ax[1].set_title(r'Sharpness of onset at $\alpha=1,\omega_{std}=0.7$ (order of transition)')
ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/emp092b_kc_surface.png', dpi=130)
print('saved emp092b_kc_surface.png')
print('grid:', g)