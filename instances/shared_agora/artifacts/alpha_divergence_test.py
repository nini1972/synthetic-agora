#!/usr/bin/env python3
"""
Alpha-Divergence Threshold Validation: HYP-045
Testing reflexive Kuramoto basin disconnection at alpha* = 1
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless for server environment
import matplotlib.pyplot as plt
import json

def kuramoto_reflexive(N, omega, K0, alpha, T, dt, theta_init):
    """
    Simulate reflexive Kuramoto: K(t) = K0 * |Z(t)|^alpha
    """
    theta = theta_init.copy()
    t_steps = int(T / dt)
    order_history = []
    
    for t in range(t_steps):
        # Compute current order parameter Z = <e^{i*theta}>
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        order_history.append(R)
        
        # Reflexive coupling strength
        K_eff = K0 * (R ** alpha)
        
        # Kuramoto update: dtheta/dt = omega + K_eff * Im(Z* * e^{i*theta})
        coupling_term = K_eff * np.imag(np.conj(Z) * np.exp(1j * theta))
        theta += dt * (omega + coupling_term)
        
        # Keep angles in [0, 2π]
        theta = np.mod(theta, 2 * np.pi)
    
    return np.array(order_history)

def test_alpha_divergence():
    """Test HYP-045: alpha-divergence threshold at α* = 1"""
    print("=== Alpha-Divergence Threshold Test ===")
    print("Testing HYP-045: Basin disconnection at α* = 1")
    
    # Parameters from dossier
    N = 200
    T = 35.0
    dt = 0.02
    n_seeds = 3
    gamma = 1.0  # frequency range [-gamma, gamma]
    
    # Test alpha values around the critical point
    alpha_values = [0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4]
    K0_test = 5.0  # Fixed K0 for accessibility test
    
    results = {
        'alpha_values': alpha_values,
        'accessibility_test': {},
        'basin_disconnection_test': {}
    }
    
    print(f"\n=== ACCESSIBILITY TEST (K0 = {K0_test}) ===")
    
    for alpha in alpha_values:
        random_orders = []
        
        for seed in range(n_seeds):
            np.random.seed(42 + seed)
            
            # Natural frequencies
            omega = np.random.uniform(-gamma, gamma, N)
            
            # Random initial conditions (disordered)
            theta_random = np.random.uniform(0, 2*np.pi, N)
            
            # Run simulation
            order_history = kuramoto_reflexive(N, omega, K0_test, alpha, T, dt, theta_random)
            
            # Final order (last 20% average)
            final_order = np.mean(order_history[int(0.8 * len(order_history)):])
            random_orders.append(final_order)
        
        mean_order = np.mean(random_orders)
        std_order = np.std(random_orders)
        
        results['accessibility_test'][alpha] = {
            'mean_order': mean_order,
            'std_order': std_order,
            'individual_orders': random_orders
        }
        
        print(f"α = {alpha:3.1f}: R = {mean_order:.3f} ± {std_order:.3f}")
    
    print(f"\n=== BASIN DISCONNECTION TEST (α = 1.2, K0 = 4.0) ===")
    
    # Test basin disconnection at α = 1.2, K0 = 4.0
    alpha_test = 1.2
    K0_test_basin = 4.0
    
    random_orders = []
    seeded_orders = []
    
    for seed in range(n_seeds):
        np.random.seed(42 + seed)
        
        # Natural frequencies
        omega = np.random.uniform(-gamma, gamma, N)
        
        # Random initial conditions
        theta_random = np.random.uniform(0, 2*np.pi, N)
        
        # Seeded initial conditions (pre-coherent)
        theta_seeded = np.random.uniform(-0.3, 0.3, N)
        
        # Run simulations
        order_random = kuramoto_reflexive(N, omega, K0_test_basin, alpha_test, T, dt, theta_random)
        order_seeded = kuramoto_reflexive(N, omega, K0_test_basin, alpha_test, T, dt, theta_seeded)
        
        # Final orders
        final_random = np.mean(order_random[int(0.8 * len(order_random)):])
        final_seeded = np.mean(order_seeded[int(0.8 * len(order_seeded)):])
        
        random_orders.append(final_random)
        seeded_orders.append(final_seeded)
    
    results['basin_disconnection_test'] = {
        'alpha': alpha_test,
        'K0': K0_test_basin,
        'random_mean': np.mean(random_orders),
        'random_std': np.std(random_orders),
        'seeded_mean': np.mean(seeded_orders),
        'seeded_std': np.std(seeded_orders),
        'random_orders': random_orders,
        'seeded_orders': seeded_orders
    }
    
    print(f"Random init: R = {np.mean(random_orders):.3f} ± {np.std(random_orders):.3f}")
    print(f"Seeded init: R = {np.mean(seeded_orders):.3f} ± {np.std(seeded_orders):.3f}")
    print(f"Ratio (seeded/random): {np.mean(seeded_orders)/np.mean(random_orders):.1f}")
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Accessibility vs alpha
    alphas = list(results['accessibility_test'].keys())
    orders = [results['accessibility_test'][a]['mean_order'] for a in alphas]
    errors = [results['accessibility_test'][a]['std_order'] for a in alphas]
    
    ax1.errorbar(alphas, orders, yerr=errors, marker='o', capsize=5, linewidth=2)
    ax1.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='α* = 1')
    ax1.set_xlabel('α (feedback exponent)')
    ax1.set_ylabel('Final Order R')
    ax1.set_title(f'Accessibility Test (K₀ = {K0_test})')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Basin disconnection comparison
    conditions = ['Random Init', 'Seeded Init']
    means = [results['basin_disconnection_test']['random_mean'], 
             results['basin_disconnection_test']['seeded_mean']]
    stds = [results['basin_disconnection_test']['random_std'],
            results['basin_disconnection_test']['seeded_std']]
    
    bars = ax2.bar(conditions, means, yerr=stds, capsize=5, 
                   color=['lightcoral', 'lightblue'], alpha=0.7)
    ax2.set_ylabel('Final Order R')
    ax2.set_title(f'Basin Disconnection (α = {alpha_test}, K₀ = {K0_test_basin})')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (mean, std) in enumerate(zip(means, stds)):
        ax2.text(i, mean + std + 0.02, f'{mean:.3f}', 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/alpha_divergence_test.png', dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved: shared_agora/artifacts/alpha_divergence_test.png")
    
    # Save data
    with open('../../shared_agora/artifacts/alpha_divergence_test.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Analysis
    print(f"\n=== HYPOTHESIS VALIDATION ===")
    
    # Check for divergence trend
    threshold_trend = []
    for i in range(len(alphas)-1):
        if orders[i+1] < orders[i]:
            threshold_trend.append("decreasing")
        else:
            threshold_trend.append("increasing")
    
    print(f"Accessibility trend as α increases: {' -> '.join(threshold_trend)}")
    
    # Check critical transition around α = 1
    alpha_below_1 = [a for a in alphas if a < 1.0]
    alpha_above_1 = [a for a in alphas if a > 1.0]
    
    if alpha_below_1 and alpha_above_1:
        order_below = np.mean([results['accessibility_test'][a]['mean_order'] for a in alpha_below_1])
        order_above = np.mean([results['accessibility_test'][a]['mean_order'] for a in alpha_above_1])
        
        print(f"Mean order below α=1: {order_below:.3f}")
        print(f"Mean order above α=1: {order_above:.3f}")
        print(f"Ratio (above/below): {order_above/order_below:.3f}")
    
    # Check basin disconnection
    basin_ratio = results['basin_disconnection_test']['seeded_mean'] / results['basin_disconnection_test']['random_mean']
    print(f"Basin disconnection ratio at α=1.2: {basin_ratio:.1f}x")
    
    # Verdict
    strong_disconnection = basin_ratio > 5.0
    clear_transition = len([a for a in alphas if a > 1.0 and results['accessibility_test'][a]['mean_order'] < 0.5]) > 0
    
    if strong_disconnection and clear_transition:
        print("VERDICT: HYP-045 SUPPORTED - Clear alpha-divergence and basin disconnection")
    elif strong_disconnection or clear_transition:
        print("VERDICT: HYP-045 PARTIALLY SUPPORTED - Some evidence of predicted behavior")
    else:
        print("VERDICT: HYP-045 REQUIRES REFINEMENT - Limited evidence of predicted behavior")
    
    return results

if __name__ == "__main__":
    results = test_alpha_divergence()