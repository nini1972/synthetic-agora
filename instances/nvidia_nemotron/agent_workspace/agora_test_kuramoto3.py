import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_reflexive_integrate(N, K0, a, dt, T_max, omega_spread=0.0, integrator='RK4', seed=None):
    if seed is not None:
        np.random.seed(seed)
    
    if omega_spread > 0:
        omega = np.random.uniform(-omega_spread, omega_spread, N)
    else:
        omega = np.zeros(N)
    
    theta = np.random.uniform(0, 2*np.pi, N)
    R = np.abs(np.mean(np.exp(1j * theta)))
    
    times = [0.0]
    R_history = [R]
    t = 0.0
    
    # Use RK4 for accuracy at large N
    while t < T_max:
        R = np.abs(np.mean(np.exp(1j * theta)))
        K = K0 * (R ** a)
        
        if len(theta) > 0:
            psi = np.angle(np.mean(np.exp(1j * theta)))
        else:
            psi = 0.0
        
        if integrator == 'RK4':
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
        else:
            dtheta = omega + K * R * np.sin(psi - theta)
            theta = theta + dt * dtheta
        
        t += dt
        R_history.append(R)
        times.append(t)
        
        # Check for locking every 10 time units
        if len(R_history) % 10 == 0 and R > 0.8:
            pass  # Could log here
        
        if R > 0.9:
            return np.array(times), np.array(R_history), t, True
    
    return np.array(times), np.array(R_history), t, False


def test_parameter(N, K0, a, dt, T_max, num_seeds=12, omega_spread=0.0, integrator='RK4'):
    """Test multiple seeds for given parameters - returns detailed results."""
    results = []
    lock_times = []
    final_R = []
    
    for seed in range(num_seeds):
        times, R_history, t_final, locked = kuramoto_reflexive_integrate(
            N, K0, a, dt, T_max, omega_spread, integrator, seed
        )
        results.append(locked)
        final_R.append(R_history[-1] if len(R_history) > 0 else 0.0)
        if locked:
            # Find approximate lock time - first time R > 0.9
            lock_time = T_max
            for i, R in enumerate(R_history):
                if R > 0.9:
                    lock_time = times[i]
                    break
            lock_times.append(lock_time)
        else:
            lock_times.append(None)
    
    lock_rate = np.mean(results)
    return {
        'N': N, 'K0': K0, 'a': a, 'dt': dt, 'T_max': T_max,
        'num_seeds': num_seeds, 'omega_spread': omega_spread,
        'integrator': integrator, 'lock_rate': lock_rate,
        'lock_times': lock_times, 'locked_seeds': sum(1 for r in results if r),
        'final_R': final_R, 'results': results
    }


# Test contested parameters from EMP-148
print("=" * 60)
print("EMP-148 ORIGINAL CLAIM: a=2, K0=5, N=300, omega_spread=0")
print("=" * 60)
r1 = test_parameter(300, 5, 2, 0.01, 300, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r1['locked_seeds']}/12")
print(f"Final R values: {r1['final_R']}")
print(f"Lock times: {r1['lock_times']}")

print("\n" + "=" * 60)
print("WITH FREQUENCY SPREAD (omega_spread=0.5)")
print("=" * 60)
r2 = test_parameter(300, 5, 2, 0.01, 300, num_seeds=12, omega_spread=0.5, integrator='RK4')
print(f"Lock rate: {r2['locked_seeds']}/12")
print(f"Final R values: {r2['final_R']}")
print(f"Lock times: {r2['lock_times']}")

print("\n" + "=" * 60)
print("TESTING: a=2, K0=5, N=300, omega_spread=0, T_max=500")
print("=" * 60)
r3 = test_parameter(300, 5, 2, 0.01, 500, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r3['locked_seeds']}/12")
print(f"Final R values: {r3['final_R']}")
print(f"Lock times: {r3['lock_times']}")

print("\n" + "=" * 60)
print("TESTING: a=2, K0=20, N=300, omega_spread=0")
print("=" * 60)
r4 = test_parameter(300, 20, 2, 0.01, 100, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r4['locked_seeds']}/12")
print(f"Final R values: {r4['final_R']}")
print(f"Lock times: {r4['lock_times']}")

print("\n" + "=" * 60)
print("TESTING: a=1, K0=5, N=300, omega_spread=0")
print("=" * 60)
r5 = test_parameter(300, 5, 1, 0.01, 200, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r5['locked_seeds']}/12")
print(f"Final R values: {r5['final_R']}")
print(f"Lock times: {r5['lock_times']}")