"""
Thomas Attractor Lyapunov Spectrum - Ultra-Fast Replication
Uses vectorized numpy operations and minimal integration time.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def compute_lyapunov_fast(b_val, T_total=100, dt=0.05):
    """Compute maximal Lyapunov exponent - ultra fast version."""
    np.random.seed(42)
    
    state = np.array([0.1, 0.2, 0.3])
    v = np.array([1.0, 0.0, 0.0])  # Single tangent vector for max Lyapunov
    
    n_steps = int(T_total / dt)
    lyap_sum = 0.0
    n_measure = 0
    
    for i in range(n_steps):
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
        
        # Jacobian
        x, y, z = state
        J = np.array([[-b_val, np.cos(y), 0],
                      [0, -b_val, np.cos(z)],
                      [np.cos(x), 0, -b_val]])
        
        # Evolve tangent vector (Euler for speed)
        v = v + dt * (J @ v)
        
        # Renormalize and accumulate after transient
        if i > 100:  # Shorter transient
            norm_v = np.linalg.norm(v)
            if norm_v > 0:
                lyap_sum += np.log(norm_v)
                v = v / norm_v
                n_measure += 1
    
    if n_measure > 0:
        return lyap_sum / (n_measure * dt)
    return 0.0

def main():
    # Coarse sweep with focus near critical region
    b_values = np.array([0.05, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.19, 
                         0.195, 0.20, 0.205, 0.208, 0.21, 0.215, 0.22, 0.23, 
                         0.25, 0.28, 0.30])
    
    print("=" * 70)
    print("Thomas Attractor - Ultra-Fast Lyapunov Replication")
    print("=" * 70)
    
    results = []
    for b in b_values:
        lyap1 = compute_lyapunov_fast(b)
        results.append({'b': float(b), 'lyap_1': float(lyap1)})
        print(f"b = {b:.3f}: λ₁ = {lyap1:.6f}")
    
    bs = [r['b'] for r in results]
    lyap1 = [r['lyap_1'] for r in results]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.plot(bs, lyap1, 'b-o', markersize=6, linewidth=2, label='Our replication')
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax1.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c = 0.208186')
    ax1.fill_between(bs, 0.22, 0.36, alpha=0.2, color='green', label='EMP-011 range (MiniMax)')
    ax1.axhline(y=0.035, color='orange', linestyle=':', alpha=0.7, label='Dossier λ₁ ≈ 0.035')
    ax1.set_xlabel('Dissipation parameter b', fontsize=12)
    ax1.set_ylabel('Maximal Lyapunov exponent λ₁', fontsize=12)
    ax1.set_title('Thomas Attractor: λ₁ vs Dissipation', fontsize=14)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Rate of change
    dlyap1 = np.diff(lyap1) / np.diff(bs)
    ax2.plot(bs[:-1], dlyap1, 'b-o', markersize=6)
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax2.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c')
    ax2.set_xlabel('Dissipation parameter b', fontsize=12)
    ax2.set_ylabel('dλ₁/db', fontsize=12)
    ax2.set_title('Rate of Change of λ₁', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    fig_path = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/thomas_independent_replication.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\nFigure saved to: {fig_path}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    lyap1_arr = np.array(lyap1)
    bs_arr = np.array(bs)
    
    # Find zero crossing
    sign_changes = []
    for i in range(len(lyap1_arr)-1):
        if lyap1_arr[i] * lyap1_arr[i+1] < 0:
            b_cross = bs_arr[i] + (bs_arr[i+1] - bs_arr[i]) * (-lyap1_arr[i]) / (lyap1_arr[i+1] - lyap1_arr[i])
            sign_changes.append(b_cross)
    
    if sign_changes:
        print(f"λ₁ crosses zero at b ≈ {sign_changes[0]:.4f}")
    else:
        if all(lyap1_arr > 0):
            print("λ₁ > 0 for ALL tested b values → System remains CHAOTIC throughout")
        elif all(lyap1_arr < 0):
            print("λ₁ < 0 for ALL tested b values → System is NON-CHAOTIC throughout")
        else:
            print("No clean zero crossing detected")
    
    print(f"\nλ₁ range: [{min(lyap1_arr):.4f}, {max(lyap1_arr):.4f}]")
    
    # Check near claimed b_c
    idx_bc = np.argmin(np.abs(bs_arr - 0.208))
    print(f"\nAt b ≈ 0.208 (claimed critical): λ₁ = {lyap1_arr[idx_bc]:.4f}")
    
    # Check for sharp vs smooth transition
    dlyap1_arr = np.diff(lyap1_arr) / np.diff(bs_arr)
    max_jump_idx = np.argmax(np.abs(dlyap1_arr))
    print(f"Max |dλ₁/db| = {abs(dlyap1_arr[max_jump_idx]):.2f} at b = {bs_arr[max_jump_idx]:.3f}")
    
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    # Determine which camp we support
    if sign_changes:
        b_crit = sign_changes[0]
        if abs(b_crit - 0.208186) < 0.03:
            print("SUPPORTS Dossier #002: Transition from chaos to order near b_c ≈ 0.208")
        else:
            print(f"PARTIALLY SUPPORTS: Found transition at b ≈ {b_crit:.3f}, not exactly at 0.208")
    elif all(lyap1_arr > 0):
        print("SUPPORTS EMP-011 (MiniMax): No bifurcation found, system chaotic throughout")
    elif all(lyap1_arr < 0):
        print("SUPPORTS Dossier #002: System non-chaotic in tested range")
    
    # Save results
    results_path = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/thomas_replication_results.json'
    with open(results_path, 'w') as f:
        json.dump({
            'b_values': [float(b) for b in bs],
            'lyap_1': [float(l) for l in lyap1],
            'sign_changes': [float(s) for s in sign_changes],
            'claimed_bc': 0.208186
        }, f, indent=2)

if __name__ == '__main__':
    main()
