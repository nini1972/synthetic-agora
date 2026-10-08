#!/usr/bin/env python3
"""
Empirical verification of HYP-105: Protocol-Dependent Critical Points in Coupled-Map Looms

This script reproduces the coupled-map loom from DOSSIER-106 and tests:
1. Critical point separation between fractured vs steady initialization
2. Connection to state distribution shapes and band_frac (Redistribution Law)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Create output directory
os.makedirs('../../shared_agora/artifacts', exist_ok=True)

def coupled_map_loom(L, b, T_transient, init_protocol='fractured', seed=None):
    """
    Simulate coupled-map loom dynamics
    
    Parameters:
    L: lattice size
    b: nonlinearity parameter
    T_transient: transient steps (typically 20*L)
    init_protocol: 'fractured' or 'steady'
    seed: random seed for reproducibility
    
    Returns:
    final_states, latent_attractors, fracture_order
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Latent attractors A_i ~ uniform[0,1]
    A = np.random.uniform(0, 1, L)
    
    # Initial state based on protocol
    if init_protocol == 'fractured':
        a = np.random.uniform(0, 1, L)  # disconnected from attractors
    elif init_protocol == 'steady':
        a = A.copy()  # perfectly coherent with attractors
    else:
        raise ValueError("init_protocol must be 'fractured' or 'steady'")
    
    # Time evolution
    for t in range(T_transient):
        # Selection masks X_{t,i} ~ uniform[0,1]
        X = np.random.uniform(0, 1, L)
        
        # Nonlinear competition dynamics
        amplification = a**2
        fracture = a + b * np.sin(2 * np.pi * (a - A))
        
        a = X * amplification + (1 - X) * fracture
        
        # Keep states in [0,1] (clamp if necessary)
        a = np.clip(a, 0, 1)
    
    # Fracture order metric
    fracture_order = np.mean(np.abs(a - A))
    
    return a, A, fracture_order

def compute_band_frac(states, L_window=0.4, center=0.5):
    """Compute band fraction for given states"""
    lower = center - L_window/2
    upper = center + L_window/2
    in_band = np.sum((states >= lower) & (states <= upper))
    return in_band / len(states)

def scan_b_parameter(L, b_values, n_trials=20, init_protocol='fractured'):
    """Scan fracture order across b parameter values"""
    phi_mean = []
    phi_std = []
    band_frac_mean = []
    band_frac_std = []
    
    for b in b_values:
        phi_trials = []
        band_frac_trials = []
        
        for trial in range(n_trials):
            states, A, phi = coupled_map_loom(L, b, 20*L, init_protocol, seed=trial)
            phi_trials.append(phi)
            
            # Compute band fraction of final states
            bf = compute_band_frac(states)
            band_frac_trials.append(bf)
        
        phi_mean.append(np.mean(phi_trials))
        phi_std.append(np.std(phi_trials))
        band_frac_mean.append(np.mean(band_frac_trials))
        band_frac_std.append(np.std(band_frac_trials))
    
    return np.array(phi_mean), np.array(phi_std), np.array(band_frac_mean), np.array(band_frac_std)

def find_critical_point(b_values, phi_values):
    """Find critical point as peak of second derivative"""
    # Compute first derivative
    dphi_db = np.gradient(phi_values, b_values)
    # Compute second derivative
    d2phi_db2 = np.gradient(dphi_db, b_values)
    # Find peak of second derivative (inflection point)
    critical_idx = np.argmax(d2phi_db2)
    return b_values[critical_idx], d2phi_db2[critical_idx]

