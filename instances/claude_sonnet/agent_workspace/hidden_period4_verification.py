"""
Empirical Verification of HYP-102: Hidden Period-4 Structures in Coupled Logistic Map Lattices
Testing symbolic motif analysis approach from Frontier dossier DOSSIER-105
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from scipy.stats import describe

def coupled_logistic_lattice(N, r, epsilon, steps, x0=None):
    """
    Simulate 1D coupled logistic map lattice with periodic boundary conditions
    
    x_i^{t+1} = (1-ε)f(x_i^t) + (ε/2)[f(x_{i-1}^t) + f(x_{i+1}^t)]
    where f(x) = rx(1-x)
    """
    if x0 is None:
        x0 = np.random.random(N)
    
    trajectory = np.zeros((steps, N))
    trajectory[0] = x0
    
    for t in range(1, steps):
        x_curr = trajectory[t-1]
        
        # Apply logistic map
        f_x = r * x_curr * (1 - x_curr)
        
        # Couple with neighbors (periodic boundary)
        f_left = np.roll(f_x, 1)  # f(x_{i-1})
        f_right = np.roll(f_x, -1)  # f(x_{i+1})
        
        # Update rule
        trajectory[t] = (1 - epsilon) * f_x + (epsilon / 2) * (f_left + f_right)
    
    return trajectory

def symbolic_motif_analysis(time_series, motif_width=4, max_lag=50):
    """
    Convert time series to binary motifs and compute lag consistency
    """
    # Convert to binary based on median threshold
    median_val = np.median(time_series)
    binary_series = (time_series > median_val).astype(int)
    
    # Generate motifs
    motifs = []
    for i in range(len(binary_series) - motif_width + 1):
        motif = tuple(binary_series[i:i+motif_width])
        motifs.append(motif)
    
    # Compute lag consistency
    lag_consistency = []
    
    for lag in range(1, max_lag + 1):
        if lag >= len(motifs):
            break
            
        # Count matching motifs at this lag
        matches = 0
        comparisons = len(motifs) - lag
        
        for i in range(comparisons):
            if motifs[i] == motifs[i + lag]:
                matches += 1
        
        consistency = matches / comparisons if comparisons > 0 else 0
        lag_consistency.append(consistency)
    
    return np.array(lag_consistency), motifs

def period4_residue_analysis(lag_consistency):
    """
    Analyze lag consistency by period-4 residues
    """
    lags = np.arange(1, len(lag_consistency) + 1)
    
    # Group by residue mod 4
    residues = {}
    for r in range(4):
        mask = (lags % 4) == r
        if np.any(mask):
            residues[r] = lag_consistency[mask]
    
    # Compute statistics for each residue
    residue_stats = {}
    for r, values in residues.items():
        if len(values) > 0:
            residue_stats[r] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'count': len(values),
                'values': values
            }
    
    return residue_stats

def verify_hidden_period4():
    """
    Independent verification of hidden period-4 structure claim
    """
    print("Hidden Period-4 Structure Verification")
    print("=" * 50)
    
    # Parameters from DOSSIER-105
    r = 3.865
    epsilon = 0.132
    N = 100  # Lattice size
    steps = 5000  # Time steps
    
    print(f"System parameters:")
    print(f"  r (logistic parameter): {r}")
    print(f"  ε (coupling strength): {epsilon}")
    print(f"  N (lattice sites): {N}")
    print(f"  steps: {steps}")
    
    # Generate coupled logistic lattice trajectory
    print(f"\nGenerating coupled logistic lattice trajectory...")
    np.random.seed(42)  # For reproducibility
    trajectory = coupled_logistic_lattice(N, r, epsilon, steps)
    
    # Analyze middle site (avoid boundary effects)
    middle_site = N // 2
    time_series = trajectory[:, middle_site]
    
    print(f"Analyzing site {middle_site} time series...")
    print(f"  Value range: [{np.min(time_series):.3f}, {np.max(time_series):.3f}]")
    print(f"  Mean: {np.mean(time_series):.3f}")
    print(f"  Std: {np.std(time_series):.3f}")
    
    # Check for chaos (approximate Lyapunov exponent)
    print(f"\nChaos verification:")
    
    # Slightly perturbed initial condition
    x0_pert = np.random.random(N)
    x0_pert += 1e-8 * np.random.random(N)  # Small perturbation
    
    traj_pert = coupled_logistic_lattice(N, r, epsilon, min(1000, steps), x0_pert)
    
    if steps >= 1000:
        separation = np.abs(trajectory[:1000, middle_site] - traj_pert[:1000, middle_site])
        
        # Look for exponential growth
        growth_start = 50
        growth_end = 200
        
        if growth_end < len(separation):
            growth_region = separation[growth_start:growth_end]
            time_region = np.arange(growth_end - growth_start)
            
            # Fit exponential growth
            valid_mask = growth_region > 1e-12
            if np.sum(valid_mask) > 10:
                log_sep = np.log(growth_region[valid_mask])
                t_valid = time_region[valid_mask]
                
                if len(t_valid) > 5:
                    coeffs = np.polyfit(t_valid, log_sep, 1)
                    lyap_est = coeffs[0]
                    print(f"  Lyapunov exponent estimate: {lyap_est:.4f}")
                    chaos_detected = lyap_est > 0.01
                else:
                    chaos_detected = False
            else:
                chaos_detected = False
        else:
            chaos_detected = False
    else:
        chaos_detected = False
    
    print(f"  Chaotic behavior: {'✓' if chaos_detected else '?'}")
    
    # Symbolic motif analysis
    print(f"\nSymbolic motif analysis:")
    
    # Skip initial transient
    transient = 500
    analysis_series = time_series[transient:]
    
    print(f"  Using {len(analysis_series)} time points after transient removal")
    
    # Compute lag consistency
    lag_consistency, motifs = symbolic_motif_analysis(analysis_series, motif_width=4, max_lag=50)
    
    print(f"  Generated {len(motifs)} motifs of width 4")
    print(f"  Computing consistency for {len(lag_consistency)} lags")
    
    # Period-4 residue analysis
    residue_stats = period4_residue_analysis(lag_consistency)
    
    print(f"\nPeriod-4 residue analysis:")
    for r in sorted(residue_stats.keys()):
        stats = residue_stats[r]
        print(f"  Residue {r} (lags ≡ {r} mod 4): mean = {stats['mean']:.4f} ± {stats['std']:.4f} (n={stats['count']})")
    
    # Compute period-4 parity contrast (even vs odd lags)
    even_lags = lag_consistency[::2]  # lags 2, 4, 6, ...
    odd_lags = lag_consistency[1::2]  # lags 1, 3, 5, ...
    
    even_mean = np.mean(even_lags)
    odd_mean = np.mean(odd_lags)
    
    parity_contrast = (even_mean - odd_mean) / (even_mean + odd_mean) if (even_mean + odd_mean) > 0 else 0
    
    print(f"\nParity analysis:")
    print(f"  Even lags mean: {even_mean:.4f}")
    print(f"  Odd lags mean: {odd_mean:.4f}")
    print(f"  Parity contrast: {parity_contrast:.4f}")
    
    # Specific period-4 signal detection
    # Check residues 0 and 2 (even) vs residues 1 and 3 (odd)
    if 0 in residue_stats and 2 in residue_stats and 1 in residue_stats and 3 in residue_stats:
        even_residues = np.concatenate([residue_stats[0]['values'], residue_stats[2]['values']])
        odd_residues = np.concatenate([residue_stats[1]['values'], residue_stats[3]['values']])
        
        even_res_mean = np.mean(even_residues)
        odd_res_mean = np.mean(odd_residues)
        
        residue_contrast = (even_res_mean - odd_res_mean) / (even_res_mean + odd_res_mean) if (even_res_mean + odd_res_mean) > 0 else 0
        
        print(f"  Even residues (0,2) mean: {even_res_mean:.4f}")
        print(f"  Odd residues (1,3) mean: {odd_res_mean:.4f}") 
        print(f"  Residue contrast: {residue_contrast:.4f}")
        
        period4_detected = residue_contrast > 0.3  # Significant contrast threshold
    else:
        period4_detected = False
        residue_contrast = 0.0
    
    # Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Time series
    t_plot = np.arange(len(analysis_series[:1000]))
    ax1.plot(t_plot, analysis_series[:1000], 'b-', linewidth=0.8)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('x(t)')
    ax1.set_title('Chaotic Time Series (Site 50)', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Lag consistency
    lags = np.arange(1, len(lag_consistency) + 1)
    ax2.plot(lags, lag_consistency, 'ko-', markersize=4, linewidth=1)
    ax2.set_xlabel('Lag')
    ax2.set_ylabel('Motif Consistency')
    ax2.set_title('Lag Consistency Analysis', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Residue comparison
    if residue_stats:
        residues = []
        means = []
        stds = []
        for r in sorted(residue_stats.keys()):
            residues.append(r)
            means.append(residue_stats[r]['mean'])
            stds.append(residue_stats[r]['std'])
        
        ax3.errorbar(residues, means, yerr=stds, fmt='o-', capsize=5, linewidth=2, markersize=8)
        ax3.set_xlabel('Lag Residue (mod 4)')
        ax3.set_ylabel('Mean Consistency')
        ax3.set_title('Period-4 Residue Analysis', fontweight='bold')
        ax3.set_xticks(residues)
        ax3.grid(True, alpha=0.3)
    
    # Binary motif pattern
    binary_series = (analysis_series > np.median(analysis_series)).astype(int)
    ax4.plot(binary_series[:200], 'k-', linewidth=2)
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Binary State')
    ax4.set_title('Binary Symbolic Encoding', fontweight='bold')
    ax4.set_ylim(-0.1, 1.1)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hidden_period4_verification.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nVisualization saved: hidden_period4_verification.png")
    
    # Assessment
    print(f"\n" + "="*50)
    print(f"VERIFICATION ASSESSMENT")
    print(f"="*50)
    
    # Claims from dossier to verify:
    # 1. Residue 0: mean ≈ 0.931 ± 0.006
    # 2. Residue 2: mean ≈ 0.728 ± 0.004
    # 3. Residues 1,3: mean ≈ 0.0015 (random level)
    # 4. Parity contrast ≈ 0.828
    
    verification_success = False
    
    if 0 in residue_stats and 2 in residue_stats:
        res0_close = 0.8 < residue_stats[0]['mean'] < 0.98  # Allow some variation
        res2_close = 0.6 < residue_stats[2]['mean'] < 0.85
        
        if 1 in residue_stats and 3 in residue_stats:
            res1_low = residue_stats[1]['mean'] < 0.1
            res3_low = residue_stats[3]['mean'] < 0.1
            
            verification_success = res0_close and res2_close and res1_low and res3_low and period4_detected
        else:
            verification_success = res0_close and res2_close and period4_detected
    
    if verification_success:
        print(f"✓ HIDDEN PERIOD-4 STRUCTURE CONFIRMED")
        print(f"  - Even residues show high consistency")
        print(f"  - Odd residues show low (random) consistency") 
        print(f"  - Strong residue contrast detected: {residue_contrast:.3f}")
        verdict = "CONFIRMED"
        confidence = 0.9
    elif period4_detected:
        print(f"⚠ PARTIAL PERIOD-4 STRUCTURE DETECTED")
        print(f"  - Some period-4 signal present but weaker than claimed")
        print(f"  - Residue contrast: {residue_contrast:.3f}")
        verdict = "PARTIAL"
        confidence = 0.7
    else:
        print(f"✗ NO SIGNIFICANT PERIOD-4 STRUCTURE DETECTED")
        print(f"  - Residue patterns do not match claims")
        print(f"  - Contrast too weak: {residue_contrast:.3f}")
        verdict = "NOT_CONFIRMED"
        confidence = 0.8
    
    # Save results
    results = {
        'system_parameters': {'r': r, 'epsilon': epsilon, 'N': N, 'steps': steps},
        'chaos_analysis': {'lyapunov_detected': bool(chaos_detected)},
        'motif_analysis': {
            'num_motifs': len(motifs),
            'num_lags': len(lag_consistency)
        },
        'residue_analysis': {r: {
            'mean': float(stats['mean']),
            'std': float(stats['std']),
            'count': int(stats['count'])
        } for r, stats in residue_stats.items()},
        'parity_analysis': {
            'even_mean': float(even_mean),
            'odd_mean': float(odd_mean), 
            'parity_contrast': float(parity_contrast)
        },
        'period4_analysis': {
            'detected': bool(period4_detected),
            'residue_contrast': float(residue_contrast),
            'verdict': verdict,
            'confidence': confidence
        }
    }
    
    with open('hidden_period4_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved: hidden_period4_results.json")
    
    return verdict, confidence

if __name__ == "__main__":
    try:
        verdict, conf = verify_hidden_period4()
        print(f"\nFinal Assessment: {verdict} (Confidence: {conf:.2f})")
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()