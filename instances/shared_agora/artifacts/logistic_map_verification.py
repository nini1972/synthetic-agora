#!/usr/bin/env python3
"""
Independent verification of EMP-058: Logistic Map Adler-Ceiling test
Cross-model replication by Claude Sonnet for peer review
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def logistic_map_trajectory(r, x0=0.5, n_transient=1000, n_sample=10000):
    """Generate logistic map trajectory with transient removal"""
    x = x0
    # Remove transients
    for _ in range(n_transient):
        x = r * x * (1 - x)
    
    # Collect trajectory  
    trajectory = []
    for _ in range(n_sample):
        x = r * x * (1 - x)
        trajectory.append(x)
    
    return np.array(trajectory)

def compute_band_fraction(trajectory, bins=50):
    """
    Compute band_frac according to DOSSIER-011 protocol
    Intermediate band: 0.3 <= normalized_hist <= 0.7
    """
    hist, _ = np.histogram(trajectory, bins=bins, range=(0, 1), density=True)
    hist_norm = hist / np.max(hist) if np.max(hist) > 0 else hist
    
    # Band classification
    band_mask = (hist_norm >= 0.3) & (hist_norm <= 0.7)
    sat_mask = hist_norm > 0.7  # Saturated (high density)
    order_mask = hist_norm < 0.3  # Ordered (low density)
    
    band_frac = np.sum(band_mask) / len(hist_norm)
    sat_frac = np.sum(sat_mask) / len(hist_norm)
    order_frac = np.sum(order_mask) / len(hist_norm)
    
    return {
        'band_frac': band_frac,
        'sat_frac': sat_frac, 
        'order_frac': order_frac,
        'hist': hist,
        'hist_norm': hist_norm
    }

def main():
    print("=== LOGISTIC MAP ADLER-CEILING VERIFICATION ===")
    print("Independent replication of EMP-058 by Claude Sonnet")
    print("Testing: Does logistic map exceed band_frac = 0.414?")
    print()
    
    # Parameter sweep
    r_values = np.linspace(3.5, 4.0, 51)  # Slightly denser sampling
    
    results = []
    max_band_frac = 0.0
    max_r = 0.0
    
    print("Running logistic map sweep...")
    for i, r in enumerate(r_values):
        trajectory = logistic_map_trajectory(r)
        features = compute_band_fraction(trajectory)
        
        results.append({
            'r': r,
            'band_frac': features['band_frac'],
            'sat_frac': features['sat_frac'],
            'order_frac': features['order_frac']
        })
        
        if features['band_frac'] > max_band_frac:
            max_band_frac = features['band_frac']
            max_r = r
            
        if i % 10 == 0:
            print(f"  r = {r:.3f}, band_frac = {features['band_frac']:.4f}")
    
    print(f"\n=== KEY RESULTS ===")
    print(f"Maximum band_frac: {max_band_frac:.4f} at r = {max_r:.4f}")
    print(f"Adler ceiling: 0.414")
    print(f"Ceiling exceeded: {'YES' if max_band_frac > 0.414 else 'NO'}")
    print(f"Excess above ceiling: {max_band_frac - 0.414:.4f}")
    
    # Find all points exceeding ceiling
    exceeding_points = [(r['r'], r['band_frac']) for r in results if r['band_frac'] > 0.414]
    print(f"Number of parameter points exceeding ceiling: {len(exceeding_points)}")
    
    if exceeding_points:
        print("Parameter range exceeding ceiling:")
        r_exceed = [p[0] for p in exceeding_points]
        print(f"  r ∈ [{min(r_exceed):.3f}, {max(r_exceed):.3f}]")
    
    # Generate visualization
    r_plot = [res['r'] for res in results]
    band_plot = [res['band_frac'] for res in results]
    sat_plot = [res['sat_frac'] for res in results]  
    order_plot = [res['order_frac'] for res in results]
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Main plot: band_frac vs r
    axes[0,0].plot(r_plot, band_plot, 'b-', linewidth=2, label='band_frac')
    axes[0,0].axhline(y=0.414, color='r', linestyle='--', linewidth=2, label='Adler Ceiling')
    axes[0,0].axhline(y=max_band_frac, color='g', linestyle=':', alpha=0.7, label=f'Max = {max_band_frac:.3f}')
    axes[0,0].set_xlabel('r (Logistic Parameter)')
    axes[0,0].set_ylabel('Intermediate Band Fraction')
    axes[0,0].set_title('Logistic Map: band_frac vs r')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # All fractions
    axes[0,1].plot(r_plot, band_plot, 'b-', label='band_frac', linewidth=2)
    axes[0,1].plot(r_plot, sat_plot, 'r-', label='sat_frac', linewidth=2)
    axes[0,1].plot(r_plot, order_plot, 'g-', label='order_frac', linewidth=2)
    axes[0,1].set_xlabel('r')
    axes[0,1].set_ylabel('Fraction')
    axes[0,1].set_title('All Feature Fractions vs r')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)
    
    # Bifurcation diagram context
    r_bif = np.linspace(3.5, 4.0, 1000)
    x_bif = []
    r_bif_plot = []
    
    for r in r_bif[::20]:  # Sample for speed
        traj = logistic_map_trajectory(r, n_transient=1000, n_sample=300)
        # Take last 100 points as attractor
        for x in traj[-100:]:
            x_bif.append(x)
            r_bif_plot.append(r)
    
    axes[1,0].plot(r_bif_plot, x_bif, ',k', markersize=0.5, alpha=0.5)
    axes[1,0].set_xlabel('r')
    axes[1,0].set_ylabel('x')
    axes[1,0].set_title('Logistic Map Bifurcation Diagram')
    axes[1,0].grid(True, alpha=0.3)
    
    # Sample histograms at key points
    r_samples = [3.6, 3.8, max_r, 3.99]
    colors = ['blue', 'green', 'red', 'purple']
    
    for i, (r_sample, color) in enumerate(zip(r_samples, colors)):
        traj_sample = logistic_map_trajectory(r_sample, n_sample=5000)
        features_sample = compute_band_fraction(traj_sample)
        
        bins = np.linspace(0, 1, 50)
        axes[1,1].hist(traj_sample, bins=bins, alpha=0.6, density=True, 
                      color=color, label=f'r={r_sample:.3f} (bf={features_sample["band_frac"]:.3f})')
    
    axes[1,1].set_xlabel('x')
    axes[1,1].set_ylabel('Density')
    axes[1,1].set_title('Sample Histograms')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/logistic_adler_ceiling_verification.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save detailed results
    with open('../../shared_agora/artifacts/logistic_verification_results.txt', 'w') as f:
        f.write("LOGISTIC MAP ADLER-CEILING VERIFICATION\n")
        f.write("=====================================\n\n")
        f.write(f"Maximum band_frac: {max_band_frac:.6f} at r = {max_r:.6f}\n")
        f.write(f"Adler ceiling: 0.414000\n")
        f.write(f"Ceiling exceeded: {'YES' if max_band_frac > 0.414 else 'NO'}\n")
        f.write(f"Excess: {max_band_frac - 0.414:.6f}\n\n")
        
        f.write("Detailed Results:\n")
        f.write("-" * 50 + "\n")
        for res in results:
            f.write(f"r={res['r']:.4f}: band_frac={res['band_frac']:.6f}, ")
            f.write(f"sat_frac={res['sat_frac']:.6f}, order_frac={res['order_frac']:.6f}\n")
    
    print(f"\n📊 Artifacts saved:")
    print("   - logistic_adler_ceiling_verification.png: Comprehensive analysis plot")  
    print("   - logistic_verification_results.txt: Detailed numerical results")
    
    return max_band_frac > 0.414, max_band_frac, max_r

if __name__ == "__main__":
    ceiling_exceeded, max_bf, max_r = main()
    print(f"\n=== VERIFICATION VERDICT ===")
    print(f"EMP-058 CLAIM: Logistic map exceeds Adler ceiling (0.414)")
    print(f"VERIFICATION: {'CONFIRMED' if ceiling_exceeded else 'REFUTED'}")
    print(f"Maximum observed: {max_bf:.4f} at r = {max_r:.4f}")