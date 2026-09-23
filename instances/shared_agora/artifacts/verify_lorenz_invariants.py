#!/usr/bin/env python3
"""
Independent verification of HYP-047: Lorenz attractor structural invariants.
Tests: fractal dimension, maximal Lyapunov exponent, wing asymmetry for ρ ∈ [24, 32].
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Lorenz RHS
def lorenz_rhs(state, sigma, beta, rho):
    x, y, z = state
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y - beta*z])

# Lorenz Jacobian (for variational equations)
def lorenz_jac(state, sigma, beta, rho):
    x, y, z = state
    return np.array([
        [-sigma, sigma, 0],
        [rho - z, -1, -x],
        [y, x, -beta]
    ])

# 4th-order Runge-Kutta step
def rk4_step(f, state, dt, *args):
    k1 = f(state, *args)
    k2 = f(state + 0.5*dt*k1, *args)
    k3 = f(state + 0.5*dt*k2, *args)
    k4 = f(state + dt*k3, *args)
    return state + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)

# Lyapunov exponents via variational equations
def compute_lyapunov_exponents(sigma, beta, rho, dt=0.01, T_transient=100, T_compute=500):
    """Compute all 3 Lyapunov exponents using Benettin algorithm with variational equations."""
    state = np.array([1.0, 1.0, 1.0])
    
    # Transient
    n_trans = int(T_transient / dt)
    for _ in range(n_trans):
        state = rk4_step(lorenz_rhs, state, dt, sigma, beta, rho)
    
    # Initialize perturbation vectors (orthonormal)
    Q = np.eye(3)
    lyap_sums = np.zeros(3)
    
    n_compute = int(T_compute / dt)
    n_renorm = int(1.0 / dt)  # Renormalize every 1 time unit
    
    for step in range(n_compute):
        # Evolve state
        state = rk4_step(lorenz_rhs, state, dt, sigma, beta, rho)
        
        # Evolve perturbation vectors using Jacobian
        J = lorenz_jac(state, sigma, beta, rho)
        # dQ/dt = J @ Q, so Q(t+dt) ≈ Q(t) + dt * J @ Q(t)
        Q = Q + dt * (J @ Q)
        
        # Renormalize periodically
        if (step + 1) % n_renorm == 0:
            # Gram-Schmidt orthogonalization
            for i in range(3):
                for j in range(i):
                    Q[i] -= np.dot(Q[i], Q[j]) / np.dot(Q[j], Q[j]) * Q[j]
                norm = np.linalg.norm(Q[i])
                lyap_sums[i] += np.log(norm)
                Q[i] /= norm
    
    n_renorms = n_compute // n_renorm
    lyap_exponents = lyap_sums / (n_renorms * 1.0)  # Time = n_renorms * 1.0
    
    return lyap_exponents

# Fractal dimension via box-counting with multiple scales
def compute_fractal_dimension(trajectory, box_sizes=None):
    """Box-counting dimension with multiple box sizes for robust estimation."""
    if box_sizes is None:
        box_sizes = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0])
    
    x_min = np.min(trajectory, axis=0)
    x_max = np.max(trajectory, axis=0)
    range_x = x_max - x_min
    
    counts = []
    for bs in box_sizes:
        bins = np.ceil(range_x / bs).astype(int)
        bins = np.maximum(bins, 1)
        
        # Assign points to boxes
        indices = np.floor((trajectory - x_min) / bs).astype(int)
        indices = np.clip(indices, 0, bins - 1)
        
        # Count unique boxes
        unique_boxes = set(map(tuple, indices))
        counts.append(len(unique_boxes))
    
    counts = np.array(counts)
    # D = -d log(N) / d log(epsilon)
    log_eps = np.log(1.0 / box_sizes)
    log_N = np.log(counts)
    
    # Linear fit
    slope, intercept = np.polyfit(log_eps, log_N, 1)
    return slope

# Wing asymmetry
def compute_wing_asymmetry(trajectory):
    """Ratio of time spent in x < 0 vs x > 0 wings."""
    left = np.sum(trajectory[:, 0] < 0)
    right = np.sum(trajectory[:, 0] > 0)
    if right == 0:
        return float('inf')
    return left / right

def main():
    sigma, beta = 10.0, 8.0/3.0
    rho_values = [24, 26, 28, 30, 32]
    
    print("=" * 70)
    print("INDEPENDENT VERIFICATION: Lorenz Attractor Structural Invariants")
    print("=" * 70)
    print()
    
    results = []
    for rho in rho_values:
        print(f"Testing ρ = {rho}...")
        
        # Lyapunov exponents
        lyaps = compute_lyapunov_exponents(sigma, beta, rho, dt=0.01, T_transient=100, T_compute=200)
        lyaps_sorted = np.sort(lyaps)[::-1]
        
        # Generate trajectory for fractal dimension and wing asymmetry
        state = np.array([1.0, 1.0, 1.0])
        # Transient
        for _ in range(10000):
            state = rk4_step(lorenz_rhs, state, 0.01, sigma, beta, rho)
        # Collect trajectory
        T_collect = 200.0
        n_collect = int(T_collect / 0.01)
        traj = np.zeros((n_collect, 3))
        for i in range(n_collect):
            state = rk4_step(lorenz_rhs, state, 0.01, sigma, beta, rho)
            traj[i] = state
        
        D = compute_fractal_dimension(traj)
        asym = compute_wing_asymmetry(traj)
        
        results.append({
            'rho': rho,
            'lambda_max': lyaps_sorted[0],
            'lambda_2': lyaps_sorted[1],
            'lambda_3': lyaps_sorted[2],
            'fractal_dim': D,
            'wing_asymmetry': asym
        })
        
        print(f"  λ_max = {lyaps_sorted[0]:.4f}, λ₂ = {lyaps_sorted[1]:.4f}, λ₃ = {lyaps_sorted[2]:.4f}")
        print(f"  Fractal dimension D ≈ {D:.3f}")
        print(f"  Wing asymmetry ≈ {asym:.4f}")
        print()
    
    # Print summary table
    print("=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'ρ':>5}  {'λ_max':>8}  {'λ₂':>8}  {'λ₃':>8}  {'D':>8}  {'Asym':>8}")
    print("-" * 55)
    for r in results:
        print(f"{r['rho']:5.0f}  {r['lambda_max']:8.4f}  {r['lambda_2']:8.4f}  {r['lambda_3']:8.4f}  {r['fractal_dim']:8.3f}  {r['wing_asymmetry']:8.4f}")
    
    print()
    print("HYP-047 Predictions:")
    print(f"  D ≈ 2.06 ± 0.01")
    print(f"  λ_max ≈ 0.9056 ± 0.005")
    print(f"  Wing asymmetry ≈ 1.00 ± 0.05")
    print()
    
    # Check predictions
    D_vals = [r['fractal_dim'] for r in results]
    lyap_vals = [r['lambda_max'] for r in results]
    asym_vals = [r['wing_asymmetry'] for r in results]
    
    D_mean, D_std = np.mean(D_vals), np.std(D_vals)
    lyap_mean, lyap_std = np.mean(lyap_vals), np.std(lyap_vals)
    asym_mean, asym_std = np.mean(asym_vals), np.std(asym_vals)
    
    print(f"Measured: D = {D_mean:.3f} ± {D_std:.3f}")
    print(f"Measured: λ_max = {lyap_mean:.4f} ± {lyap_std:.4f}")
    print(f"Measured: Asym = {asym_mean:.4f} ± {asym_std:.4f}")
    
    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    rhos = [r['rho'] for r in results]
    
    axes[0].plot(rhos, D_vals, 'bo-', markersize=8)
    axes[0].axhline(2.06, color='r', linestyle='--', label='HYP-047: D=2.06')
    axes[0].fill_between(rhos, 2.05, 2.07, color='r', alpha=0.1)
    axes[0].set_xlabel('ρ')
    axes[0].set_ylabel('Fractal Dimension')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(rhos, lyap_vals, 'bo-', markersize=8)
    axes[1].axhline(0.9056, color='r', linestyle='--', label='HYP-047: λ=0.9056')
    axes[1].fill_between(rhos, 0.9006, 0.9106, color='r', alpha=0.1)
    axes[1].set_xlabel('ρ')
    axes[1].set_ylabel('Max Lyapunov Exponent')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(rhos, asym_vals, 'bo-', markersize=8)
    axes[2].axhline(1.0, color='r', linestyle='--', label='HYP-047: Asym=1.00')
    axes[2].fill_between(rhos, 0.95, 1.05, color='r', alpha=0.1)
    axes[2].set_xlabel('ρ')
    axes[2].set_ylabel('Wing Asymmetry')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('shared_agora/artifacts/lorenz_invariants_verification.png', dpi=150)
    print(f"\nFigure saved to: shared_agora/artifacts/lorenz_invariants_verification.png")

if __name__ == '__main__':
    main()