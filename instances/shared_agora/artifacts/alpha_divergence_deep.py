#!/usr/bin/env python3
"""Deep dive: Alpha divergence - tracking transients and phase portraits.

Key question: Does the disordered→ordered transition at α>1 proceed through
a finite-time "quench" triggered by rare large fluctuations, or through
continuous diffusion? 

Also: what coupling convention does the dossier use?
Option A: dθ/dt = ω - K₀ R^α sin(θ-ψ) [what I've been using]
Option B: dθ/dt = ω - (K₀/N) R^α Σ_j sin(θ_j - θ) [mean-field with 1/N]
Option C: dθ/dt = ω - K₀ R^α/N Σ_j sin(θ_j - θ) 

Let me verify by testing multiple conventions.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_kuramoto(N, K0, alpha, omega, theta_init, T, dt, convention='A'):
    """Run Kuramoto with different coupling conventions."""
    n_steps = int(T / dt)
    theta = theta_init.copy()
    R_history = []
    
    for step in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        psi = np.angle(Z)
        
        if convention == 'A':
            # dθ_i = ω_i - K₀ R^α sin(θ_i - ψ)
            K_eff = K0 * (R ** alpha)
            dtheta = omega - K_eff * np.sin(theta - psi)
        elif convention == 'B':
            # dθ_i = ω_i - (K₀/N) Σ_j R^α sin(θ_j - θ_i) 
            # = ω_i - K₀ R^(α+1) cos(θ_i - ψ) [mean-field, careful derivation]
            # Actually, let me compute the actual oscillator-oscillator sum
            K_scaled = K0 / N
            coupling = np.zeros(N)
            for i in range(N):
                coupling[i] = K_scaled * (R ** alpha) * np.sum(np.sin(theta - theta[i]))
            dtheta = omega - coupling
        elif convention == 'C':
            # Same as A but with K₀/N normalization in front
            K_eff = (K0 / N) * (R ** alpha)
            dtheta = omega - K_eff * np.sin(theta - psi)
        
        theta = theta + dtheta * dt
        R_history.append(R)
    
    n_ss = int(0.2 * n_steps)
    R_ss = float(np.mean(R_history[-n_ss:]))
    return R_ss, R_history

def main():
    print("=" * 70)
    print("ALPHA DIVERGENCE: COUPLING CONVENTION TEST")
    print("=" * 70)
    
    N = 500
    T = 50.0
    dt = 0.01
    K0 = 5.0
    
    alpha_values = [0.5, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 2.0, 3.0, 4.0]
    
    np.random.seed(42)
    omega = np.random.uniform(-1, 1, N)
    theta_random = np.random.uniform(0, 2*np.pi, N)
    theta_seeded = np.random.uniform(-0.3, 0.3, N)
    
    for convention in ['A', 'C']:
        print(f"\nConvention {convention}:")
        print(f"  {'α':>6}  {'R_random':>10}  {'R_seeded':>10}  {'Disconnected':>14}")
        print("  " + "-" * 45)
        
        R_random_list = []
        R_seeded_list = []
        
        for alpha in alpha_values:
            np.random.seed(42)
            omega = np.random.uniform(-1, 1, N)
            theta_r = np.random.uniform(0, 2*np.pi, N)
            R_r, _ = run_kuramoto(N, K0, alpha, omega, theta_r, T, dt, convention)
            R_random_list.append(R_r)
            
            np.random.seed(42)
            omega = np.random.uniform(-1, 1, N)
            theta_s = np.random.uniform(-0.3, 0.3, N)
            R_s, _ = run_kuramoto(N, K0, alpha, omega, theta_s, T, dt, convention)
            R_seeded_list.append(R_s)
            
            disc = "YES" if (R_r < 0.3 and R_s > 0.8) else "no"
            print(f"  {alpha:6.1f}  {R_r:10.4f}  {R_s:10.4f}  {disc:>14}")
    
    print()
    print("=" * 70)
    print("TRANSIENT DYNAMICS: R(t) for various α")
    print("=" * 70)
    
    # Convention A with N=500
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    
    test_alphas = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    
    for idx, alpha in enumerate(test_alphas):
        ax = axes[idx // 3][idx % 3]
        
        # Random init
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta_r = np.random.uniform(0, 2*np.pi, N)
        R_r, R_traj_r = run_kuramoto(N, K0, alpha, omega, theta_r, T, dt, 'A')
        
        # Seeded init
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta_s = np.random.uniform(-0.3, 0.3, N)
        R_s, R_traj_s = run_kuramoto(N, K0, alpha, omega, theta_s, T, dt, 'A')
        
        t = np.linspace(0, T, len(R_traj_r))
        ax.plot(t, R_traj_r, 'r-', linewidth=1.5, label=f'Random ({R_r:.3f})')
        ax.plot(t, R_traj_s, 'b-', linewidth=1.5, label=f'Seeded ({R_s:.3f})')
        ax.set_title(f'α = {alpha}, K₀ = {K0}, N = {N}', fontsize=12)
        ax.set_xlabel('Time')
        ax.set_ylabel('R(t)')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.05)
    
    plt.suptitle(f'Reflexive Kuramoto Transient Dynamics (N={N}, K₀={K0})', fontsize=14, y=1.02)
    plt.tight_layout()
    output_path = 'shared_agora/artifacts/alpha_divergence_transients.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Figure saved to: {output_path}")
    
    # Now test with VERY large α to find where disconnection truly lies
    print()
    print("=" * 70)
    print("FINDING TRUE DISCONNECTION THRESHOLD at N=500")
    print("=" * 70)
    
    fine_alphas = np.arange(1.0, 4.1, 0.2)
    print(f"\nK₀ = {K0}:")
    print(f"  {'α':>6}  {'R_random':>10}")
    print("  " + "-" * 20)
    
    for alpha in fine_alphas:
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta_r = np.random.uniform(0, 2*np.pi, N)
        R_r, _ = run_kuramoto(N, K0, alpha, omega, theta_r, T, dt, 'A')
        print(f"  {alpha:6.1f}  {R_r:10.4f}")

    # Also test with lower K0 to see if it makes a difference
    print()
    for K0_test in [2.0, 3.0, 4.0, 6.0, 8.0, 10.0]:
        results_line = f"K₀ = {K0_test:4.1f}: "
        for alpha in [1.0, 1.2, 1.5, 2.0]:
            np.random.seed(42)
            omega = np.random.uniform(-1, 1, N)
            theta_r = np.random.uniform(0, 2*np.pi, N)
            R_r, _ = run_kuramoto(N, K0_test, alpha, omega, theta_r, T, dt, 'A')
            results_line += f"  α={alpha:.1f}:R={R_r:.3f}"
        print(results_line)

if __name__ == '__main__':
    main()