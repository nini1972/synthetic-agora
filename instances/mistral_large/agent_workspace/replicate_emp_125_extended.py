#!/usr/bin/env python3
"""
Red-team replication of EMP-125 (Period-4 Symbolic Order Not Detected)
with EXTENDED time steps (T=2000) to test for transient masking.
"""

import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

# Parameters
r_range = np.linspace(3.8625, 3.865, 3)
eps_range = np.linspace(0.130, 0.134, 3)
N = 100
T_short = 500  # EMP-125's time steps
T_long = 2000   # Extended time steps
threshold = 0.5
motif_width = 4
max_lag = 20

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

# Simulation for a single (r, eps) pair
def simulate_parameter_pair(args):
    r, eps, T = args
    x = np.random.rand(N)
    trajectory = np.zeros((T, N))
    for t in range(T):
        x = coupled_logistic_map(x, r, eps)
        trajectory[t] = x
    motifs = symbolic_encoding(trajectory, motif_width)
    c4 = phase_contrast(motifs)
    return c4

# Main replication
def replicate():
    # Test both T=500 and T=2000
    params_short = [(r, eps, T_short) for r in r_range for eps in eps_range]
    params_long = [(r, eps, T_long) for r in r_range for eps in eps_range]
    
    with Pool() as pool:
        c4_short = pool.map(simulate_parameter_pair, params_short)
        c4_long = pool.map(simulate_parameter_pair, params_long)
    
    # Reshape results
    c4_short = np.array(c4_short).reshape(len(r_range), len(eps_range))
    c4_long = np.array(c4_long).reshape(len(r_range), len(eps_range))
    
    # Plot results
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.imshow(c4_short, cmap='viridis', origin='lower', extent=[0.130, 0.134, 3.8625, 3.865])
    plt.colorbar(label='$C_4$')
    plt.xlabel('$\\varepsilon$')
    plt.ylabel('$r$')
    plt.title('$C_4$ (T=500, EMP-125 Replication)')
    
    plt.subplot(1, 2, 2)
    plt.imshow(c4_long, cmap='viridis', origin='lower', extent=[0.130, 0.134, 3.8625, 3.865])
    plt.colorbar(label='$C_4$')
    plt.xlabel('$\\varepsilon$')
    plt.ylabel('$r$')
    plt.title('$C_4$ (T=2000, Extended)')
    
    plt.tight_layout()
    plt.savefig('replicate_emp_125_extended.png')
    
    # Report
    with open('REPORT_replicate_emp_125_extended.md', 'w') as f:
        f.write("# Red-Team Replication of EMP-125 (Extended Time Steps)\n\n")
        f.write("## Parameters\n")
        f.write(f"- r: {r_range}\n")
        f.write(f"- ε: {eps_range}\n")
        f.write(f"- N: {N}\n")
        f.write(f"- T (short): {T_short}\n")
        f.write(f"- T (long): {T_long}\n\n")
        
        f.write("## Results\n")
        f.write("![C4 Heatmaps](./replicate_emp_125_extended.png)\n\n")
        
        f.write("### Short Time Steps (T=500, EMP-125 Replication):\n")
        f.write(f"- Max $C_4$: {np.max(c4_short):.3f}\n")
        f.write(f"- Mean $C_4$: {np.mean(c4_short):.3f}\n\n")
        
        f.write("### Extended Time Steps (T=2000):\n")
        f.write(f"- Max $C_4$: {np.max(c4_long):.3f}\n")
        f.write(f"- Mean $C_4$: {np.mean(c4_long):.3f}\n\n")
        
        f.write("## Interpretation\n")
        if np.max(c4_long) > 0.1:
            f.write("✅ **Period-4 structure detected with extended time steps (T=2000).**\n")
            f.write("EMP-125's results may be **masked by transient dynamics** due to insufficient simulation time.\n")
        else:
            f.write("❌ **No period-4 structure detected even with extended time steps.**\n")
            f.write("EMP-125's results are **robust** to simulation time. Further investigation needed.\n")

if __name__ == "__main__":
    replicate()