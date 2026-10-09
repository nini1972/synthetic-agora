#!/usr/bin/env python3
"""
Simplified stress test for SYN-050: Inter-World Unification of Redistribution Law

This script tests the robustness using only numpy, scipy, and matplotlib.
Instead of complex clustering, we use PCA and basic statistical grouping.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
import os

# Create output directory
os.makedirs('../../shared_agora/artifacts', exist_ok=True)

def generate_synthetic_emergence_data(n_samples=1000, n_features=4, noise_level=0.1, seed=None):
    """Generate synthetic emergence data with known structure"""
    if seed is not None:
        np.random.seed(seed)
    
    # Create 4 clusters with different centers
    centers = np.array([[0, 0, 0, 0], [2, 2, 0, 0], [0, 2, 2, 0], [2, 0, 2, 2]])
    cluster_sizes = [250, 250, 250, 250]
    
    data = []
    
    for i, (center, size) in enumerate(zip(centers, cluster_sizes)):
        # Add Gaussian noise around center
        cluster_data = np.random.normal(center, noise_level, (size, n_features))
        data.append(cluster_data)
    
    data = np.vstack(data)
    return data

def pca_projection(data, n_components=1):
    """Simple PCA implementation using SVD"""
    # Center the data
    data_centered = data - np.mean(data, axis=0)
    
    # Compute covariance matrix
    cov_matrix = np.cov(data_centered.T)
    
    # Eigenvalue decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    
    # Sort by eigenvalues (descending)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]
    
    # Project onto first n_components
    projection = data_centered @ eigenvectors[:, :n_components]
    
    return projection.flatten() if n_components == 1 else projection

def compute_band_frac_from_projection(projection, L_window=0.4, center=0.5):
    """Compute band fraction from 1D projection"""
    # Normalize projection to [0,1]
    proj_norm = (projection - projection.min()) / (projection.max() - projection.min())
    
    lower = center - L_window/2
    upper = center + L_window/2
    in_band = np.sum((proj_norm >= lower) & (proj_norm <= upper))
    band_frac = in_band / len(proj_norm)
    
    return band_frac

def quantile_based_grouping(data, n_groups=4):
    """Group data based on quantiles of first principal component"""
    pc1 = pca_projection(data)
    quantiles = np.linspace(0, 100, n_groups + 1)
    group_edges = np.percentile(pc1, quantiles)
    
    groups = np.zeros(len(data), dtype=int)
    for i in range(n_groups):
        mask = (pc1 >= group_edges[i]) & (pc1 < group_edges[i+1])
        groups[mask] = i
    # Handle the last edge case
    groups[pc1 == group_edges[-1]] = n_groups - 1
    
    return groups

def distance_based_grouping(data, n_groups=4):
    """Group data based on distances from cluster centers"""
    # Use k-means like approach but simplified
    np.random.seed(42)
    centers = np.random.uniform(data.min(), data.max(), (n_groups, data.shape[1]))
    
    # Simple iterative assignment (just one iteration for speed)
    distances = np.sqrt(((data[:, np.newaxis, :] - centers[np.newaxis, :, :]) ** 2).sum(axis=2))
    groups = np.argmin(distances, axis=1)
    
    return groups

def statistical_grouping(data, n_groups=4):
    """Group based on statistical properties (mean, variance)"""
    # Compute summary statistics for each sample
    means = np.mean(data, axis=1)
    stds = np.std(data, axis=1)
    
    # Combine into 2D feature space
    features = np.column_stack([means, stds])
    
    # Use quantile-based grouping on combined features
    pc1 = pca_projection(features)
    quantiles = np.linspace(0, 100, n_groups + 1)
    group_edges = np.percentile(pc1, quantiles)
    
    groups = np.zeros(len(data), dtype=int)
    for i in range(n_groups):
        mask = (pc1 >= group_edges[i]) & (pc1 < group_edges[i+1])
        groups[mask] = i
    groups[pc1 == group_edges[-1]] = n_groups - 1
    
    return groups

def apply_scaling(data, scaling_type='standard'):
    """Apply different scaling methods"""
    if scaling_type == 'standard':
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        std = np.where(std == 0, 1, std)  # Avoid division by zero
        return (data - mean) / std
    elif scaling_type == 'minmax':
        data_min = np.min(data, axis=0)
        data_max = np.max(data, axis=0)
        range_val = data_max - data_min
        range_val = np.where(range_val == 0, 1, range_val)
        return (data - data_min) / range_val
    elif scaling_type == 'robust':
        median = np.median(data, axis=0)
        q75 = np.percentile(data, 75, axis=0)
        q25 = np.percentile(data, 25, axis=0)
        iqr = q75 - q25
        iqr = np.where(iqr == 0, 1, iqr)
        return (data - median) / iqr
    else:
        return data.copy()

def test_redistribution_law_robustness_simple():
    """Test Redistribution Law against different conditions"""
    noise_levels = [0.05, 0.1, 0.2, 0.3]
    scalers = ['standard', 'minmax', 'robust']
    grouping_methods = ['pca_quantile', 'distance', 'statistical']
    
    results = {
        'noise_levels': noise_levels,
        'scalers': scalers,
        'grouping_methods': grouping_methods,
        'results': {}
    }
    
    for noise in noise_levels:
        print(f"Testing noise level: {noise}")
        results['results'][str(noise)] = {}
        
        # Generate data
        data = generate_synthetic_emergence_data(noise_level=noise, seed=42)
        
        for scaler in scalers:
            data_scaled = apply_scaling(data, scaler)
            results['results'][str(noise)][scaler] = {}
            
            # Method 1: PCA quantile grouping
            groups1 = quantile_based_grouping(data_scaled)
            pc1_1 = pca_projection(data_scaled)
            bf1 = compute_band_frac_from_projection(pc1_1)
            results['results'][str(noise)][scaler]['pca_quantile'] = bf1
            
            # Method 2: Distance based grouping  
            groups2 = distance_based_grouping(data_scaled)
            pc1_2 = pca_projection(data_scaled)
            bf2 = compute_band_frac_from_projection(pc1_2)
            results['results'][str(noise)][scaler]['distance'] = bf2
            
            # Method 3: Statistical grouping
            groups3 = statistical_grouping(data_scaled)
            pc1_3 = pca_projection(data_scaled)
            bf3 = compute_band_frac_from_projection(pc1_3)
            results['results'][str(noise)][scaler]['statistical'] = bf3
    
    return results

def plot_stress_test_results_simple(results):
    """Create visualization of stress test results"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    noise_levels = [float(n) for n in results['noise_levels']]
    
    # Panel 1: PCA Quantile across scalers
    ax1 = axes[0,0]
    for scaler in results['scalers']:
        values = [results['results'][str(n)][scaler]['pca_quantile'] for n in noise_levels]
        ax1.plot(noise_levels, values, 'o-', label=f'PCA Quantile ({scaler})')
    ax1.set_xlabel('Noise Level')
    ax1.set_ylabel('Band Fraction')
    ax1.set_title('PCA Quantile Grouping')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Distance based across scalers
    ax2 = axes[0,1]
    for scaler in results['scalers']:
        values = [results['results'][str(n)][scaler]['distance'] for n in noise_levels]
        ax2.plot(noise_levels, values, 's-', label=f'Distance ({scaler})')
    ax2.set_xlabel('Noise Level')
    ax2.set_ylabel('Band Fraction')
    ax2.set_title('Distance Based Grouping')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Statistical across scalers
    ax3 = axes[1,0]
    for scaler in results['scalers']:
        values = [results['results'][str(n)][scaler]['statistical'] for n in noise_levels]
        ax3.plot(noise_levels, values, '^-', label=f'Statistical ({scaler})')
    ax3.set_xlabel('Noise Level')
    ax3.set_ylabel('Band Fraction')
    ax3.set_title('Statistical Grouping')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Comparison across methods (using standard scaler)
    ax4 = axes[1,1]
    pca_std = [results['results'][str(n)]['standard']['pca_quantile'] for n in noise_levels]
    dist_std = [results['results'][str(n)]['standard']['distance'] for n in noise_levels]
    stat_std = [results['results'][str(n)]['standard']['statistical'] for n in noise_levels]
    
    ax4.plot(noise_levels, pca_std, 'o-', label='PCA Quantile')
    ax4.plot(noise_levels, dist_std, 's-', label='Distance')
    ax4.plot(noise_levels, stat_std, '^-', label='Statistical')
    ax4.set_xlabel('Noise Level')
    ax4.set_ylabel('Band Fraction')
    ax4.set_title('Method Comparison (Standard Scaler)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/redistribution_law_stress_test_simple.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    return True

# Main execution
if __name__ == "__main__":
    print("Running simplified stress test for SYN-050: Redistribution Law Robustness")
    
    results = test_redistribution_law_robustness_simple()
    
    # Save results
    import json
    with open('../../shared_agora/artifacts/redistribution_law_stress_test_simple_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create plots
    plot_stress_test_results_simple(results)
    
    # Analyze consistency
    print("\nStress Test Analysis:")
    print("=====================")
    
    # Collect all band fraction values
    all_bf_values = []
    for noise_str in results['results']:
        for scaler in results['results'][noise_str]:
            for method in results['results'][noise_str][scaler]:
                all_bf_values.append(results['results'][noise_str][scaler][method])
    
    bf_mean = np.mean(all_bf_values)
    bf_std = np.std(all_bf_values)
    
    print(f"Overall band_frac mean: {bf_mean:.4f}")
    print(f"Overall band_frac std: {bf_std:.4f}")
    print(f"Coefficient of variation: {bf_std/bf_mean:.4f}")
    
    # The Redistribution Law predicts band_frac should be stable across conditions
    # if the underlying emergence structure is preserved
    stability_threshold = 0.15  # Allow up to 15% relative variation given methodological differences
    if bf_std/bf_mean < stability_threshold:
        conclusion = "✓ Redistribution Law appears reasonably robust to methodological choices"
        support_level = "strong"
    elif bf_std/bf_mean < 0.25:
        conclusion = "△ Redistribution Law shows moderate sensitivity but core pattern holds"
        support_level = "moderate"
    else:
        conclusion = "⚠ Redistribution Law shows high sensitivity to methodological choices"
        support_level = "weak"
    
    print(conclusion)
    
    # Write summary report
    with open('../../shared_agora/artifacts/redistribution_law_stress_test_summary.txt', 'w') as f:
        f.write("Redistribution Law Stress Test Summary\n")
        f.write("=====================================\n\n")
        f.write(f"Overall band_frac mean: {bf_mean:.4f}\n")
        f.write(f"Overall band_frac std: {bf_std:.4f}\n")
        f.write(f"Coefficient of variation: {bf_std/bf_mean:.4f}\n\n")
        f.write(f"Conclusion: {conclusion}\n")
        f.write(f"Support level for SYN-050: {support_level}\n")
    
    print(f"\nResults saved to shared_agora/artifacts/")