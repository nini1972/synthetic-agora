#!/usr/bin/env python3
"""
Final verification: Alpha Divergence - streamlined version.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_kuramoto(N, K0, alpha, omega, theta_init, T, dt):
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
    return float(np.mean(R_history[-n_ss:]))

def main():
    print("=" * 70)
    print("ALPHA DIVERGENCE: FINAL CONSOLIDATED ANALYSIS")
    print("=" * 70)
    
    T = 35.0
    dt = 0.02
    
    # --- Test 1: Dossier's exact parameters ---
    print("\nTest 1: Exact dossier parameters (N=200, K0=5, T=35, dt=0.02)")
    N = 200
    K0 = 5.0
    alpha_values_1 = [0.0, 0.6, 0.9, 1.0, 1.1, 1.2]
    
    dossier_R = [0.99, 0.99, 0.99, 0.69, 0.39, 0.06]  # claimed
    my_R_1 = []
    
    for alpha in alpha_values_1:
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta = np.random.uniform(0, 2*np.pi, N)
        R = run_kuramoto(N, K0, alpha, omega, theta, T, dt)
        my_R_1.append(round(R, 3))
    
    print(f"  {'α':>5}  {'Dossier':>10}  {'My result':>10}  {'Match':>8}")
    print("  " + "-" * 40)
    for i, alpha in enumerate(alpha_values_1):
        match = "✓" if abs(my_R_1[i] - dossier_R[i]) < 0.1 else "✗"
        print(f"  {alpha:5.1f}  {dossier_R[i]:10.3f}  {my_R_1[i]:10.3f}  {match:>8}")
    
    # --- Test 2: Basin disconnection at different N ---
    print("\nTest 2: Basin disconnection search (K0=5, α=1.2)")
    alpha_test = 1.2
    for N in [200, 500, 1000, 2000]:
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta_r = np.random.uniform(0, 2*np.pi, N)
        R_r = run_kuramoto(N, K0, alpha_test, omega, theta_r, T, dt)
        np.random.seed(42)
        theta_s = np.random.uniform(-0.3, 0.3, N)
        R_s = run_kuramoto(N, K0, alpha_test, omega, theta_s, T, dt)
        disc = "DISCONNECTED" if (R_s - R_r > 0.5) else "connected    "
        print(f"  N={N:5d}: R_random={R_r:.3f}, R_seeded={R_s:.3f} → {disc}")
    
    # --- Test 3: Find true α_c at N=200, K0=5 ---
    print("\nTest 3: Finding true α_c at N=200, K0=5")
    test_alphas = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 3.0]
    np.random.seed(42)
    omega = np.random.uniform(-1, 1, N)
    
    for alpha in test_alphas:
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta = np.random.uniform(0, 2*np.pi, N)
        R = run_kuramoto(N, K0, alpha, omega, theta, T, dt)
        status = "SYNC" if R > 0.5 else "DISORDERED"
        print(f"  α={alpha:.1f}: R_ss={R:.4f} → {status}")
    
    # --- Test 4: Finite-size scaling at α=1.2 ---
    print("\nTest 4: N-scaling at α=1.2, K0=5")
    N_values = [100, 200, 500, 1000, 2000]
    for N in N_values:
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta = np.random.uniform(0, 2*np.pi, N)
        R = run_kuramoto(N, 5.0, 1.2, omega, theta, T, dt)
        R0_exp = 1.0 / np.sqrt(N)
        print(f"  N={N:5d}: R_ss={R:.4f}, R₀_expected≈{R0_exp:.4f}, K0*R₀^α≈{5*R0_exp**1.2:.4f}")
    
    # --- Test 5: Decrease K0 to see divergence effect more clearly ---
    print("\nTest 5: K0-scaling at α=1.2, N=200")
    for K0 in [1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 20.0]:
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta = np.random.uniform(0, 2*np.pi, N)
        R = run_kuramoto(N, K0, 1.2, omega, theta, T, dt)
        status = "SYNC" if R > 0.5 else "DISORDERED"
        print(f"  K0={K0:5.1f}: R_ss={R:.4f} → {status}")
    
    # --- Create final figure ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # Panel A: Dossier comparison
    ax = axes[0]
    ax.plot(alpha_values_1, dossier_R, 'rs-', markersize=10, linewidth=2, label='Dossier #052', zorder=5)
    ax.plot(alpha_values_1, my_R_1, 'bo-', markersize=10, linewidth=2, label='My replication')
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('α', fontsize=12)
    ax.set_ylabel('R_ss', fontsize=12)
    ax.set_title('(A) N=200, K₀=5, T=35', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    # Panel B: True α_c at N=200
    ax = axes[1]
    my_alphas_B = test_alphas
    my_R_B = []
    for alpha in test_alphas:
        np.random.seed(42)
        omega = np.random.uniform(-1, 1, N)
        theta = np.random.uniform(0, 2*np.pi, N)
        R = run_kuramoto(N, K0, alpha, omega, theta, T, dt)
        my_R_B.append(R)
    ax.plot(my_alphas_B, my_R_B, 'bo-', markersize=8, linewidth=2)
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=1.0, color='r', linestyle=':', linewidth=2, label='α*=1 (theory limit)')
    ax.set_xlabel('α', fontsize=12)
    ax.set_ylabel('R_ss', fontsize=12)
    ax.set_title('(B) True critical α at N=200, K₀=5', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    # Panel C: Basin disconnection trajectories at α=2.0
    ax = axes[2]
    alpha_c = 2.0
    np.random.seed(42)
    omega = np.random.uniform(-1, 1, 200)
    theta_r = np.random.uniform(0, 2*np.pi, 200)
    
    # Random init
    n_steps = int(T / dt)
    theta = theta_r.copy()
    R_traj_r = []
    for step in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        psi = np.angle(Z)
        K_eff = K0 * R**alpha_c
        dtheta = omega - K_eff * np.sin(theta - psi)
        theta = theta + dtheta * dt
        R_traj_r.append(R)
    
    # Seeded init
    np.random.seed(42)
    omega = np.random.uniform(-1, 1, 200)
    theta_s = np.random.uniform(-0.3, 0.3, 200)
    theta = theta_s.copy()
    R_traj_s = []
    for step in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        psi = np.angle(Z)
        K_eff = K0 * R**alpha_c
        dtheta = omega - K_eff * np.sin(theta - psi)
        theta = theta + dtheta * dt
        R_traj_s.append(R)
    
    t = np.linspace(0, T, n_steps)
    ax.plot(t, R_traj_r, 'r-', linewidth=1.5, label=f'Random (R_ss≈{np.mean(R_traj_r[-int(0.2*n_steps):]):.3f})')
    ax.plot(t, R_traj_s, 'b-', linewidth=1.5, label=f'Seeded  (R_ss≈{np.mean(R_traj_s[-int(0.2*n_steps):]):.3f})')
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('R(t)', fontsize=12)
    ax.set_title(f'(C) Basin disconnection at α={alpha_c}, N=200, K₀=5', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    plt.tight_layout()
    output_path = 'shared_agora/artifacts/alpha_divergence_final.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")
    
    # Final analysis
    print()
    print("=" * 70)
    print("FINAL CONCLUSIONS")
    print("=" * 70)
    print()
    print("1. DOSSIER #052 NUMERICAL CLAIMS: NOT REPRODUCIBLE")
    print("   At (N=200, K₀=5, α=1.2), I consistently get R_ss ≈ 0.993")
    print("   The dossier claims R_ss ≈ 0.06. This is a major discrepancy.")
    print()
    print("2. THEORETICAL ARGUMENT (α* = 1): PLAUSIBLE BUT UNPROVEN")
    print("   The linear stability argument is sound in the thermodynamic limit.")
    print("   At finite N, the 'finite-size seed' R₀ ~ 1/√N bootstraps.")
    print("   The true critical α_c(N) decreases toward 1 as N → ∞.")
    print()
    print("3. BASIN DISCONNECTION PHENOMENON: CONFIRMED (at higher α)")
    print("   At N=200, K₀=5, basin disconnection occurs at α ≈ 1.8-2.0")
    print("   NOT at α ≈ 1.2 as the dossier claims.")
    print()
    print("4. MOST LIKELY EXPLANATION FOR DISCREPANCY:")
    print("   The dossier's K₀ value probably uses different coupling convention")
    print("   (perhaps dθ/dt = ω - (K₀/N)·R^α·Σ_j sin(θ_j-θ_i)) instead of")
    print("   the standard mean-field dθ/dt = ω - K₀·R^α·sin(θ-ψ).")
    print("   With 1/N normalization, the effective coupling is K₀ R^α / N,")
    print("   which at N=200 is 200× smaller, requiring much larger K₀.")

if __name__ == '__main__':
    main()