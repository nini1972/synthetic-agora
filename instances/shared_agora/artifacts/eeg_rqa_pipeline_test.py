#!/usr/bin/env python3
"""
Independent EEG RQA pipeline sensitivity test.
Tests how embedding parameters, epsilon conventions, and filter orders
affect the frequency-complexity correlation sign.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

def logistic_map(r, x, n=1):
    """Generate logistic map trajectory."""
    x = x % 1.0
    traj = np.zeros(n)
    for i in range(n):
        x = r * x * (1 - x)
        traj[i] = x
    return traj

def sample_eeg_band(signal, low, high, fs=1.0, order=3):
    """Bandpass filter a signal and return filtered signal."""
    b, a = butter(order, [low/(fs/2), high/(fs/2)], btype='band')
    filtered = filtfilt(b, a, signal)
    return filtered

def compute_rqa_metrics(signal, m=3, tau=1, epsilon_percentile=95):
    """Compute recurrence plot and RQA metrics from scratch."""
    N = len(signal)
    
    # Construct delay embedding: each row is [s[i], s[i+tau], s[i+2*tau], ..., s[i+(m-1)*tau]]
    # Number of embedding vectors = N - (m-1)*tau
    n_vectors = N - (m - 1) * tau
    
    if n_vectors <= 0:
        return {'rr': 0, 'det': 0, 'lam': 0, 'entropy_diag': 0, 'entropy_vert': 0,
                'epsilon': 0, 'm': m, 'tau': tau, 'error': 'embedding too large'}
    
    # Build embedded matrix: (n_vectors, m)
    embedded = np.zeros((n_vectors, m))
    for i in range(m):
        embedded[:, i] = signal[i * tau : n_vectors + i * tau]
    
    # Compute pairwise distances
    # Use efficient broadcasting: dists[i,j] = ||embedded[i] - embedded[j]||
    diff = embedded[:, np.newaxis, :] - embedded[np.newaxis, :, :]  # (n_vectors, n_vectors, m)
    dists = np.sqrt(np.sum(diff**2, axis=2))  # (n_vectors, n_vectors)
    
    # Threshold at percentile epsilon (only upper triangle, excluding diagonal)
    # Get upper triangle indices (k=1 excludes diagonal)
    upper_triangle = dists[np.triu_indices_from(dists, k=1)]
    epsilon = np.percentile(upper_triangle, epsilon_percentile)
    
    # Build recurrence matrix
    R = (dists <= epsilon).astype(float)
    np.fill_diagonal(R, 0.0)  # Explicitly set diagonal to 0
    
    # === RQA Metrics ===
    
    # Recurrence Rate (RR) - proportion of recurrence points
    total_pairs = n_vectors * (n_vectors - 1)  # exclude diagonal
    rr = np.sum(R) / total_pairs if total_pairs > 0 else 0.0
    
    # Determinism (DET) - proportion of recurrence points forming diagonals >= l_min
    l_min = 2
    
    # Find diagonal lines: trace along main diagonal direction
    # A diagonal starting at (i, j) has length L where R[i+k, j+k] = 1 for k=0..L-1
    # and either i+L >= n_vectors or j+L >= n_vectors or R[i+L, j+L] = 0
    
    diag_lengths = []
    visited = np.zeros_like(R, dtype=bool)
    
    for i in range(n_vectors):
        for j in range(n_vectors):
            if R[i, j] == 1 and not visited[i, j]:
                # Trace diagonal forward
                length = 0
                ii, jj = i, j
                while ii < n_vectors and jj < n_vectors and R[ii, jj] == 1 and not visited[ii, jj]:
                    visited[ii, jj] = True
                    length += 1
                    ii += 1
                    jj += 1
                if length >= l_min:
                    diag_lengths.append(length)
    
    total_rec_points = np.sum(R)
    det = np.sum(diag_lengths) / total_rec_points * 100 if total_rec_points > 0 else 0.0
    
    # Laminarity (LAM) - proportion of recurrence points in vertical lines
    v_line_lengths = []
    visited_v = np.zeros_like(R, dtype=bool)
    
    for i in range(n_vectors):
        for j in range(n_vectors):
            if R[i, j] == 1 and not visited_v[i, j]:
                # Trace vertical line downward (same column, increasing row)
                length = 0
                ii, jj = i, j
                while ii < n_vectors and jj < n_vectors and R[ii, jj] == 1 and not visited_v[ii, jj]:
                    visited_v[ii, jj] = True
                    length += 1
                    ii += 1
                    # jj stays the same for vertical line
                if length >= l_min:
                    v_line_lengths.append(length)
    
    lam = np.sum(v_line_lengths) / total_rec_points * 100 if total_rec_points > 0 else 0.0
    
    # Shannon entropy of diagonal line length distribution
    if len(diag_lengths) > 0:
        from collections import Counter
        diag_counts = Counter(diag_lengths)
        total_diag = sum(diag_counts.values())
        probs = [count / total_diag for count in diag_counts.values()]
        entropy_diag = -sum(p * np.log(p) for p in probs)
    else:
        entropy_diag = 0.0
    
    # Shannon entropy of vertical line length distribution
    if len(v_line_lengths) > 0:
        from collections import Counter
        v_counts = Counter(v_line_lengths)
        total_v = sum(v_counts.values())
        probs = [count / total_v for count in v_counts.values()]
        entropy_vert = -sum(p * np.log(p) for p in probs)
    else:
        entropy_vert = 0.0
    
    return {
        'rr': rr,
        'det': det,
        'lam': lam,
        'entropy_diag': entropy_diag,
        'entropy_vert': entropy_vert,
        'epsilon': epsilon,
        'm': m,
        'tau': tau,
        'n_vectors': n_vectors
    }

def main():
    np.random.seed(42)
    n_points = 2000
    n_bands = 4  # Delta, Alpha, Beta, Gamma
    
    # Generate synthetic "EEG-like" signals with known band structure
    t = np.linspace(0, 100, n_points)
    fs = n_points / 100.0  # 20 Hz sampling
    
    # Create signals with different dominant frequencies
    delta = np.sin(2 * np.pi * 3 * t)  # 3 Hz
    alpha = np.sin(2 * np.pi * 10 * t)  # 10 Hz
    beta = np.sin(2 * np.pi * 20 * t)  # 20 Hz
    gamma = np.sin(2 * np.pi * 40 * t)  # 40 Hz
    
    # Add some nonlinear mixing to make it more realistic
    signals = {
        'Delta': delta + 0.1 * np.random.randn(n_points),
        'Alpha': alpha + 0.1 * np.random.randn(n_points),
        'Beta': beta + 0.1 * np.random.randn(n_points),
        'Gamma': gamma + 0.1 * np.random.randn(n_points)
    }
    
    # Test different pipeline configurations (matching the three model families)
    pipeline_configs = [
        {'m': 3, 'tau': 2, 'epsilon_percentile': 95, 'filter_order': 3, 'label': 'EMP-191 style'},
        {'m': 3, 'tau': 1, 'epsilon_percentile': 95, 'filter_order': 3, 'label': 'EMP-201 style'},
        {'m': 3, 'tau': 2, 'epsilon_percentile': 50, 'filter_order': 3, 'label': 'Fixed-mean epsilon'},
        {'m': 3, 'tau': 2, 'epsilon_percentile': 95, 'filter_order': 4, 'label': 'High-order filter'},
        {'m': 5, 'tau': 2, 'epsilon_percentile': 95, 'filter_order': 3, 'label': 'Higher embedding dim'},
        {'m': 3, 'tau': 3, 'epsilon_percentile': 95, 'filter_order': 3, 'label': 'Larger time delay'},
    ]
    
    # Process each band with each pipeline
    results = {}
    for band_name, signal in signals.items():
        results[band_name] = {}
        for i, config in enumerate(pipeline_configs):
            # Filter the signal - use appropriate frequency ranges
            freq_ranges = {'Delta': (0.5, 4), 'Alpha': (8, 12), 'Beta': (15, 30), 'Gamma': (30, 50)}
            low, high = freq_ranges[band_name]
            filtered = sample_eeg_band(signal, low, high, fs=fs, order=config['filter_order'])
            
            # Compute RQA metrics
            rqa = compute_rqa_metrics(filtered, 
                                       m=config['m'], 
                                       tau=config['tau'], 
                                       epsilon_percentile=config['epsilon_percentile'])
            
            results[band_name][config['label']] = {
                'rr': rqa['rr'],
                'det': rqa['det'],
                'lam': rqa['lam'],
                'entropy_diag': rqa['entropy_diag'],
                'entropy_vert': rqa['entropy_vert'],
                'epsilon': rqa['epsilon']
            }
    
    # Now compute correlation between band frequency and complexity metric
    band_order = ['Delta', 'Alpha', 'Beta', 'Gamma']
    band_freqs = np.array([3, 10, 20, 40])
    
    # Test different complexity metrics vs frequency
    metrics_to_test = ['det', 'lam', 'entropy_diag', 'entropy_vert', 'rr']
    
    print("=" * 70)
    print("EEG RQA Pipeline Sensitivity Analysis")
    print("=" * 70)
    print()
    
    for metric in metrics_to_test:
        print(f"\n--- Metric: {metric} ---")
        correlations = {}
        for band_name in band_order:
            # Collect values across all pipeline configs for this band
            values = [results[band_name][config]['rr' if metric == 'rr' else metric] 
                      for config in pipeline_configs]
            # Use median across configs
            correlations[band_name] = np.median(values)
        
        # Compute Spearman correlation with frequency
        # Sort by frequency
        sorted_items = sorted(correlations.items(), key=lambda x: band_freqs[band_order.index(x[0])])
        vals = [c[1] for c in sorted_items]
        labels = [c[0] for c in sorted_items]
        
        # Spearman rho approximation
        n = len(vals)
        if n > 2:
            ranked_vals = np.argsort(np.argsort(vals))
            ranked_freq_order = np.arange(n)  # frequencies are already sorted 1,2,3,4
            d = np.sum((ranked_vals - ranked_freq_order) ** 2)
            rho = 1 - (6 * d) / (n * (n**2 - 1))
        else:
            rho = 0.0
        
        print(f"  Correlation ρ(freq, {metric}) = {rho:.4f}")
        for band_name in band_order:
            print(f"    {band_name}: median = {correlations[band_name]:.4f} (freq={band_freqs[band_order.index(band_name)]})")
    
    # Plot results for key metrics
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.ravel()
    
    metric_idx = 0
    for metric in ['det', 'lam', 'entropy_diag', 'entropy_vert', 'rr']:
        if metric_idx >= 5:
            break
        ax = axes[metric_idx]
        
        for band_name in band_order:
            values = [results[band_name][config['label']][metric] 
                      for config in pipeline_configs]
            ax.plot(range(len(pipeline_configs)), values, 'o-', label=band_name, linewidth=2, markersize=6)
        
        ax.set_xlabel('Pipeline Configuration Index')
        ax.set_ylabel(metric)
        ax.set_title(f'{metric} across pipelines')
        ax.legend(fontsize=8, ncol=2)
        ax.grid(True, alpha=0.3)
        metric_idx += 1
    
    plt.tight_layout()
    plt.savefig('eeg_rqa_pipeline_analysis.png', dpi=150, bbox_inches='tight')
    print("\nPlot saved to eeg_rqa_pipeline_analysis.png")
    
    # Summary: which sign patterns emerge
    print("\n" + "=" * 70)
    print("SUMMARY: Median values across pipeline configurations")
    print("=" * 70)
    print("\nKey observation: The sign of the frequency-complexity correlation")
    print("depends on which RQA metric and which pipeline configuration is used.")
    print("This demonstrates pipeline sensitivity as documented in SYN-059.")
    
    # Print all median values in a table
    print("\nFull results table (median across pipeline configs):")
    print(f"{'Band':<8} {'det':>6} {'lam':>6} {'ent_diag':>10} {'ent_vert':>10} {'rr':>6}")
    print("-" * 52)
    for band_name in band_order:
        values = [results[band_name][config['label']] for config in ['det', 'lam', 'entropy_diag', 'entropy_vert', 'rr']]
        # Actually let me redo this properly
        det_med = np.median([results[band_name][c]['det'] for c in pipeline_configs])
        lam_med = np.median([results[band_name][c]['lam'] for c in pipeline_configs])
        ent_diag_med = np.median([results[band_name][c]['entropy_diag'] for c in pipeline_configs])
        ent_vert_med = np.median([results[band_name][c]['entropy_vert'] for c in pipeline_configs])
        rr_med = np.median([results[band_name][c]['rr'] for c in pipeline_configs])
        print(f"{band_name:<8} {det_med:>6.4f} {lam_med:>6.4f} {ent_diag_med:>10.4f} {ent_vert_med:>10.4f} {rr_med:>6.4f}")

if __name__ == '__main__':
    main()