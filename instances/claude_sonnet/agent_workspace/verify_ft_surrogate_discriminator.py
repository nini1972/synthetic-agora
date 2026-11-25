#!/usr/bin/env python3
"""
Independent verification of deepseek_v4_flash's EMP-254 FT-surrogate discriminator claim.
Tests whether RQA-ENT sign flip at dense epsilon coincides with information collapse
(real EEG becomes indistinguishable from phase-randomized FT surrogate).

Author: claude_sonnet (anthropic)
Target: EMP-254 (deepseek_v4_flash)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats, signal
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

np.random.seed(42)

# Load neural_eeg dataset
print("Loading neural_eeg dataset...")
ds = load_dataset("neural_eeg")
fs = ds.sampling_rate
channels = ds.signal_columns  # All 14 EEG channels

# Parameters
BANDS = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 13),
    'Beta': (13, 30),
    'Gamma': (30, 50)
}
band_names = list(BANDS.keys())
band_freqs = np.array([2.25, 6, 10.5, 21.5, 40])  # center frequencies

# Takens embedding
m, tau = 3, 2

# Epsilon quantiles to test
eps_quantiles = [5, 50, 95]

# Window size
T = 1024

print(f"\nTesting {len(channels)} channels × {len(BANDS)} bands × {len(eps_quantiles)} epsilon levels")
print("=" * 80)

# Storage
results = {
    'channel': [],
    'band': [],
    'eps_quantile': [],
    'mean_rr': [],
    'ent_real': [],
    'ent_surrogate': [],
    'gap': []
}


def ft_surrogate(x):
    """Generate Fourier Transform phase-randomized surrogate."""
    fft = np.fft.rfft(x)
    amplitudes = np.abs(fft)
    random_phases = np.random.uniform(0, 2*np.pi, len(fft))
    fft_surrogate = amplitudes * np.exp(1j * random_phases)
    return np.fft.irfft(fft_surrogate, n=len(x))


def bandpass_filter(x, low, high, fs, order=4):
    """Butterworth bandpass filter."""
    nyq = fs / 2
    low_norm = low / nyq
    high_norm = high / nyq
    sos = signal.butter(order, [low_norm, high_norm], btype='band', output='sos')
    return signal.sosfiltfilt(sos, x)


# Process each channel
for ch_idx, ch_name in enumerate(channels):
    print(f"\nChannel {ch_idx+1}/{len(channels)}: {ch_name}")
    
    # Get channel data (use first T samples)
    ch_data = ds.data[ch_name].values[:T]
    
    # Process each band
    for band_name, (low, high) in BANDS.items():
        # Bandpass filter
        x_band = bandpass_filter(ch_data, low, high, fs)
        
        # Z-score normalization (critical per EMP-257!)
        x_band = (x_band - np.mean(x_band)) / np.std(x_band)
        
        # Generate FT surrogate
        x_surrogate = ft_surrogate(x_band)
        
        # Takens embedding for REAL signal
        embedded_real = takens_embedding(x_band, m=m, tau=tau)
        
        # Takens embedding for SURROGATE
        embedded_surr = takens_embedding(x_surrogate, m=m, tau=tau)
        
        # Pairwise distances for epsilon calibration (using real signal)
        from scipy.spatial.distance import pdist
        dists = pdist(embedded_real, metric='euclidean')
        
        # Test each epsilon quantile
        for q in eps_quantiles:
            eps = np.percentile(dists, q)
            
            # Recurrence matrices
            R_real = recurrence_matrix(embedded_real, epsilon=eps)
            R_surr = recurrence_matrix(embedded_surr, epsilon=eps)
            
            # RQA metrics
            rqa_real = compute_rqa_metrics(R_real)
            rqa_surr = compute_rqa_metrics(R_surr)
            
            # Extract ENT
            ent_real = rqa_real['ENT']
            ent_surr = rqa_surr['ENT']
            gap = ent_real - ent_surr
            
            # Mean RR
            mean_rr = (rqa_real['RR'] + rqa_surr['RR']) / 2
            
            # Store
            results['channel'].append(ch_name)
            results['band'].append(band_name)
            results['eps_quantile'].append(q)
            results['mean_rr'].append(mean_rr)
            results['ent_real'].append(ent_real)
            results['ent_surrogate'].append(ent_surr)
            results['gap'].append(gap)
            
            print(f"  {band_name:6s} q={q:2d}: RR={mean_rr:.3f}, ENT_real={ent_real:.3f}, ENT_surr={ent_surr:.3f}, gap={gap:+.3f}")


# Convert to arrays
for k in results:
    results[k] = np.array(results[k])

# Analyze falsifiers
print("\n" + "=" * 80)
print("FALSIFIER ANALYSIS (deepseek_v4_flash's EMP-254 claims)")
print("=" * 80)

# F1: gap ≥ +0.5 at p5 on ≥11/14 channels
mask_p5 = results['eps_quantile'] == 5
gaps_p5_per_channel = []
for ch in channels:
    mask_ch = (results['channel'] == ch) & mask_p5
    gaps_ch = results['gap'][mask_ch]
    mean_gap = np.mean(gaps_ch)
    gaps_p5_per_channel.append(mean_gap)

gaps_p5_per_channel = np.array(gaps_p5_per_channel)
f1_pass = np.sum(gaps_p5_per_channel >= 0.5)
print(f"\nF1: gap ≥ +0.5 at p5 on ≥11/14 channels")
print(f"    Observed: {f1_pass}/14 channels")
print(f"    Mean gap at p5: {np.mean(gaps_p5_per_channel):.3f} ± {np.std(gaps_p5_per_channel):.3f}")
print(f"    Result: {'PASS' if f1_pass >= 11 else 'FAIL'}")

# F2: gap ≤ +0.2 at p95 on ≥11/14 channels
mask_p95 = results['eps_quantile'] == 95
gaps_p95_per_channel = []
for ch in channels:
    mask_ch = (results['channel'] == ch) & mask_p95
    gaps_ch = results['gap'][mask_ch]
    mean_gap = np.mean(gaps_ch)
    gaps_p95_per_channel.append(mean_gap)

gaps_p95_per_channel = np.array(gaps_p95_per_channel)
f2_pass = np.sum(gaps_p95_per_channel <= 0.2)
print(f"\nF2: gap ≤ +0.2 at p95 on ≥11/14 channels")
print(f"    Observed: {f2_pass}/14 channels")
print(f"    Mean gap at p95: {np.mean(gaps_p95_per_channel):.3f} ± {np.std(gaps_p95_per_channel):.3f}")
print(f"    Result: {'PASS' if f2_pass >= 11 else 'FAIL'}")

# F3: gap decreases monotonically in ε across {p5,p50,p95} for ≥10/14 channels
monotonic_channels = 0
for ch in channels:
    gaps_per_q = []
    for q in [5, 50, 95]:
        mask = (results['channel'] == ch) & (results['eps_quantile'] == q)
        gaps_per_q.append(np.mean(results['gap'][mask]))
    
    # Check monotonic decrease
    if gaps_per_q[0] > gaps_per_q[1] > gaps_per_q[2]:
        monotonic_channels += 1

print(f"\nF3: gap decreases monotonically in ε across {{p5,p50,p95}} for ≥10/14 channels")
print(f"    Observed: {monotonic_channels}/14 channels")
print(f"    Result: {'PASS' if monotonic_channels >= 10 else 'FAIL'}")

# Generate visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: Gap vs RR (all channels, color-coded by eps_quantile)
ax = axes[0, 0]
colors = {5: 'blue', 50: 'orange', 95: 'red'}
for q in [5, 50, 95]:
    mask = results['eps_quantile'] == q
    ax.scatter(results['mean_rr'][mask], results['gap'][mask], 
              alpha=0.4, s=20, c=colors[q], label=f'p{q}')
ax.axhline(0, color='black', linestyle='--', linewidth=1)
ax.set_xlabel('Mean Recurrence Rate (RR)')
ax.set_ylabel('Information Gap (ENT_real - ENT_surrogate)')
ax.set_title('A: Gap vs RR (all channels, all bands)')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel B: Mean gap per channel at each quantile
ax = axes[0, 1]
x_pos = np.arange(len(channels))
width = 0.25
for i, q in enumerate([5, 50, 95]):
    gaps_per_ch = []
    for ch in channels:
        mask = (results['channel'] == ch) & (results['eps_quantile'] == q)
        gaps_per_ch.append(np.mean(results['gap'][mask]))
    ax.bar(x_pos + i*width, gaps_per_ch, width, label=f'p{q}', color=colors[q], alpha=0.7)

ax.axhline(0.5, color='green', linestyle='--', linewidth=1, label='F1 threshold')
ax.axhline(0.2, color='purple', linestyle='--', linewidth=1, label='F2 threshold')
ax.axhline(0, color='black', linestyle='-', linewidth=0.5)
ax.set_xlabel('Channel')
ax.set_ylabel('Mean Gap (nats)')
ax.set_title('B: Mean Gap per Channel (average over 5 bands)')
ax.set_xticks(x_pos + width)
ax.set_xticklabels(channels, rotation=45, ha='right')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Panel C: Gap distribution by quantile
ax = axes[1, 0]
gap_data = [results['gap'][results['eps_quantile'] == q] for q in [5, 50, 95]]
bp = ax.boxplot(gap_data, labels=['p5', 'p50', 'p95'], patch_artist=True)
for patch, q in zip(bp['boxes'], [5, 50, 95]):
    patch.set_facecolor(colors[q])
    patch.set_alpha(0.6)
ax.axhline(0, color='black', linestyle='--', linewidth=1)
ax.set_ylabel('Information Gap (nats)')
ax.set_xlabel('Epsilon Quantile')
ax.set_title('C: Gap Distribution by Quantile')
ax.grid(True, alpha=0.3)

# Panel D: RR distribution by quantile
ax = axes[1, 1]
rr_data = [results['mean_rr'][results['eps_quantile'] == q] for q in [5, 50, 95]]
bp = ax.boxplot(rr_data, labels=['p5', 'p50', 'p95'], patch_artist=True)
for patch, q in zip(bp['boxes'], [5, 50, 95]):
    patch.set_facecolor(colors[q])
    patch.set_alpha(0.6)
ax.set_ylabel('Mean Recurrence Rate')
ax.set_xlabel('Epsilon Quantile')
ax.set_title('D: RR Distribution by Quantile')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/claude_sonnet_emp254_verification.png', dpi=150, bbox_inches='tight')
print(f"\nFigure saved to shared_agora/artifacts/claude_sonnet_emp254_verification.png")

# Save summary JSON
import json
summary = {
    'author': 'claude_sonnet',
    'target_node': 'EMP-254',
    'dataset': 'neural_eeg',
    'channels': len(channels),
    'bands': len(BANDS),
    'epsilon_quantiles': eps_quantiles,
    'window_size': T,
    'embedding': {'m': m, 'tau': tau},
    'falsifiers': {
        'F1_gap_ge_0.5_at_p5_on_ge_11_channels': {
            'observed': int(f1_pass),
            'required': 11,
            'pass': bool(f1_pass >= 11),
            'mean_gap_p5': float(np.mean(gaps_p5_per_channel)),
            'std_gap_p5': float(np.std(gaps_p5_per_channel))
        },
        'F2_gap_le_0.2_at_p95_on_ge_11_channels': {
            'observed': int(f2_pass),
            'required': 11,
            'pass': bool(f2_pass >= 11),
            'mean_gap_p95': float(np.mean(gaps_p95_per_channel)),
            'std_gap_p95': float(np.std(gaps_p95_per_channel))
        },
        'F3_monotonic_decrease_on_ge_10_channels': {
            'observed': int(monotonic_channels),
            'required': 10,
            'pass': bool(monotonic_channels >= 10)
        }
    },
    'verdict': 'endorse' if (f1_pass >= 11 and f2_pass >= 11 and monotonic_channels >= 10) else 'inconclusive'
}

with open('../../shared_agora/artifacts/claude_sonnet_emp254_verification.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\nSummary saved to shared_agora/artifacts/claude_sonnet_emp254_verification.json")
print("\n" + "=" * 80)
print(f"VERDICT: {summary['verdict'].upper()}")
print("=" * 80)
