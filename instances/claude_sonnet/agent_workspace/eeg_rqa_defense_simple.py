#!/usr/bin/env python3
"""
ACTIVE DEFENSE: EMP-182 Replication Diagnostic (Simplified)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
import sys

sys.path.insert(0, '/app/colony_lib')
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

# Load EEG dataset
ds = load_dataset('neural_eeg')
print(f"Dataset shape: {ds['data'].shape}")
print(f"Available columns: {ds.columns}")

# Get AF3 channel
af3_signal = ds['AF3']
print(f"AF3 signal length: {len(af3_signal)} samples")

# Band-pass filter definitions
bands = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 12),
    'Beta': (12, 30),
    'Gamma': (30, 45)
}

# Use first 5000 samples
N = 5000
signal = af3_signal[:N]
fs = 128  # Standard EEG sampling rate

def apply_bandpass(signal, lowcut, highcut, fs, order=5):
    """Apply Butterworth bandpass filter"""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, signal)

def compute_rqa_for_band(signal, m=3, tau=2, eps=10):
    """Compute RQA metrics for a signal"""
    embedded = takens_embedding(signal, m=m, tau=tau)
    R = recurrence_matrix(embedded, epsilon=eps)
    metrics = compute_rqa_metrics(R)
    return metrics

print(f"\n{'='*80}")
print(f"FULL BAND PROFILE (order=5, eps=10, matching EMP-182)")
print(f"{'='*80}\n")

results = {}
for band_name, (low, high) in bands.items():
    print(f"Processing {band_name}...")
    filtered = apply_bandpass(signal, low, high, fs, order=5)
    
    # Compute statistics
    filt_std = np.std(filtered)
    
    # RQA metrics
    metrics = compute_rqa_for_band(filtered, m=3, tau=2, eps=10)
    
    results[band_name] = {
        'std': filt_std,
        'metrics': metrics
    }
    
    print(f"  RQA: RR={metrics['RR']:.3f}, DET={metrics['DET']:.3f}, LAM={metrics['LAM']:.3f}, ENT={metrics['ENT']:.3f}")

# EMP-182 reported values
emp182_rr = {'Delta': 0.59, 'Theta': 0.046, 'Alpha': 0.010, 'Beta': 0.015, 'Gamma': 0.030}
emp182_det = {'Delta': 0.99, 'Theta': 0.87, 'Alpha': 0.99, 'Beta': 0.87, 'Gamma': 0.93}
emp182_ent = {'Delta': 6.97, 'Theta': 4.96, 'Alpha': 5.01, 'Beta': 4.05, 'Gamma': 4.40}

print(f"\n{'='*80}")
print(f"COMPARISON TABLE")
print(f"{'='*80}\n")

print(f"{'Band':6s} | My RR  | EMP-182 | My DET | EMP-182 | My ENT | EMP-182")
print("-" * 70)
for band in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']:
    my_rr = results[band]['metrics']['RR']
    my_det = results[band]['metrics']['DET']
    my_ent = results[band]['metrics']['ENT']
    
    emp_rr = emp182_rr[band]
    emp_det = emp182_det[band]
    emp_ent = emp182_ent[band]
    
    print(f"{band:6s} | {my_rr:6.3f} | {emp_rr:7.3f} | {my_det:6.3f} | {emp_det:7.3f} | {my_ent:6.3f} | {emp_ent:7.3f}")

# Calculate agreement
print(f"\nAGREEMENT ANALYSIS:")
for metric_name in ['RR', 'DET', 'ENT']:
    emp_dict = emp182_rr if metric_name == 'RR' else (emp182_det if metric_name == 'DET' else emp182_ent)
    my_vals = [results[b]['metrics'][metric_name] for b in bands.keys()]
    emp_vals = [emp_dict[b] for b in bands.keys()]
    
    corr = np.corrcoef(my_vals, emp_vals)[0, 1]
    mae = np.mean([abs(m - e) for m, e in zip(my_vals, emp_vals)])
    
    print(f"  {metric_name}: correlation={corr:.3f}, MAE={mae:.3f}")

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('ACTIVE DEFENSE: My Replication vs EMP-182', fontsize=14, fontweight='bold')

band_order = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
x = np.arange(len(band_order))

# Panel 1: RR comparison
ax = axes[0, 0]
my_rrs = [results[b]['metrics']['RR'] for b in band_order]
emp_rrs = [emp182_rr[b] for b in band_order]
ax.plot(x, my_rrs, 'o-', label='My replication', linewidth=2, markersize=8)
ax.plot(x, emp_rrs, 's--', label='EMP-182', linewidth=2, markersize=8)
ax.set_xticks(x)
ax.set_xticklabels(band_order)
ax.set_ylabel('Recurrence Rate')
ax.set_title('RR: My Replication vs EMP-182')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 2: DET comparison
ax = axes[0, 1]
my_dets = [results[b]['metrics']['DET'] for b in band_order]
emp_dets = [emp182_det[b] for b in band_order]
ax.plot(x, my_dets, 'o-', label='My replication', linewidth=2, markersize=8)
ax.plot(x, emp_dets, 's--', label='EMP-182', linewidth=2, markersize=8)
ax.axhline(0.93, color='gray', linestyle=':', label='HYP-131 claimed >0.93')
ax.set_xticks(x)
ax.set_xticklabels(band_order)
ax.set_ylabel('Determinism')
ax.set_title('DET: My Replication vs EMP-182')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 3: ENT comparison
ax = axes[1, 0]
my_ents = [results[b]['metrics']['ENT'] for b in band_order]
emp_ents = [emp182_ent[b] for b in band_order]
ax.plot(x, my_ents, 'o-', label='My replication', linewidth=2, markersize=8)
ax.plot(x, emp_ents, 's--', label='EMP-182', linewidth=2, markersize=8)
ax.scatter([2, 4], [6.47, 7.06], s=200, marker='*', color='red', label='HYP-131 claimed', zorder=5)
ax.set_xticks(x)
ax.set_xticklabels(band_order)
ax.set_ylabel('Shannon Entropy')
ax.set_title('ENT: My Replication vs EMP-182 vs HYP-131')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 4: Agreement matrix
ax = axes[1, 1]
metrics_names = ['RR', 'DET', 'ENT']
agreement = np.zeros((len(band_order), len(metrics_names)))
for i, band in enumerate(band_order):
    my_vals = [results[band]['metrics'][m] for m in metrics_names]
    emp_vals = [emp182_rr[band], emp182_det[band], emp182_ent[band]]
    agreement[i, :] = [1 - abs(m - e) / (abs(m) + abs(e) + 1e-6) for m, e in zip(my_vals, emp_vals)]

im = ax.imshow(agreement, cmap='RdYlGn', vmin=0, vmax=1)
ax.set_xticks(range(len(metrics_names)))
ax.set_yticks(range(len(band_order)))
ax.set_xticklabels(metrics_names)
ax.set_yticklabels(band_order)
ax.set_title('Agreement: My Replication vs EMP-182')
plt.colorbar(im, ax=ax, label='Agreement (1=perfect)')

for i in range(len(band_order)):
    for j in range(len(metrics_names)):
        ax.text(j, i, f'{agreement[i,j]:.2f}', ha='center', va='center', color='black', fontsize=9)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/eeg_rqa_active_defense.png', dpi=150, bbox_inches='tight')
print(f"\nArtifact saved: ../../shared_agora/artifacts/eeg_rqa_active_defense.png")
