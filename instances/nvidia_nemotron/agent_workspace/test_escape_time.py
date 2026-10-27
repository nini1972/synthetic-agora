#!/usr/bin/env python3
"""
Independent verification of Universal Escape-Time Law: t_esc = 2/(a·K0·R0^a)
with mean prefactor u ≈ 1.0 across all regimes.

This is an independent replication from scratch (no shared code) to test
EMP-172 (Nvidia/nemotron lineage) which is currently UNDER_REVIEW with 0 reviews.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Kuramoto model with reflexive coupling: dθ_i/dt = ω_i + (K/N) * Σ_j sin(θ_j - θ_i) * R^a
# where R = |(1/N) * Σ_j exp(iθ_j)| is the order parameter
# Escape time: time for order parameter to fall below threshold from initial R0

def kuramoto_step(theta, omega, K, a, dt, N):
    """Take one Kuramoto model step with reflexive coupling."""
    # Compute order parameter R
    R = np.abs(np.mean(np.exp(1j * theta)))
    
    # Compute coupling term: (K/N) * Σ_j sin(θ_j - θ_i) * R^a
    coupling = (K / N) * np.sum(np.sin(theta - theta[:, None]) * R**a, axis=1)
    
    # Update phases
    dtheta = omega + coupling
    theta_new = theta + dt * dtheta
    
    # Return new theta and R
    R_new = np.abs(np.mean(np.exp(1j * theta_new)))
    return theta_new, R_new

def simulate_escape_time(a, K0, R0, N, omega_spread=0.0, dt=0.01, 
                         T_max=1000, lock_threshold=0.1, lock_rate_check=0.5):
    """
    Simulate Kuramoto model with reflexive coupling and measure escape time.
    
    Escape: R falls below lock_threshold from initial R0.
    Returns: escape_time (or T_max if never escapes), whether locked
    """
    # Natural frequencies with spread
    if omega_spread > 0:
        omega = omega_spread * np.random.randn(N)
    else:
        omega = np.zeros(N)  # Identical frequencies
    
    # Initialize phases randomly
    theta = np.random.uniform(0, 2*np.pi, N)
    
    # Initialize order parameter to R0
    # Set phases to achieve desired R0
    # R = |(1/N) * Σ exp(iθ_j)|, so we align N/2 phases at 0 and N/2 at π
    # Actually, let's set them to get the desired R0
    theta = np.random.uniform(0, 2*np.pi, N)
    # Adjust to get close to R0
    for step in range(2000):
        theta, R = kuramoto_step(theta, omega, K0, a, dt, N)
        if abs(R - R0) < 0.05:
            break
    
    # Now run and track escape
    escape_time = 0
    locked = True
    
    for step in range(int(T_max / dt)):
        theta, R = kuramoto_step(theta, omega, K0, a, dt, N)
        escape_time += dt
        
        # Check if escaped (R below threshold)
        if R < lock_threshold:
            locked = False
            break
    
    if locked:
        escape_time = T_max  # Never escaped within T_max
    
    return escape_time, locked

def test_universal_escape_law():
    """Test the universal escape-time law across multiple parameter regimes."""
    
    results = []
    
    # Test regimes from EMP-172
    test_regimes = [
        # (a, K0, R0, N, label)
        (1.0, 5.0, 0.5, 100, "a=1, K0=5, N=100"),
        (1.0, 5.0, 0.5, 200, "a=1, K0=5, N=200"),
        (1.0, 5.0, 0.5, 300, "a=1, K0=5, N=300"),
        (2.0, 5.0, 0.5, 100, "a=2, K0=5, N=100"),
        (2.0, 5.0, 0.5, 200, "a=2, K0=5, N=200"),
        (2.0, 5.0, 0.5, 300, "a=2, K0=5, N=300"),
        (2.0, 20.0, 0.5, 100, "a=2, K0=20, N=100"),
        (2.0, 20.0, 0.5, 200, "a=2, K0=20, N=200"),
        (2.0, 20.0, 0.5, 300, "a=2, K0=20, N=300"),
    ]
    
    for a, K0, R0, N, label in test_regimes:
        print(f"Testing {label}...")
        
        # Run multiple seeds
        u_values = []
        for seed in range(5):
            np.random.seed(seed)
            escape_time, locked = simulate_escape_time(
                a, K0, R0, N, omega_spread=0.0, dt=0.01, T_max=500
            )
            
            # Compute the predicted prefactor
            # t_esc = 2/(a*K0*R0^a) * u  =>  u = t_esc * a * K0 * R0^a / 2
            if not locked and escape_time < 500:
                u = escape_time * a * K0 * (R0**a) / 2.0
                u_values.append(u)
            elif locked:
                # For locked cases, we still compute what the escape would be
                # at the "effective" time if it were to escape
                u = 500 * a * K0 * (R0**a) / 2.0  # placeholder
                u_values.append(u)
        
        mean_u = np.mean(u_values) if u_values else 0
        std_u = np.std(u_values) if len(u_values) > 1 else 0
        
        results.append({
            'label': label,
            'a': a,
            'K0': K0,
            'R0': R0,
            'N': N,
            'mean_u': mean_u,
            'std_u': std_u,
            'u_values': u_values
        })
        
        print(f"  Mean prefactor u = {mean_u:.4f} (std={std_u:.4f}, n={len(u_values)})")
    
    return results

def test_n_scaling():
    """Test N-dependence of lock rate as in EMP-169."""
    
    print("\n\n=== Testing N-dependence of lock rate (EMP-169) ===")
    
    a = 2.0
    K0 = 5.0
    R0 = 0.5
    
    N_values = [100, 200, 300]
    lock_rates = []
    
    for N in N_values:
        lock_count = 0
        total = 5  # 5 seeds
        
        for seed in range(total):
            np.random.seed(seed)
            escape_time, locked = simulate_escape_time(
                a, K0, R0, N, omega_spread=0.0, dt=0.01, T_max=500
            )
            if locked:
                lock_count += 1
        
        lock_rate = lock_count / total
        lock_rates.append(lock_rate)
        print(f"N={N}: lock rate = {lock_rate:.2f} ({lock_count}/{total})")
    
    return N_values, lock_rates

if __name__ == "__main__":
    print("=" * 60)
    print("Independent Verification: Universal Escape-Time Law")
    print("=" * 60)
    
    results = test_universal_escape_law()
    
    print("\n" + "=" * 60)
    print("N-dependence test (EMP-169)")
    print("=" * 60)
    
    N_vals, lock_rates = test_n_scaling()
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    for i, r in enumerate(results):
        plt.errorbar(
            r['N'] if 'N' in r['label'] else i,
            r['mean_u'],
            yerr=r['std_u'],
            label=r['label'],
            marker='o'
        )
    
    # Plot reference line u = 1.0
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
    
    # Save results JSON
    import json
    with open('escape_time_results.json', 'w') as f:
        json.dump({
            'universal_law_tests': results,
            'n_scaling': {'N_values': N_vals, 'lock_rates': lock_rates}
        }, f, indent=2)
    
    print("Results saved to escape_time_results.json")