#!/usr/bin/env python3
"""
Replication of EMP-035: Thomas Attractor Lempel-Ziv Complexity

Goal: Verify LZ monotonicity across dissipation parameter b.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from lempel_ziv_complexity import lempel_ziv_complexity
import os

# Parameters
b_vals = np.linspace(0.05, 0.32, 28)
T_transient = 1000
T_integration = 5000
dt = 0.05
n_sym_list = [4, 6, 8, 12, 16]  # Alphabet sizes for LZ

# Thomas attractor ODE
def thomas_attractor(t, state, b):
    x, y, z = state
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    return [dx, dy, dz]

# Symbolic encoding
def symbolic_encode(trajectory, n_sym):
    bins = np.linspace(np.min(trajectory), np.max(trajectory), n_sym + 1)
    return np.digitize(trajectory, bins) - 1

# Main analysis
def analyze_thomas_lz():
    results = {
        'b': b_vals,
        'lz': {n_sym: np.zeros(len(b_vals)) for n_sym in n_sym_list}
    }

    for i, b in enumerate(b_vals):
        print(f"Processing b = {b:.3f}")
        
        # Integrate trajectory
        sol = solve_ivp(
            thomas_attractor,
            [0, T_transient + T_integration],
            [0.1, 0.1, 0.1],
            args=(b,),
            t_eval=np.arange(0, T_transient + T_integration, dt),
            method='RK45'
        )
        
        # Skip transient
        trajectory = sol.y[:, int(T_transient/dt):].T
        x, y, z = trajectory.T
        
        # Lempel-Ziv complexity (vary alphabet size)
        for n_sym in n_sym_list:
            x_sym = symbolic_encode(x, n_sym)
            y_sym = symbolic_encode(y, n_sym)
            z_sym = symbolic_encode(z, n_sym)
            combined = np.vstack([x_sym, y_sym, z_sym]).T.flatten()
            results['lz'][n_sym][i] = lempel_ziv_complexity(combined)
    
    return results

# Plotting
def plot_results(results):
    plt.figure(figsize=(10, 5))
    
    # LZ complexity
    for n_sym in n_sym_list:
        plt.plot(results['b'], results['lz'][n_sym], 'o-', label=f'LZ (n_sym={n_sym})')
    plt.axvline(x=0.208, color='r', linestyle='--', label='b_c')
    plt.xlabel('Dissipation Parameter b')
    plt.ylabel('LZ Complexity')
    plt.legend()
    plt.title('Lempel-Ziv Complexity vs. Dissipation Parameter b')
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/replicate_thomas_lz_complexity.png')
    plt.close()

# Run analysis
if __name__ == "__main__":
    results = analyze_thomas_lz()
    plot_results(results)
    print("Replication complete. Artifact saved to ../../shared_agora/artifacts/replicate_thomas_lz_complexity.png")