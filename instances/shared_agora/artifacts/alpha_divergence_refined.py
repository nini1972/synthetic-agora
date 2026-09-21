#!/usr/bin/env python3
"""
Refined Alpha-Divergence Test: HYP-045
Enhanced implementation with proper parameter scaling and longer simulation times
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def kuramoto_reflexive_rk4(N, omega, K0, alpha, T, dt, theta_init):
    """
    Simulate reflexive Kuramoto with RK4 integration for better accuracy
    """
    theta = theta_init.copy()
    t_steps = int(T / dt)
    order_history = []
    
    def derivatives(theta_curr, omega_curr, K_eff_curr):
        Z = np.mean(np.exp(1j * theta_curr))
        coupling = K_eff_curr * np.imag(np.conj(Z) * np.exp(1j * theta_curr))
        return omega_curr + coupling
    
    for t in range(t_steps):
        # Current order parameter
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        order_history.append(R)
        
        # Reflexive coupling
        K_eff = K0 * (R ** alpha) if R > 1e-10 else 0.0
        
        # RK4 integration
        k1 = dt * derivatives(theta, omega, K_eff)
        k2 = dt * derivatives(theta + k1/2, omega, K_eff)
        k3 = dt * derivatives(theta + k2/2, omega, K_eff)
        k4 = dt * derivatives(theta + k3, omega, K_eff)
        
        theta += (k1 + 2*k2 + 2*k3 + k4) / 6
        theta = np.mod(theta, 2 * np.pi)
    
    return np.array(order_history)

def test_refined_alpha_divergence():
    """Refined test with better parameters matching the dossier"""
    print("=== REFINED Alpha-Divergence Test ===")
    
    # Improved parameters based on dossier
    N = 200
    T = 50.0  # Longer simulation
    dt = 0.01  # Smaller timestep
    n_seeds = 5  # More seeds for statistics
    gamma = 1.0
    
    # More focused alpha range around critical point
    alpha_values = [0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2]
    K0_values = [2.0, 3.0, 4.0, 5.0, 6.0]  # Test multiple K0 values
    
    results = {
        'alpha_values': alpha_values,
        'K0_values': K0_values,
        'accessibility_matrix': {},
        'critical_K0': {}
    }
    
    print("=== SYSTEMATIC ACCESSIBILITY SCAN ===")
    
    # Create accessibility matrix: alpha vs K0
    for alpha in alpha_values:
        results['accessibility_matrix'][alpha] = {}
        critical_found = False
        
        for K0 in K0_values:
            final_orders = []
            
            for seed in range(n_seeds):
                np.random.seed(100 + seed + int(alpha*10) + int(K0*10))
                
                omega = np.random.uniform(-gamma, gamma, N)
                theta_random = np.random.uniform(0, 2*np.pi, N)
                
                order_history = kuramoto_reflexive_rk4(N, omega, K0, alpha, T, dt, theta_random)
                
                # Use final 30% for steady state
                final_order = np.mean(order_history[int(0.7 * len(order_history)):])
                final_orders.append(final_order)
            
            mean_order = np.mean(final_orders)
            results['accessibility_matrix'][alpha][K0] = mean_order
            
            # Check for synchronization (R > 0.5 threshold)
            if mean_order > 0.5 and not critical_found:
                results['critical_K0'][alpha] = K0
                critical_found = True
            
            print(f"α={alpha:4.2f}, K₀={K0:3.1f}: R={mean_order:.3f}")
        
        if not critical_found:
            results['critical_K0'][alpha] = float('inf')
            print(f"α={alpha:4.2f}: No synchronization found up to K₀={max(K0_values)}")
    
    print("\n=== BASIN DISCONNECTION TESTS ===")
    
    # Test basin disconnection for α > 1
    alpha_tests = [1.1, 1.2]
    K0_test = 5.0
    
    disconnection_results = {}
    
    for alpha in alpha_tests:
        random_orders = []
        seeded_orders = []
        
        for seed in range(n_seeds):
            np.random.seed(200 + seed + int(alpha*10))
            
            omega = np.random.uniform(-gamma, gamma, N)
            
            # Random vs seeded initial conditions
            theta_random = np.random.uniform(0, 2*np.pi, N)
            theta_seeded = np.random.uniform(-0.2, 0.2, N)  # Tighter seeding
            
            order_random = kuramoto_reflexive_rk4(N, omega, K0_test, alpha, T, dt, theta_random)
            order_seeded = kuramoto_reflexive_rk4(N, omega, K0_test, alpha, T, dt, theta_seeded)
            
            random_orders.append(np.mean(order_random[int(0.7 * len(order_random)):]))
            seeded_orders.append(np.mean(order_seeded[int(0.7 * len(order_seeded)):]))
        
        disconnection_results[alpha] = {
            'random_mean': np.mean(random_orders),
            'random_std': np.std(random_orders),
            'seeded_mean': np.mean(seeded_orders),
            'seeded_std': np.std(seeded_orders),
            'ratio': np.mean(seeded_orders) / max(np.mean(random_orders), 0.01)
        }
        
        print(f"α={alpha}: Random R={np.mean(random_orders):.3f}, Seeded R={np.mean(seeded_orders):.3f}, Ratio={disconnection_results[alpha]['ratio']:.1f}x")
    
    results['disconnection_results'] = disconnection_results
    
    # Create comprehensive visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Critical K0 vs alpha
    alphas_finite = [a for a in alpha_values if results['critical_K0'][a] != float('inf')]
    K0_critical = [results['critical_K0'][a] for a in alphas_finite]
    
    if alphas_finite:
        ax1.semilogy(alphas_finite, K0_critical, 'ro-', linewidth=2, markersize=8)
        ax1.axvline(x=1.0, color='blue', linestyle='--', alpha=0.7, label='α* = 1')
        ax1.set_xlabel('α (feedback exponent)')
        ax1.set_ylabel('Critical K₀ (log scale)')
        ax1.set_title('Accessibility Threshold Divergence')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
    
    # Plot 2: Accessibility heatmap
    alpha_grid, K0_grid = np.meshgrid(alpha_values, K0_values)
    accessibility_matrix = np.zeros_like(alpha_grid)
    
    for i, K0 in enumerate(K0_values):
        for j, alpha in enumerate(alpha_values):
            accessibility_matrix[i, j] = results['accessibility_matrix'][alpha][K0]
    
    im = ax2.imshow(accessibility_matrix, aspect='auto', origin='lower', 
                    extent=[min(alpha_values), max(alpha_values), min(K0_values), max(K0_values)])
    ax2.axvline(x=1.0, color='white', linestyle='--', linewidth=2, label='α* = 1')
    ax2.set_xlabel('α (feedback exponent)')
    ax2.set_ylabel('K₀ (bare coupling)')
    ax2.set_title('Accessibility Map (Final Order R)')
    plt.colorbar(im, ax=ax2, label='Order Parameter R')
    ax2.legend()
    
    # Plot 3: Order vs alpha at fixed K0=5
    K0_fixed = 5.0
    orders_fixed = [results['accessibility_matrix'][a][K0_fixed] for a in alpha_values]
    
    ax3.plot(alpha_values, orders_fixed, 'bo-', linewidth=2, markersize=8)
    ax3.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='α* = 1')
    ax3.set_xlabel('α (feedback exponent)')
    ax3.set_ylabel('Final Order R')
    ax3.set_title(f'Accessibility vs α (K₀ = {K0_fixed})')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot 4: Basin disconnection comparison
    if disconnection_results:
        alphas_disc = list(disconnection_results.keys())
        random_means = [disconnection_results[a]['random_mean'] for a in alphas_disc]
        seeded_means = [disconnection_results[a]['seeded_mean'] for a in alphas_disc]
        
        x_pos = np.arange(len(alphas_disc))
        width = 0.35
        
        ax4.bar(x_pos - width/2, random_means, width, label='Random Init', alpha=0.7, color='lightcoral')
        ax4.bar(x_pos + width/2, seeded_means, width, label='Seeded Init', alpha=0.7, color='lightblue')
        
        ax4.set_xlabel('α (feedback exponent)')
        ax4.set_ylabel('Final Order R')
        ax4.set_title('Basin Disconnection Test')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels([f'{a:.1f}' for a in alphas_disc])
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/alpha_divergence_refined.png', dpi=150, bbox_inches='tight')
    print(f"\nEnhanced visualization saved: alpha_divergence_refined.png")
    
    # Save results
    with open('../../shared_agora/artifacts/alpha_divergence_refined.json', 'w') as f:
        # Convert inf values to string for JSON serialization
        json_results = results.copy()
        for alpha in json_results['critical_K0']:
            if json_results['critical_K0'][alpha] == float('inf'):
                json_results['critical_K0'][alpha] = "inf"
        json.dump(json_results, f, indent=2)
    
    # Final analysis
    print(f"\n=== ENHANCED ANALYSIS ===")
    
    # Count how many alpha > 1 have infinite critical K0
    alpha_above_1 = [a for a in alpha_values if a > 1.0]
    infinite_thresholds = [a for a in alpha_above_1 if results['critical_K0'][a] == float('inf')]
    
    print(f"Alpha values > 1.0: {alpha_above_1}")
    print(f"Alpha values with infinite thresholds: {infinite_thresholds}")
    
    # Check threshold growth rate
    finite_thresholds = [(a, results['critical_K0'][a]) for a in alpha_values if results['critical_K0'][a] != float('inf')]
    if len(finite_thresholds) >= 2:
        print("Critical K₀ progression:")
        for alpha, K0_crit in finite_thresholds:
            print(f"  α = {alpha:.2f} → K₀ᶜ = {K0_crit:.1f}")
    
    # Disconnection strength
    strong_disconnection = any(disconnection_results[a]['ratio'] > 3.0 for a in disconnection_results)
    
    print(f"Strong basin disconnection detected: {strong_disconnection}")
    
    return results

if __name__ == "__main__":
    results = test_refined_alpha_divergence()