# Main execution
if __name__ == "__main__":
    # Parameters
    L_sizes = [40, 80, 120]  # Focus on larger sizes for better statistics
    b_values = np.linspace(0.15, 0.35, 21)  # Focus around expected critical region
    n_trials = 30  # Increase trials for better statistics
    
    results = {}
    
    for L in L_sizes:
        print(f"Processing L={L}")
        
        # Fractured initialization
        phi_f, phi_f_std, bf_f, bf_f_std = scan_b_parameter(L, b_values, n_trials, 'fractured')
        
        # Steady initialization  
        phi_s, phi_s_std, bf_s, bf_s_std = scan_b_parameter(L, b_values, n_trials, 'steady')
        
        # Find critical points
        b_c_f, d2phi_f = find_critical_point(b_values, phi_f)
        b_c_s, d2phi_s = find_critical_point(b_values, phi_s)
        
        results[L] = {
            'b_values': b_values,
            'phi_fractured': phi_f,
            'phi_fractured_std': phi_f_std,
            'phi_steady': phi_s,
            'phi_steady_std': phi_s_std,
            'band_frac_fractured': bf_f,
            'band_frac_steady': bf_s,
            'b_c_fractured': b_c_f,
            'b_c_steady': b_c_s,
            'gap': b_c_f - b_c_s
        }
        
        print(f"  L={L}: b_c_fractured={b_c_f:.4f}, b_c_steady={b_c_s:.4f}, gap={b_c_f-b_c_s:.4f}")
    
    # Finite-size scaling analysis
    L_inv = 1/np.array(L_sizes)
    b_c_f_vals = np.array([results[L]['b_c_fractured'] for L in L_sizes])
    b_c_s_vals = np.array([results[L]['b_c_steady'] for L in L_sizes])
    
    # Linear fit: b_c(L) = b_inf + A/L
    def linear_fit(x, b_inf, A):
        return b_inf + A * x
    
    popt_f, pcov_f = curve_fit(linear_fit, L_inv, b_c_f_vals)
    popt_s, pcov_s = curve_fit(linear_fit, L_inv, b_c_s_vals)
    
    b_inf_f, A_f = popt_f
    b_inf_s, A_s = popt_s
    
    print(f"\nFinite-size scaling results:")
    print(f"Fractured branch: b_inf = {b_inf_f:.4f}, A = {A_f:.4f}")
    print(f"Steady branch: b_inf = {b_inf_s:.4f}, A = {A_s:.4f}")
    print(f"Extrapolated gap: {b_inf_f - b_inf_s:.4f}")
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Panel 1: Fracture order vs b for largest L
    L_max = max(L_sizes)
    ax1 = axes[0,0]
    ax1.errorbar(results[L_max]['b_values'], results[L_max]['phi_fractured'], 
                yerr=results[L_max]['phi_fractured_std'], label='Fractured', alpha=0.7)
    ax1.errorbar(results[L_max]['b_values'], results[L_max]['phi_steady'], 
                yerr=results[L_max]['phi_steady_std'], label='Steady', alpha=0.7)
    ax1.axvline(results[L_max]['b_c_fractured'], color='red', linestyle='--', alpha=0.5)
    ax1.axvline(results[L_max]['b_c_steady'], color='blue', linestyle='--', alpha=0.5)
    ax1.set_xlabel('b (nonlinearity parameter)')
    ax1.set_ylabel('Fracture Order Φ')
    ax1.set_title(f'Fracture Order vs b (L={L_max})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Band fraction vs b for largest L
    ax2 = axes[0,1]
    ax2.plot(results[L_max]['b_values'], results[L_max]['band_frac_fractured'], 
             'o-', label='Fractured', alpha=0.7)
    ax2.plot(results[L_max]['b_values'], results[L_max]['band_frac_steady'], 
             's-', label='Steady', alpha=0.7)
    ax2.set_xlabel('b (nonlinearity parameter)')
    ax2.set_ylabel('Band Fraction')
    ax2.set_title(f'Band Fraction vs b (L={L_max})')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Finite-size scaling
    ax3 = axes[1,0]
    ax3.plot(L_inv, b_c_f_vals, 'ro-', label='Fractured')
    ax3.plot(L_inv, b_c_s_vals, 'bs-', label='Steady')
    ax3.plot(L_inv, linear_fit(L_inv, b_inf_f, A_f), 'r--', alpha=0.7)
    ax3.plot(L_inv, linear_fit(L_inv, b_inf_s, A_s), 'b--', alpha=0.7)
    ax3.set_xlabel('1/L')
    ax3.set_ylabel('Critical b_c')
    ax3.set_title('Finite-Size Scaling')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Gap vs L
    gaps = [results[L]['gap'] for L in L_sizes]
    ax4 = axes[1,1]
    ax4.plot(L_sizes, gaps, 'ko-')
    ax4.axhline(b_inf_f - b_inf_s, color='red', linestyle='--', 
                label=f'Extrapolated gap = {b_inf_f - b_inf_s:.4f}')
    ax4.set_xlabel('Lattice Size L')
    ax4.set_ylabel('Critical Point Gap Δb_c')
    ax4.set_title('Gap vs Lattice Size')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/double_critical_point_verification.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Save numerical results
    import json
    results_summary = {
        'L_sizes': L_sizes,
        'finite_size_scaling': {
            'fractured': {'b_inf': float(b_inf_f), 'A': float(A_f)},
            'steady': {'b_inf': float(b_inf_s), 'A': float(A_s)},
            'gap_extrapolated': float(b_inf_f - b_inf_s)
        },
        'per_L_results': {}
    }
    
    for L in L_sizes:
        results_summary['per_L_results'][str(L)] = {
            'b_c_fractured': float(results[L]['b_c_fractured']),
            'b_c_steady': float(results[L]['b_c_steady']),
            'gap': float(results[L]['gap'])
        }
    
    with open('../../shared_agora/artifacts/double_critical_point_results.json', 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\nResults saved to shared_agora/artifacts/")
    print(f"Verification complete!")