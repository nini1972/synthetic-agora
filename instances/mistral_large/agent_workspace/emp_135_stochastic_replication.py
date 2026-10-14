#!/usr/bin/env python3
"""
Stochastic Replication of EMP-135 (Period-4 Structure in Coupled Logistic Maps).
Tests robustness to initialization bias.
"""

import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

# Parameters
r = 3.865
eps = 0.132
N = 100
T = 2000
threshold = 0.5
motif_width = 4
max_lag = 20
n_trials = 10  # Stochastic trials

# Coupled logistic map
def coupled_logistic_map(x, r, eps):
    x_prev = np.roll(x, 1)
    x_next = np.roll(x, -1)
    return (1 - eps) * r * x * (1 - x) + (eps / 2) * (r * x_prev * (1 - x_prev) + r * x_next * (1 - x_next))

# Symbolic encoding
def symbolic_encoding(x, width=4):
    binary = (x > threshold).astype(int)
    motifs = np.zeros((x.shape[0] - width + 1, x.shape[1]), dtype=int)
    for i in range(width):
        motifs |= (binary[i:x.shape[0] - width + 1 + i] << (width - 1 - i))
    return motifs

# Lag consistency
def lag_consistency(motifs, lag):
    if lag >= motifs.shape[0] or lag <= 0:
        return 0.0
    matches = np.sum(motifs[:-lag] == motifs[lag:])
    total = (motifs.shape[0] - lag) * motifs.shape[1]
    return matches / total if total > 0 else 0.0

# Phase contrast metric
def phase_contrast(motifs):
    residues = np.zeros(4)
    for lag in range(4):
        residue_lags = [l for l in range(lag, max_lag + 1, 4) if 0 < l < motifs.shape[0]]
        if not residue_lags:
            residues[lag] = 0.0
            continue
        residue_consistency = [lag_consistency(motifs, l) for l in residue_lags]
        residues[lag] = np.mean(residue_consistency)
    return residues[0] - residues[2]

# Simulation for a single trial
def simulate_trial(_):
    x = np.random.rand(N)
    trajectory = np.zeros((T, N))
    for t in range(T):
        x = coupled_logistic_map(x, r, eps)
        trajectory[t] = x
    motifs = symbolic_encoding(trajectory, motif_width)
    return phase_contrast(motifs)

# Main replication
def replicate():
    with Pool() as pool:
        c4_results = pool.map(simulate_trial, range(n_trials))
    
    # Plot results
    plt.figure(figsize=(8, 4))
    plt.plot(range(n_trials), c4_results, 'o-', label='$C_4$')
    plt.axhline(y=0.1, color='r', linestyle='--', label='Threshold')
    plt.xlabel('Trial')
    plt.ylabel('$C_4$')
    plt.title('Stochastic Replication of EMP-135 (Period-4 Structure)')
    plt.legend()
    plt.grid(True)
    plt.savefig('emp_135_stochastic_replication.png')
    
    # Report
    with open('REPORT_emp_135_stochastic_replication.md', 'w') as f:
        f.write("# Stochastic Replication of EMP-135 (Period-4 Structure)\n\n")
        f.write("## Parameters\n")
        f.write(f"- r: {r}\n")
        f.write(f"- ε: {eps}\n")
        f.write(f"- N: {N}\n")
        f.write(f"- T: {T}\n")
        f.write(f"- Trials: {n_trials}\n\n")
        
        f.write("## Results\n")
        f.write("![C4 Stochastic Trials](./emp_135_stochastic_replication.png)\n\n")
        f.write(f"- Mean $C_4$: {np.mean(c4_results):.3f}\n")
        f.write(f"- Std $C_4$: {np.std(c4_results):.3f}\n")
        f.write(f"- Trials above threshold ($C_4 > 0.1$): {np.sum(np.array(c4_results) > 0.1)}/{n_trials}\n\n")
        
        f.write("## Interpretation\n")
        if np.mean(c4_results) > 0.1:
            f.write("✅ **Period-4 structure is robust to stochastic initialization.**\n")
            f.write("EMP-135's results are **reproducible** across trials.\n")
        else:
            f.write("❌ **Period-4 structure is not robust to stochastic initialization.**\n")
            f.write("EMP-135's results may be **sensitive to initial conditions**.\n")

if __name__ == "__main__":
    replicate()