#!/usr/bin/env python3
"""
Local parameter scan for Period-4 Symbolic Order in coupled logistic map lattices.

System:
    x_i^{t+1} = (1-ε)r x_i^t(1-x_i^t) + (ε/2)[r x_{i-1}^t(1-x_{i-1}^t) + r x_{i+1}^t(1-x_{i+1}^t)]

Parameters: r=3.8625-3.865, ε=0.130-0.134, N=100, T=2000
"""

import numpy as np
import matplotlib.pyplot as plt

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

# Parameters
r_vals = np.linspace(3.8625, 3.865, 10)
eps_vals = np.linspace(0.130, 0.134, 10)
N = 100  # System size
T = 2000  # Time steps
threshold = 0.5

# Symbolic encoding
def symbolic_encoding(x):
    return (x > threshold).astype(int)

# Motif consistency at lag mod 4
def motif_consistency(symbolic, lag):
    matches = 0
    total = 0
    for t in range(T - lag):
        for i in range(N):
            if symbolic[t, i] == symbolic[t + lag, i]:
                matches += 1
            total += 1
    return matches / total if total > 0 else 0

# Phase contrast metric
def phase_contrast(symbolic):
    consistency = [motif_consistency(symbolic, 4 * k + lag) for lag in range(4) for k in range(1, (T - lag) // 4)]
    consistency = [np.mean(consistency[i::4]) for i in range(4)]
    return consistency[0] - consistency[2]

# Coupled logistic map
def coupled_logistic_map(r, epsilon, N, T):
    x = np.random.rand(N)
    symbolic = np.zeros((T, N), dtype=int)
    for t in range(T):
        x_prev = x.copy()
        for i in range(N):
            left = x_prev[i-1] if i > 0 else x_prev[-1]
            right = x_prev[i+1] if i < N-1 else x_prev[0]
            x[i] = (1 - epsilon) * r * x_prev[i] * (1 - x_prev[i]) + \
                   (epsilon / 2) * (r * left * (1 - left) + r * right * (1 - right))
        symbolic[t] = symbolic_encoding(x)
    return phase_contrast(symbolic)

# Scan parameter space
results = np.zeros((len(r_vals), len(eps_vals)))
for i, r in enumerate(r_vals):
    for j, eps in enumerate(eps_vals):
        results[i, j] = coupled_logistic_map(r, eps, N, T)

# Plot results
plt.figure(figsize=(10, 8))
plt.imshow(results, extent=[min(eps_vals), max(eps_vals), min(r_vals), max(r_vals)], origin='lower', aspect='auto', cmap='viridis')
plt.colorbar(label='Phase Contrast Metric (C4)')
plt.xlabel('Coupling Strength (ε)')
plt.ylabel('Growth Rate (r)')
plt.title('Parameter Scan for Period-4 Symbolic Order')
plt.savefig('period4_parameter_scan_local.png')

# Save results
np.save('period4_parameter_scan_local.npy', results)

# Report
with open('REPORT_local.md', 'w') as f:
    f.write("# Local Parameter Scan for Period-4 Symbolic Order\n\n")
    f.write("## Parameters\n")
    f.write(f"- r: {r_vals}\n")
    f.write(f"- ε: {eps_vals}\n")
    f.write(f"- N: {N}\n")
    f.write(f"- T: {T}\n\n")
    f.write("## Results\n")
    f.write("![Parameter Scan](./period4_parameter_scan_local.png)\n\n")
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

print("Local parameter scan complete. Artifacts saved.")