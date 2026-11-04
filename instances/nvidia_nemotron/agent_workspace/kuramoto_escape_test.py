#!/usr/bin/env python3
"""
World C: Independent replication of Kuramoto escape-time law from DOSSIER-004
Testing: t_esc = 2/(a*K0*R0^a) where R0 is initial order parameter
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from colony_lib.dynamics import simulate_kuramoto
from colony_lib.persistence import StageTracker

# Stage tracking for multi-stage builds
tracker = StageTracker('kuramoto_escape_2024')

def run_kuramoto_escape_trial(N, a, K0, kappa, seed, max_time=200, dt=0.01):
    """Run a single Kuramoto model trial and record escape time."""
    np.random.seed(seed)
    
    # Initialize phases uniformly and random natural frequencies
    phases = np.random.uniform(0, 2*np.pi, N)
    omegas = np.random.uniform(-kappa, kappa, N)
    
    # Compute initial order parameter R0
    R0 = np.abs(np.sum(np.exp(1j*phases))) / N
    
    if R0 < 1e-10:
        return None, R0  # Purely incoherent start
    
    # Store history for escape detection
    R_history = [R0]
    t_history = [0.0]
    
    # Time evolution with reflexive coupling K = K0 * R^a
    t = 0.0
    R = R0
    locked = False
    
    while t < max_time and not locked:
        # Compute mean field
        psi = np.angle(np.sum(np.exp(1j*phases)))
        
        # Reflexive coupling: K = K0 * R^a
        K = K0 * (R ** a) if R > 0 and a > 0 else 0.0
        
        # Update phases (Kuramoto with state-dependent coupling)
        dphases = omegas + K * R * np.sin(psi - phases)
        phases = phases + dphases * dt
        
        # Recompute order parameter
        R_new = np.abs(np.sum(np.exp(1j*phases))) / N
        R = (R + R_new) / 2  # Simple average for stability
        
        t += dt
        R_history.append(R)
        t_history.append(t)
        
        # Check for locking: R > 0.5 indicates synchronization
        if R > 0.5:
            locked = True
    
    escape_time = t if locked else max_time
    return escape_time, R_history[-1]

def test_escape_law():
    """Test the universal escape-time law across parameter combinations."""
    
    # Parameters from the Frontier dossier
    a_values = [1.0, 2.0]
    K0_values = [5.0, 20.0]
    kappa_values = [1.0]  # uniform natural frequencies width
    N_values = [100, 300, 600, 1000]
    n_seeds = 12  # 12 seeds as in the dossier
    
    results = []
    
    for N in N_values:
        for a in a_values:
            for K0 in K0_values:
                for kappa in kappa_values:
                    escape_times = []
                    final_R = []
                    
                    for seed in range(n_seeds):
                        t_esc, r_final = run_kuramoto_escape_trial(N, a, K0, kappa, seed, max_time=200)
                        if t_esc is not None:
                            escape_times.append(t_esc)
                            final_R.append(r_final)
                    
                    if escape_times:
                        median_t_esc = np.median(escape_times)
                        # Predicted t_esc = 2/(a*K0*R0^a)
                        # But we need R0 from the initial condition
                        # Let's compute the universal variable u = a*K0*R0^a*t_esc/2
                        
                        # Compute R0 from first seed
                        _, r0 = run_kuramoto_escape_trial(N, a, K0, kappa, 0)
                        if r0 is not None and r0 > 0:
                            u_values = [a * K0 * (r0 ** a) * t_esc / 2 for t_esc in escape_times]
                            median_u = np.median(u_values)
                            
                            results.append({
                                'N': N, 'a': a, 'K0': K0, 'kappa': kappa,
                                'n_success': len(escape_times),
                                'n_trials': n_seeds,
                                'median_t_esc': median_t_esc,
                                'median_u': median_u,
                                'r0': r0
                            })
                            
                            print(f"N={N}, a={a}, K0={K0}: "
                                  f"success={len(escape_times)}/{n_seeds}, "
                                  f"median_t_esc={median_t_esc:.4f}, "
                                  f"median_u={median_u:.4f}, "
                                  f"R0={r0:.6f}")
    
    return results

# Run the test
print("=" * 70)
print("Kuramoto Escape-Time Law Empirical Test")
print("=" * 70)
results = test_escape_law()

# Analyze N-scaling
print("\n" + "=" * 70)
print("N-Scaling Analysis (for a=2.0 where t_esc ~ N)")
print("=" * 70)

a2_results = [r for r in results if r['a'] == 2.0]
if a2_results:
    # Sort by N and compute ratio
    a2_sorted = sorted(a2_results, key=lambda x: x['N'])
    print(f"{'N':>6} {'median_t_esc':>14} {'R0':>10} {'u':>10} {'success/trials':>14}")
    print("-" * 64)
    for r in a2_sorted[:8]:  # Show first 8
        print(f"{r['N']:>6} {r['median_t_esc']:>14.4f} {r['r0']:>10.6f} {r['median_u']:>10.4f} {r['n_success']}/{r['n_trials']:>5}    {'expected ~N scaling':>25}")
    
    # Check if t_esc scales linearly with N
    n_vals = [r['N'] for r in a2_sorted]
    t_vals = [r['median_t_esc'] for r in a2_sorted]
    if len(n_vals) >= 2:
        # Simple linear fit through log-log
        log_n = np.log(n_vals)
        log_t = np.log(t_vals)
        coeffs = np.polyfit(log_n, log_t, 1)
        print(f"\nLog-log fit slope (expected ~1.0 for a=2): {coeffs[0]:.4f}")

# Plot universal collapse
print("\n" + "=" * 70)
print("Universal collapse check: u = a*K0*R0^a*t_esc/2")
print("=" * 70)
all_u = [r['median_u'] for r in results]
print(f"Median u across all results: {np.median(all_u):.4f}")
print(f"p10: {np.percentile(all_u, 10):.4f}, p90: {np.percentile(all_u, 90):.4f}")
print(f"Expected range from dossier: [0.066, 0.325]")

# Save plot
plt.figure(figsize=(10, 6))
for a in [1.0, 2.0]:
    a_results = [r for r in results if r['a'] == a]
    if a_results:
        n_vals = [r['N'] for r in a_results]
        t_vals = [r['median_t_esc'] for r in a_results]
        plt.plot(n_vals, t_vals, 'o-', label=f'a={a}', markersize=6)

plt.xscale('log')
plt.yscale('log')
plt.xlabel('N (system size)')
plt.ylabel('Median Escape Time t_esc')
plt.title('N-scaling of Escape Time in Reflexive Kuramoto')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('kur_escape_n_scaling.png', dpi=150)
plt.close()

print("\nPlot saved as kur_escape_n_scaling.png")
print("\nTest complete!")