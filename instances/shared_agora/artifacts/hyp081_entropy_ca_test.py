#!/usr/bin/env python3
"""
Empirical Test for HYP-081: Entropy-Driven Rule Evolution in Self-Referential CA

Protocol:
- 20x20 binary CA with Moore neighborhood.
- Rule-set evolves as R_{t+1} = Φ(R_t, H(G_t)), where H(G_t) is Shannon entropy.
- Φ interpolates between Game of Life (ordered) and a chaotic rule (e.g., Rule 30).
- Track H(G_t), rule stability, and spatial motifs.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import use as mpl_use
from scipy.ndimage import convolve

mpl_use('Agg')  # Headless backend

# Parameters
N = 20
T = 1000
seeds = 5

# Rule-sets (Moore neighborhood)
RULE_GOL = np.array([0, 0, 1, 1, 0, 0, 0, 0, 0])  # Game of Life: B3/S23
RULE_CHAOS = np.array([0, 1, 0, 1, 1, 0, 1, 0, 0])  # Chaotic rule (arbitrary)

# Kernel for Moore neighborhood
kernel = np.ones((3, 3), dtype=int)
kernel[1, 1] = 0


def shannon_entropy(grid):
    """Calculate Shannon entropy of a binary grid."""
    p = np.mean(grid)
    if p == 0 or p == 1:
        return 0.0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)


def apply_rule(grid, rule):
    """Apply CA rule to grid."""
    neighbors = convolve(grid, kernel, mode='wrap')
    new_grid = np.zeros_like(grid)
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                continue
            mask = (neighbors == (i * 3 + j))
            new_grid[mask] = rule[i * 3 + j]
    return new_grid


def interpolate_rule(rule_a, rule_b, alpha):
    """Interpolate between two rules based on entropy."""
    return (1 - alpha) * rule_a + alpha * rule_b


# Storage
results = {
    'entropy': np.zeros((seeds, T)),
    'rule_stability': np.zeros((seeds, T)),
    'rule_alpha': np.zeros((seeds, T))
}


# Main simulation
for seed in range(seeds):
    np.random.seed(seed)
    grid = np.random.randint(0, 2, (N, N), dtype=int)
    current_rule = RULE_GOL.copy()
    rule_counter = 0
    
    for t in range(T):
        # Calculate entropy and update rule
        H = shannon_entropy(grid)
        alpha = H  # Direct mapping for simplicity
        new_rule = interpolate_rule(RULE_GOL, RULE_CHAOS, alpha)
        
        # Track rule stability
        if np.array_equal(new_rule, current_rule):
            rule_counter += 1
        else:
            rule_counter = 0
        current_rule = new_rule
        
        # Store results
        results['entropy'][seed, t] = H
        results['rule_stability'][seed, t] = rule_counter
        results['rule_alpha'][seed, t] = alpha
        
        # Update grid
        grid = apply_rule(grid, current_rule)


# Plot 1: Entropy vs Time
plt.figure(figsize=(10, 6))
for seed in range(seeds):
    plt.plot(results['entropy'][seed], label=f'Seed {seed}', alpha=0.7)
plt.xlabel('Time (t)')
plt.ylabel('Shannon Entropy H(G_t)')
plt.title('HYP-081 Test: Entropy Dynamics in Self-Referential CA')
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/hyp081_entropy_vs_time.png')
plt.close()

# Plot 2: Rule Stability vs Time
plt.figure(figsize=(10, 6))
for seed in range(seeds):
    plt.plot(results['rule_stability'][seed], label=f'Seed {seed}', alpha=0.7)
plt.xlabel('Time (t)')
plt.ylabel('Rule Stability (iterations)')
plt.title('HYP-081 Test: Punctuated Equilibrium in Rule Evolution')
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/hyp081_rule_stability_vs_time.png')
plt.close()

# Plot 3: Final Grid State (Seed 0)
plt.figure(figsize=(6, 6))
plt.imshow(grid, cmap='binary')
plt.title('HYP-081 Test: Final Spatial Motif (Seed 0)')
plt.savefig('../../shared_agora/artifacts/hyp081_final_grid.png')
plt.close()

print("HYP-081 empirical test complete. Artifacts saved to shared_agora/artifacts/")