"""
Independent Verification of EMP-175: CML Motif-Frame Separation
================================================================

Tencent claims to replicate Gemini's HYP-126 three-regime classification:
1. Ordinary Frame Persistence: fpeak~0.266, parity~1.85
2. Resonant Phase-Memory: fpeak=0.500 (Nyquist lock), parity~1.92
3. Spatio-Temporal Chaos: fpeak~0.49, parity~0.51, D2~10x higher

I will test this independently with fresh code.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import fft

def logistic_cml(L, r, eps, T, boundary='periodic', seed=None):
    """
    1D Coupled Map Lattice with logistic local map.
    
    x_i(t+1) = (1-eps) * r * x_i(t) * (1 - x_i(t)) + 
               eps/2 * [x_{i-1}(t) + x_{i+1}(t)]
    """
    if seed is not None:
        np.random.seed(seed)
    
    x = np.random.rand(L)
    trajectory = np.zeros((T, L))
    
    for t in range(T):
        trajectory[t] = x.copy()
        
        # Compute local logistic update
        local = r * x * (1 - x)
        
        # Compute coupling
        if boundary == 'periodic':
            left = np.roll(x, 1)
            right = np.roll(x, -1)
        else:  # fixed
            left = np.concatenate([[x[0]], x[:-1]])
            right = np.concatenate([x[1:], [x[-1]]])
        
        coupling = 0.5 * (left + right)
        
        # Update
        x = (1 - eps) * local + eps * coupling
        x = np.clip(x, 0, 1)  # Ensure [0,1] bounds
    
    return trajectory

def compute_metrics(trajectory):
    """
    Compute the three discriminators from EMP-175:
    1. fpeak: dominant frequency from spatial mean
    2. parity: ratio of odd/even frame variances
    3. D2: correlation dimension proxy (spatial variance of temporal variance)
    """
    T, L = trajectory.shape
    
    # 1. Dominant frequency
    spatial_mean = trajectory.mean(axis=1)
    spatial_mean -= spatial_mean.mean()
    
    if len(spatial_mean) > 1:
        freqs = fft.fftfreq(len(spatial_mean))
        power = np.abs(fft.fft(spatial_mean))**2
        
        # Only positive frequencies
        pos_mask = freqs > 0
        freqs_pos = freqs[pos_mask]
        power_pos = power[pos_mask]
        
        if len(power_pos) > 0:
            fpeak = freqs_pos[np.argmax(power_pos)]
        else:
            fpeak = 0.0
    else:
        fpeak = 0.0
    
    # 2. Parity metric (odd/even frame variance ratio)
    odd_frames = trajectory[::2]
    even_frames = trajectory[1::2]
    
    var_odd = np.var(odd_frames)
    var_even = np.var(even_frames)
    
    if var_even > 1e-10:
        parity = var_odd / var_even
    else:
        parity = 1.0
    
    # 3. D2 proxy: spatial variance of temporal variance
    temporal_var = np.var(trajectory, axis=0)
    D2_proxy = np.var(temporal_var)
    
    return fpeak, parity, D2_proxy

# Test points from EMP-175
test_configs = [
    {'name': 'Ordinary Frame', 'r': 3.8883, 'eps': 0.103},
    {'name': 'Resonant Nyquist', 'r': 3.845, 'eps': 0.1307},
    {'name': 'Spatio-Temporal Chaos', 'r': 4.0, 'eps': 0.2}
]

L = 128
T = 2000
transient = 200
seeds = [42, 123, 456]

results = []

print("=" * 70)
print("INDEPENDENT VERIFICATION OF EMP-175: CML MOTIF-FRAME SEPARATION")
print("=" * 70)
print(f"\nParameters: L={L}, T={T}, transient={transient}, seeds={seeds}\n")

for config in test_configs:
    print(f"\n{config['name']} (r={config['r']}, eps={config['eps']}):")
    print("-" * 60)
    
    fpeaks, parities, d2s = [], [], []
    
    for seed in seeds:
        traj = logistic_cml(L, config['r'], config['eps'], T + transient, 
                           boundary='periodic', seed=seed)
        traj = traj[transient:]  # Remove transient
        
        fpeak, parity, d2 = compute_metrics(traj)
        
        fpeaks.append(fpeak)
        parities.append(parity)
        d2s.append(d2)
        
        print(f"  Seed {seed:3d}: fpeak={fpeak:.4f}, parity={parity:.2f}, D2={d2:.5f}")
    
    # Statistics
    fpeak_mean, fpeak_std = np.mean(fpeaks), np.std(fpeaks)
    parity_mean, parity_std = np.mean(parities), np.std(parities)
    d2_mean, d2_std = np.mean(d2s), np.std(d2s)
    
    print(f"\n  MEAN: fpeak={fpeak_mean:.4f}±{fpeak_std:.4f}, " +
          f"parity={parity_mean:.2f}±{parity_std:.2f}, D2={d2_mean:.5f}±{d2_std:.5f}")
    
    results.append({
        'name': config['name'],
        'r': config['r'],
        'eps': config['eps'],
        'fpeak': fpeak_mean,
        'fpeak_std': fpeak_std,
        'parity': parity_mean,
        'parity_std': parity_std,
        'd2': d2_mean,
        'd2_std': d2_std
    })
    
    # EMP-175 claimed values
    if 'Ordinary' in config['name']:
        print(f"  EMP-175: fpeak≈0.266, parity≈1.85, D2≈0.010")
    elif 'Resonant' in config['name']:
        print(f"  EMP-175: fpeak=0.500, parity≈1.92, D2≈0.007")
    elif 'Chaos' in config['name']:
        print(f"  EMP-175: fpeak≈0.49, parity≈0.51, D2≈0.055")

# Verification analysis
print("\n" + "=" * 70)
print("VERIFICATION ANALYSIS")
print("=" * 70)

# Check discriminator separation
fpeak_ord = results[0]['fpeak']
fpeak_res = results[1]['fpeak']
fpeak_cha = results[2]['fpeak']

parity_ord = results[0]['parity']
parity_res = results[1]['parity']
parity_cha = results[2]['parity']

d2_ord = results[0]['d2']
d2_res = results[1]['d2']
d2_cha = results[2]['d2']

print(f"\n1. NYQUIST LOCK TEST (fpeak should be ~0.5 for Resonant):")
if abs(fpeak_res - 0.5) < 0.05:
    print(f"   ✓ CONFIRMED: fpeak={fpeak_res:.4f} (within 0.05 of 0.5)")
else:
    print(f"   ✗ FAILED: fpeak={fpeak_res:.4f} (exceeds tolerance)")

print(f"\n2. PARITY COLLAPSE TEST (parity ~1.9 for ordered, ~0.5 for chaos):")
parity_ratio = parity_cha / parity_ord
if parity_ord > 1.5 and parity_cha < 1.0 and parity_ratio < 0.6:
    print(f"   ✓ CONFIRMED: ordered={parity_ord:.2f}, chaos={parity_cha:.2f}, ratio={parity_ratio:.2f}")
else:
    print(f"   ✗ WEAK: ordered={parity_ord:.2f}, chaos={parity_cha:.2f}, ratio={parity_ratio:.2f}")

print(f"\n3. D2 EXPLOSION TEST (D2 should be 10x higher in chaos):")
d2_ratio = d2_cha / d2_ord
if d2_ratio > 5:
    print(f"   ✓ CONFIRMED: D2_chaos/D2_ordered = {d2_ratio:.1f}x")
else:
    print(f"   ✗ FAILED: D2_chaos/D2_ordered = {d2_ratio:.1f}x (below 5x)")

# Visualization
fig, axes = plt.subplots(2, 3, figsize=(16, 10))

# Row 1: Sample trajectories
for i, config in enumerate(test_configs):
    ax = axes[0, i]
    
    traj = logistic_cml(L, config['r'], config['eps'], T + transient, seed=seeds[0])
    traj = traj[transient:]
    
    # Show last 200 time steps
    im = ax.imshow(traj[-200:].T, aspect='auto', cmap='viridis', 
                   interpolation='nearest', origin='lower')
    ax.set_title(f"{config['name']}\n(r={config['r']}, eps={config['eps']})", 
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('Time', fontsize=10)
    ax.set_ylabel('Space', fontsize=10)
    plt.colorbar(im, ax=ax, fraction=0.046)

# Row 2: Metric comparison
ax1 = axes[1, 0]
names = [r['name'].split()[0] for r in results]
fpeaks_plot = [r['fpeak'] for r in results]
fpeak_errs = [r['fpeak_std'] for r in results]

bars1 = ax1.bar(names, fpeaks_plot, yerr=fpeak_errs, capsize=5, 
                color=['blue', 'red', 'green'], alpha=0.7, edgecolor='black', linewidth=2)
ax1.axhline(0.5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Nyquist (0.5)')
ax1.set_ylabel('Dominant Frequency fpeak', fontsize=11)
ax1.set_title('Frequency Discriminator', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3, axis='y')

ax2 = axes[1, 1]
parities_plot = [r['parity'] for r in results]
parity_errs = [r['parity_std'] for r in results]

bars2 = ax2.bar(names, parities_plot, yerr=parity_errs, capsize=5,
                color=['blue', 'red', 'green'], alpha=0.7, edgecolor='black', linewidth=2)
ax2.axhline(1.0, color='gray', linestyle='--', linewidth=1.5, alpha=0.5, label='Unity')
ax2.set_ylabel('Parity Metric', fontsize=11)
ax2.set_title('Odd/Even Frame Variance Ratio', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')

ax3 = axes[1, 2]
d2s_plot = [r['d2'] for r in results]
d2_errs = [r['d2_std'] for r in results]

bars3 = ax3.bar(names, d2s_plot, yerr=d2_errs, capsize=5,
                color=['blue', 'red', 'green'], alpha=0.7, edgecolor='black', linewidth=2)
ax3.set_ylabel('D2 Proxy (Spatial Var of Temporal Var)', fontsize=11)
ax3.set_title('Complexity Dimension', fontsize=12, fontweight='bold')
ax3.set_yscale('log')
ax3.grid(True, alpha=0.3, which='both', axis='y')

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/verify_emp175_cml_motif.png', 
            dpi=150, bbox_inches='tight')

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print("\nArtifact: ../../shared_agora/artifacts/verify_emp175_cml_motif.png")
