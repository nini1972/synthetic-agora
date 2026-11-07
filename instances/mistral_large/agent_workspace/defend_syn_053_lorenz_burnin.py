#!/usr/bin/env python3
"""
Active Defense: SYN-053 (Q = -λ_max - D_2 - K)
- Tests transient robustness in Lorenz high-ρ regimes.
- Uses burn-in correction and finite-time Lyapunov exponents.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from numpy.linalg import eigvals

# --- Lorenz System ---
def lorenz(t, state, rho):
    x, y, z = state
    dxdt = 10 * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - (8/3) * z
    return [dxdt, dydt, dzdt]

# --- Jacobian ---
def lorenz_jacobian(state, rho):
    x, y, z = state
    return np.array([
        [-10, 10, 0],
        [rho - z, -1, -x],
        [y, x, -8/3]
    ])

# --- Finite-Time Lyapunov Exponent ---
def finite_time_lyapunov(traj, rho, dt=0.01, T=100):
    """Compute λ_max over finite trajectory."""
    n = len(traj)
    lyap = 0.0
    for i in range(n - 1):
        J = lorenz_jacobian(traj[i], rho)
        lyap += np.log(np.abs(eigvals(J))).max()
    return lyap / (n * dt)

# --- Q Metric ---
def compute_q(traj, rho):
    """Compute Q = -λ_max - D_2 - K."""
    λ_max = finite_time_lyapunov(traj, rho)
    D_2 = np.log(np.abs(eigvals(lorenz_jacobian(traj[-1], rho)))).sum() / 3
    K = 0  # Conservative systems
    return -λ_max - D_2 - K

# --- Parameters ---
rho_values = np.linspace(10, 50, 20)
burn_in = 1000
T_measure = 10000
dt = 0.01

# --- Main ---
if __name__ == "__main__":
    q_results = []
    
    for rho in rho_values:
        # Initial state
        state0 = np.random.uniform(-1, 1, 3)
        
        # Burn-in
        sol = solve_ivp(
            lorenz, [0, burn_in], state0, args=(rho,),
            dense_output=True, rtol=1e-6, atol=1e-8
        )
        traj_burnin = sol.y.T
        
        # Measurement
        sol = solve_ivp(
            lorenz, [0, T_measure], traj_burnin[-1], args=(rho,),
            dense_output=True, rtol=1e-6, atol=1e-8
        )
        traj = sol.y.T
        
        # Compute Q
        q = compute_q(traj, rho)
        q_results.append(q)
        print(f"ρ={rho:.1f}, Q={q:.3f}")
    
    # --- Plot ---
    plt.figure(figsize=(10, 6))
    plt.plot(rho_values, q_results, 'o-', label='Q = -λ_max - D_2 - K')
    plt.axhline(-2, color='red', linestyle='--', label='Edge of Chaos (Q ≈ -2)')
    plt.xlabel('ρ (Lorenz Parameter)')
    plt.ylabel('Q')
    plt.title('SYN-053 Active Defense: Lorenz High-ρ Transient Robustness')
    plt.legend()
    plt.grid(True)
    plt.savefig('world_c_results/syn_053_lorenz_burnin_defense.png')
    plt.close()