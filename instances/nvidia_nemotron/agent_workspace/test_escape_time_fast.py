#!/usr/bin/env python3
"""
Independent verification of Universal Escape-Time Law: t_esc = 2/(a·K0·R0^a)
with mean prefactor u ≈ 1.0 across all regimes.
Optimized version for faster execution.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate_escape_time_fast(a, K0, R0, N, omega_spread=0.0, dt=0.01, 
                               T_max=200, lock_threshold=0.1):
    """
    Fast Kuramoto model step with reflexive coupling.
    Escape: R falls below lock_threshold from initial R0.
    """
    # Natural frequencies
    if omega_spread > 0:
        omega = omega_spread * np.random.randn(N)
    else:
        omega = np.zeros(N)
    
    # Initialize phases - set to achieve desired R0
    # Use: align phases such that R = R0 initially
    # Method: set N/2 phases at 0, N/2 phases at π gives R=0
    # For general R0, we use a simpler initialization
    theta = np.random.uniform(0, 2*np.pi, N)
    
    # Quick thermalization: just a few steps to get reasonable state
    for _ in range(20):
        # Compute R
        exp_iθ = np.exp(1j * theta)
        R = np.abs(np.mean(exp_iθ))
        # Compute coupling
        sin_diff = np.sin(theta[:, None] - theta[None, :])
        coupling = (K0 / N) * np.sum(sin_diff * (R0**a), axis=1)
        theta = theta + dt * (omega + coupling)
    
    # Now track escape
    escape_time = 0
    locked = True
    
    for step in range(int(T_max / dt)):
        # Compute R
        exp_iθ = np.exp(1j * theta)
        R = np.abs(np.mean(exp_iθ))
        
        # Compute coupling with current R^a
        sin_diff = np.sin(theta[:, None] - theta[None, :])
        coupling = (K0 / N) * np.sum(sin_diff * (R**a), axis=1)
        
        # Update
        theta = theta + dt * (omega + coupling)
        
        escape_time += dt
        
        # Check escape
        if R < lock_threshold:
            locked = False
            break
    
    if locked:
        escape_time = T_max
    
    # Compute prefactor u = t_esc * a * K0 * R0^a / 2
    if not locked and escape_time < T_max:
        u = escape_time * a * K0 * (R0**a) / 2.0
    else:
        u = None  # locked or timed out
    
    return escape_time, locked, u

def test_universal_escape_law():
    """Test across parameter regimes."""
    
    results = []
    
    test_regimes = [
        (1.0, 5.0, 0.5, 100),
        (1.0, 5.0, 0.5, 200),
        (1.0, 5.0, 0.5, 300),
        (2.0, 5.0, 0.5, 100),
        (2.0, 5.0, 0.5, 200),
        (2.0, 5.0, 0.5, 300),
        (2.0, 20.0, 0.5, 100),
        (2.0, 20.0, 0.5, 200),
        (2.0, 20.0, 0.5, 300),
    ]
    
    for a, K0, R0, N in test_regimes:
        print(f"Testing a={a}, K0={K0}, R0={R0}, N={N}...")
        
        u_values = []
        for seed in range(3):  # 3 seeds for speed
            np.random.seed(seed)
            escape_time, locked, u = simulate_escape_time_fast(a, K0, R0, N)
            if u is not None:
                u_values.append(u)
        
        mean_u = np.mean(u_values) if u_values else 0
        std_u = np.std(u_values) if len(u_values) > 1 else 0
        
        results.append({
            'a': a, 'K0': K0, 'R0': R0, 'N': N,
            'mean_u': mean_u, 'std_u': std_u, 'u_values': u_values,
            'n_tested': len(u_values)
        })
        
        print(f"  Mean u = {mean_u:.4f} (std={std_u:.4f}, n={len(u_values)})")
    
    return results

def test_n_scaling():
    """Test N-dependence of lock rate."""
    
    print("\nN-dependence test (EMP-169): a=2, K0=5, R0=0.5")
    
    a, K0, R0 = 2.0, 5.0, 0.5
    N_values = [100, 200, 300]
    lock_rates = []
    
    for N in N_values:
        lock_count = 0
        for seed in range(3):
            np.random.seed(seed)
            escape_time, locked, _ = simulate_escape_time_fast(a, K0, R0, N)
            if locked:
                lock_count += 1
        lock_rate = lock_count / 3
        lock_rates.append(lock_rate)
        print(f"N={N}: lock rate = {lock_rate:.2f} ({lock_count}/3)")
    
    return N_values, lock_rates

if __name__ == "__main__":
    print("=" * 60)
    print("Independent Verification: Universal Escape-Time Law")
    print("=" * 60)
    
    results = test_universal_escape_law()
    
    print("\n" + "=" * 60)
    print("N-dependence test")
    print("=" * 60)
    
    N_vals, lock_rates = test_n_scaling()
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    for i, r in enumerate(results):
        label = f"a={r['a']}, K0={r['K0']}, N={r['N']}"
        plt.errorbar(i, r['mean_u'], yerr=r['std_u'], label=label, marker='o')
    
    # Reference line u = 1.0
    plt.axhline(y=1.0, color='k', linestyle='--', label='u = 1.0 (theoretical)')
    
    plt.xlabel('Parameter Regime')
    plt.ylabel('Mean Prefactor u')
    plt.title('Universal Escape-Time Law: Prefactor u across Regimes')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_path = 'escape_time_test_results.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to {output_path}")
    plt.close()
    
    # Save results
    import json
    with open('escape_time_results.json', 'w') as f:
        json.dump({
            'universal_law_tests': results,
            'n_scaling': {'N_values': N_vals, 'lock_rates': lock_rates}
        }, f, indent=2)
    
    print("Results saved to escape_time_results.json")