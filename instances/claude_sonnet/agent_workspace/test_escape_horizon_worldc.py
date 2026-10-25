"""
World C High-Fidelity Test: Escape Horizon vs Lock Barrier in Reflexive Kuramoto
===================================================================================

Tests FRONTIER DOSSIER-087 hypothesis: "Failed lock" cells are actually slow-lock
cells with algebraically diverging escape times t_esc ~ 1/R0^a.

Specifically targets EMP-163's "failed lock" regime (a=2, K0=5, γ=0.85) with
EXTENDED integration time T=500 to test if lock eventually occurs.

Protocol:
1. Reflexive Kuramoto: dθ/dt = ω + K0·R^a·sin(Ψ-θ)
2. Parameters: a=2, K0=5, N=300
3. Frequency distributions: Lorentzian with γ ∈ {0.5, 0.7, 0.85, 1.0}
4. Initial conditions: random phases θ ~ U(0,2π)
5. Measure:
   - Initial order R0 (mean over t=0-5)
   - Escape time t_esc (first crossing R>0.7)
   - Lock fraction at t ∈ {10, 50, 100, 200, 500}
   - Test scaling law t_esc = C/(a·K0·R0^a)
6. 20 independent seeds per γ value
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import json

def lorentzian_frequencies(gamma, N, seed):
    """Generate Lorentzian frequencies ω ~ γ/((ω-ω0)^2 + γ^2)"""
    rng = np.random.RandomState(seed)
    # Use inverse CDF: F^(-1)(u) = ω0 + γ·tan(π(u-0.5))
    u = rng.uniform(0, 1, N)
    return gamma * np.tan(np.pi * (u - 0.5))

def reflexive_kuramoto_rhs(theta, t, omega, K0, a):
    """Right-hand side for reflexive Kuramoto ODE"""
    N = len(theta)
    # Order parameter
    z = np.mean(np.exp(1j * theta))
    R = np.abs(z)
    Psi = np.angle(z)
    
    # Coupling strength K = K0 * R^a
    K_eff = K0 * (R ** a)
    
    # dθ/dt = ω + K_eff * sin(Ψ - θ)
    dtheta_dt = omega + K_eff * np.sin(Psi - theta)
    return dtheta_dt

def simulate_one_seed(gamma, K0, a, N, T, dt, seed):
    """Simulate one seed and measure escape time"""
    omega = lorentzian_frequencies(gamma, N, seed)
    theta0 = np.random.RandomState(seed + 1000).uniform(0, 2*np.pi, N)
    
    # Time grid
    t_eval = np.arange(0, T, dt)
    
    # Integrate
    solution = odeint(reflexive_kuramoto_rhs, theta0, t_eval, 
                      args=(omega, K0, a), rtol=1e-6, atol=1e-8)
    
    # Compute R(t)
    R_trajectory = np.abs(np.mean(np.exp(1j * solution), axis=1))
    
    # Initial R0: mean over first 5 time units
    idx_init = int(5.0 / dt)
    R0 = np.mean(R_trajectory[:idx_init])
    
    # Escape time: first crossing R > 0.7
    escape_idx = np.where(R_trajectory > 0.7)[0]
    if len(escape_idx) > 0:
        t_esc = t_eval[escape_idx[0]]
        locked = True
    else:
        t_esc = np.inf
        locked = False
    
    # Lock fractions at checkpoints
    checkpoints = [10, 50, 100, 200, 500]
    lock_at_checkpoint = {}
    for t_check in checkpoints:
        if t_check <= T:
            idx = int(t_check / dt)
            lock_at_checkpoint[t_check] = float(R_trajectory[idx] > 0.7)
        else:
            lock_at_checkpoint[t_check] = None
    
    # Final R
    R_final = R_trajectory[-1]
    
    return {
        'R0': R0,
        't_esc': t_esc,
        'locked': locked,
        'lock_at_checkpoint': lock_at_checkpoint,
        'R_final': R_final,
        'R_trajectory': R_trajectory[::10]  # Downsample for storage
    }

def main():
    # Parameters
    K0 = 5.0
    a = 2.0
    N = 300
    T = 500.0  # Extended integration time
    dt = 0.05
    n_seeds = 20
    
    gamma_values = [0.5, 0.7, 0.85, 1.0]
    
    results = {}
    
    print("=" * 70)
    print("WORLD C: Escape Horizon Test for Reflexive Kuramoto")
    print("=" * 70)
    print(f"Parameters: K0={K0}, a={a}, N={N}, T={T}, dt={dt}")
    print(f"Testing γ values: {gamma_values}")
    print(f"Seeds per γ: {n_seeds}")
    print()
    
    # Run simulations
    for gamma in gamma_values:
        print(f"Testing γ = {gamma:.2f}...")
        gamma_results = []
        
        for seed in range(n_seeds):
            result = simulate_one_seed(gamma, K0, a, N, T, dt, seed)
            gamma_results.append(result)
            
            if seed % 5 == 0:
                print(f"  Seed {seed}: R0={result['R0']:.4f}, "
                      f"t_esc={result['t_esc']:.2f}, "
                      f"R_final={result['R_final']:.4f}")
        
        results[gamma] = gamma_results
        
        # Summary statistics
        R0_mean = np.mean([r['R0'] for r in gamma_results])
        t_esc_values = [r['t_esc'] for r in gamma_results if np.isfinite(r['t_esc'])]
        lock_fraction_500 = np.mean([r['lock_at_checkpoint'][500] for r in gamma_results])
        
        print(f"  Summary: <R0>={R0_mean:.4f}, "
              f"median(t_esc)={np.median(t_esc_values) if t_esc_values else 'inf':.2f}, "
              f"P(lock at t=500)={lock_fraction_500:.2f}")
        print()
    
    # Test scaling law t_esc = C / (a * K0 * R0^a)
    print("=" * 70)
    print("SCALING LAW TEST: t_esc = C / (a * K0 * R0^a)")
    print("=" * 70)
    
    all_R0 = []
    all_t_esc = []
    all_gamma = []
    
    for gamma in gamma_values:
        for r in results[gamma]:
            if np.isfinite(r['t_esc']):
                all_R0.append(r['R0'])
                all_t_esc.append(r['t_esc'])
                all_gamma.append(gamma)
    
    all_R0 = np.array(all_R0)
    all_t_esc = np.array(all_t_esc)
    all_gamma = np.array(all_gamma)
    
    # Compute scaled variable u = a * K0 * R0^a * t_esc / 2
    u_scaled = a * K0 * (all_R0 ** a) * all_t_esc / 2
    
    print(f"Scaled escape time u = a·K0·R0^a·t_esc/2:")
    print(f"  Median: {np.median(u_scaled):.3f}")
    print(f"  10th percentile: {np.percentile(u_scaled, 10):.3f}")
    print(f"  90th percentile: {np.percentile(u_scaled, 90):.3f}")
    print(f"  Range: [{np.min(u_scaled):.3f}, {np.max(u_scaled):.3f}]")
    print(f"  Frontier prediction: [0.07, 0.33]")
    print()
    
    # Create figure
    fig = plt.figure(figsize=(14, 10))
    
    # Panel 1: Lock fraction vs time for each γ
    ax1 = plt.subplot(2, 3, 1)
    checkpoints = [10, 50, 100, 200, 500]
    for gamma in gamma_values:
        lock_fractions = []
        for t_check in checkpoints:
            frac = np.mean([r['lock_at_checkpoint'][t_check] for r in results[gamma] 
                           if r['lock_at_checkpoint'][t_check] is not None])
            lock_fractions.append(frac)
        ax1.plot(checkpoints, lock_fractions, 'o-', label=f'γ={gamma}', linewidth=2)
    ax1.set_xlabel('Time', fontsize=11)
    ax1.set_ylabel('Lock Fraction (R > 0.7)', fontsize=11)
    ax1.set_title('Lock Probability vs Integration Time', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([-0.05, 1.05])
    
    # Panel 2: Escape time distribution
    ax2 = plt.subplot(2, 3, 2)
    for gamma in gamma_values:
        t_esc_values = [r['t_esc'] for r in results[gamma] if np.isfinite(r['t_esc'])]
        if t_esc_values:
            ax2.hist(t_esc_values, bins=15, alpha=0.5, label=f'γ={gamma}')
    ax2.set_xlabel('Escape Time t_esc', fontsize=11)
    ax2.set_ylabel('Count', fontsize=11)
    ax2.set_title('Escape Time Distribution', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Scaling collapse u = a·K0·R0^a·t_esc/2
    ax3 = plt.subplot(2, 3, 3)
    colors = plt.cm.viridis(np.linspace(0, 1, len(gamma_values)))
    for i, gamma in enumerate(gamma_values):
        mask = all_gamma == gamma
        ax3.scatter(all_R0[mask], u_scaled[mask], alpha=0.6, s=50, 
                   color=colors[i], label=f'γ={gamma}')
    ax3.axhline(0.07, color='red', linestyle='--', alpha=0.5, label='Frontier: [0.07, 0.33]')
    ax3.axhline(0.33, color='red', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Initial Order R0', fontsize=11)
    ax3.set_ylabel('Scaled Time u = a·K0·R0^a·t/2', fontsize=11)
    ax3.set_title('Scaling Law Collapse Test', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Median escape time vs gamma
    ax4 = plt.subplot(2, 3, 4)
    median_t_esc = []
    for gamma in gamma_values:
        t_esc_values = [r['t_esc'] for r in results[gamma] if np.isfinite(r['t_esc'])]
        if t_esc_values:
            median_t_esc.append(np.median(t_esc_values))
        else:
            median_t_esc.append(np.nan)
    ax4.semilogy(gamma_values, median_t_esc, 'o-', linewidth=2, markersize=8)
    ax4.set_xlabel('Lorentzian Width γ', fontsize=11)
    ax4.set_ylabel('Median Escape Time t_esc', fontsize=11)
    ax4.set_title('Escape Time vs Frequency Distribution Width', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Panel 5: R0 vs gamma
    ax5 = plt.subplot(2, 3, 5)
    for gamma in gamma_values:
        R0_values = [r['R0'] for r in results[gamma]]
        ax5.scatter([gamma] * len(R0_values), R0_values, alpha=0.5, s=30)
    ax5.set_xlabel('Lorentzian Width γ', fontsize=11)
    ax5.set_ylabel('Initial Order R0', fontsize=11)
    ax5.set_title('Initial Fluctuation Amplitude vs γ', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # Panel 6: t_esc vs 1/R0^a test
    ax6 = plt.subplot(2, 3, 6)
    for i, gamma in enumerate(gamma_values):
        mask = all_gamma == gamma
        ax6.scatter(1.0 / (all_R0[mask] ** a), all_t_esc[mask], alpha=0.6, s=50,
                   color=colors[i], label=f'γ={gamma}')
    # Theoretical line t_esc = C / (a * K0 * R0^a)
    x_theory = np.linspace(10, 10000, 100)
    C_median = np.median(u_scaled) * 2  # Convert u back to C
    ax6.plot(x_theory, C_median / (a * K0) * x_theory, 'k--', linewidth=2, 
            label=f'Theory: C={C_median:.2f}')
    ax6.set_xlabel('1 / R0^a', fontsize=11)
    ax6.set_ylabel('Escape Time t_esc', fontsize=11)
    ax6.set_title('Scaling Law Test: t_esc ~ 1/R0^a', fontsize=12, fontweight='bold')
    ax6.set_xscale('log')
    ax6.set_yscale('log')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('escape_horizon_worldc_test.png', dpi=150, bbox_inches='tight')
    print("Figure saved: escape_horizon_worldc_test.png")
    
    # Save numerical results
    summary = {
        'parameters': {
            'K0': K0,
            'a': a,
            'N': N,
            'T': T,
            'dt': dt,
            'n_seeds': n_seeds
        },
        'gamma_values': gamma_values,
        'scaling_law': {
            'u_median': float(np.median(u_scaled)),
            'u_p10': float(np.percentile(u_scaled, 10)),
            'u_p90': float(np.percentile(u_scaled, 90)),
            'u_range': [float(np.min(u_scaled)), float(np.max(u_scaled))],
            'frontier_prediction': [0.07, 0.33]
        },
        'lock_fractions_at_t500': {
            gamma: float(np.mean([r['lock_at_checkpoint'][500] for r in results[gamma]]))
            for gamma in gamma_values
        },
        'median_escape_times': {
            gamma: float(np.median([r['t_esc'] for r in results[gamma] if np.isfinite(r['t_esc'])]))
            if any(np.isfinite(r['t_esc']) for r in results[gamma]) else None
            for gamma in gamma_values
        }
    }
    
    with open('escape_horizon_worldc_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Summary saved: escape_horizon_worldc_summary.json")
    
    print("=" * 70)
    print("WORLD C JOB COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
