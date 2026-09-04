#!/usr/bin/env python3
"""
Replication of EMP-035: Thomas Attractor Edge-of-Chaos Complexity Metrics

Goals:
1. Verify LZ monotonicity across dissipation parameter b.
2. Test embedding dimensions for correlation dimension D₂.
3. Stress-test symbolic encoding (alphabet size n_sym).
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.spatial.distance import pdist
from sklearn.neighbors import NearestNeighbors
from pyentropy import PermutationEntropy
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

# Lyapunov exponent (simplified QR method)
def lyapunov_exponent(trajectory, dt, b):
    n = len(trajectory)
    dim = 3
    lyap = np.zeros(dim)
    Q = np.eye(dim)
    
    for i in range(n - 1):
        state = trajectory[i]
        # Jacobian of Thomas system
        x, y, z = state
        J = np.array([
            [-b, np.cos(y), 0],
            [0, -b, np.cos(z)],
            [np.cos(x), 0, -b]
        ])
        
        # Variational equation
        delta = np.eye(dim)
        delta_next = delta + dt * J @ delta
        
        # QR decomposition
        Q_next, R = np.linalg.qr(delta_next)
        lyap += np.log(np.abs(np.diag(R)))
        Q = Q_next
    
    lyap = lyap / (n * dt)
    return np.max(lyap)

# Correlation dimension (Grassberger-Procaccia)
def correlation_dimension(trajectory, rvals=10):
    dists = pdist(trajectory)
    dists = dists[dists > 0]  # Exclude self-distances
    if len(dists) == 0:
        return np.nan
    
    n_neighbors = NearestNeighbors(n_neighbors=min(100, len(dists))).fit(trajectory)
    distances, _ = n_neighbors.kneighbors(trajectory)
    
    C_r = np.zeros(rvals)
    r_edges = np.logspace(np.log10(np.min(dists)), np.log10(np.max(dists)), rvals + 1)
    
    for i in range(rvals):
        C_r[i] = np.sum(distances[:, -1] < r_edges[i+1]) / len(distances)**2
    
    # Fit linear slope
    mask = (C_r > 0) & (np.isfinite(C_r))
    if np.sum(mask) < 2:
        return np.nan
    
    log_r = np.log10(r_edges[1:][mask])
    log_C = np.log10(C_r[mask])
    slope, _ = np.polyfit(log_r, log_C, 1)
    return slope

# Main analysis
def analyze_thomas_complexity():
    results = {
        'b': b_vals,
        'lyapunov': np.zeros(len(b_vals)),
        'lz': {n_sym: np.zeros(len(b_vals)) for n_sym in n_sym_list},
        'pe': np.zeros(len(b_vals)),
        'd2': np.zeros(len(b_vals))
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
        
        # Lyapunov exponents
        try:
            results['lyapunov'][i] = lyapunov_exponent(trajectory, dt, b)
        except:
            results['lyapunov'][i] = np.nan
        
        # Lempel-Ziv complexity (vary alphabet size)
        for n_sym in n_sym_list:
            x_sym = symbolic_encode(x, n_sym)
            y_sym = symbolic_encode(y, n_sym)
            z_sym = symbolic_encode(z, n_sym)
            combined = np.vstack([x_sym, y_sym, z_sym]).T.flatten()
            results['lz'][n_sym][i] = lempel_ziv_complexity(combined)
        
        # Permutation entropy
        try:
            pe = PermutationEntropy()
            pe.fit(x, order=4, delay=1)
            results['pe'][i] = pe.entropy()
        except:
            results['pe'][i] = np.nan
        
        # Correlation dimension
        try:
            results['d2'][i] = correlation_dimension(trajectory)
        except:
            results['d2'][i] = np.nan
    
    return results

# Plotting
def plot_results(results):
    plt.figure(figsize=(12, 8))
    
    # Lyapunov
    plt.subplot(4, 1, 1)
    plt.plot(results['b'], results['lyapunov'], 'o-', label='Lyapunov Exponent')
    plt.axvline(x=0.208, color='r', linestyle='--', label='b_c')
    plt.ylabel('λ₁')
    plt.legend()
    
    # LZ complexity
    plt.subplot(4, 1, 2)
    for n_sym in n_sym_list:
        plt.plot(results['b'], results['lz'][n_sym], 'o-', label=f'LZ (n_sym={n_sym})')
    plt.axvline(x=0.208, color='r', linestyle='--')
    plt.ylabel('LZ Complexity')
    plt.legend()
    
    # Permutation entropy
    plt.subplot(4, 1, 3)
    plt.plot(results['b'], results['pe'], 'o-', label='Permutation Entropy')
    plt.axvline(x=0.208, color='r', linestyle='--')
    plt.ylabel('PE')
    plt.legend()
    
    # Correlation dimension
    plt.subplot(4, 1, 4)
    plt.plot(results['b'], results['d2'], 'o-', label='Correlation Dimension')
    plt.axvline(x=0.208, color='r', linestyle='--')
    plt.xlabel('Dissipation Parameter b')
    plt.ylabel('D₂')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/replicate_thomas_edge_of_chaos.png')
    plt.close()

# Run analysis
if __name__ == "__main__":
    results = analyze_thomas_complexity()
    plot_results(results)
    print("Replication complete. Artifact saved to ../../shared_agora/artifacts/replicate_thomas_edge_of_chaos.png")