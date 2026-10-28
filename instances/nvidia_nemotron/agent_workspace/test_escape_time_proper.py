#!/usr/bin/env python3
"""
Independent verification of Universal Escape-Time Law: t_esc = 2/(a·K0·R0^a)
with mean prefactor u ≈ 1.0 across all regimes.
Proper initialization to achieve desired R0.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def set_phases_for_R(N, R_target, seed=None):
    """
    Initialize N phases such that the order parameter R = |(1/N)Σexp(iθ_j)| ≈ R_target.
    Method: place phases to achieve exact R_target using inverse transform.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if R_target >= 1.0:
        R_target = 0.99
    
    # Use the analytical approach:
    # If we set m phases at angle 0 and (N-m) phases at angle π,
    # then R = |(m/N)*1 + ((N-m)/N)*(-1)| = |(2m/N) - 1|
    # So for R_target, we need m = N/2 * (1 + R_target)
    
    m = int(N / 2 * (1 + R_target))
    m = max(0, min(N, m))  # Clamp
    
    theta = np.ones(N) * np.pi  # Start with all at π
    theta[:m] = 0  # Set first m phases to 0
    
    # Add small random perturbations to break symmetry
    jitter = np.random.uniform(-0.3, 0.3, N)
    theta = (theta + jitter) % (2*np.pi)
    
    # Compute actual R
    exp_iθ = np.exp(1j * theta)
    R_actual = np.abs(np.mean(exp_iθ))
    
    return theta, R_actual

def kuramoto_r_step(theta, omega, K, a, dt, N):
    """One Kuramoto step with reflexive coupling - fast vectorized version."""
    # Compute order parameter R
    exp_iθ = np.exp(1j * theta)
    R = np.abs(np.mean(exp_iθ))
    
    # Compute pairwise sin differences efficiently
    # sin(θ_i - θ_j) = sinθ_i*cosθ_j - cosθ_i*sinθ_j
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    
    # Σ_j sin(θ_i - θ_j) * R^a = R^a * (sinθ_i * Σcosθ_j - cosθ_i * Σsinθ_j)
    sum_cos = np.sum(cos_theta)
    sum_sin = np.sum(sin_theta)
    
    coupling_i = (K / N) * (sin_theta * sum_cos - cos_theta * sum_sin) * (R**a)
    
    # Update
    dtheta = omega + coupling_i
    theta_new = theta + dt * dtheta
    
    return theta_new, R

def simulate_escape_time_proper(A, K0, R0, N, omega_spread=0.0, dt=0.01,
                                 T_max=200, lock_threshold=0.1, seed=None):
    """
    Simulate Kuramoto model with proper R0 initialization.
    Returns: (escape_time, locked, prefactor_u)
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Initialize phases for desired R0
    theta, R_init = set_phases_for_R(N, R0, seed=seed)
    
    # Determine omega vector
    if omega_spread > 0:
        omega = omega_spread * np.random.randn(N)
    else:
        omega = np.zeros(N)
    
    # Track escape
    escape_time = 0.0
    locked = True
    
    for step in range(int(T_max / dt)):
        theta, R = kuramoto_r_step(theta, omega, K0, A, dt, N)
        escape_time += dt
        
        # Check escape (R below threshold)
        if R < lock_threshold:
            locked = False
            break
    
    if locked:
        escape_time = T_max
    
    # Compute prefactor u = t_esc * a * K0 * R0^a / 2
    if not locked and escape_time < T_max:
        u = escape_time * A * K0 * (R0**A) / 2.0
    else:
        u = None
    
    return escape_time, locked, u

def test_universal_escape_law():
    """Test across parameter regimes from EMP-172."""
    
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
    
    for a_val, K0, R0, N in test_regimes:
        print(f"Testing a={a_val}, K0={K0}, R0={R0}, N={N}...")
        
        u_values = []
        for seed in range(5):  # 5 seeds
            np.random.seed(seed)
            escape_time, locked, u = simulate_escape_time_proper(a_val, K0, R0, N)
            if u is not None:
                u_values.append(u)
            else:
                print(f"  Seed {seed}: locked or timed out (escape_time={escape_time:.1f})")
        
        if u_values:
            mean_u = np.mean(u_values)
            std_u = np.std(u_values)
        else:
            mean_u = 0
            std_u = 0
        
        results.append({
            'a': a_val, 'K0': K0, 'R0': R0, 'N': N,
            'mean_u': mean_u, 'std_u': std_u, 'u_values': u_values,
            'n_tested': len(u_values)
        })
        
        print(f"  Mean u = {mean_u:.4f} (std={std_u:.4f}, n={len(u_values)})")
    
    return results

def test_n_scaling():
    """Test N-dependence of lock rate from EMP-169."""
    
    print("\nN-dependence test (EMP-169): a=2, K0=5, R0=0.5")
    
    a_val, K0, R0 = 2.0, 5.0, 0.5
    N_values = [100, 200, 300]
    lock_rates = []
    
    for N in N_values:
        lock_count = 0
        for seed in range(5):
            np.random.seed(seed)
            escape_time, locked, _ = simulate_escape_time_proper(a_val, K0, R0, N)
            if locked:
                lock_count += 1
        lock_rate = lock_count / 5
        lock_rates.append(lock_rate)
        print(f"N={N}: lock rate = {lock_rate:.2f} ({lock_count}/5)")
    
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