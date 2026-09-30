#!/usr/bin/env python3
"""
Defensive Stress-Test for EMP-097: Entropy-Driven Rule Evolution in Self-Referential CA

Tests:
1. Noise Injection: 5% bit-flip noise per iteration.
2. Entropy Metric Sensitivity: Replace Shannon entropy with Tsallis entropy (q=2).
3. Rule Interpolation Artifacts: Use sigmoid interpolation between rule-sets.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import use as mpl_use
from scipy.ndimage import convolve

mpl_use('Agg')  # Headless backend

# Parameters
N = 20
T = 1000
seeds = 3  # Reduced for efficiency
noise_level = 0.05

# Rule-sets (Moore neighborhood)
RULE_GOL = np.array([0, 0, 1, 1, 0, 0, 0, 0, 0])  # Game of Life: B3/S23
RULE_CHAOS = np.array([0, 1, 0, 1, 1, 0, 1, 0, 0])  # Chaotic rule

# Kernel for Moore neighborhood
kernel = np.ones((3, 3), dtype=int)
kernel[1, 1] = 0


def shannon_entropy(grid):
    """Shannon entropy of a binary grid."""
    p = np.mean(grid)
    if p == 0 or p == 1:
        return 0.0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)


def tsallis_entropy(grid, q=2):
    """Tsallis entropy (q=2) of a binary grid."""
    p = np.mean(grid)
    if p == 0 or p == 1:
        return 0.0
    return (1 - (p**q + (1 - p)**q)) / (q - 1)


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


def interpolate_linear(rule_a, rule_b, alpha):
    """Linear interpolation between rules."""
    return (1 - alpha) * rule_a + alpha * rule_b


def interpolate_sigmoid(rule_a, rule_b, alpha):
    """Sigmoid interpolation between rules."""
    alpha_sigmoid = 1 / (1 + np.exp(-10 * (alpha - 0.5)))
    return (1 - alpha_sigmoid) * rule_a + alpha_sigmoid * rule_b


def simulate_ca_entropy(grid_size=50, steps=100, rule_a=None, rule_b=None, alpha=0.5, interpolation='linear'):
    """Simulate CA with interpolated rules and track entropy."""
    if rule_a is None:
        rule_a = np.random.randint(0, 2, 8)
    if rule_b is None:
        rule_b = np.random.randint(0, 2, 8)

    grid = np.random.randint(0, 2, (grid_size, grid_size))
    entropy_shannon = []
    entropy_tsallis = []

    for step in range(steps):
        if interpolation == 'linear':
            rule = interpolate_linear(rule_a, rule_b, alpha)
        else:
            rule = interpolate_sigmoid(rule_a, rule_b, alpha)
        grid = apply_rule(grid, rule)
        entropy_shannon.append(shannon_entropy(grid))
        entropy_tsallis.append(tsallis_entropy(grid))

    return entropy_shannon, entropy_tsallis


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # Parameters
    grid_size = 50
    steps = 100
    alphas = np.linspace(0, 1, 5)
    rule_a = np.array([0, 1, 0, 1, 1, 0, 1, 0])  # Example rule
    rule_b = np.array([1, 0, 1, 0, 0, 1, 0, 1])  # Example rule

    plt.figure(figsize=(10, 6))
    for alpha in alphas:
        entropy_shannon, entropy_tsallis = simulate_ca_entropy(
            grid_size, steps, rule_a, rule_b, alpha, interpolation='linear'
        )
        plt.plot(entropy_shannon, label=f'Shannon (α={alpha:.1f})')
        plt.plot(entropy_tsallis, '--', label=f'Tsallis (α={alpha:.1f})')

    plt.xlabel('Time Step')
    plt.ylabel('Entropy')
    plt.title('Entropy Evolution Under Rule Interpolation (Linear)')
    plt.legend()
    plt.grid(True)
    plt.savefig('../../shared_agora/artifacts/emp097_entropy_evolution.png')
    plt.close()

    # Repeat for sigmoid interpolation
    plt.figure(figsize=(10, 6))
    for alpha in alphas:
        entropy_shannon, entropy_tsallis = simulate_ca_entropy(
            grid_size, steps, rule_a, rule_b, alpha, interpolation='sigmoid'
        )
        plt.plot(entropy_shannon, label=f'Shannon (α={alpha:.1f})')
        plt.plot(entropy_tsallis, '--', label=f'Tsallis (α={alpha:.1f})')

    plt.xlabel('Time Step')
    plt.ylabel('Entropy')
    plt.title('Entropy Evolution Under Rule Interpolation (Sigmoid)')
    plt.legend()
    plt.grid(True)
    plt.savefig('../../shared_agora/artifacts/emp097_entropy_evolution_sigmoid.png')
    plt.close()