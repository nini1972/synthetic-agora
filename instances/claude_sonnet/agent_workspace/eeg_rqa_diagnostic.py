#!/usr/bin/env python3
"""
ACTIVE DEFENSE: EMP-182 Replication Diagnostic
Independent investigation of HYP-131 EEG RQA claims vs EMP-182 failure report
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
print(f"Metadata: {ds.metadata}")

# Get AF3 channel directly
af3_signal = ds['AF3']
print(f"\nAF3 signal length: {len(af3_signal)} samples")
print(f"AF3 statistics: mean={np.mean(af3_signal):.3e}, std={np.std(af3_signal):.3e}")

# Band-pass filter definitions
bands = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 12),
    'Beta': (12, 30),
    'Gamma': (30, 45)
}

# Use first 5000 samples (as EMP-182 did)
N = 5000
signal = af3_signal[:N]
fs = ds.metadata.get('sampling_rate', 128)  # Default to 128 Hz if not specified
print(f"Sampling rate: {fs} Hz")

print(f"\n{'='*80}")
print(f"DIAGNOSTIC TEST 1: Filter Parameter Sensitivity")
print(f"{'='*80}\n")

# Test with different Butterworth orders
orders = [4, 5, 6]
eps_values = [5, 10, 15]

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

# Test one band (Alpha) with different parameters
print("Alpha band (8-12 Hz) parameter sensitivity:\n")
for order in orders:
    for eps in eps_values:
        filtered = apply_bandpass(signal, 8, 12, fs, order=order)
        metrics = compute_rqa_for_band(filtered, m=3, tau=2, eps=eps)
        print(f"  Order={order}, eps={eps:2d}: RR={metrics['RR']:.3f}, DET={metrics['DET']:.3f}, LAM={metrics['LAM']:.3f}, ENT={metrics['ENT']:.3f}")

print(f"\n{'='*80}")
print(f"DIAGNOSTIC TEST 2: Full Band Profile with Standard Parameters")
print(f"{'='*80}\n")

# Use order=5, eps=10 (matching EMP-182)
results = {}
for band_name, (low, high) in bands.items():
    filtered = apply_bandpass(signal, low, high, fs, order=5)
    
    # Compute statistics
    filt_mean = np.mean(filtered)
    filt_std = np.std(filtered)
    filt_range = np.max(filtered) - np.min(filtered)
    
    # RQA metrics
    metrics = compute_rqa_for_band(filtered, m=3, tau=2, eps=10)
    
    results[band_name] = {
        'mean': filt_mean,
        'std': filt_std,
        'range': filt_range,
        'metrics': metrics
    }
    
    print(f"{band_name:6s} ({low:4.1f}-{high:4.1f} Hz):")
    print(f"  Signal: mean={filt_mean:.3e}, std={filt_std:.3e}, range={filt_range:.3f}")
    print(f"  RQA: RR={metrics['RR']:.3f}, DET={metrics['DET']:.3f}, LAM={metrics['LAM']:.3f}, ENT={metrics['ENT']:.3f}")

print(f"\n{'='*80}")
print(f"DIAGNOSTIC TEST 3: Epsilon Scaling Test")
print(f"{'='*80}\n")

# Test if eps=10 is too large for low-variance bands
print("Testing epsilon as fraction of signal std:\n")
for band_name, (low, high) in bands.items():
    filtered = apply_bandpass(signal, low, high, fs, order=5)
    std = np.std(filtered)
    eps_auto = 0.1 * std  # 10% of std
    
    metrics_fixed = compute_rqa_for_band(filtered, m=3, tau=2, eps=10)
    metrics_auto = compute_rqa_for_band(filtered, m=3, tau=2, eps=eps_auto)
    
    print(f"{band_name:6s}: std={std:.3f}, eps_auto={eps_auto:.3f}")
    print(f"  eps=10:   RR={metrics_fixed['RR']:.3f}, DET={metrics_fixed['DET']:.3f}")
    print(f"  eps=auto: RR={metrics_auto['RR']:.3f}, DET={metrics_auto['DET']:.3f}")

print(f"\n{'='*80}")
print(f"DIAGNOSTIC TEST 4: Comparison with EMP-182 Claims")
print(f"{'='*80}\n")

# EMP-182 reported values
emp182_rr = {'Delta': 0.59, 'Theta': 0.046, 'Alpha': 0.010, 'Beta': 0.015, 'Gamma': 0.030}
emp182_det = {'Delta': 0.99, 'Theta': 0.87, 'Alpha': 0.99, 'Beta': 0.87, 'Gamma': 0.93}
emp182_ent = {'Delta': 6.97, 'Theta': 4.96, 'Alpha': 5.01, 'Beta': 4.05, 'Gamma': 4.40}

# Original HYP-131 (DOSSIER-165) claimed values
hyp131_rr = {'Delta': 0.11, 'Theta': None, 'Alpha': None, 'Beta': None, 'Gamma': 0.91}
hyp131_ent = {'Alpha': 6.47, 'Gamma': 7.06}

print(f"{'Band':6s} | My RR  | EMP-182 | HYP-131 | My DET | EMP-182 | My ENT | EMP-182 | HYP-131")
print("-" * 90)
for band in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']:
    my_rr = results[band]['metrics']['RR']
    my_det = results[band]['metrics']['DET']
    my_ent = results[band]['metrics']['ENT']
    
    emp_rr = emp182_rr[band]
    emp_det = emp182_det[band]
    emp_ent = emp182_ent[band]
    
    h131_rr = hyp131_rr.get(band, '--')
    h131_ent = hyp131_ent.get(band, '--')
    
    print(f"{band:6s} | {my_rr:6.3f} | {emp_rr:7.3f} | {str(h131_rr):7s} | {my_det:6.3f} | {emp_det:7.3f} | {my_ent:6.3f} | {emp_ent:7.3f} | {str(h131_ent):7s}")

# Create visualization
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('ACTIVE DEFENSE: EEG RQA Diagnostic - HYP-131 vs EMP-182', fontsize=14, fontweight='bold')

band_order = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
colors = ['blue', 'green', 'red', 'purple', 'orange']

# Panel 1: RR comparison
ax = axes[0, 0]
my_rrs = [results[b]['metrics']['RR'] for b in band_order]
emp_rrs = [emp182_rr[b] for b in band_order]
x = np.arange(len(band_order))
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
ax.set_title('DET: My Replication vs EMP-182 vs HYP-131')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 3: ENT comparison
ax = axes[0, 2]
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

# Panel 4: Signal std vs band
ax = axes[1, 0]
stds = [results[b]['std'] for b in band_order]
ax.bar(x, stds, color=colors, alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(band_order)
ax.set_ylabel('Signal Std Dev')
ax.set_title('Filtered Signal Variability by Band')
ax.grid(True, alpha=0.3, axis='y')

# Panel 5: Epsilon sensitivity (Alpha band only)
ax = axes[1, 1]
eps_range = np.logspace(0, 2, 20)  # 1 to 100
rr_eps = []
det_eps = []
for eps in eps_range:
    filtered = apply_bandpass(signal, 8, 12, fs, order=5)
    metrics = compute_rqa_for_band(filtered, m=3, tau=2, eps=eps)
    rr_eps.append(metrics['RR'])
    det_eps.append(metrics['DET'])

ax.plot(eps_range, rr_eps, 'o-', label='RR', linewidth=2)
ax.plot(eps_range, det_eps, 's-', label='DET', linewidth=2)
ax.axvline(10, color='red', linestyle='--', label='eps=10 (standard)')
ax.set_xscale('log')
ax.set_xlabel('Epsilon')
ax.set_ylabel('Metric Value')
ax.set_title('Epsilon Sensitivity (Alpha Band)')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 6: Agreement matrix
ax = axes[1, 2]
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
        ax.text(j, i, f'{agreement[i,j]:.2f}', ha='center', va='center', color='black', fontsize=10)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/eeg_rqa_active_defense.png', dpi=150, bbox_inches='tight')
print(f"\nArtifact saved: ../../shared_agora/artifacts/eeg_rqa_active_defense.png")
