#!/usr/bin/env python3
"""
Optimized local parameter scan for Period-4 Symbolic Order in coupled logistic map lattices.

Optimizations:
- Reduced time steps (T=500).
- Vectorized lattice updates.
- Parallelized parameter scans.

System:
    x_i^{t+1} = (1-ε)r x_i^t(1-x_i^t) + (ε/2)[r x_{i-1}^t(1-x_{i-1}^t) + r x_{i+1}^t(1-x_{i+1}^t)]

Parameters: r=3.8625-3.865, ε=0.130-0.134, N=100, T=500
"""

import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

# Parameters
r_vals = np.linspace(3.8625, 3.865, 10)
eps_vals = np.linspace(0.130, 0.134, 10)
N = 100  # System size
T = 500  # Reduced time steps
threshold = 0.5

# Symbolic encoding
def symbolic_encoding(x):
    return (x > threshold).astype(int)

# Motif consistency at lag mod 4
def motif_consistency(symbolic, lag):
    matches = np.sum(symbolic[:-lag] == symbolic[lag:])
    total = symbolic.size - lag * N
    return matches / total if total > 0 else 0

# Phase contrast metric
def phase_contrast(symbolic):
    consistency = [motif_consistency(symbolic, 4 * k + lag) for lag in range(4) for k in range(1, (T - lag) // 4)]
    consistency = [np.mean(consistency[i::4]) for i in range(4)]
    return consistency[0] - consistency[2]

# Coupled logistic map (vectorized)
def coupled_logistic_map(args):
    r, eps = args
    x = np.random.rand(N)
    symbolic = np.zeros((T, N), dtype=int)
    for t in range(T):
        x_prev = x.copy()
        left = np.roll(x_prev, 1)
        right = np.roll(x_prev, -1)
        x = (1 - eps) * r * x_prev * (1 - x_prev) + (eps / 2) * (r * left * (1 - left) + r * right * (1 - right))
        symbolic[t] = symbolic_encoding(x)
    return phase_contrast(symbolic)

# Parallel parameter scan
if __name__ == "__main__":
    with Pool(cpu_count()) as pool:
        results = pool.map(coupled_logistic_map, [(r, eps) for r in r_vals for eps in eps_vals])
    results = np.array(results).reshape(len(r_vals), len(eps_vals))

    # Plot results
    plt.figure(figsize=(10, 8))
    plt.imshow(results, extent=[min(eps_vals), max(eps_vals), min(r_vals), max(r_vals)], origin='lower', aspect='auto', cmap='viridis')
    plt.colorbar(label='Phase Contrast Metric (C4)')
    plt.xlabel('Coupling Strength (ε)')
    plt.ylabel('Growth Rate (r)')
    plt.title('Optimized Parameter Scan for Period-4 Symbolic Order')
    plt.savefig('period4_parameter_scan_optimized.png')

    # Save results
    np.save('period4_parameter_scan_optimized.npy', results)

    # Report
    with open('REPORT_optimized.md', 'w') as f:
        f.write("# Optimized Parameter Scan for Period-4 Symbolic Order\n\n")
        f.write("## Parameters\n")
        f.write(f"- r: {r_vals}\n")
        f.write(f"- ε: {eps_vals}\n")
        f.write(f"- N: {N}\n")
        f.write(f"- T: {T}\n\n")
        f.write("## Results\n")
        f.write("![Parameter Scan](./period4_parameter_scan_optimized.png)\n\n")
        f.write("### Max C4: {:.3f}\n".format(np.max(results)))
        f.write("### Min C4: {:.3f}\n".format(np.min(results)))
        f.write("### Mean C4: {:.3f}\n\n".format(np.mean(results)))
        f.write("## Conclusion\n")
        if np.max(results) > 0.1:
            f.write("Period-4 symbolic order detected in the parameter space.\n")
            idx = np.unravel_index(np.argmax(results), results.shape)
            f.write(f"Optimal parameters: r={r_vals[idx[0]]:.5f}, ε={eps_vals[idx[1]]:.5f}\n")
        else:
            f.write("No period-4 symbolic order detected in the parameter space.\n")

    print("Optimized parameter scan complete. Artifacts saved.")