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
    
    # Simple Euler for speed
    while t < T_max:
        R = np.abs(np.mean(np.exp(1j * theta)))
        K = K0 * (R ** a)
        
        if len(theta) > 0:
            psi = np.angle(np.mean(np.exp(1j * theta)))
        else:
            psi = 0.0
        
        dtheta = omega + K * R * np.sin(psi - theta)
        theta = theta + dt * dtheta
        
        t += dt
        R_history.append(R)
        times.append(t)
        
        if R > 0.9:
            return np.array(times), np.array(R_history), t, True
    
    return np.array(times), np.array(R_history), t, False


def test_parameter(N, K0, a, dt, T_max, num_seeds=6, omega_spread=0.0, integrator='Euler'):
    results = []
    lock_times = []
    
    for seed in range(num_seeds):
        times, R_history, t_final, locked = kuramoto_reflexive_integrate(
            N, K0, a, dt, T_max, omega_spread, integrator, seed
        )
        results.append(locked)
        if locked:
            for i, R in enumerate(R_history):
                if R > 0.9:
                    lock_times.append(times[i])
                    break
            else:
                lock_times.append(t_final)
        else:
            lock_times.append(None)
    
    lock_rate = np.mean(results)
    return {
        'N': N, 'K0': K0, 'a': a, 'dt': dt, 'T_max': T_max,
        'num_seeds': num_seeds, 'omega_spread': omega_spread,
        'integrator': integrator, 'lock_rate': lock_rate,
        'lock_times': lock_times, 'locked_seeds': sum(1 for r in results if r),
        'results': results
    }


# Quick test
print("a=2, K0=5, N=50, omega_spread=0, Euler, 120 time units")
r1 = test_parameter(50, 5, 2, 0.01, 120, num_seeds=6, omega_spread=0.0, integrator='Euler')
print(f"Lock rate: {r1['locked_seeds']}/6, times: {r1['lock_times']}")

print("\na=2, K0=5, N=50, omega_spread=0, RK4, 120 time units")
r2 = test_parameter(50, 5, 2, 0.01, 120, num_seeds=6, omega_spread=0.0, integrator='RK4')
print(f"Lock rate: {r2['locked_seeds']}/6, times: {r2['lock_times']}")

print("\na=2, K0=5, N=50, omega_spread=0, Euler, 200 time units")
r3 = test_parameter(50, 5, 2, 0.01, 200, num_seeds=6, omega_spread=0.0, integrator='Euler')
print(f"Lock rate: {r3['locked_seeds']}/6, times: {r3['lock_times']}")

print("\na=1, K0=5, N=50, omega_spread=0, Euler, 200 time units")
r4 = test_parameter(50, 5, 1, 0.01, 200, num_seeds=6, omega_spread=0.0, integrator='Euler')
print(f"Lock rate: {r4['locked_seeds']}/6, times: {r4['lock_times']}")

print("\na=2, K0=20, N=100, omega_spread=0, Euler, 100 time units")
r5 = test_parameter(100, 20, 2, 0.01, 100, num_seeds=6, omega_spread=0.0, integrator='Euler')
print(f"Lock rate: {r5['locked_seeds']}/6, times: {r5['lock_times']}")