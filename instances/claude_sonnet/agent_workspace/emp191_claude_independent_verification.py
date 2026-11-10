#!/usr/bin/env python3
"""
Independent Claude Sonnet Verification of EMP-191
==================================================
EMP-191 claims: "EEG RQA Complexity Decreases with Band Frequency (ρ=-0.90)"
Key assertion: Under RR-matched conditions, ENT decreases monotonically from Delta→Gamma.

Protocol:
1. Load neural_eeg (14-channel, fs=128 Hz) from colony_lib.datasets
2. Band-pass filter (Butterworth, canonical bands)
3. Takens embedding (m=3, τ=2)
4. Compute RQA metrics under THREE conditions:
   (A) Fixed ε=0.1 on z-scored (HYP-131 recipe)
   (B) Amplitude-matched ε
   (C) RR-matched ε (target RR~5%)
5. Compute Spearman correlation ρ(freq, ENT) for each condition
6. Multi-channel sign test: ENT(Gamma) - ENT(Alpha) < 0 across all 14 channels

Expected outcome: ρ ~ -0.90 under RR-matching, confirming EMP-191.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import spearmanr
import json

# Load EEG dataset
from colony_lib.datasets import load_dataset
ds = load_dataset('neural_eeg')
data = ds['data']  # shape (n_channels, n_samples)
fs = ds['fs']  # 128 Hz
n_channels, n_samples = data.shape

print(f"[INFO] Loaded neural_eeg: {n_channels} channels, {n_samples} samples, fs={fs} Hz")

# Canonical bands (Hz)
bands = {
    'Delta': (0.5, 4.0),
    'Theta': (4.0, 8.0),
    'Alpha': (8.0, 13.0),
    'Beta': (13.0, 30.0),
    'Gamma': (30.0, 64.0)  # Nyquist-safe (fs/2 = 64 Hz)
}
band_names = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
band_freqs = [2.25, 6.0, 10.5, 21.5, 47.0]  # midpoint frequencies

# Takens embedding parameters
m, tau = 3, 2

# RQA helper functions
def takens_embedding(x, m, tau):
    """Delay embedding."""
    n = len(x)
    n_vectors = n - (m-1)*tau
    embedded = np.zeros((n_vectors, m))
    for i in range(m):
        embedded[:, i] = x[i*tau : i*tau + n_vectors]
    return embedded

def recurrence_matrix(embedded, epsilon):
    """Compute recurrence matrix."""
    from scipy.spatial.distance import cdist
    D = cdist(embedded, embedded, metric='euclidean')
    R = (D < epsilon).astype(np.uint8)
    return R

def compute_rqa_simple(R):
    """Compute RR, DET, LAM, ENT."""
    N = R.shape[0]
    RR = np.sum(R) / (N * N)
    
    # DET: diagonal line structures
    diag_lengths = []
    for k in range(-(N-1), N):
        diag = np.diag(R, k=k)
        if len(diag) < 2:
            continue
        runs = []
        count = 0
        for val in diag:
            if val == 1:
                count += 1
            else:
                if count >= 2:
                    runs.append(count)
                count = 0
        if count >= 2:
            runs.append(count)
        diag_lengths.extend(runs)
    
    if diag_lengths:
        DET = sum(diag_lengths) / max(1, np.sum(R))
        L = np.mean(diag_lengths)
    else:
        DET = 0.0
        L = 0.0
    
    # LAM: vertical line structures
    vert_lengths = []
    for j in range(N):
        col = R[:, j]
        runs = []
        count = 0
        for val in col:
            if val == 1:
                count += 1
            else:
                if count >= 2:
                    runs.append(count)
                count = 0
        if count >= 2:
            runs.append(count)
        vert_lengths.extend(runs)
    
    if vert_lengths:
        LAM = sum(vert_lengths) / max(1, np.sum(R))
    else:
        LAM = 0.0
    
    # ENT: Shannon entropy of diagonal line lengths
    if diag_lengths:
        counts = np.bincount(diag_lengths)
        probs = counts / counts.sum()
        probs = probs[probs > 0]
        ENT = -np.sum(probs * np.log(probs))
    else:
        ENT = 0.0
    
    return {'RR': RR, 'DET': DET, 'LAM': LAM, 'ENT': ENT, 'L': L}

# Test on single representative channel (AF3, channel 0)
channel_idx = 0
signal_raw = data[channel_idx, :]

# Design filters
filters = {}
for name, (low, high) in bands.items():
    nyq = 0.5 * fs
    low_norm = low / nyq
    high_norm = high / nyq
    # Use order=3 for stability (following poolside_laguna's fix)
    b, a = signal.butter(3, [low_norm, high_norm], btype='band')
    filters[name] = (b, a)

# Condition A: Fixed ε=0.1 on z-scored (HYP-131 recipe)
results_A = {}
for name in band_names:
    b, a = filters[name]
    filtered = signal.filtfilt(b, a, signal_raw)
    zscore = (filtered - np.mean(filtered)) / np.std(filtered)
    embedded = takens_embedding(zscore, m, tau)
    R = recurrence_matrix(embedded, epsilon=0.1)
    rqa = compute_rqa_simple(R)
    results_A[name] = rqa
    print(f"[A] {name}: RR={rqa['RR']:.4f}, DET={rqa['DET']:.4f}, LAM={rqa['LAM']:.4f}, ENT={rqa['ENT']:.4f}")

# Condition C: RR-matched ε (target RR~5%)
target_rr = 0.05
results_C = {}
for name in band_names:
    b, a = filters[name]
    filtered = signal.filtfilt(b, a, signal_raw)
    zscore = (filtered - np.mean(filtered)) / np.std(filtered)
    embedded = takens_embedding(zscore, m, tau)
    
    # Binary search for ε to achieve target RR
    eps_low, eps_high = 0.01, 10.0
    for _ in range(20):
        eps_mid = (eps_low + eps_high) / 2.0
        R = recurrence_matrix(embedded, epsilon=eps_mid)
        rr_mid = np.sum(R) / (R.shape[0] ** 2)
        if rr_mid < target_rr:
            eps_low = eps_mid
        else:
            eps_high = eps_mid
    
    # Final RQA with tuned ε
    R = recurrence_matrix(embedded, epsilon=eps_mid)
    rqa = compute_rqa_simple(R)
    results_C[name] = rqa
    print(f"[C] {name}: ε={eps_mid:.4f}, RR={rqa['RR']:.4f}, DET={rqa['DET']:.4f}, LAM={rqa['LAM']:.4f}, ENT={rqa['ENT']:.4f}")

# Compute Spearman correlations
ent_A = [results_A[name]['ENT'] for name in band_names]
ent_C = [results_C[name]['ENT'] for name in band_names]
rr_A = [results_A[name]['RR'] for name in band_names]

rho_A, _ = spearmanr(band_freqs, ent_A)
rho_C, _ = spearmanr(band_freqs, ent_C)
rho_rr_A, _ = spearmanr(band_freqs, rr_A)

print(f"\n[RESULT] Spearman ρ(freq, ENT) — Condition A (fixed ε): {rho_A:.2f}")
print(f"[RESULT] Spearman ρ(freq, ENT) — Condition C (RR-matched): {rho_C:.2f}")
print(f"[RESULT] Spearman ρ(freq, RR) — Condition A (fixed ε): {rho_rr_A:.2f}")

# Multi-channel sign test: ENT(Gamma) - ENT(Alpha) < 0
sign_test_results = []
for ch_idx in range(n_channels):
    signal_ch = data[ch_idx, :]
    
    # Alpha
    b, a = filters['Alpha']
    filtered_alpha = signal.filtfilt(b, a, signal_ch)
    zscore_alpha = (filtered_alpha - np.mean(filtered_alpha)) / np.std(filtered_alpha)
    embedded_alpha = takens_embedding(zscore_alpha, m, tau)
    
    # Gamma
    b, a = filters['Gamma']
    filtered_gamma = signal.filtfilt(b, a, signal_ch)
    zscore_gamma = (filtered_gamma - np.mean(filtered_gamma)) / np.std(filtered_gamma)
    embedded_gamma = takens_embedding(zscore_gamma, m, tau)
    
    # RR-matched ε for each band
    def find_matched_epsilon(embedded, target_rr=0.05):
        eps_low, eps_high = 0.01, 10.0
        for _ in range(20):
            eps_mid = (eps_low + eps_high) / 2.0
            R = recurrence_matrix(embedded, epsilon=eps_mid)
            rr_mid = np.sum(R) / (R.shape[0] ** 2)
            if rr_mid < target_rr:
                eps_low = eps_mid
            else:
                eps_high = eps_mid
        return eps_mid
    
    eps_alpha = find_matched_epsilon(embedded_alpha)
    eps_gamma = find_matched_epsilon(embedded_gamma)
    
    R_alpha = recurrence_matrix(embedded_alpha, epsilon=eps_alpha)
    R_gamma = recurrence_matrix(embedded_gamma, epsilon=eps_gamma)
    
    rqa_alpha = compute_rqa_simple(R_alpha)
    rqa_gamma = compute_rqa_simple(R_gamma)
    
    delta_ent = rqa_gamma['ENT'] - rqa_alpha['ENT']
    sign_test_results.append(delta_ent)

n_negative = sum(1 for x in sign_test_results if x < 0)
n_total = len(sign_test_results)
p_value = 2 ** (-n_total) if n_negative == n_total else None

print(f"\n[SIGN TEST] ENT(Gamma) - ENT(Alpha) < 0 in {n_negative}/{n_total} channels")
if p_value:
    print(f"[SIGN TEST] p-value (exact binomial): {p_value:.6f}")

# Plot results
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Panel 1: Condition A ENT vs frequency
axes[0].plot(band_freqs, ent_A, 'o-', color='crimson', markersize=8, label=f'Condition A (ρ={rho_A:.2f})')
axes[0].set_xlabel('Band Frequency (Hz)', fontsize=11)
axes[0].set_ylabel('Shannon Entropy (nats)', fontsize=11)
axes[0].set_title('Fixed ε=0.1 (HYP-131 recipe)', fontsize=12, fontweight='bold')
axes[0].grid(alpha=0.3)
axes[0].legend()

# Panel 2: Condition C ENT vs frequency
axes[1].plot(band_freqs, ent_C, 's-', color='steelblue', markersize=8, label=f'Condition C (ρ={rho_C:.2f})')
axes[1].set_xlabel('Band Frequency (Hz)', fontsize=11)
axes[1].set_ylabel('Shannon Entropy (nats)', fontsize=11)
axes[1].set_title('RR-Matched ε (EMP-191 protocol)', fontsize=12, fontweight='bold')
axes[1].grid(alpha=0.3)
axes[1].legend()

# Panel 3: Multi-channel sign test histogram
axes[2].hist(sign_test_results, bins=15, color='forestgreen', alpha=0.7, edgecolor='black')
axes[2].axvline(0, color='red', linestyle='--', linewidth=2, label='Δ=0')
axes[2].set_xlabel('ENT(Gamma) - ENT(Alpha)', fontsize=11)
axes[2].set_ylabel('Channel Count', fontsize=11)
axes[2].set_title(f'Sign Test: {n_negative}/{n_total} < 0', fontsize=12, fontweight='bold')
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('emp191_claude_verification.png', dpi=150, bbox_inches='tight')
print("\n[ARTIFACT] Saved: emp191_claude_verification.png")

# Save metrics to JSON
summary = {
    'condition_A': {
        'spearman_rho': float(rho_A),
        'ENT_values': ent_A,
        'RR_values': rr_A
    },
    'condition_C': {
        'spearman_rho': float(rho_C),
        'ENT_values': ent_C
    },
    'sign_test': {
        'n_negative': n_negative,
        'n_total': n_total,
        'delta_ent_values': sign_test_results,
        'p_value': p_value
    }
}

with open('emp191_claude_verification.json', 'w') as f:
    json.dump(summary, f, indent=2)
print("[ARTIFACT] Saved: emp191_claude_verification.json")
