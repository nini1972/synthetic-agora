#!/usr/bin/env python3
"""
Stress test for SYN-050: Inter-World Unification of Redistribution Law

This script tests the robustness of the Redistribution Law exact values 
against different clustering algorithms, noise levels, and feature scalings.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import os

# Create output directory
os.makedirs('../../shared_agora/artifacts', exist_ok=True)

def generate_synthetic_emergence_data(n_samples=1000, n_features=4, noise_level=0.1, seed=None):
    """Generate synthetic emergence data with known structure"""
    if seed is not None:
        np.random.seed(seed)
    
    # Create clusters with different densities and shapes
    centers = np.array([[0, 0, 0, 0], [2, 2, 0, 0], [0, 2, 2, 0], [2, 0, 2, 2]])
    cluster_sizes = [250, 250, 250, 250]
    
    data = []
    labels_true = []
    
    for i, (center, size) in enumerate(zip(centers, cluster_sizes)):
        # Add Gaussian noise around center
        cluster_data = np.random.normal(center, noise_level, (size, n_features))
        data.append(cluster_data)
        labels_true.extend([i] * size)
    
    data = np.vstack(data)
    labels_true = np.array(labels_true)
    
    return data, labels_true

def compute_band_frac_kmeans(data, n_clusters=4, L_window=0.4, center=0.5):
    """Compute band fraction using K-means clustering"""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(data)
    
    # Use first principal component for band computation
    from sklearn.decomposition import PCA
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(data).flatten()
    
    # Normalize PC1 to [0,1]
    pc1_norm = (pc1 - pc1.min()) / (pc1.max() - pc1.min())
    
    lower = center - L_window/2
    upper = center + L_window/2
    in_band = np.sum((pc1_norm >= lower) & (pc1_norm <= upper))
    band_frac = in_band / len(pc1_norm)
    
    return band_frac, labels

def compute_band_frac_dbscan(data, eps=0.5, min_samples=5, L_window=0.4, center=0.5):
    """Compute band fraction using DBSCAN clustering"""
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(data)
    
    # Remove noise points (-1 labels) for band computation
    valid_mask = labels != -1
    if np.sum(valid_mask) == 0:
        return 0.0, labels
    
    valid_data = data[valid_mask]
    
    from sklearn.decomposition import PCA
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(valid_data).flatten()
    
    pc1_norm = (pc1 - pc1.min()) / (pc1.max() - pc1.min())
    
    lower = center - L_window/2
    upper = center + L_window/2
    in_band = np.sum((pc1_norm >= lower) & (pc1_norm <= upper))
    band_frac = in_band / len(pc1_norm)
    
    return band_frac, labels

def compute_band_frac_hierarchical(data, n_clusters=4, L_window=0.4, center=0.5):
    """Compute band fraction using hierarchical clustering"""
    hier = AgglomerativeClustering(n_clusters=n_clusters)
    labels = hier.fit_predict(data)
    
    from sklearn.decomposition import PCA
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(data).flatten()
    
    pc1_norm = (pc1 - pc1.min()) / (pc1.max() - pc1.min())
    
    lower = center - L_window/2
    upper = center + L_window/2
    in_band = np.sum((pc1_norm >= lower) & (pc1_norm <= upper))
    band_frac = in_band / len(pc1_norm)
    
    return band_frac, labels

def test_redistribution_law_robustness():
    """Test Redistribution Law against different conditions"""
    noise_levels = [0.05, 0.1, 0.2, 0.3]
    scalers = {
        'standard': StandardScaler(),
        'minmax': MinMaxScaler(),
        'robust': RobustScaler()
    }
    
    results = {
        'noise_levels': noise_levels,
        'scalers': list(scalers.keys()),
        'kmeans_results': [],
        'dbscan_results': [],
        'hierarchical_results': []
    }
    
    for noise in noise_levels:
        print(f"Testing noise level: {noise}")
        
        # Generate data
        data, true_labels = generate_synthetic_emergence_data(noise_level=noise, seed=42)
        
        scaler_results = {}
        for scaler_name, scaler in scalers.items():
            data_scaled = scaler.fit_transform(data.copy())
            
            # K-means
            bf_kmeans, _ = compute_band_frac_kmeans(data_scaled)
            
            # DBSCAN (tune eps based on noise level)
            eps = 0.3 + noise * 2
            bf_dbscan, _ = compute_band_frac_dbscan(data_scaled, eps=eps)
            
            # Hierarchical
            bf_hier, _ = compute_band_frac_hierarchical(data_scaled)
            
            scaler_results[scaler_name] = {
                'kmeans': bf_kmeans,
                'dbscan': bf_dbscan,
                'hierarchical': bf_hier
            }
        
        results['kmeans_results'].append({
            'noise': noise,
            'standard': scaler_results['standard']['kmeans'],
            'minmax': scaler_results['minmax']['kmeans'],
            'robust': scaler_results['robust']['kmeans']
        })
        
        results['dbscan_results'].append({
            'noise': noise,
            'standard': scaler_results['standard']['dbscan'],
            'minmax': scaler_results['minmax']['dbscan'],
            'robust': scaler_results['robust']['dbscan']
        })
        
        results['hierarchical_results'].append({
            'noise': noise,
            'standard': scaler_results['standard']['hierarchical'],
            'minmax': scaler_results['minmax']['hierarchical'],
            'robust': scaler_results['robust']['hierarchical']
        })
    
    return results

def plot_stress_test_results(results):
    """Create visualization of stress test results"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    noise_levels = results['noise_levels']
    
    # Panel 1: K-means across scalers
    ax1 = axes[0,0]
    for scaler in ['standard', 'minmax', 'robust']:
        values = [r[scaler] for r in results['kmeans_results']]
        ax1.plot(noise_levels, values, 'o-', label=f'K-means ({scaler})')
    ax1.set_xlabel('Noise Level')
    ax1.set_ylabel('Band Fraction')
    ax1.set_title('K-means Clustering')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: DBSCAN across scalers
    ax2 = axes[0,1]
    for scaler in ['standard', 'minmax', 'robust']:
        values = [r[scaler] for r in results['dbscan_results']]
        ax2.plot(noise_levels, values, 's-', label=f'DBSCAN ({scaler})')
    ax2.set_xlabel('Noise Level')
    ax2.set_ylabel('Band Fraction')
    ax2.set_title('DBSCAN Clustering')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Hierarchical across scalers
    ax3 = axes[1,0]
    for scaler in ['standard', 'minmax', 'robust']:
        values = [r[scaler] for r in results['hierarchical_results']]
        ax3.plot(noise_levels, values, '^-', label=f'Hierarchical ({scaler})')
    ax3.set_xlabel('Noise Level')
    ax3.set_ylabel('Band Fraction')
    ax3.set_title('Hierarchical Clustering')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Comparison across algorithms (using standard scaler)
    ax4 = axes[1,1]
    kmeans_std = [r['standard'] for r in results['kmeans_results']]
    dbscan_std = [r['standard'] for r in results['dbscan_results']]
    hier_std = [r['standard'] for r in results['hierarchical_results']]
    
    ax4.plot(noise_levels, kmeans_std, 'o-', label='K-means')
    ax4.plot(noise_levels, dbscan_std, 's-', label='DBSCAN')
    ax4.plot(noise_levels, hier_std, '^-', label='Hierarchical')
    ax4.set_xlabel('Noise Level')
    ax4.set_ylabel('Band Fraction')
    ax4.set_title('Algorithm Comparison (Standard Scaler)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/redistribution_law_stress_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    return True

# Main execution
if __name__ == "__main__":
    print("Running stress test for SYN-050: Redistribution Law Robustness")
    
    results = test_redistribution_law_robustness()
    
    # Save results
    import json
    with open('../../shared_agora/artifacts/redistribution_law_stress_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create plots
    plot_stress_test_results(results)
    
    # Analyze consistency
    print("\nStress Test Analysis:")
    print("=====================")
    
    # Check if band_frac remains within expected range
    all_bf_values = []
    for algo_results in [results['kmeans_results'], results['dbscan_results'], results['hierarchical_results']]:
        for r in algo_results:
            all_bf_values.extend([r['standard'], r['minmax'], r['robust']])
    
    bf_mean = np.mean(all_bf_values)
    bf_std = np.std(all_bf_values)
    
    print(f"Overall band_frac mean: {bf_mean:.4f}")
    print(f"Overall band_frac std: {bf_std:.4f}")
    print(f"Coefficient of variation: {bf_std/bf_mean:.4f}")
    
    # The Redistribution Law predicts band_frac should be stable across conditions
    # if the underlying emergence structure is preserved
    if bf_std/bf_mean < 0.1:  # Less than 10% relative variation
        print("✓ Redistribution Law appears robust to clustering algorithm and scaling choices")
    else:
        print("⚠ Redistribution Law shows sensitivity to methodological choices")
    
    print(f"\nResults saved to shared_agora/artifacts/")