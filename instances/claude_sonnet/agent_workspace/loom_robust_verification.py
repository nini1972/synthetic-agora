#!/usr/bin/env python3
"""
Robust verification of Loom Double Critical Point using smoother parameter sweeps
and inflection point detection.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter1d
import json

def loom_step(a, A, X, b):
    """Single step of the loom dynamics with proper bounds."""
    amplification = X * a**2
    fracture = (1 - X) * (a + b * np.sin(2 * np.pi * (a - A)))
    result = amplification + fracture
    return np.clip(result, 0, 1)  # Ensure [0,1] bounds

def simulate_loom_ensemble(L, b, protocol='fractured', steps=None, n_trials=50):
    """
    Simulate loom with ensemble averaging for robustness.
    """
    if steps is None:
        steps = 20 * L
    
    fracture_orders = []
    
    for trial in range(n_trials):
        # Fixed attractors per L (consistent across protocols and trials)
        np.random.seed(42 + L)
        A = np.random.uniform(0, 1, L)
        
        # Protocol-dependent initialization
        if protocol == 'fractured':
            np.random.seed(123 + trial + L)  # Different seed per trial
            a = np.random.uniform(0, 1, L)
        elif protocol == 'coherent':
            a = A.copy()
        
        # Evolution with trial-specific random masks
        for t in range(steps):
            np.random.seed(1000 + t + trial * 10000 + L)
            X = np.random.uniform(0, 1, L)
            a = loom_step(a, A, X, b)
        
        # Compute fracture order
        fo = np.mean(np.abs(a - A))
        fracture_orders.append(fo)
    
    return np.mean(fracture_orders), np.std(fracture_orders)

def smooth_critical_point_detection(b_values, fracture_orders, smoothing_sigma=1.0):
    """
    Detect critical point using smoothed second derivative.
    """
    # Smooth the data
    smooth_fo = gaussian_filter1d(fracture_orders, sigma=smoothing_sigma)
    
    # Compute derivatives
    first_deriv = np.gradient(smooth_fo, b_values)
    second_deriv = np.gradient(first_deriv, b_values)
    
    # Find maximum of second derivative (steepest increase region)
    max_idx = np.argmax(second_deriv)
    b_critical = b_values[max_idx]
    
    return b_critical, smooth_fo, second_deriv

def verify_loom_robust():
    """Robust verification with finer parameter sweeps."""
    print("Robust Loom Double Critical Point Verification")
    print("=" * 55)
    
    # Finer parameter grid
    L_values = [20, 30, 50, 80]
    b_values = np.linspace(0.05, 0.35, 31)  # Focused range from dossier
    protocols = ['fractured', 'coherent']
    
    results = {
        'L_values': L_values,
        'b_values': b_values.tolist(),
        'protocols': protocols,
        'critical_points': {},
        'fracture_curves': {},
        'fracture_errors': {},
        'finite_size_scaling': {}
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    for i, protocol in enumerate(protocols):
        print(f"\nAnalyzing {protocol} protocol:")
        b_c_values = []
        
        # Compute fracture order curves for each L
        for j, L in enumerate(L_values):
            print(f"  L = {L}... ", end='', flush=True)
            
            fracture_means = []
            fracture_errs = []
            
            for b in b_values:
                fo_mean, fo_std = simulate_loom_ensemble(L, b, protocol, n_trials=30)
                fracture_means.append(fo_mean)
                fracture_errs.append(fo_std)
            
            fracture_means = np.array(fracture_means)
            fracture_errs = np.array(fracture_errs)
            
            # Detect critical point
            b_c, smooth_fo, second_deriv = smooth_critical_point_detection(b_values, fracture_means)
            b_c_values.append(b_c)
            
            print(f"b_c = {b_c:.4f}")
            
            # Store results
            results['critical_points'][f'{protocol}_L{L}'] = b_c
            results['fracture_curves'][f'{protocol}_L{L}'] = fracture_means.tolist()
            results['fracture_errors'][f'{protocol}_L{L}'] = fracture_errs.tolist()
            
            # Plot fracture order curves with error bars
            color = plt.cm.viridis(j / len(L_values))
            axes[i, 0].errorbar(b_values, fracture_means, yerr=fracture_errs, 
                              label=f'L={L}', alpha=0.8, color=color, capsize=3)
            axes[i, 0].plot(b_values, smooth_fo, '--', color=color, alpha=0.6)
            
            # Plot second derivative for critical point detection
            axes[i, 1].plot(b_values, second_deriv, 'o-', label=f'L={L}', 
                          color=color, alpha=0.8)
            axes[i, 1].axvline(b_c, color=color, linestyle='--', alpha=0.7)
        
        # Finite-size scaling
        print(f"  Finite-size scaling...")
        
        # Linear fit: b_c(L) = b_inf + A/L
        inv_L = 1.0 / np.array(L_values)
        coeffs = np.polyfit(inv_L, b_c_values, 1)
        b_inf = coeffs[1]
        A = coeffs[0]
        
        # Estimate error from fit residuals
        fit_line = coeffs[1] + coeffs[0] * inv_L
        residuals = np.array(b_c_values) - fit_line
        b_inf_err = np.std(residuals) / np.sqrt(len(L_values))
        
        results['finite_size_scaling'][protocol] = {
            'b_c_values': b_c_values,
            'b_inf': b_inf,
            'A': A,
            'b_inf_err': b_inf_err
        }
        
        print(f"  b_inf = {b_inf:.4f} ± {b_inf_err:.4f}")
        print(f"  A = {A:.3f}")
        
        # Plot finite-size scaling
        L_fine = np.linspace(1/max(L_values), 1/min(L_values), 100)
        fit_curve = b_inf + A * L_fine
        
        # Format plots
        axes[i, 0].set_xlabel('Fracture parameter b')
        axes[i, 0].set_ylabel('Fracture order Φ')
        axes[i, 0].set_title(f'{protocol.capitalize()} protocol - Fracture transitions')
        axes[i, 0].legend()
        axes[i, 0].grid(True, alpha=0.3)
        
        axes[i, 1].set_xlabel('Fracture parameter b')
        axes[i, 1].set_ylabel('d²Φ/db² (smoothed)')
        axes[i, 1].set_title(f'{protocol.capitalize()} protocol - Critical detection')
        axes[i, 1].legend()
        axes[i, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('loom_robust_verification.png', dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved: loom_robust_verification.png")
    
    # Gap analysis
    b_inf_fractured = results['finite_size_scaling']['fractured']['b_inf']
    b_inf_coherent = results['finite_size_scaling']['coherent']['b_inf']
    gap = b_inf_fractured - b_inf_coherent
    
    err_fractured = results['finite_size_scaling']['fractured']['b_inf_err']
    err_coherent = results['finite_size_scaling']['coherent']['b_inf_err']
    gap_uncertainty = np.sqrt(err_fractured**2 + err_coherent**2)
    
    print("\n" + "=" * 55)
    print("COINCIDENCE GAP ANALYSIS")
    print("=" * 55)
    print(f"b_inf (fractured): {b_inf_fractured:.4f} ± {err_fractured:.4f}")
    print(f"b_inf (coherent):  {b_inf_coherent:.4f} ± {err_coherent:.4f}")
    print(f"Gap Δb = {gap:.4f} ± {gap_uncertainty:.4f}")
    print(f"Relative gap: {gap/np.mean([b_inf_fractured, b_inf_coherent]):.1%}")
    
    results['gap_analysis'] = {
        'b_inf_fractured': b_inf_fractured,
        'b_inf_coherent': b_inf_coherent,
        'gap': gap,
        'gap_uncertainty': gap_uncertainty,
        'gap_significance': abs(gap) / gap_uncertainty if gap_uncertainty > 0 else 0
    }
    
    # Assessment
    expected_gap = 0.021  # From dossier: b_inf^fractured > b_inf^coherent
    gap_significance = abs(gap) / gap_uncertainty if gap_uncertainty > 0 else 0
    
    print(f"Gap significance: {gap_significance:.1f}σ")
    
    if gap > 0 and gap_significance > 2.0:  # 2-sigma detection
        if abs(gap - expected_gap) < 0.01:
            verdict = "VERIFIED"
            confidence = 0.95
            assessment = f"✓ Significant positive gap: {gap:.4f} ≈ {expected_gap:.4f} (expected)"
        else:
            verdict = "PARTIAL"
            confidence = 0.8
            assessment = f"⚠ Significant gap but different magnitude: {gap:.4f} vs {expected_gap:.4f}"
    elif gap > 0:
        verdict = "INCONCLUSIVE"
        confidence = 0.6
        assessment = f"? Positive gap detected but low significance: {gap_significance:.1f}σ"
    else:
        verdict = "REFUTED"
        confidence = 0.8
        assessment = f"✗ No positive gap or wrong direction: {gap:.4f}"
    
    print(f"\n{assessment}")
    
    # Save results
    with open('loom_robust_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved: loom_robust_results.json")
    print(f"Final Assessment: {verdict} (Confidence: {confidence:.2f})")
    
    return verdict, confidence

if __name__ == "__main__":
    verify_loom_robust()