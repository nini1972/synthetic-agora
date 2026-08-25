"""
Thomas Attractor: Focused Critical Region Analysis
===================================================
Higher precision RK4 for both state and tangent vectors.
Focused on b in [0.18, 0.25] with finer resolution.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def compute_lyapunov_rk4(b_val, T_transient=100, T_measure=300, dt=0.01):
    """Compute maximal Lyapunov exponent using full RK4 for tangent vectors."""
    np.random.seed(42)
    
    state = np.array([0.1, 0.2, 0.3])
    v = np.array([1.0, 0.0, 0.0])  # Tangent vector
    
    n_transient = int(T_transient / dt)
    n_measure = int(T_measure / dt)
    n_total = n_transient + n_measure
    
    lyap_sum = 0.0
    count = 0
    
    def rhs(s, b):
        return np.array([np.sin(s[1]) - b * s[0],
                        np.sin(s[2]) - b * s[1],
                        np.sin(s[0]) - b * s[2]])
    
    def jacobian(s, b):
        x, y, z = s
        return np.array([[-b, np.cos(y), 0],
                        [0, -b, np.cos(z)],
                        [np.cos(x), 0, -b]])
    
    for i in range(n_total):
        # RK4 for state
        k1 = rhs(state, b_val)
        k2 = rhs(state + 0.5*dt*k1, b_val)
        k3 = rhs(state + 0.5*dt*k2, b_val)
        k4 = rhs(state + dt*k3, b_val)
        state = state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        
        # RK4 for tangent vector
        J1 = jacobian(state, b_val)
        k1v = J1 @ v
        k2v = J1 @ (v + 0.5*dt*k1v)
        k3v = J1 @ (v + 0.5*dt*k2v)
        k4v = J1 @ (v + dt*k3v)
        v = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
        
        # Renormalize and accumulate after transient
        if i >= n_transient:
            norm_v = np.linalg.norm(v)
            if norm_v > 0:
                lyap_sum += np.log(norm_v)
                v = v / norm_v
                count += 1
    
    if count > 0:
        return lyap_sum / (count * dt)
    return 0.0

def main():
    # Focused sweep on critical region
    b_values = np.arange(0.18, 0.25, 0.005)
    
    print("=" * 70)
    print("Thomas Attractor: Focused Critical Region Analysis")
    print("RK4 integration, dt=0.01, T_transient=100, T_measure=300")
    print("=" * 70)
    
    results = []
    for b in b_values:
        lyap1 = compute_lyapunov_rk4(b)
        results.append({'b': float(b), 'lyap_1': float(lyap1)})
        print(f"b = {b:.3f}: λ₁ = {lyap1:.6f}")
    
    bs = np.array([r['b'] for r in results])
    lyap1 = np.array([r['lyap_1'] for r in results])
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.plot(bs, lyap1, 'b-o', markersize=4, linewidth=1.5, label='Our replication (RK4)')
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax1.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c = 0.208186')
    ax1.set_xlabel('Dissipation parameter b', fontsize=12)
    ax1.set_ylabel('Maximal Lyapunov exponent λ₁', fontsize=12)
    ax1.set_title('Thomas Attractor: λ₁ in Critical Region (RK4)', fontsize=14)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Rate of change
    dlyap1 = np.diff(lyap1) / np.diff(bs)
    ax2.plot(bs[:-1], dlyap1, 'b-o', markersize=4)
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax2.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c')
    ax2.set_xlabel('Dissipation parameter b', fontsize=12)
    ax2.set_ylabel('dλ₁/db', fontsize=12)
    ax2.set_title('Rate of Change of λ₁', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    fig_path = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/thomas_critical_region_rk4.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\nFigure saved to: {fig_path}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Find minimum
    min_idx = np.argmin(lyap1)
    print(f"Minimum λ₁ = {lyap1[min_idx]:.6f} at b = {bs[min_idx]:.3f}")
    
    # Find zero crossing
    sign_changes = []
    for i in range(len(lyap1)-1):
        if lyap1[i] * lyap1[i+1] < 0:
            b_cross = bs[i] + (bs[i+1] - bs[i]) * (-lyap1[i]) / (lyap1[i+1] - lyap1[i])
            sign_changes.append(b_cross)
    
    if sign_changes:
        print(f"λ₁ crosses zero at b ≈ {sign_changes[0]:.4f}")
        print("→ SUPPORTS CRISIS BIFURCATION HYPOTHESIS")
    else:
        if all(lyap1 > 0):
            print("λ₁ > 0 for all tested b → No bifurcation detected")
            print("→ CONTRADICTS CRISIS BIFURCATION HYPOTHESIS")
            if lyap1[min_idx] < 0.01:
                print(f"  BUT λ₁ is very small ({lyap1[min_idx]:.4f}) near b = {bs[min_idx]:.3f}")
                print("  → System is NEAR critical but doesn't cross")
        elif all(lyap1 < 0):
            print("λ₁ < 0 for all tested b → System non-chaotic throughout")
    
    # Check monotonicity
    diffs = np.diff(lyap1)
    if all(diffs < 0):
        print("\nλ₁ is MONOTONICALLY DECREASING → Supports EMP-011's smooth transition claim")
    elif all(diffs > 0):
        print("\nλ₁ is MONOTONICALLY INCREASING")
    else:
        # Find local minima
        local_min_idx = []
        for i in range(1, len(lyap1)-1):
            if lyap1[i] < lyap1[i-1] and lyap1[i] < lyap1[i+1]:
                local_min_idx.append(i)
        if local_min_idx:
            print(f"\nλ₁ has LOCAL MINIMUM at b = {bs[local_min_idx[0]]:.3f}")
            print("→ NON-MONOTONIC behavior detected")
    
    # Save results
    results_path = '/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/thomas_critical_region_results.json'
    with open(results_path, 'w') as f:
        json.dump({
            'b_values': [float(b) for b in bs],
            'lyap_1': [float(l) for l in lyap1],
            'sign_changes': [float(s) for s in sign_changes],
            'min_lyap': float(lyap1[min_idx]),
            'min_b': float(bs[min_idx]),
            'claimed_bc': 0.208186
        }, f, indent=2)
    print(f"\nResults saved to: {results_path}")

if __name__ == '__main__':
    main()
