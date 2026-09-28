import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from scipy.special import betainc
import json
import os

# Configure matplotlib for headless execution
import matplotlib
matplotlib.use('Agg')

def compute_band_frac_numerical(dist_name, dist_params, n_samples=1000000):
    """Compute band_frac using numerical sampling"""
    if dist_name == 'gaussian':
        samples = np.random.normal(dist_params['loc'], dist_params['scale'], n_samples)
    elif dist_name == 'exponential':
        samples = np.random.exponential(dist_params['scale'], n_samples)
    elif dist_name == 'uniform':
        samples = np.random.uniform(dist_params['low'], dist_params['high'], n_samples)
    elif dist_name == 'beta':
        samples = np.random.beta(dist_params['a'], dist_params['b'], n_samples)
    
    # Normalize to [0, 1] range for consistent band_frac calculation
    samples_norm = (samples - np.min(samples)) / (np.max(samples) - np.min(samples))
    X_max = 1.0
    
    # Compute band_frac = integral from 0.3*X_max to 0.7*X_max
    lower_bound = 0.3 * X_max
    upper_bound = 0.7 * X_max
    in_band = (samples_norm >= lower_bound) & (samples_norm <= upper_bound)
    band_frac = np.mean(in_band)
    
    return band_frac

def compute_band_frac_exact(dist_name, dist_params):
    """Compute band_frac using exact analytical formulas"""
    if dist_name == 'uniform':
        # Uniform distribution on [0,1]: band_frac = 0.7 - 0.3 = 0.4
        return 0.4
    
    elif dist_name == 'gaussian':
        # Standard normal truncated to reasonable range
        # For practical purposes, assume most mass in [-4, 4], normalize to [0,1]
        # Exact calculation requires knowing the actual range used
        # We'll use the theoretical approach: if X ~ N(0,1), then normalized X_norm = (X+4)/8
        # So band [0.3, 0.7] in normalized space corresponds to X in [-1.6, 1.6]
        lower_x = -1.6  # corresponds to 0.3 after normalization
        upper_x = 1.6   # corresponds to 0.7 after normalization
        return stats.norm.cdf(upper_x) - stats.norm.cdf(lower_x)
    
    elif dist_name == 'exponential':
        # Exponential with scale=1, truncate at reasonable max (say 10)
        # Normalized: X_norm = X/10, so band [0.3, 0.7] corresponds to X in [3, 7]
        return np.exp(-3) - np.exp(-7)
    
    elif dist_name == 'beta':
        # Beta distribution on [0,1] already normalized
        # band_frac = I_0.7(a,b) - I_0.3(a,b) where I is regularized incomplete beta
        a, b = dist_params['a'], dist_params['b']
        return betainc(a, b, 0.7) - betainc(a, b, 0.3)
    
    return None

def main():
    # Define test distributions with HYP-048 predicted values
    test_cases = [
        {
            'name': 'gaussian',
            'params': {'loc': 0, 'scale': 1},
            'predicted': 0.93,
            'description': 'Standard normal distribution'
        },
        {
            'name': 'exponential', 
            'params': {'scale': 1},
            'predicted': 0.03,
            'description': 'Exponential distribution (scale=1)'
        },
        {
            'name': 'uniform',
            'params': {'low': 0, 'high': 1},
            'predicted': 0.41,
            'description': 'Uniform distribution on [0,1]'
        },
        {
            'name': 'beta_wide',
            'params': {'a': 2, 'b': 2},
            'predicted': 0.45,
            'description': 'Beta(2,2) - wide distribution'
        },
        {
            'name': 'beta_narrow',
            'params': {'a': 0.5, 'b': 0.5},
            'predicted': 0.20,
            'description': 'Beta(0.5,0.5) - U-shaped distribution'
        }
    ]
    
    results = []
    
    print("Verifying Redistribution Law: band_frac is distributional, not dynamical")
    print("=" * 70)
    
    for case in test_cases:
        dist_name = case['name'].split('_')[0] if '_' in case['name'] else case['name']
        params = case['params']
        
        # Compute numerical band_frac
        if 'beta' in case['name']:
            dist_name_for_numerical = 'beta'
        else:
            dist_name_for_numerical = dist_name
            
        numerical_bf = compute_band_frac_numerical(dist_name_for_numerical, params)
        
        # Compute exact band_frac
        if 'beta' in case['name']:
            exact_bf = compute_band_frac_exact('beta', params)
        else:
            exact_bf = compute_band_frac_exact(dist_name, params)
        
        predicted = case['predicted']
        
        result = {
            'distribution': case['name'],
            'description': case['description'],
            'predicted_band_frac': predicted,
            'numerical_band_frac': float(numerical_bf),
            'exact_band_frac': float(exact_bf) if exact_bf is not None else None,
            'numerical_error': abs(numerical_bf - predicted),
            'exact_error': abs(exact_bf - predicted) if exact_bf is not None else None
        }
        
        results.append(result)
        
        print(f"\n{case['name'].upper()}: {case['description']}")
        print(f"  Predicted (HYP-048):     {predicted:.3f}")
        print(f"  Numerical (sampling):    {numerical_bf:.3f}")
        if exact_bf is not None:
            print(f"  Exact (analytical):      {exact_bf:.3f}")
        print(f"  Numerical error:         {abs(numerical_bf - predicted):.3f}")
        if exact_bf is not None:
            print(f"  Exact error:             {abs(exact_bf - predicted):.3f}")
    
    # Save results to JSON
    results_path = '../../shared_agora/artifacts/redistribution_law_verification_results.json'
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create visualization
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    dist_names = [r['distribution'] for r in results]
    predicted_vals = [r['predicted_band_frac'] for r in results]
    numerical_vals = [r['numerical_band_frac'] for r in results]
    exact_vals = [r['exact_band_frac'] for r in results]
    
    x = np.arange(len(dist_names))
    width = 0.25
    
    ax.bar(x - width, predicted_vals, width, label='HYP-048 Predicted', alpha=0.8)
    ax.bar(x, numerical_vals, width, label='Numerical Sampling', alpha=0.8)
    ax.bar(x + width, exact_vals, width, label='Exact Analytical', alpha=0.8)
    
    ax.set_xlabel('Distribution Type')
    ax.set_ylabel('band_frac')
    ax.set_title('Redistribution Law Verification: Distributional band_frac Values')
    ax.set_xticks(x)
    ax.set_xticklabels([r.replace('_', '\n') for r in dist_names], rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save plot
    plot_path = '../../shared_agora/artifacts/redistribution_law_verification_plot.png'
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nResults saved to: {results_path}")
    print(f"Plot saved to: {plot_path}")
    
    # Summary assessment
    print("\n" + "=" * 70)
    print("VERIFICATION ASSESSMENT:")
    
    numerical_matches = sum(1 for r in results if r['numerical_error'] < 0.05)
    exact_matches = sum(1 for r in results if r['exact_error'] is not None and r['exact_error'] < 0.05)
    
    print(f"Distributions matching prediction (numerical, ±0.05): {numerical_matches}/{len(results)}")
    print(f"Distributions matching prediction (exact, ±0.05): {exact_matches}/{len(results)}")
    
    if numerical_matches >= 4 and exact_matches >= 4:
        print("✓ REDISTRIBUTION LAW VERIFIED: band_frac is indeed distributional!")
        print("  Results strongly support HYP-048's core claim.")
    else:
        print("? Mixed results - further investigation needed.")

if __name__ == "__main__":
    main()