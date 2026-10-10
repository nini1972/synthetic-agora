#!/usr/bin/env python3
"""
World C script to replicate Frontier Dossier #105's hidden period-4 structure
in coupled logistic map lattices using 4-bit motif encoding and LOCAL dynamics.

System:
    x_i^{t+1} = (1-ε)r x_i^t(1-x_i^t) + (ε/2)[r x_{i-1}^t(1-x_{i-1}^t) + r x_{i+1}^t(1-x_{i+1}^t)]

Parameters: r=3.865, ε=0.132, N=100, T=2000
"""

import numpy as np
import matplotlib.pyplot as plt

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

# Parameters
r = 3.865
eps = 0.132
N = 100  # System size
T = 2000  # Time steps
threshold = 0.5
motif_width = 4
max_lag = 20  # Maximum lag for analysis

# Local dynamics: Coupled logistic map
def coupled_logistic_map(x, r, eps):
    x_prev = np.roll(x, 1)
    x_next = np.roll(x, -1)
    return (1 - eps) * r * x * (1 - x) + (eps / 2) * (r * x_prev * (1 - x_prev) + r * x_next * (1 - x_next))

# Symbolic encoding: 4-bit motifs
def symbolic_encoding(x, width=4):
    binary = (x > threshold).astype(int)
    motifs = np.zeros((T - width + 1, N), dtype=int)
    for i in range(width):
        motifs |= (binary[i:T - width + 1 + i] << (width - 1 - i))
    return motifs

# Lag consistency (patched)
def lag_consistency(motifs, lag):
    if lag >= motifs.shape[0]:
        return 0.0  # Edge case: lag too large
    matches = np.sum(motifs[:-lag] == motifs[lag:])
    total = (motifs.shape[0] - lag) * motifs.shape[1]
    return matches / total if total > 0 else 0.0

# Main simulation
def simulate():
    # Initialize lattice
    x = np.random.rand(N)
    
    # Run simulation
    trajectory = np.zeros((T, N))
    for t in range(T):
        x = coupled_logistic_map(x, r, eps)
        trajectory[t] = x
    
    # Symbolic encoding
    motifs = symbolic_encoding(trajectory, motif_width)
    
    # Lag consistency analysis
    lags = np.arange(1, max_lag + 1)
    consistency = np.array([lag_consistency(motifs, lag) for lag in lags])
    
    # Period-4 residue analysis
    residues = np.zeros(4)
    for lag in range(4):
        residue_lags = np.arange(lag, max_lag + 1, 4)
        residue_consistency = [lag_consistency(motifs, l) for l in residue_lags]
        residues[lag] = np.mean(residue_consistency)
    
    # Parity contrast
    parity_contrast = residues[0] - residues[2]
    
    # Plot results
    plt.figure(figsize=(12, 6))
    
    # Lag consistency
    plt.subplot(1, 2, 1)
    plt.plot(lags, consistency, 'o-', label='Lag Consistency')
    plt.xlabel('Lag (τ)')
    plt.ylabel('Consistency')
    plt.title('Lag Consistency Analysis')
    plt.grid(True)
    
    # Period-4 residues
    plt.subplot(1, 2, 2)
    plt.bar(range(4), residues, color=['red', 'blue', 'green', 'orange'])
    plt.xticks(range(4), ['0 mod 4', '1 mod 4', '2 mod 4', '3 mod 4'])
    plt.ylabel('Mean Consistency')
    plt.title(f'Period-4 Residue Analysis\nParity Contrast: {parity_contrast:.3f}')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('world_c_period4_patched.png')
    
    # Report
    with open('REPORT_world_c_period4_patched.md', 'w') as f:
        f.write("# World C Replication of Frontier Dossier #105 (Patched)\n\n")
        f.write("## Parameters\n")
        f.write(f"- r: {r}\n")
        f.write(f"- ε: {eps}\n")
        f.write(f"- N: {N}\n")
        f.write(f"- T: {T}\n")
        f.write(f"- Motif Width: {motif_width}\n")
        f.write(f"- Max Lag: {max_lag}\n\n")
        
        f.write("## Results\n")
        f.write("![Lag Consistency and Period-4 Residues](./world_c_period4_patched.png)\n\n")
        f.write("### Period-4 Residues:\n")
        for lag in range(4):
            f.write(f"- Residue {lag} (lags ≡ {lag} mod 4): {residues[lag]:.3f}\n")
        f.write(f"- **Parity Contrast (C4)**: {parity_contrast:.3f}\n\n")
        
        f.write("## Interpretation\n")
        if parity_contrast > 0.1:
            f.write("✅ **Period-4 structure detected** in the tested parameter regime.\n")
            f.write("The parity contrast (C4) exceeds the threshold, confirming the Frontier's claim.\n")
        else:
            f.write("❌ **No period-4 structure detected** in the tested parameter regime.\n")
            f.write("The parity contrast (C4) is below the threshold, refuting the Frontier's claim.\n")

if __name__ == "__main__":
    simulate()