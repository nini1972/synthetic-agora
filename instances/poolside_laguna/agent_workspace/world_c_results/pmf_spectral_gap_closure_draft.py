#!/usr/bin/env python3
"""
World C Script Draft: PMF Spectral Gap Closure Test (SYN-062)

Objective: Test if Primordial Magnetic Fields (PMFs) induce spectral gap closure
in the normalized Laplacian of a cosmic web proxy (IEEE 14-bus power grid).

Usage:
- Submit via `submit_world_c_job(title="PMF Spectral Gap Closure Test", 
  script_content=..., stage_name="pmf_spectral_gap")`.
- Resume via `StageTracker('pmf_spectral_gap').load_stage(B_value)`.
"""

import numpy as np
from colony_lib.persistence import StageTracker
from colony_lib.datasets import load_dataset
from colony_lib.network_topology import laplacian_spectrum, generate_topology
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- Parameters ---
B_values = np.linspace(0.1, 10.0, 50)  # PMF strength (nG)
B_crit = 3.0  # Critical PMF strength (nG)
rho_B_rho_rad = 5.1e-7  # Energy density ratio (B=3 nG)

# --- Load Cosmic Web Proxy ---
dataset = load_dataset("power_grid_ieee")
A = dataset['adjacency_matrix']  # IEEE 14-bus adjacency matrix
N = A.shape[0]

# --- PMF-Induced Weight Perturbation ---
def compute_pmf_stress(B):
    """Compute normalized PMF-induced stress."""
    return (B / B_crit)**2 * rho_B_rho_rad

def perturb_weights(A, B, pmf_direction=np.array([1.0, 0.0])):
    """Perturb weights with PMF-induced anisotropic stress."""
    sigma_B = compute_pmf_stress(B)
    W = A.astype(float)  # Baseline weights (binary → float)
    
    # Compute edge angles relative to PMF direction
    pos = dataset['positions']  # Node positions (2D)
    for i in range(N):
        for j in range(i + 1, N):
            if A[i, j] > 0:
                r_ij = pos[j] - pos[i]
                theta_ij = np.arctan2(r_ij[1], r_ij[0])
                W[i, j] += sigma_B * np.cos(2 * theta_ij)
                W[j, i] = W[i, j]  # Symmetric
    
    return W

# --- Spectral Analysis ---
def compute_spectral_ratio(W):
    """Compute λ₂/λ₁ for the symmetric normalized Laplacian."""
    D = np.diag(np.sum(W, axis=1))
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(D) + 1e-10))
    L_sym = D_inv_sqrt @ (D - W) @ D_inv_sqrt
    evals = laplacian_spectrum(L_sym)
    return evals[1] / evals[0]  # λ₂ / λ₁

# --- Main Simulation ---
def run_simulation():
    tracker = StageTracker('pmf_spectral_gap')
    results = []
    
    for B in B_values:
        if tracker.is_done(f'B_{B:.2f}'):
            ratio = tracker.get_stage(f'B_{B:.2f}')
        else:
            W = perturb_weights(A, B)
            ratio = compute_spectral_ratio(W)
            tracker.save_stage(f'B_{B:.2f}', ratio)
        results.append((B, ratio))
    
    return results

# --- Plot ---
def plot_results(results):
    B_vals, ratios = zip(*results)
    plt.figure(figsize=(10, 6))
    plt.plot(B_vals, ratios, 'o-', label='$λ₂ / λ₁$')
    plt.axhline(y=1.1, color='r', linestyle='--', label='Critical Threshold')
    plt.axvline(x=B_crit, color='g', linestyle=':', label='$B_{\mathrm{crit}}$')
    plt.xlabel('PMF Strength $B$ (nG)')
    plt.ylabel('Spectral Ratio $λ₂ / λ₁$')
    plt.title('SYN-062: PMF-Induced Spectral Gap Closure')
    plt.legend()
    plt.grid(True)
    plt.savefig('pmf_spectral_gap_closure.png')
    plt.close()

# --- Report ---
def generate_report(results):
    with open('REPORT.md', 'w') as f:
        f.write('# SYN-062: PMF-Induced Spectral Gap Closure Test\n\n')
        f.write('| PMF Strength $B$ (nG) | Spectral Ratio $λ₂ / λ₁$ |\n')
        f.write('|-------------------------|---------------------------|\n')
        for B, ratio in results:
            f.write(f'| {B:.2f} | {ratio:.4f} |\n')
        f.write('\n## Key Findings:\n')
        f.write('- **Spectral gap closure** ($λ₂ / λ₁ < 1.1$) indicates **PMF-induced criticality**.
')
        f.write('- **$B_{\mathrm{crit}} = 3.0$ nG** is the **hypothesized threshold**.
')
        f.write('\n## Artifact:\n')
        f.write('![PMF Spectral Gap Closure](pmf_spectral_gap_closure.png)\n')

# --- Main ---
if __name__ == "__main__":
    results = run_simulation()
    plot_results(results)
    generate_report(results)