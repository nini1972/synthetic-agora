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
        
        if R > 0.9:
            return np.array(times), np.array(R_history), t, True
    
    return np.array(times), np.array(R_history), t, False


def test_parameter(N, K0, a, dt, T_max, num_seeds=12, omega_spread=0.0, integrator='RK4'):
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


# Test with smaller N first, then scale
print("Testing with N=50, a=2, K0=5, 12 seeds:")
r1 = test_parameter(50, 5, 2, 0.01, 100, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r1['locked_seeds']}/12, Final R: {r1['final_R']}")

print("\nTesting with N=100, a=2, K0=5, 12 seeds:")
r2 = test_parameter(100, 5, 2, 0.01, 100, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r2['locked_seeds']}/12, Final R: {r2['final_R']}")

print("\nTesting with N=200, a=2, K0=5, 12 seeds:")
r3 = test_parameter(200, 5, 2, 0.01, 100, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r3['locked_seeds']}/12, Final R: {r3['final_R']}")

print("\nTesting with N=300, a=2, K0=5, 6 seeds:")
r4 = test_parameter(300, 5, 2, 0.01, 100, num_seeds=6, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r4['locked_seeds']}/6, Final R: {r4['final_R']}")

print("\nTesting with N=300, a=2, K0=5, 12 seeds, shorter time:")
r5 = test_parameter(300, 5, 2, 0.01, 50, num_seeds=12, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r5['locked_seeds']}/12, Final R: {r5['final_R']}")