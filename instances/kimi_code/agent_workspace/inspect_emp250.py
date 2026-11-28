import json, pandas as pd, numpy as np
from scipy.stats import spearmanr

with open('world_c_results/replicate_emp250_fast_results.json') as f:
    data = json.load(f)
df = pd.DataFrame(data['results'])
band_freq = {'Delta': 2.25, 'Theta': 6.0, 'Alpha': 10.5, 'Beta': 21.5, 'Gamma': 37.5}
df['freq'] = df['band'].map(band_freq)

# Check RR actual closeness
print('Mean absolute RR deviation from target:')
print((df['RR_actual']-df['RR_target']).abs().groupby([df['norm'], df['RR_target']]).mean().reset_index(name='mean_abs_err').to_string(index=False))

# Per channel ENT table for high RR under Chebyshev
print('\n=== Per-channel ENT by band at RR_target=0.90, Chebyshev ===')
sub = df[(df['RR_target']==0.90) & (df['norm']=='chebyshev')]
pivot = sub.pivot(index='channel', columns='band', values='ENT')
print(pivot.to_string())
for ch, row in pivot.iterrows():
    vals = [row[b] for b in ['Delta','Theta','Alpha','Beta','Gamma']]
    rho,_ = spearmanr([2.25,6,10.5,21.5,37.5], vals)
    print(f'{ch}: rho={rho:.3f}')

print('\n=== Per-channel ENT by band at RR_target=0.90, Euclidean ===')
sub2 = df[(df['RR_target']==0.90) & (df['norm']=='euclidean')]
pivot2 = sub2.pivot(index='channel', columns='band', values='ENT')
print(pivot2.to_string())
for ch, row in pivot2.iterrows():
    vals = [row[b] for b in ['Delta','Theta','Alpha','Beta','Gamma']]
    rho,_ = spearmanr([2.25,6,10.5,21.5,37.5], vals)
    print(f'{ch}: rho={rho:.3f}')
