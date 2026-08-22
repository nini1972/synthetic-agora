import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def thomas_system(state, b):
    x, y, z = state
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    return np.array([dx, dy, dz])

def rk4_step(state, b, dt):
    k1 = thomas_system(state, b)
    k2 = thomas_system(state + 0.5*dt*k1, b)
    k3 = thomas_system(state + 0.5*dt*k2, b)
    k4 = thomas_system(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def lyapunov_exponent(b, dt=0.02, T_transient=300, T_lyap=800):
    state = np.array([0.1, 0.0, 0.0])
    for _ in range(T_transient):
        state = rk4_step(state, b, dt)

    d0 = 1e-8
    perturbation = np.array([d0, 0, 0])
    state_pert = state + perturbation

    lyap_sum = 0.0
    n_steps = 0
    for i in range(T_lyap):
        state = rk4_step(state, b, dt)
        state_pert = rk4_step(state_pert, b, dt)
        diff = state_pert - state
        d = np.linalg.norm(diff)
        if d > 0:
            lyap_sum += np.log(d / d0)
            state_pert = state + (d0 / d) * diff
            n_steps += 1
    return lyap_sum / (n_steps * dt)

# Reduced sweep: 10 values
b_values = np.linspace(0.05, 0.30, 10)
print(f"{'b':>8} | {'Lambda_1':>10}")
print("-" * 25)

lyap_results = []
for b in b_values:
    lam = lyapunov_exponent(b)
    lyap_results.append(lam)
    print(f"{b:8.4f} | {lam:10.5f}")

plt.figure(figsize=(10, 6))
plt.plot(b_values, lyap_results, 'bo-', linewidth=2)
plt.axvline(x=0.208186, color='red', linestyle='--', label='$b_c = 0.208186$ (claimed)')
plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
plt.xlabel('Damping parameter $b$')
plt.ylabel('Maximal Lyapunov Exponent $\\lambda_1$')
plt.title('Thomas Cyclically Symmetric Attractor: Lyapunov Spectrum')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/r19z_thomas_lyapunov.png')
print("\nPlot saved.")