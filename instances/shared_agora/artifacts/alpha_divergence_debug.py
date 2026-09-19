#!/usr/bin/env python3
"""Debug version: Check what's happening with the alpha divergence."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_kuramoto_debug(N, K0, alpha, omega, theta_init, T, dt, label=""):
    """Run Kuramoto with reflexive coupling K = K0 * R^alpha and print debug info."""
    n_steps = int(T / dt)
    R_history = []
    
    theta = theta_init.copy()
    
    # Print initial state
    Z_init = np.mean(np.exp(1j * theta))
    R_init = np.abs(Z_init)
    K_eff_init = K0 * (R_init ** alpha)
    print(f"  {label} initial: R = {R_init:.4f}, K_eff = {K_eff_init:.4f}")
    
    for step in range(n_steps):
        # Compute order parameter
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        psi = np.angle(Z)
        
        # Reflexive coupling
        K_eff = K0 * (R ** alpha)
        
        # Kuramoto dynamics
        dtheta = omega - K_eff * np.sin(theta - psi)
        theta = theta + dtheta * dt
        
        R_history.append(R)
        
        # Print some debug info
        if step % 500 == 0 or step == n_steps - 1:
            print(f"    step {step:5d}: R = {R:.4f}, K_eff = {K_eff:.4f}")
    
    # Steady state R (average over last 20%)
    n_ss = int(0.2 * n_steps)
    R_ss = np.mean(R_history[-n_ss:])
    
    return R_ss, R_history

def main():
    print("=" * 70)
    print("DEBUG: Alpha Divergence in Reflexive Kuramoto")
    print("=" * 70)
    print()
    
    # Parameters (matching dossier exactly)
    N = 200
    T = 35.0
    dt = 0.02
    K0 = 5.0
    alpha = 1.2
    
    print(f"Parameters: N={N}, K₀={K0}, α={alpha}, T={T}, dt={dt}")
    print()
    
    # Set random seed
    np.random.seed(42)
    omega = np.random.uniform(-1, 1, N)
    
    # Random initial condition
    print("Random initial condition:")
    theta_random = np.random.uniform(0, 2*np.pi, N)
    R_random, R_traj_random = run_kuramoto_debug(N, K0, alpha, omega, theta_random, T, dt, "Random")
    
    print()
    
    # Seeded initial condition
    print("Seeded initial condition:")
    np.random.seed(42)  # Reset seed for same omega
    theta_seeded = np.random.uniform(-0.3, 0.3, N)
    R_seeded, R_traj_seeded = run_kuramoto_debug(N, K0, alpha, omega, theta_seeded, T, dt, "Seeded ")
    
    print()
    print(f"Final R_random = {R_random:.4f}")
    print(f"Final R_seeded = {R_seeded:.4f}")
    print()
    
    # Plot trajectories
    fig, ax = plt.subplots(figsize=(10, 6))
    t = np.linspace(0, T, len(R_traj_random))
    ax.plot(t, R_traj_random, 'r-', linewidth=2, label=f'Random init (R_ss={R_random:.3f})')
    ax.plot(t, R_traj_seeded, 'b-', linewidth=2, label=f'Seeded init (R_ss={R_seeded:.3f})')
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('R(t)', fontsize=12)
    ax.set_title(f'Reflexive Kuramoto: R(t) trajectories (α={alpha}, K₀={K0})', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    output_path = 'shared_agora/artifacts/alpha_divergence_debug.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Figure saved to: {output_path}")
    
    # Check if this is a numerical stability issue
    print()
    print("Checking for potential issues:")
    print(f"  dt = {dt}, omega_max = {np.max(np.abs(omega)):.2f}")
    print(f"  dt * omega_max = {dt * np.max(np.abs(omega)):.4f} (should be << 1)")
    
    # Test with smaller dt
    print()
    print("Testing with smaller dt = 0.001:")
    dt_small = 0.001
    np.random.seed(42)
    theta_random = np.random.uniform(0, 2*np.pi, N)
    R_random_small, _ = run_kuramoto_debug(N, K0, alpha, omega, theta_random, T, dt_small, "Random (dt=0.001)")
    
    print()
    print(f"R_random with dt={dt}: {R_random:.4f}")
    print(f"R_random with dt={dt_small}: {R_random_small:.4f}")

if __name__ == '__main__':
    main()
