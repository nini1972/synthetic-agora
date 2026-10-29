import json, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

rows = json.load(open('cml_ic_horizon_stress.json'))
regimes = ['Ordinary', 'Resonant', 'STS-Chaos']
sigmas = [0.001, 0.01, 0.05, 0.20]
colors = {'Ordinary': '#1f77b4', 'Resonant': '#2ca02c', 'STS-Chaos': '#d62728'}

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
# panel A: peak_f vs sigma (T=400)
ax = axes[0]
for rg in regimes:
    ys = [next(x for x in rows if x['regime']==rg and x['sigma']==s and x['T']==400)['peak_f_med'] for s in sigmas]
    ax.plot(range(len(sigmas)), ys, 'o-', color=colors[rg], label=rg, lw=2)
ax.axhline(0.45, ls='--', c='gray', label='Nyquist threshold')
ax.set_xticks(range(len(sigmas))); ax.set_xticklabels([str(s) for s in sigmas])
ax.set_xlabel('IC dispersion σ'); ax.set_ylabel('median spectral peak f')
ax.set_title('A. peak_f vs IC noise (L=128, T=400)'); ax.legend(); ax.grid(alpha=.3)

# panel B: Delta2 vs sigma
ax = axes[1]
for rg in regimes:
    ys = [next(x for x in rows if x['regime']==rg and x['sigma']==s and x['T']==400)['d2_med'] for s in sigmas]
    ax.semilogy(range(len(sigmas)), ys, 's-', color=colors[rg], label=rg, lw=2)
ax.axhline(0.006, ls='--', c='gray', label='Δ₂<0.006 rule')
ax.set_xticks(range(len(sigmas))); ax.set_xticklabels([str(s) for s in sigmas])
ax.set_xlabel('IC dispersion σ'); ax.set_ylabel('median Δ₂ (lag-2 drift)')
ax.set_title('B. Δ₂ vs IC noise — only Resonant separates'); ax.legend(); ax.grid(alpha=.3)

# panel C: discriminability bars
ax = axes[2]
pf = [np.mean([x['P_nyq'] for x in rows if x['regime']==rg]) for rg in regimes]
d2 = [np.mean([x['P_d2'] for x in rows if x['regime']==rg]) for rg in regimes]
xpos = np.arange(len(regimes)); w=0.35
ax.bar(xpos-w/2, pf, w, label='P(peak_f>0.45)', color='#ff7f0e')
ax.bar(xpos+w/2, d2, w, label='P(Δ₂<0.006)', color='#9467bd')
ax.set_xticks(xpos); ax.set_xticklabels(regimes)
ax.set_ylabel('mean detection probability'); ax.set_title('C. Two rules: discriminability')
ax.legend(); ax.grid(alpha=.3, axis='y')

plt.tight_layout(); plt.savefig('hyp126_stress_verdict.png', dpi=130)
print("Saved hyp126_stress_verdict.png")
