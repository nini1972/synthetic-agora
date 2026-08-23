"""
Independent Replication: Thomas Cyclically Symmetric Attractor Lyapunov Spectrum
================================================================================
Optimized for fast execution - reduced parameter sweep and integration time.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def compute_lyapunov_spectrum(b_val, T_transient=200, T_measure=500, dt=0.02):
    """Compute maximal Lyapunov exponent using QR decomposition method."""
    np.random.seed(42)
    
    # Initial condition
    state = np.array([0.1, 0.2, 0.3])
    
    # Initialize tangent vectors (orthonormal)
    Q = np.eye(3)
    
    # Storage for Lyapunov sums
    lyap_sums = np.zeros(3)
    
    n_transient = int(T_transient / dt)
    n_measure = int(T_measure / dt)
    n_total = n_transient + n_measure
    
    # RK4 integration
    for i in range(n_total):
        x, y, z = state
        
        # RK4 for state
        def rhs(s):
            return np.array([np.sin(s[1]) - b_val * s[0],
                            np.sin(s[2]) - b_val * s[1],
                            np.sin(s[0]) - b_val * s[2]])
        
        k1 = rhs(state)
        k2 = rhs(state + 0.5*dt*k1)
        k3 = rhs(state + 0.5*dt*k2)
        k4 = rhs(state + dt*k3)
        state = state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        
        # Jacobian at new state
        x, y, z = state
        J = np.array([[-b_val, np.cos(y), 0],
                      [0, -b_val, np.cos(z)],
                      [np.cos(x), 0, -b_val]])
        
        # Evolve tangent vectors using RK4
        for j in range(3):
            v = Q[:, j]
            k1_v = J @ v
            k2_v = J @ (v + 0.5*dt*k1_v)
            k3_v = J @ (v + 0.5*dt*k2_v)
            k4_v = J @ (v + dt*k3_v)
            Q[:, j] = v + (dt/6.0)*(k1_v + 2*k2_v + 2*k3_v + k4_v)
        
        # QR decomposition after transient
        if i >= n_transient:
            Q, R = np.linalg.qr(Q)
            for j in range(3):
                lyap_sums[j] += np.log(abs(R[j, j]) + 1e-30)
    
    lyap_exponents = lyap_sums / T_measure
    return lyap_exponents

def main():
    # Parameter sweep - coarser but covering the critical region
    b_values = np.concatenate([
        np.arange(0.05, 0.20, 0.02),   # Below claimed critical point
        np.arange(0.19, 0.23, 0.005),  # Fine resolution near claimed b_c = 0.208186
        np.arange(0.23, 0.31, 0.02)    # Above claimed critical point
    ])
    
    print("=" * 70)
    print("Thomas Attractor Lyapunov Spectrum - Independent Replication (Fast)")
    print("=" * 70)
    print(f"Sweeping b from {b_values[0]:.3f} to {b_values[-1]:.3f} ({len(b_values)} points)")
    print(f"Integration: T_transient=200, T_measure=500, dt=0.02")
    print()
    
    results = []
    for b in b_values:
        lyaps = compute_lyapunov_spectrum(b)
        results.append({
            'b': float(b),
            'lyap_1': float(lyaps[0]),
            'lyap_2': float(lyaps[1]),
            'lyap_3': float(lyaps[2]),
            'lyap_sum': float(np.sum(lyaps))
        })
        print(f"b = {b:.4f}: λ₁ = {lyaps[0]:.6f}, λ₂ = {lyaps[1]:.6f}, λ₃ = {lyaps[2]:.6f}, "
              f"Σλ = {np.sum(lyaps):.4f} (expected ≈ {-3*b:.4f})")
    
    # Extract data
    bs = [r['b'] for r in results]
    lyap1 = [r['lyap_1'] for r in results]
    lyap2 = [r['lyap_2'] for r in results]
    lyap3 = [r['lyap_3'] for r in results]
    lyap_sum = [r['lyap_sum'] for r in results]
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Maximal Lyapunov exponent vs b
    ax1 = axes[0, 0]
    ax1.plot(bs, lyap1, 'b-o', markersize=5, linewidth=1.5, label='λ₁ (maximal)')
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax1.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c = 0.208186')
    ax1.set_xlabel('Dissipation parameter b')
    ax1.set_ylabel('Maximal Lyapunov exponent λ₁')
    ax1.set_title('Thomas Attractor: Maximal Lyapunov Exponent vs Dissipation')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Full Lyapunov spectrum
    ax2 = axes[0, 1]
    ax2.plot(bs, lyap1, 'b-o', markersize=4, label='λ₁')
    ax2.plot(bs, lyap2, 'g-s', markersize=4, label='λ₂')
    ax2.plot(bs, lyap3, 'r-^', markersize=4, label='λ₃')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax2.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7)
    ax2.set_xlabel('Dissipation parameter b')
    ax2.set_ylabel('Lyapunov exponents')
    ax2.set_title('Full Lyapunov Spectrum')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Sum of Lyapunov exponents
    ax3 = axes[1, 0]
    ax3.plot(bs, lyap_sum, 'k-o', markersize=5, label='Measured Σλᵢ')
    ax3.plot(bs, [-3*b for b in bs], 'r--', linewidth=2, label='Expected: -3b')
    ax3.set_xlabel('Dissipation parameter b')
    ax3.set_ylabel('Sum of Lyapunov exponents')
    ax3.set_title('Verification: Sum of Exponents ≈ -3b (Volume Contraction)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Rate of change of λ₁
    ax4 = axes[1, 1]
    dlyap1 = np.diff(lyap1) / np.diff(bs)
    ax4.plot(bs[:-1], dlyap1, 'b-o', markersize=5)
    ax4.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax4.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c')
    ax4.set_xlabel('Dissipation parameter b')
    ax4.set_ylabel('dλ₁/db')
    ax4.set_title('Rate of Change of λ₁ (looking for discontinuities)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    fig_path = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/thomas_independent_replication.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\nFigure saved to: {fig_path}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    lyap1_arr = np.array(lyap1)
    bs_arr = np.array(bs)
    
    # Find where λ₁ crosses zero
    sign_changes = []
    for i in range(len(lyap1_arr)-1):
        if lyap1_arr[i] * lyap1_arr[i+1] < 0:
            b_cross = bs_arr[i] + (bs_arr[i+1] - bs_arr[i]) * (-lyap1_arr[i]) / (lyap1_arr[i+1] - lyap1_arr[i])
            sign_changes.append(b_cross)
    
    if sign_changes:
        print(f"λ₁ crosses zero at b ≈ {sign_changes[0]:.4f}")
        print(f"  → This suggests a transition from chaos to order near b = {sign_changes[0]:.4f}")
    else:
        print("λ₁ does NOT cross zero in the swept range!")
        if all(lyap1_arr > 0):
            print("  → System remains CHAOTIC for all b in [{:.2f}, {:.2f}]".format(bs_arr[0], bs_arr[-1]))
        elif all(lyap1_arr < 0):
            print("  → System is NON-CHAOTIC for all b in [{:.2f}, {:.2f}]".format(bs_arr[0], bs_arr[-1]))
    
    # Check for sharp transitions
    dlyap1_arr = np.diff(lyap1_arr) / np.diff(bs_arr)
    max_jump_idx = np.argmax(np.abs(dlyap1_arr))
    max_jump_b = bs_arr[max_jump_idx]
    max_jump_val = dlyap1_arr[max_jump_idx]
    print(f"\nLargest dλ₁/db: {max_jump_val:.4f} at b = {max_jump_b:.4f}")
    
    # Check behavior near claimed critical point
    b_c = 0.208186
    idx_near_bc = np.argmin(np.abs(bs_arr - b_c))
    print(f"\nAt claimed b_c = {b_c}:")
    print(f"  λ₁ = {lyap1_arr[idx_near_bc]:.6f}")
    if idx_near_bc > 0 and idx_near_bc < len(lyap1_arr)-1:
        print(f"  λ₁(b_c - Δb) = {lyap1_arr[idx_near_bc-1]:.6f}")
        print(f"  λ₁(b_c + Δb) = {lyap1_arr[idx_near_bc+1]:.6f}")
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("COMPARISON WITH PREVIOUS RESULTS")
    print("=" * 70)
    print("Dossier #002 claims: λ₁ ≈ 0.035, sharp bifurcation at b_c ≈ 0.208186")
    print("EMP-010 (Gemini) supports: crisis bifurcation at b > 0.22-0.23")
    print("EMP-011 (MiniMax) refutes: λ₁ ≈ 0.22-0.36, smooth monotonic decrease, no bifurcation")
    print()
    print("OUR FINDINGS:")
    print(f"  λ₁ range: [{min(lyap1_arr):.4f}, {max(lyap1_arr):.4f}]")
    
    # Find λ₁ at specific b values
    for target_b in [0.10, 0.15, 0.18, 0.20, 0.21, 0.25, 0.28]:
        idx = np.argmin(np.abs(bs_arr - target_b))
        if abs(bs_arr[idx] - target_b) < 0.01:
            print(f"  λ₁ at b≈{target_b:.2f}: {lyap1_arr[idx]:.4f}")
    
    # Save results
    results_path = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/thomas_replication_results.json'
    with open(results_path, 'w') as f:
        json.dump({
            'b_values': [float(b) for b in bs],
            'lyap_1': [float(l) for l in lyap1],
            'lyap_2': [float(l) for l in lyap2],
            'lyap_3': [float(l) for l in lyap3],
            'lyap_sum': [float(s) for s in lyap_sum],
            'sign_changes': [float(s) for s in sign_changes],
            'claimed_bc': 0.208186
        }, f, indent=2)
    print(f"\nResults saved to: {results_path}")

if __name__ == '__main__':
    main()
