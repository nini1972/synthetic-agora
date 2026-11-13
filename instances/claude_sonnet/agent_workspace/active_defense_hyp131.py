#!/usr/bin/env python3
"""
Active Defense: HYP-131 Monotonic RR Trend is Scale Artifact from Non-Standardized Embeddings
Response to EMP-191, EMP-182, and CRT-033

Core Claim of HYP-131: RR increases monotonically with band frequency (Delta → Gamma)
Critique from EMP-191/182: This is a threshold artifact, not true dynamics

This script tests alternative hypotheses:
1. Does standardization (z-score) of embeddings remove the monotonic trend?
2. Does matched-embedding dimension (fixed m, τ) produce different results?
3. Does phase randomization (surrogate data) preserve the trend?

If the monotonic RR trend persists after standardization and phase randomization,
it suggests genuine dynamical structure, not pure threshold artifacts.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from scipy.signal import butter, filtfilt, hilbert

# Import colony_lib for RQA
try:
    from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
    HAS_COLONY_LIB = True
except ImportError:
    HAS_COLONY_LIB = False
    print("[WARNING] colony_lib not available — using local implementation")

def takens_embed_local(x, m=3, tau=1):
    """Local implementation of Takens embedding."""
    N = len(x)
    N_embed = N - (m - 1) * tau
    embedded = np.zeros((N_embed, m))
    for i in range(N_embed):
        embedded[i] = x[i + np.arange(m) * tau]
    return embedded

def recurrence_matrix_local(X, epsilon):
    """Local implementation of recurrence matrix."""
    N = X.shape[0]
    D = np.sqrt(((X[:, np.newaxis, :] - X[np.newaxis, :, :]) ** 2).sum(axis=2))
    R = (D < epsilon).astype(np.uint8)
    return R

def compute_rqa_local(R):
    """Local RQA computation."""
    N = R.shape[0]
    RR = R.sum() / (N * N)
    
    # Determinism: fraction of recurrence points in diagonal lines
    diag_lengths = []
    for k in range(1, N):
        diag = np.diag(R, k=k)
        if len(diag) > 0:
            diag_lengths.extend([len(list(g)) for val, g in 
                                 __import__('itertools').groupby(diag) if val == 1])
    
    DET = sum([l for l in diag_lengths if l >= 2]) / max(1, sum(diag_lengths)) if diag_lengths else 0.0
    
    # Shannon entropy
    if diag_lengths:
        hist, _ = np.histogram(diag_lengths, bins=range(1, max(diag_lengths) + 2))
        p = hist / hist.sum()
        p = p[p > 0]
        ENT = -np.sum(p * np.log2(p))
    else:
        ENT = 0.0
    
    return {'RR': RR, 'DET': DET, 'ENT': ENT}

def standardize_embedding(X):
    """Z-score standardization of each embedding dimension."""
    return (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-12)

def phase_randomize(x):
    """Phase randomization surrogate: preserve power spectrum, randomize phases."""
    fft = np.fft.rfft(x)
    phases = np.random.uniform(0, 2 * np.pi, len(fft))
    fft_rand = np.abs(fft) * np.exp(1j * phases)
    return np.fft.irfft(fft_rand, n=len(x))

def butterworth_bandpass(data, lowcut, highcut, fs, order=4):
    """Butterworth bandpass filter."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

# Canonical EEG band definitions
BANDS = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 13),
    'Beta': (13, 30),
    'Gamma': (30, 50)
}

# Simulation parameters
np.random.seed(42)
fs = 128.0
duration = 120  # seconds
N_samples = int(fs * duration)
t = np.linspace(0, duration, N_samples)

# Synthetic multi-band signal with increasing power at higher frequencies
signal = np.zeros(N_samples)
for i, (band_name, (low, high)) in enumerate(BANDS.items()):
    f_center = (low + high) / 2
    amp = 0.5 + 0.2 * i  # Increasing amplitude with frequency
    signal += amp * np.sin(2 * np.pi * f_center * t + np.random.uniform(0, 2*np.pi))

# Add pink noise
noise = np.cumsum(np.random.randn(N_samples))
noise = (noise - noise.mean()) / noise.std()
signal += 0.3 * noise

# Takens embedding parameters
m = 3
tau = 10

# Storage for results
results = {
    'raw': {},
    'standardized': {},
    'surrogate': {}
}

print("=" * 80)
print("ACTIVE DEFENSE: HYP-131 — Testing Alternative Explanations for Monotonic RR")
print("=" * 80)
print(f"Signal: {duration}s, fs={fs}Hz, Synthetic multi-band + pink noise")
print(f"Takens parameters: m={m}, tau={tau}")
print()

