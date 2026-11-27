import json, numpy as np, pandas as pd
from scipy.stats import spearmanr

with open('world_c_results/replicate_emp250_fast_results.json') as f:
    data = json.load(f)

df = pd.DataFrame(data['results'])
band_freq = {'Delta': 2.25, 'Theta': 6.0, 'Alpha': 10.5, 'Beta': 21.5, 'Gamma': 37.5}
df['freq'] = df['band'].map(band_freq)

# Per channel Spearman rho(ENT, freq)
rhos = []
for (ch, norm, RR_t), sub in df.groupby(['channel', 'norm', 'RR_target']):
    sub = sub.sort_values('freq')
    rho, p = spearmanr(sub['freq'], sub['ENT'])
    rhos.append({'channel': ch, 'norm': norm, 'RR_target': RR_t, 'rho': rho, 'p': p})
rho_df = pd.DataFrame(rhos)

# Aggregate median rho across channels and fraction negative per (norm, RR_target)
summary = rho_df.groupby(['norm', 'RR_target']).agg(
    median_rho=('rho', 'median'),
    mean_rho=('rho', 'mean'),
    frac_negative=('rho', lambda s: np.mean(s < 0)),
    frac_significant=('p', lambda s: np.mean(s < 0.05)),
    rho_iqr=('rho', lambda s: np.percentile(s, 75) - np.percentile(s, 25)),
).reset_index()
print('\n=== Per (norm, RR_target) rho(ENT, freq) across channels ===')
print(summary.to_string(index=False))

# Also median ENT per band across channels
print('\n=== Median ENT by band, norm, RR_target ===')
med = df.groupby(['band', 'freq', 'norm', 'RR_target'])['ENT'].median().reset_index()
for norm in med['norm'].unique():
    print(f'\n--- {norm} ---')
    sub = med[med['norm']==norm].pivot(index='RR_target', columns='band', values='ENT')
    print(sub.to_string())

# Save summary JSON
summary.to_json('emp250_rho_summary.json', orient='records', indent=2)
rho_df.to_json('emp250_per_channel_rhos.json', orient='records', indent=2)
print('\nSaved emp250_rho_summary.json and emp250_per_channel_rhos.json')
