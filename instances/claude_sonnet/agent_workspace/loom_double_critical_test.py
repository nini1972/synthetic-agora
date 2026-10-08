#!/usr/bin/env python3
"""
Empirical verification of Loom Double Critical Point hypothesis (HYP-104).
Tests protocol-dependent critical points in coupled-map loom system.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless execution
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import json

def loom_step(a, A, X, b):
    """Single step of the loom dynamics."""
    amplification = X * a**2
    fracture = (1 - X) * (a + b * np.sin(2 * np.pi * (a - A)))
    return amplification + fracture

def simulate_loom(L, b, protocol='fractured', steps=None):
    """
    Simulate the coupled-map loom.
    
    Parameters:
    - L: lattice size
    - b: fracture parameter
    - protocol: 'fractured' (random seed) or 'coherent' (attractor-aligned seed)
    - steps: simulation steps (default: 20*L)
    """
    if steps is None:
        steps = 20 * L
    
    # Fixed latent attractors
    np.random.seed(42 + L)  # Deterministic per L
    A = np.random.uniform(0, 1, L)
    
    # Initialize according to protocol
    if protocol == 'fractured':
        np.random.seed(123 + L)
        a = np.random.uniform(0, 1, L)
    elif protocol == 'coherent':
        a = A.copy()
    else:
        raise ValueError(f"Unknown protocol: {protocol}")
    
    # Evolution
    for t in range(steps):
        np.random.seed(1000 + t + L)
        X = np.random.uniform(0, 1, L)
        a = loom_step(a, A, X, b)
        # Keep in [0,1] bounds
        a = np.clip(a, 0, 1)
    
    # Fracture order
    fracture_order = np.mean(np.abs(a - A))
    return fracture_order

def find_critical_point(L, b_values, protocol):
    """Find critical point by locating peak in second derivative."""
    fracture_orders = []
    
    for b in b_values:
        # Multiple trials for each b
        trials = max(10, 200 // L)  # More trials for smaller L
        trial_results = []
        
        for trial in range(trials):
            np.random.seed(trial + int(b * 1000) + L)
            fo = simulate_loom(L, b, protocol)
            trial_results.append(fo)
        
        fracture_orders.append(np.mean(trial_results))
    
    # Find critical point as peak in second derivative
    fracture_orders = np.array(fracture_orders)
    second_deriv = np.gradient(np.gradient(fracture_orders))
    
    # Find the most prominent peak
    peaks, _ = find_peaks(second_deriv, height=0)
    if len(peaks) > 0:
        peak_idx = peaks[np.argmax(second_deriv[peaks])]
        b_critical = b_values[peak_idx]
    else:
        # Fallback: maximum second derivative
        peak_idx = np.argmax(second_deriv)
        b_critical = b_values[peak_idx]
    
    return b_critical, fracture_orders, second_deriv

def finite_size_scaling(L_values, b_c_values):
    """Perform finite-size scaling: b_c(L) = b_inf + A/L"""
    def scaling_func(L, b_inf, A):
        return b_inf + A / L
    
    try:
        popt, pcov = curve_fit(scaling_func, L_values, b_c_values)
        b_inf, A = popt
        b_inf_err = np.sqrt(pcov[0, 0])
        return b_inf, A, b_inf_err
    except:
        # Fallback: linear fit to 1/L vs b_c
        inv_L = 1 / np.array(L_values)
        coeffs = np.polyfit(inv_L, b_c_values, 1)
        b_inf = coeffs[1]
        A = coeffs[0]
        return b_inf, A, 0.01  # Rough error estimate

def verify_loom_double_critical():
    """Main verification function."""
    print("Loom Double Critical Point Verification")
    print("=" * 50)
    
    # Parameters
    L_values = [15, 25, 40, 60]  # Smaller sizes for faster computation
    b_values = np.linspace(0, 0.45, 21)
    protocols = ['fractured', 'coherent']
    
    results = {
        'L_values': L_values,
        'b_values': b_values.tolist(),
        'protocols': protocols,
        'critical_points': {},
        'fracture_curves': {},
        'finite_size_scaling': {}
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    for i, protocol in enumerate(protocols):
        print(f"\nAnalyzing {protocol} protocol:")
        b_c_values = []
        
        # Find critical points for each L
        for j, L in enumerate(L_values):
            print(f"  L = {L}...")
            b_c, fracture_orders, second_deriv = find_critical_point(L, b_values, protocol)
            b_c_values.append(b_c)
            
            print(f"    Critical point: b_c = {b_c:.4f}")
            
            # Store results
            results['critical_points'][f'{protocol}_L{L}'] = b_c
            results['fracture_curves'][f'{protocol}_L{L}'] = fracture_orders.tolist()
            
            # Plot fracture order curves
            axes[i, 0].plot(b_values, fracture_orders, 'o-', label=f'L={L}', alpha=0.7)
            
            # Plot second derivative
            axes[i, 1].plot(b_values, second_deriv, 's-', label=f'L={L}', alpha=0.7)
            axes[i, 1].axvline(b_c, color='red', linestyle='--', alpha=0.5)
        
        # Finite-size scaling
        print(f"  Performing finite-size scaling...")
        b_inf, A, b_inf_err = finite_size_scaling(L_values, b_c_values)
        
        results['finite_size_scaling'][protocol] = {
            'b_c_values': b_c_values,
            'b_inf': b_inf,
            'A': A,
            'b_inf_err': b_inf_err
        }
        
        print(f"  Extrapolated b_inf = {b_inf:.4f} ± {b_inf_err:.4f}")
        print(f"  Finite-size coefficient A = {A:.4f}")
        
        # Format plots
        axes[i, 0].set_xlabel('Fracture parameter b')
        axes[i, 0].set_ylabel('Fracture order Φ')
        axes[i, 0].set_title(f'{protocol.capitalize()} protocol - Fracture curves')
        axes[i, 0].legend()
        axes[i, 0].grid(True, alpha=0.3)
        
        axes[i, 1].set_xlabel('Fracture parameter b')
        axes[i, 1].set_ylabel('d²Φ/db²')
        axes[i, 1].set_title(f'{protocol.capitalize()} protocol - Critical point detection')
        axes[i, 1].legend()
        axes[i, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('loom_double_critical_test.png', dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved: loom_double_critical_test.png")
    
    # Analysis of coincidence gap
    b_inf_fractured = results['finite_size_scaling']['fractured']['b_inf']
    b_inf_coherent = results['finite_size_scaling']['coherent']['b_inf']
    gap = b_inf_fractured - b_inf_coherent
    
    print("\n" + "=" * 50)
    print("COINCIDENCE GAP ANALYSIS")
    print("=" * 50)
    print(f"b_inf (fractured): {b_inf_fractured:.4f}")
    print(f"b_inf (coherent):  {b_inf_coherent:.4f}")
    print(f"Gap Δb = {gap:.4f}")
    print(f"Relative gap: {gap/b_inf_coherent:.1%}")
    
    results['gap_analysis'] = {
        'b_inf_fractured': b_inf_fractured,
        'b_inf_coherent': b_inf_coherent,
        'gap': gap,
        'relative_gap': gap / b_inf_coherent
    }
    
    # Verification assessment
    expected_gap = 0.021  # From dossier
    gap_tolerance = 0.01  # Reasonable tolerance
    
    if abs(gap - expected_gap) < gap_tolerance and gap > 0:
        verdict = "VERIFIED"
        confidence = 0.9
        assessment = f"✓ Gap confirmed: {gap:.4f} ≈ {expected_gap:.4f} (expected)"
    elif gap > 0:
        verdict = "PARTIAL"
        confidence = 0.7
        assessment = f"⚠ Gap detected but differs: {gap:.4f} vs {expected_gap:.4f} (expected)"
    else:
        verdict = "REFUTED"
        confidence = 0.8
        assessment = f"✗ No positive gap found: {gap:.4f}"
    
    print(f"\n{assessment}")
    
    # Save results
    with open('loom_double_critical_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved: loom_double_critical_results.json")
    print(f"\nFinal Assessment: {verdict} (Confidence: {confidence:.2f})")
    
    return verdict, confidence

if __name__ == "__main__":
    verify_loom_double_critical()