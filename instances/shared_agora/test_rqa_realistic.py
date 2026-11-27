import numpy as np
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)
n_samples = 4096
n_bands = 5
freq_centers = np.array([1, 4, 8, 15, 35])

def bandpass_fft(signal, lowcut, highcut, fs=128):
    """Bandpass filter using FFT method"""
    fft = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), d=1.0/fs)
    mask = (freqs >= lowcut) & (freqs <= highcut)
    fft_copy = fft.copy()
    fft_copy[~mask] = 0
    return np.fft.irfft(fft_copy, n=len(signal))

def takens_embed(signal, m=3, tau=2):
    """Takens delay embedding"""
    n = len(signal)
    embedded = np.column_stack([signal[tau*i:n-tau*(m-1-i)] for i in range(m)])
    return embedded

def rqa_entropy(embedded, epsilon_quantile=0.05, max_line=20):
    """Compute Shannon entropy of recurrence diagonal line lengths"""
    dists = np.linalg.norm(
        embedded[:, None, :] - embedded[None, :, :], axis=2
    )
    eps = np.quantile(dists, epsilon_quantile)
    R = (dists <= eps).astype(int)
    np.fill_diagonal(R, 0)
    
    line_lengths = []
    visited = np.zeros_like(R, dtype=bool)
    for i in range(R.shape[0]):
        for j in range(R.shape[1]):
            if R[i, j] == 1 and not visited[i, j]:
                length = 0
                ii, jj = i, j
                while ii < R.shape[0] and jj < R.shape[1] and R[ii, jj] == 1 and not visited[ii, jj]:
                    visited[ii, jj] = True
                    length += 1
                    ii += 1
                    jj += 1
                if 2 <= length <= max_line:
                    line_lengths.append(length)
    
    if len(line_lengths) < 3:
        return 0.0
    
    from collections import Counter
    counts = Counter(line_lengths)
    probs = np.array(list(counts.values()), dtype=float) / len(line_lengths)
    if np.any(probs <= 0) or np.sum(probs) == 0:
        return 0.0
    ent = float(-np.sum(probs * np.log(probs)))
    return ent

# Generate realistic band-limited signals with decreasing entropy at higher frequencies
# (simulating EEG: lower freq bands are more structured/less random)
entropies_sparse = []
entropies_dense = []

for b in range(n_bands):
    lowcut = freq_centers[b]
    highcut = freq_centers[b+1] if b+1 < n_bands else 50
    
    # Generate signal with band-specific entropy characteristics
    # Lower frequency bands: more structured (e.g., 1/f characteristics)
    # Higher frequency bands: noisier
    if b <= 1:  # Delta, Theta - structured
        base_slope = -0.5  # 1/f slope
    else:  # Alpha, Beta, Gamma - noisier
        base_slope = -1.5
    
    t = np.arange(n_samples)
    # Create signal with 1/f-like characteristics + noise
    white = np.random.randn(n_samples)
    # Approximate 1/f by integrating (creates red noise)
    integrated = np.cumsum(white)
    
    # Bandpass filter
    filtered = bandpass_fft(integrated, lowcut, highcut, fs=128)
    
    # Takens embedding
    embedded = takens_embed(filtered, m=3, tau=2)
    
    # Sparse ε (p5 → RR≈0.05): should show ENT decreasing with frequency
    ent_s = rqa_entropy(embedded, epsilon_quantile=0.05, max_line=20)
    entropies_sparse.append(ent_s)
    
    # Dense ε (p95 → RR≈0.95): should show ENT increasing with frequency
    ent_d = rqa_entropy(embedded, epsilon_quantile=0.95, max_line=20)
    entropies_dense.append(ent_d)

rho_sparse, p_sparse = spearmanr(freq_centers, entropies_sparse)
rho_dense, p_dense = spearmanr(freq_centers, entropies_dense)

print(f'Sparse ε (p5): RQA-ENT per band = {entropies_sparse}')
print(f'Spearman ρ = {rho_sparse:.4f} (p = {p_sparse:.4f})')
print()
print(f'Dense ε (p95): RQA-ENT per band = {entropies_dense}')
print(f'Spearman ρ = {rho_dense:.4f} (p = {p_dense:.4f})')
print()

# Also test middle ε
rho_mid, p_mid = spearmanr(freq_centers, 
    [(s+d)/2 for s,d in zip(entropies_sparse, entropies_dense)])
print(f'Mid ε: Spearman ρ = {rho_mid:.4f} (p = {p_mid:.4f})')

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.bar(freq_centers, entropies_sparse, color='steelblue', alpha=0.7, width=2.5, label='Sparse')
ax1.set_xlabel('Frequency (Hz)')
ax1.set_ylabel('RQA-ENT')
ax1.set_title(f'Sparse ε (RR≈0.05): ρ = {rho_sparse:.3f}')
ax1.legend()
ax1.set_xticks(freq_centers)

ax2.bar(freq_centers, entropies_dense, color='darkorange', alpha=0.7, width=2.5, label='Dense')
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('RQA-ENT')
ax2.set_title(f'Dense ε (RR≈0.95): ρ = {rho_dense:.3f}')
ax2.legend()
ax2.set_xticks(freq_centers)

plt.tight_layout()
plt.savefig('rqa_ent_realistic_test.png', dpi=150)
print('Plot saved as rqa_ent_realistic_test.png')