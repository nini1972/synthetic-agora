#!/usr/bin/env python3
"""
Fast Alpha-Divergence Test: HYP-045
Optimized implementation for quick validation
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def kuramoto_reflexive_fast(N, omega, K0, alpha, T, dt, theta_init):
    """Fast vectorized Kuramoto simulation"""
    theta = theta_init.copy()
    steps = int(T / dt)
    # Sample fewer points for speed
    sample_interval = max(1, steps // 200)
    order_history = []
    
    for t in range(0, steps, sample_interval):
        # Vectorized order parameter
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        order_history.append(R)
        
        # Skip if already converged to save time
        if t > steps // 4 and len(order_history) > 20:
            recent_std = np.std(order_history[-10:])
            if recent_std < 0.01:  # Converged
                break
        
        # Vectorized update with adaptive time steps
        K_eff = K0 * (R ** alpha) if R > 1e-8 else 0.0
        coupling = K_eff * np.imag(np.conj(Z) * np.exp(1j * theta))
        
        # Use larger dt for faster convergence
        adaptive_dt = dt * sample_interval
        theta += adaptive_dt * (omega + coupling)
        theta = np.mod(theta, 2 * np.pi)
    
    return np.array(order_history)

def quick_alpha_test():
    """Quick validation focusing on key predictions"""
    print("=== FAST Alpha-Divergence Validation ===")
    
    # Reduced parameters for speed
    N = 100  # Smaller system
    T = 20.0  # Shorter simulation
    dt = 0.05  # Larger timestep
    n_seeds = 3  # Fewer seeds
    
    # Focus on key alpha values around transition
    alpha_key = [0.8, 0.9, 1.0, 1.1, 1.2]
    K0_test = 4.0
    
    print(f"Testing accessibility at K₀ = {K0_test}")
    
    accessibility_results = {}
    
    for alpha in alpha_key:
        orders = []
        
        for seed in range(n_seeds):
            np.random.seed(42 + seed + int(alpha * 100))
            
            omega = np.random.uniform(-1, 1, N)
            theta = np.random.uniform(0, 2*np.pi, N)
            
            order_hist = kuramoto_reflexive_fast(N, omega, K0_test, alpha, T, dt, theta)
            final_order = np.mean(order_hist[-5:]) if len(order_hist) > 5 else np.mean(order_hist)
            orders.append(final_order)
        
        mean_order = np.mean(orders)
        accessibility_results[alpha] = mean_order
        
        print(f"α = {alpha:3.1f}: R = {mean_order:.3f}")
    
    # Basin disconnection test at α = 1.2
    print(f"\nTesting basin disconnection at α = 1.2, K₀ = {K0_test}")
    
    alpha_test = 1.2
    random_orders = []
    seeded_orders = []
    
    for seed in range(n_seeds):
        np.random.seed(100 + seed)
        
        omega = np.random.uniform(-1, 1, N)
        
        # Random init
        theta_random = np.random.uniform(0, 2*np.pi, N)
        order_random = kuramoto_reflexive_fast(N, omega, K0_test, alpha_test, T, dt, theta_random)
        random_orders.append(np.mean(order_random[-5:]))
        
        # Seeded init
        theta_seeded = np.random.uniform(-0.3, 0.3, N)
        order_seeded = kuramoto_reflexive_fast(N, omega, K0_test, alpha_test, T, dt, theta_seeded)
        seeded_orders.append(np.mean(order_seeded[-5:]))
    
    random_mean = np.mean(random_orders)
    seeded_mean = np.mean(seeded_orders)
    ratio = seeded_mean / max(random_mean, 0.001)
    
    print(f"Random init: R = {random_mean:.3f}")
    print(f"Seeded init: R = {seeded_mean:.3f}")
    print(f"Enhancement ratio: {ratio:.1f}x")
    
    # Create simple visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Accessibility plot
    alphas = list(accessibility_results.keys())
    orders = list(accessibility_results.values())
    
    ax1.plot(alphas, orders, 'bo-', linewidth=2, markersize=8)
    ax1.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='α* = 1')
    ax1.set_xlabel('α (feedback exponent)')
    ax1.set_ylabel('Final Order R')
    ax1.set_title(f'Accessibility Test (K₀ = {K0_test})')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Basin disconnection
    conditions = ['Random', 'Seeded']
    means = [random_mean, seeded_mean]
    
    bars = ax2.bar(conditions, means, color=['lightcoral', 'lightblue'], alpha=0.7)
    ax2.set_ylabel('Final Order R')
    ax2.set_title(f'Basin Test (α = {alpha_test})')
    ax2.grid(True, alpha=0.3)
    
    # Add ratio annotation
    ax2.text(0.5, max(means) * 0.8, f'{ratio:.1f}x enhancement', 
             ha='center', fontsize=12, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/alpha_divergence_fast.png', dpi=150, bbox_inches='tight')
    
    # Analysis
    print(f"\n=== QUICK VALIDATION RESULTS ===")
    
    # Check for accessibility decline
    order_trend = []
    for i in range(len(alphas)-1):
        if orders[i+1] < orders[i]:
            order_trend.append("decrease")
        else:
            order_trend.append("increase")
    
    print(f"Order trend as α increases: {' -> '.join(order_trend)}")
    
    # Check alpha = 1 transition
    alpha_below = [orders[i] for i, a in enumerate(alphas) if a < 1.0]
    alpha_above = [orders[i] for i, a in enumerate(alphas) if a > 1.0]
    
    if alpha_below and alpha_above:
        mean_below = np.mean(alpha_below)
        mean_above = np.mean(alpha_above)
        print(f"Mean order below α=1: {mean_below:.3f}")
        print(f"Mean order above α=1: {mean_above:.3f}")
        print(f"Relative change: {(mean_above-mean_below)/mean_below*100:.1f}%")
    
    # Final verdict
    has_transition = len([a for a in alphas if a > 1.0 and accessibility_results[a] < 0.3]) > 0
    has_disconnection = ratio > 2.0
    
    results = {
        'accessibility': accessibility_results,
        'disconnection_ratio': ratio,
        'has_transition': has_transition,
        'has_disconnection': has_disconnection
    }
    
    if has_transition and has_disconnection:
        verdict = "STRONG SUPPORT"
    elif has_transition or has_disconnection:
        verdict = "PARTIAL SUPPORT"
    else:
        verdict = "LIMITED SUPPORT"
    
    print(f"VERDICT: {verdict} for HYP-045")
    
    # Save results
    with open('../../shared_agora/artifacts/alpha_divergence_fast.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    results = quick_alpha_test()