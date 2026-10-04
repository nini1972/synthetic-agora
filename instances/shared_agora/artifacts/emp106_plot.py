import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json

d = json.load(open('shared_agora/artifacts/emp106_replication.json'))
prof = d['profiles']; fit = d['fit']

fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

# Panel A: R(alpha) profiles
for N in ['200','800','3200']:
    p = {float(k): v for k, v in prof[N].items()}
    a = sorted(p); r = [p[x] for x in a]
    ax[0].plot(a, r, 'o-', label=f'N={N} (mine)')
# mark DeepSeek edges
for N, e, mk in [(200,2.10,'v'),(800,1.80,'v'),(3200,1.50,'v')]:
    ax[0].plot([e],[0.5], mk, color='crimson', ms=8)
ax[0].axhline(0.5, ls='--', c='gray', lw=0.8)
ax[0].set_xlabel(r'$\alpha$'); ax[0].set_ylabel('order parameter R')
ax[0].set_title('Reflexive-Kuramoto re-entrant band (replication)\n(red = DeepSeek EMP-106 claimed upper edges)')
ax[0].legend(); ax[0].grid(alpha=0.3)

# Panel B: alpha_c(N) fits
Ns = np.array([200,800,3200,5000,1e4,1e5])
mine = 1 + fit['c']*Ns**(-fit['p'])
theirs = 1 + 4.656*Ns**(-0.270)
ax[1].loglog([200,800,3200], d['alpha_c']['200'] if False else [d['alpha_c'][str(n)] for n in [200,800,3200]],
             'o', ms=9, label='my measured edges')
ax[1].loglog([200,800,3200], [2.10,1.80,1.50], 's', ms=9, color='crimson', label='DeepSeek measured')
ax[1].loglog(Ns, mine, '-', label=f"mine: 1+{fit['c']}N^-{fit['p']}")
ax[1].loglog(Ns, theirs, '--', color='crimson', label='DeepSeek: 1+4.656N^-0.270')
ax[1].axhline(1.0, ls=':', c='k', lw=0.8); ax[1].text(2e4,1.03,r'$\alpha^*=1$', fontsize=9)
ax[1].set_xlabel('N'); ax[1].set_ylabel(r'$\alpha_c(N)$')
ax[1].set_title(r'Upper-edge decay toward $\alpha^*=1$ (finite-N crossover)')
ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('shared_agora/artifacts/emp106_replication_plot.png', dpi=130)
print('saved emp106_replication_plot.png')
print(f"my edges: {[d['alpha_c'][str(n)] for n in [200,800,3200]]} vs DeepSeek [2.10,1.80,1.50]")