#!/usr/bin/env python3
"""
Empirical Validation of Two-Family Emergence Taxonomy (HYP-020)
Testing whether Thomas Labyrinth and additional substrates follow the predicted family classification

Based on Frontier Dossier #005: Universal Phase-Signature Taxonomy
Original discovery by minimax_m3 in World A Evolution Sandbox
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless mode
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import json

def extract_emergence_features(complexity_trajectory, param_range):
    """
    Extract 7-dimensional archetype feature vector from complexity trajectory
    
    Features:
    - n_phases: number of monotone segments  
    - band_frac: fraction in intermediate band [0.3, 0.7]
    - asc_frac: fraction of ascending phases
    - sat_run: longest saturation run (>0.85) 
    - order_run: longest order run (<0.15)
    - auc: area under normalized curve
    - var_d: variance of derivative (smoothness)
    """
    
    # Normalize trajectory to [0,1]
    traj_norm = (complexity_trajectory - np.min(complexity_trajectory)) / (np.max(complexity_trajectory) - np.min(complexity_trajectory))
    
    # Compute derivative for phase detection
    dtraj = np.diff(traj_norm)
    
    # Count monotone phases
    sign_changes = np.sum(np.diff(np.sign(dtraj)) != 0)
    n_phases = sign_changes + 1
    
    # Band fraction (intermediate complexity)
    band_mask = (traj_norm >= 0.3) & (traj_norm <= 0.7)
    band_frac = np.sum(band_mask) / len(traj_norm)
    
    # Ascending fraction
    asc_mask = dtraj > 0
    asc_frac = np.sum(asc_mask) / len(dtraj) if len(dtraj) > 0 else 0
    
    # Saturation runs (high complexity)
    sat_mask = traj_norm > 0.85
    sat_run = longest_run(sat_mask) / len(traj_norm)
    
    # Order runs (low complexity) 
    order_mask = traj_norm < 0.15
    order_run = longest_run(order_mask) / len(traj_norm)
    
    # Area under curve
    auc = np.trapz(traj_norm) / len(traj_norm)
    
    # Derivative variance (smoothness)
    var_d = np.var(dtraj) if len(dtraj) > 0 else 0
    
    return {
        'n_phases': n_phases,
        'band_frac': band_frac,
        'asc_frac': asc_frac, 
        'sat_run': sat_run,
        'order_run': order_run,
        'auc': auc,
        'var_d': var_d
    }

def longest_run(boolean_array):
    """Find longest consecutive True run in boolean array"""
    if len(boolean_array) == 0:
        return 0
    
    runs = []
    current_run = 0
    
    for val in boolean_array:
        if val:
            current_run += 1
        else:
            if current_run > 0:
                runs.append(current_run)
            current_run = 0
    
    if current_run > 0:
        runs.append(current_run)
    
    return max(runs) if runs else 0

def thomas_attractor(t, state, b=0.208):
    """Thomas attractor system dx/dt = sin(y) - bx, dy/dt = sin(z) - by, dz/dt = sin(x) - bz"""
    x, y, z = state
    return [np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z]

def lempel_ziv_complexity(trajectory, alphabet_size=8):
    """Compute LZ complexity using octant coding"""
    # Convert to octant symbols (0-7)
    x, y, z = trajectory[:, 0], trajectory[:, 1], trajectory[:, 2]
    symbols = ((x > 0).astype(int) * 4 + 
               (y > 0).astype(int) * 2 + 
               (z > 0).astype(int))
    
    # LZ76 algorithm
    complexity = 0
    i = 0
    while i < len(symbols):
        j = i + 1
        while j <= len(symbols):
            substring = symbols[i:j]
            if not appears_before(symbols, substring, i):
                complexity += 1
                i = j
                break
            j += 1
        else:
            # Reached end
            complexity += 1
            break
    
    return complexity / len(symbols)  # Normalize

def appears_before(sequence, pattern, before_index):
    """Check if pattern appears in sequence before given index"""
    pattern_len = len(pattern)
    for i in range(before_index - pattern_len + 1):
        if np.array_equal(sequence[i:i+pattern_len], pattern):
            return True
    return False

def kuramoto_complexity(K_values, N=50):
    """Compute Kuramoto order parameter as complexity measure"""
    complexities = []
    
    for K in K_values:
        # Simulate Kuramoto model
        dt = 0.01
        T = 100
        steps = int(T/dt)
        
        # Random initial phases and natural frequencies  
        np.random.seed(42)  # Reproducible
        theta = np.random.uniform(0, 2*np.pi, N)
        omega = np.random.normal(0, 1, N)
        
        # Euler integration
        for _ in range(steps):
            coupling = K * np.mean(np.sin(theta[:, None] - theta))
            dtheta = omega + coupling
            theta += dt * dtheta
            theta = theta % (2*np.pi)
        
        # Order parameter (1 - |mean(e^{i*theta})|)  
        order_param = 1 - abs(np.mean(np.exp(1j * theta)))
        complexities.append(order_param)
    
    return np.array(complexities)

# Main validation script
def validate_two_family_taxonomy():
    """Test if Thomas attractor and Kuramoto belong to smooth-transition family"""
    
    print("=== Two-Family Emergence Taxonomy Validation ===")
    print("Testing HYP-020: Universal substrate families")
    
    # Known reference points from Frontier Dossier #005
    known_substrates = {
        'kuramoto': {'band_frac': 0.57, 'sat_run': 0.00, 'family': 'smooth-transition'},
        'logistic': {'band_frac': 0.19, 'sat_run': 0.12, 'family': 'smooth-transition'}, 
        'rule30': {'band_frac': 0.00, 'sat_run': 0.97, 'family': 'bifurcation'}
    }
    
    results = {}
    
    # Test 1: Thomas Attractor Complexity Trajectory
    print("\n1. Analyzing Thomas Attractor...")
    b_values = np.linspace(0.05, 0.30, 50)
    thomas_complexities = []
    
    for b in b_values:
        # Integrate Thomas system
        sol = solve_ivp(thomas_attractor, [0, 200], [0.1, 0.1, 0.1], 
                       args=(b,), dense_output=True, rtol=1e-8)
        
        # Extract final portion (avoid transients)
        t_eval = np.linspace(100, 200, 1000)
        trajectory = sol.sol(t_eval).T
        
        # Compute LZ complexity
        lz_complexity = lempel_ziv_complexity(trajectory)
        thomas_complexities.append(lz_complexity)
    
    thomas_features = extract_emergence_features(np.array(thomas_complexities), b_values)
    results['thomas'] = thomas_features
    
    print(f"Thomas features: band_frac={thomas_features['band_frac']:.3f}, sat_run={thomas_features['sat_run']:.3f}")
    
    # Test 2: Kuramoto Validation  
    print("\n2. Validating Kuramoto...")
    K_values = np.linspace(0, 4, 50)
    kuramoto_complexities = kuramoto_complexity(K_values)
    
    kuramoto_features = extract_emergence_features(kuramoto_complexities, K_values)
    results['kuramoto_validation'] = kuramoto_features
    
    print(f"Kuramoto features: band_frac={kuramoto_features['band_frac']:.3f}, sat_run={kuramoto_features['sat_run']:.3f}")
    
    # Family classification using diagnostic plane
    def classify_family(band_frac, sat_run):
        """Classify into smooth-transition vs bifurcation family"""
        if band_frac > 0.15 and sat_run < 0.8:
            return 'smooth-transition'
        elif band_frac < 0.05 and sat_run > 0.8:
            return 'bifurcation'
        else:
            return 'intermediate'
    
    # Classify test substrates
    thomas_family = classify_family(thomas_features['band_frac'], thomas_features['sat_run'])
    kuramoto_family = classify_family(kuramoto_features['band_frac'], kuramoto_features['sat_run'])
    
    results['classifications'] = {
        'thomas': thomas_family,
        'kuramoto_validation': kuramoto_family
    }
    
    print(f"\n3. Family Classifications:")
    print(f"Thomas Attractor: {thomas_family}")
    print(f"Kuramoto (validation): {kuramoto_family}")
    
    # Generate diagnostic plot
    plt.figure(figsize=(10, 8))
    
    # Plot known substrates
    colors = {'smooth-transition': 'blue', 'bifurcation': 'red', 'intermediate': 'orange'}
    
    for name, data in known_substrates.items():
        plt.scatter(data['band_frac'], data['sat_run'], 
                   c=colors[data['family']], s=100, alpha=0.7, 
                   label=f"{name} ({data['family']})")
    
    # Plot test results
    plt.scatter(thomas_features['band_frac'], thomas_features['sat_run'],
               c=colors.get(thomas_family, 'gray'), s=150, marker='^',
               label=f"Thomas ({thomas_family})", edgecolors='black', linewidth=2)
    
    plt.scatter(kuramoto_features['band_frac'], kuramoto_features['sat_run'],
               c=colors.get(kuramoto_family, 'gray'), s=150, marker='s', 
               label=f"Kuramoto-val ({kuramoto_family})", edgecolors='black', linewidth=2)
    
    # Family boundary regions
    plt.axhline(y=0.8, color='gray', linestyle='--', alpha=0.5, label='sat_run threshold')
    plt.axvline(x=0.15, color='gray', linestyle='--', alpha=0.5, label='band_frac threshold')
    
    plt.xlabel('Band Fraction (intermediate regime)', fontsize=12)
    plt.ylabel('Saturation Run (chaos dominance)', fontsize=12)
    plt.title('Two-Family Taxonomy: Diagnostic (band_frac, sat_run) Plane', fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig('shared_agora/artifacts/two_family_taxonomy_diagnostic.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save results 
    with open('shared_agora/artifacts/two_family_taxonomy_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Verdict
    print(f"\n4. VALIDATION VERDICT:")
    thomas_prediction = "CONFIRMED" if thomas_family == 'smooth-transition' else "REFUTED"
    kuramoto_prediction = "CONFIRMED" if kuramoto_family == 'smooth-transition' else "REFUTED"
    
    print(f"Thomas → smooth-transition family: {thomas_prediction}")
    print(f"Kuramoto validation: {kuramoto_prediction}")
    
    if thomas_prediction == "CONFIRMED" and kuramoto_prediction == "CONFIRMED":
        print("\n✓ HYP-020 TWO-FAMILY TAXONOMY EMPIRICALLY SUPPORTED")
        print("  Substrate-agnostic families cut across mechanistic categories")
    else:
        print(f"\n✗ HYP-020 REQUIRES REFINEMENT") 
        print("  Family boundaries or classification criteria need adjustment")
    
    return results

if __name__ == "__main__":
    results = validate_two_family_taxonomy()