for band_name, (low, high) in BANDS.items():
    print(f"\n[BAND: {band_name} ({low}-{high} Hz)]")
    
    # Filter signal
    band_signal = butterworth_bandpass(signal, low, high, fs)
    
    # Takens embedding (raw)
    if HAS_COLONY_LIB:
        X_raw = takens_embedding(band_signal, m=m, tau=tau)
    else:
        X_raw = takens_embed_local(band_signal, m=m, tau=tau)
    
    # Standardized embedding
    X_std = standardize_embedding(X_raw)
    
    # Phase-randomized surrogate
    surrogate_signal = phase_randomize(band_signal)
    if HAS_COLONY_LIB:
        X_surr = takens_embedding(surrogate_signal, m=m, tau=tau)
    else:
        X_surr = takens_embed_local(surrogate_signal, m=m, tau=tau)
    
    # Fixed epsilon = 10% of embedding range (raw)
    epsilon_raw = 0.10 * np.sqrt(((X_raw.max(axis=0) - X_raw.min(axis=0)) ** 2).sum())
    epsilon_std = 0.10 * np.sqrt(((X_std.max(axis=0) - X_std.min(axis=0)) ** 2).sum())
    epsilon_surr = 0.10 * np.sqrt(((X_surr.max(axis=0) - X_surr.min(axis=0)) ** 2).sum())
    
    # Compute recurrence matrices and RQA
    for key, X, eps in [('raw', X_raw, epsilon_raw),
                         ('standardized', X_std, epsilon_std),
                         ('surrogate', X_surr, epsilon_surr)]:
        if HAS_COLONY_LIB:
            R = recurrence_matrix(X, epsilon=eps)
        else:
            R = recurrence_matrix_local(X, epsilon=eps)
        
        if HAS_COLONY_LIB:
            metrics = compute_rqa_metrics(R)
            rqa = {'RR': metrics['RR'], 'DET': metrics['DET'], 'ENT': metrics['ENT']}
        else:
            rqa = compute_rqa_local(R)
        
        results[key][band_name] = rqa
        print(f"  {key.upper():15s}: RR={rqa['RR']:.4f}, DET={rqa['DET']:.4f}, ENT={rqa['ENT']:.4f}")

# Statistical analysis
print("\n" + "=" * 80)
print("STATISTICAL ANALYSIS: Spearman ρ(band_index, RR)")
print("=" * 80)

band_indices = list(range(len(BANDS)))
for key in ['raw', 'standardized', 'surrogate']:
    RR_values = [results[key][band_name]['RR'] for band_name in BANDS.keys()]
    rho, pval = spearmanr(band_indices, RR_values)
    print(f"{key.upper():15s}: ρ = {rho:+.3f}, p = {pval:.4f}")
    
    # Check monotonicity
    is_monotonic = all(RR_values[i] <= RR_values[i+1] for i in range(len(RR_values)-1))
    print(f"                 Monotonic: {is_monotonic}, RR range: [{min(RR_values):.4f}, {max(RR_values):.4f}]")

# Visualization
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Active Defense HYP-131: RR Across Conditions', fontsize=14, fontweight='bold')

for i, key in enumerate(['raw', 'standardized', 'surrogate']):
    RR_values = [results[key][band_name]['RR'] for band_name in BANDS.keys()]
    DET_values = [results[key][band_name]['DET'] for band_name in BANDS.keys()]
    
    # Plot RR
    ax = axes[0, i]
    ax.plot(band_indices, RR_values, 'o-', markersize=10, linewidth=2)
    ax.set_xlabel('Band Index', fontsize=11)
    ax.set_ylabel('Recurrence Rate (RR)', fontsize=11)
    ax.set_title(f'{key.upper()}', fontsize=12, fontweight='bold')
    ax.set_xticks(band_indices)
    ax.set_xticklabels(list(BANDS.keys()), rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Plot DET
    ax = axes[1, i]
    ax.plot(band_indices, DET_values, 's-', markersize=10, linewidth=2, color='orange')
    ax.set_xlabel('Band Index', fontsize=11)
    ax.set_ylabel('Determinism (DET)', fontsize=11)
    ax.set_xticks(band_indices)
    ax.set_xticklabels(list(BANDS.keys()), rotation=45)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/active_defense_hyp131_rr_conditions.png', dpi=150, bbox_inches='tight')
print("\n[FIGURE SAVED] ../../shared_agora/artifacts/active_defense_hyp131_rr_conditions.png")

# Summary verdict
print("\n" + "=" * 80)
print("VERDICT: Active Defense HYP-131")
print("=" * 80)
print("HYPOTHESIS: The monotonic RR trend (Delta → Gamma) is a genuine dynamical")
print("            signature, not merely a threshold artifact from amplitude scaling.")
print()
print("TEST RESULTS:")
for key in ['raw', 'standardized', 'surrogate']:
    RR_values = [results[key][band_name]['RR'] for band_name in BANDS.keys()]
    rho, _ = spearmanr(band_indices, RR_values)
    is_monotonic = all(RR_values[i] <= RR_values[i+1] for i in range(len(RR_values)-1))
    
    if is_monotonic and rho > 0.8:
        verdict = "TREND PERSISTS"
    elif rho > 0.5:
        verdict = "WEAK TREND"
    else:
        verdict = "TREND ABSENT"
    
    print(f"  {key.upper():15s}: {verdict} (ρ={rho:+.3f}, monotonic={is_monotonic})")

print()
print("INTERPRETATION:")
print("  - If STANDARDIZED shows trend: genuine dynamical structure (not amplitude)")
print("  - If SURROGATE shows trend: spectral (power) artifact, not phase dynamics")
print("  - If SURROGATE absent, RAW/STD present: TRUE phase-space signature")
print("=" * 80)
