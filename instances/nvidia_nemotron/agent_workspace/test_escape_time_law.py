import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_reflexive_integrate(N, K0, a, dt, T_max, omega_spread, seed=None):
    if seed is not None:
        np.random.seed(seed)
    
    if omega_spread == 0:
        omega = np.zeros(N)
    else:
        # Cauchy distribution
        omega = np.random.standard_cauchy(N) * omega_spread
    
    theta = np.random.uniform(0, 2*np.pi, N)
    R = np.abs(np.mean(np.exp(1j * theta)))
    
    times = [0.0]
    R_history = [R]
    t = 0.0
    
    lock_time = None
    
    while t < T_max:
        R = np.abs(np.mean(np.exp(1j * theta)))
        K = K0 * (R ** a)
        
        if len(theta) > 0:
            psi = np.angle(np.mean(np.exp(1j * theta)))
        else:
            psi = 0.0
        
        # RK4 integrator
        dtheta = omega + K * R * np.sin(psi - theta)
        theta_mid = theta + 0.5 * dt * dtheta
        R_mid = np.abs(np.mean(np.exp(1j * theta_mid)))
        psi_mid = np.angle(np.mean(np.exp(1j * theta_mid)))
        dtheta2 = omega + K0 * (R_mid ** a) * R_mid * np.sin(psi_mid - theta_mid)
        theta_mid2 = theta + 0.5 * dt * dtheta2
        R_mid2 = np.abs(np.mean(np.exp(1j * theta_mid2)))
        psi_mid2 = np.angle(np.mean(np.exp(1j * theta_mid2)))
        dtheta3 = omega + K0 * (R_mid2 ** a) * R_mid2 * np.sin(psi_mid2 - theta_mid2)
        theta_end = theta + dt * dtheta3
        R_end = np.abs(np.mean(np.exp(1j * theta_end)))
        psi_end = np.angle(np.mean(np.exp(1j * theta_end)))
        dtheta4 = omega + K0 * (R_end ** a) * R_end * np.sin(psi_end - theta_end)
        theta = theta + (dt / 6.0) * (dtheta + 2*dtheta2 + 2*dtheta3 + dtheta4)
        
        t += dt
        R_history.append(R)
        times.append(t)
        
        # Check for lock (R > 0.9)
        if lock_time is None and R > 0.9:
            lock_time = t
    
    return np.array(times), np.array(R_history), lock_time, R_history[-1]


def test_escape_time_law(a, K0, omega_spread, N_values, num_seeds=12, T_max=200):
    """Test the universal escape-time law t_esc = 2/(a*K0*R0^a)"""
    
    results = []
    
    for N in N_values:
        R0_values = []
        t_esc_values = []
        u_values = []
        
        for seed in range(num_seeds):
            times, R_history, lock_time, final_R = kuramoto_reflexive_integrate(
                N, K0, a, dt=0.01, T_max=T_max, omega_spread=omega_spread, seed=seed
            )
            
            if lock_time is not None:
                # Estimate initial R0 from early time (first few points)
                R0_est = R_history[1] if len(R_history) > 1 else final_R
                
                # Calculate expected escape time per law
                if a > 0 and R0_est > 0:
                    t_esc_expected = 2 / (a * K0 * (R0_est ** a))
                else:
                    t_esc_expected = np.inf
                
                # Calculate u = a*K0*R0^a*t_esc/2
                u = a * K0 * (R0_est ** a) * lock_time / 2
                
                # Estimate R0 from finite-N fluctuations: R0 ~ 1/sqrt(N)
                # For random phases, expected R0 ≈ sqrt(2/N) for large N, but let's use actual
                R0_values.append(R0_est)
                t_esc_values.append(lock_time)
                u_values.append(u)
        
        results.append({
            'N': N,
            'num_seeds_tested': num_seeds,
            'locked_seeds': len([u for u in u_values if not np.isinf(u)]),
            'R0_values': R0_values,
            't_esc_values': t_esc_values,
            'u_values': u_values,
            'mean_u': np.mean([u for u in u_values if not np.isinf(u)]) if any(not np.isinf(u) for u in u_values) else None,
            'median_u': np.median([u for u in u_values if not np.isinf(u)]) if any(not np.isinf(u) for u in u_values) else None,
        })
    
    return results


# Test with parameters from the dossier: a=2, K0=5, omega_spread=0 (identical oscillators)
print("=" * 60)
print("TEST: a=2, K0=5, omega=0 (identical oscillators)")
print("=" * 60)
N_values = [100, 200, 300, 600]
results = test_escape_time_law(2, 5, 0.0, N_values, num_seeds=12, T_max=200)

for r in results:
    locked_pct = (r['locked_seeds'] / 12) * 100
    print(f"N={r['N']}: {r['locked_seeds']}/12 locked ({locked_pct:.1f}%)")
    if r['mean_u'] is not None:
        print(f"  Mean u = {r['mean_u']:.4f}, Median u = {r['median_u']:.4f}")
    else:
        print(f"  No locks within T_max=200")
    if r['R0_values']:
        print(f"  R0 values: min={min(r['R0_values']):.6f}, max={max(r['R0_values']):.6f}, mean={np.mean(r['R0_values']):.6f}")

print("\n" + "=" * 60)
print("TEST: a=2, K0=5, omega_spread=0.5 (Cauchy spread)")
print("=" * 60)
results_spread = test_escape_time_law(2, 5, 0.5, N_values, num_seeds=12, T_max=200)

for r in results_spread:
    locked_pct = (r['locked_seeds'] / 12) * 100
    print(f"N={r['N']}: {r['locked_seeds']}/12 locked ({locked_pct:.1f}%)")
    if r['mean_u'] is not None:
        print(f"  Mean u = {r['mean_u']:.4f}, Median u = {r['median_u']:.4f}")
    else:
        print(f"  No locks within T_max=200")
    if r['R0_values']:
        print(f"  R0 values: min={min(r['R0_values']):.6f}, max={max(r['R0_values']):.6f}, mean={np.mean(r['R_values']):.6f}")

print("\n" + "=" * 60)
print("TEST: a=1, K0=5, omega=0 (identical oscillators)")
print("=" * 60)
results_a1 = test_escape_time_law(1, 5, 0.0, N_values, num_seeds=12, T_max=200)

for r in results_a1:
    locked_pct = (r['locked_seeds'] / 12) * 100
    print(f"N={r['N']}: {r['locked_seeds']}/12 locked ({locked_pct:.1f}%)")
    if r['mean_u'] is not None:
        print(f"  Mean u = {r['mean_u']:.4f}, Median u = {r['median_u']:.4f}")
    else:
        print(f"  No locks within T_max=200")
    if r['R0_values']:
        print(f"  R0 values: mean={np.mean(r['R0_values']):.6f}")

print("\n" + "=" * 60)
print("TEST: a=2, K0=20, omega=0 (identical oscillators)")
print("=" * 60)
results_k20 = test_escape_time_law(2, 20, 0.0, N_values, num_seeds=12, T_max=200)

for r in results_k20:
    locked_pct = (r['locked_seeds'] / 12) * 100
    print(f"N={r['N']}: {r['locked_seeds']}/12 locked ({locked_pct:.1f}%)")
    if r['mean_u'] is not None:
        print(f"  Mean u = {r['mean_u']:.4f}, Median u = {r['median_u']:.4f}")
    else:
        print(f"  No locks within T_max=200")
    if r['R0_values']:
        print(f"  R0 values: mean={np.mean(r['R0_values']):.6f}")