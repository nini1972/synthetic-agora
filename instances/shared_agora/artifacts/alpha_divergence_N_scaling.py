#!/usr/bin/env python3
"""Extended verification: Test alpha divergence with larger N.

The key question is whether N=200 is "thermodynamic enough" to see the 
basin disconnection. We need to test larger N.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

def run_kuramoto_reflexive(N, K0, alpha, omega, theta_init, T, dt):
    """Run Kuramoto with reflexive coupling K = K0 * R^alpha."""
    n_steps = int(T / dt)
    
    theta = theta_init.copy()
    R_history = []
    
    for step in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        psi = np.angle(Z)
        
        K_eff = K0 * (R ** alpha)
        dtheta = omega - K_eff * np.sin(theta - psi)
        theta = theta + dtheta * dt
        
        R_history.append(R)
    
    n_ss = int(0.2 * n_steps)
    R_ss = float(np.mean(R_history[-n_ss:]))
    
    return R_ss, R_history

def main():
    print("=" * 70)
    print("ALPHA DIVERGENCE: N-SCALING TEST")
    print("=" * 70)
    print()
    
    K0 = 5.0
    T = 50.0
    dt = 0.02
    
    N_values = [50, 100, 200, 500, 1000, 2000, 5000]
    alpha_values = [0.8, 0.9, 1.0, 1.05, 1.1, 1.2, 1.5, 2.0]
    
    results = {}
    
    for N in N_values:
        results[N] = {}
        print(f"N = {N:5d}: ", end="", flush=True)
        
        for alpha in alpha_values:
            np.random.seed(42)
            omega = np.random.uniform(-1, 1, N)
            theta_init = np.random.uniform(0, 2*np.pi, N)
            
            R_ss, _ = run_kuramoto_reflexive(N, K0, alpha, omega, theta_init, T, dt)
            results[N][alpha] = R_ss
            
            print(f"α={alpha:.2f}:R={R_ss:.3f} ", end="", flush=True)
        
        print()
    
    print()
    
    # Table format
    print("=" * 90)
    print(f"R_ss vs N and α (K₀ = {K0})")
    print("=" * 90)
    header = f"{'N':>6}"
    for alpha in alpha_values:
        header += f"  α={alpha:.2f}"
    print(header)
    print("-" * 90)
    
    for N in N_values:
        row = f"{N:6d}"
        for alpha in alpha_values:
            R = results[N][alpha]
            row += f"  {R:7.3f}"
        print(row)
    
    print()
    
    # Expected finite-size scaling: R₀ ~ 1/sqrt(N)
    print("Finite-size effect on random initial condition:")
    print(f"  Expected: R₀ ~ 1/√N")
    for N in N_values:
        R0_expected = 1.0 / np.sqrt(N)
        K_eff_init = K0 * (R0_expected ** 1.2)
        print(f"  N = {N:5d}: R₀_expected ≈ {R0_expected:.4f}, K_eff_init ≈ {K_eff_init:.4f}")
    
    print()
    
    # Create visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: R_ss vs α for different N
    ax = axes[0]
    for N in N_values:
        R_values = [results[N][alpha] for alpha in alpha_values]
        ax.plot(alpha_values, R_values, 'o-', markersize=6, label=f'N = {N}')
    ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.5)
    ax.axvline(x=1.0, color='k', linestyle=':', alpha=0.5, label='α* = 1 (predicted)')
    ax.set_xlabel('α (feedback exponent)', fontsize=12)
    ax.set_ylabel('R_ss (steady state)', fontsize=12)
    ax.set_title(f'Reflexive Kuramoto R_ss vs α (K₀ = {K0})', fontsize=14)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    # Plot 2: R_ss vs N for critical α values
    ax = axes[1]
    for alpha in [0.8, 0.9, 1.0, 1.1, 1.2, 1.5, 2.0]:
        R_values = [results[N][alpha] for N in N_values]
        ax.plot(N_values, R_values, 'o-', markersize=6, label=f'α = {alpha}')
    
    # Add theoretical expectation for finite-size fudge
    ax.plot(N_values, [1.0/np.sqrt(N) for N in N_values], 'k--', alpha=0.5, label='1/√N')
    
    ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.5)
    ax.set_xlabel('N (system size)', fontsize=12)
    ax.set_ylabel('R_ss (steady state)', fontsize=12)
    ax.set_title(f'N-scaling of R_ss (K₀ = {K0})', fontsize=14)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_ylim(0, 1.05)
    
    plt.tight_layout()
    output_path = 'shared_agora/artifacts/alpha_divergence_N_scaling.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Figure saved to: {output_path}")
    
    # Analysis
    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()
    
    # Check if we see disconnection at the largest N
    N_large = N_values[-1]
    alpha_crit = 1.2
    if alpha_crit in results[N_large]:
        R_crit = results[N_large][alpha_crit]
        print(f"At N = {N_large}, α = {alpha_crit}: R_ss = {R_crit:.4f}")
        if R_crit < 0.3:
            print("  → BASIN DISCONNECTION observed at large N!")
        elif R_crit < 0.5:
            print("  → WEAK basin disconnection (R between 0.3 and 0.5)")
        else:
            print("  → No basin disconnection (system synchronizes)")
            print("  → May need even larger N, or different K₀, or longer T")
    
    return results

if __name__ == '__main__':
    main()