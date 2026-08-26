"""
Fast Replication: Thomas Attractor Lyapunov Spectrum (Critical Region)
====================================================================
Purpose: Verify the dip in λ₁ and sharp change in dλ₁/db near b ≈ 0.208.
Method: Reduced integration times and focused sweep on b ∈ [0.18, 0.24].
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def thomas_rhs(t, state, b):
    x, y, z = state
    return [np.sin(y) - b * x, np.sin(z) - b * y, np.sin(x) - b * z]

def thomas_jacobian(state, b):
    x, y, z = state
    return np.array([
        [-b, np.cos(y), 0],
        [0, -b, np.cos(z)],
        [np.cos(x), 0, -b]
    ])

def compute_lyapunov_spectrum(b_val, T_transient=100, T_measure=200, dt=0.01, n_lyap=3, seed=42):
    np.random.seed(seed)
    state = np.array([0.1, 0.2, 0.3])
    Q = np.eye(n_lyap)
    lyap_sums = np.zeros(n_lyap)
    
    n_transient = int(T_transient / dt)
    n_measure = int(T_measure / dt)
    n_total = n_transient + n_measure
    
    for i in range(n_total):
        # RK4 for state
        k1 = np.array(thomas_rhs(0, state, b_val))
        k2 = np.array(thomas_rhs(0, state + 0.5*dt*k1, b_val))
        k3 = np.array(thomas_rhs(0, state + 0.5*dt*k2, b_val))
        k4 = np.array(thomas_rhs(0, state + dt*k3, b_val))
        state = state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        
        # Evolve tangent vectors (RK4)
        J = thomas_jacobian(state, b_val)
        for j in range(n_lyap):
            v = Q[:, j]
            k1_v = J @ v
            k2_v = J @ (v + 0.5*dt*k1_v)
            k3_v = J @ (v + 0.5*dt*k2_v)
            k4_v = J @ (v + dt*k3_v)
            Q[:, j] = v + (dt/6.0)*(k1_v + 2*k2_v + 2*k3_v + k4_v)
        
        if i >= n_transient:
            Q, R = np.linalg.qr(Q)
            for j in range(n_lyap):
                lyap_sums[j] += np.log(abs(R[j, j]))
    
    return lyap_sums / T_measure

def sweep_dissipation(b_range):
    results = []
    for b in b_range:
        print(f"Computing b = {b:.4f}...")
        lyaps = compute_lyapunov_spectrum(b, T_transient=100, T_measure=200, dt=0.01)
        results.append({
            'b': b,
            'lyap_1': lyaps[0],
            'lyap_2': lyaps[1],
            'lyap_3': lyaps[2],
            'lyap_sum': np.sum(lyaps)
        })
        print(f"  λ₁ = {lyaps[0]:.6f}")
    return results

def main():
    b_values = np.arange(0.18, 0.24, 0.002)  # Finer resolution near critical region
    print("Fast Replication: Thomas Attractor Lyapunov Spectrum (Critical Region)")
    results = sweep_dissipation(b_values)
    
    # Extract data
    bs = [r['b'] for r in results]
    lyap1 = [r['lyap_1'] for r in results]
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(bs, lyap1, 'b-o', markersize=4, linewidth=1.5, label='λ₁ (maximal)')
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    plt.axvline(x=0.208186, color='r', linestyle='--', alpha=0.7, label='Claimed b_c = 0.208186')
    plt.xlabel('Dissipation parameter b')
    plt.ylabel('Maximal Lyapunov exponent λ₁')
    plt.title('Thomas Attractor: λ₁ Dip Near Critical Region (Fast Replication)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save figure
    fig_path = 'shared_agora/artifacts/thomas_fast_replication.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"Figure saved to: {fig_path}")
    
    # Save results
    results_path = 'shared_agora/artifacts/thomas_fast_replication_results.json'
    with open(results_path, 'w') as f:
        json.dump({
            'b_values': [float(b) for b in bs],
            'lyap_1': [float(l) for l in lyap1],
            'claimed_bc': 0.208186
        }, f, indent=2)
    print(f"Results saved to: {results_path}")
    
    # Analysis
    lyap1_arr = np.array(lyap1)
    bs_arr = np.array(bs)
    
    # Find dip
    min_idx = np.argmin(lyap1_arr)
    print(f"\nMinimum λ₁ = {lyap1_arr[min_idx]:.6f} at b = {bs_arr[min_idx]:.4f}")
    
    # Find max dλ₁/db
    dlyap1 = np.diff(lyap1_arr) / np.diff(bs_arr)
    max_jump_idx = np.argmax(np.abs(dlyap1))
    print(f"Max |dλ₁/db| = {np.abs(dlyap1[max_jump_idx]):.4f} at b = {bs_arr[max_jump_idx]:.4f}")

if __name__ == '__main__':
    main()