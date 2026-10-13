#!/usr/bin/env python3
"""
Empirical test of HYP-113: Advanced entropy measures for Conway's Game of Life
Testing whether advanced entropy measures can distinguish emergent vs chaotic patterns.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter
import hashlib

class ConwayGameOfLife:
    def __init__(self, size=100):
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.history = []
        
    def set_pattern(self, pattern, pos=(50, 50)):
        """Place a pattern at given position."""
        y, x = pos
        h, w = pattern.shape
        self.grid[y:y+h, x:x+w] = pattern
        
    def step(self):
        """Single evolution step."""
        new_grid = np.copy(self.grid)
        
        for i in range(1, self.size-1):
            for j in range(1, self.size-1):
                # Count live neighbors
                neighbors = np.sum(self.grid[i-1:i+2, j-1:j+2]) - self.grid[i, j]
                
                if self.grid[i, j] == 1:  # Currently alive
                    if neighbors < 2 or neighbors > 3:
                        new_grid[i, j] = 0  # Dies
                else:  # Currently dead
                    if neighbors == 3:
                        new_grid[i, j] = 1  # Born
                        
        self.grid = new_grid
        self.history.append(np.copy(self.grid))
        
    def evolve(self, steps=100):
        """Evolve for multiple steps."""
        self.history = [np.copy(self.grid)]
        for _ in range(steps):
            self.step()

def global_shannon_entropy(grid):
    """Calculate global Shannon entropy of the grid."""
    alive_count = np.sum(grid)
    total_cells = grid.size
    
    if alive_count == 0 or alive_count == total_cells:
        return 0.0
        
    p_alive = alive_count / total_cells
    p_dead = 1 - p_alive
    
    return -(p_alive * np.log2(p_alive) + p_dead * np.log2(p_dead))

def block_entropy(grid, block_size=3):
    """Calculate block entropy using spatial n-grams."""
    h, w = grid.shape
    blocks = []
    
    for i in range(h - block_size + 1):
        for j in range(w - block_size + 1):
            block = grid[i:i+block_size, j:j+block_size]
            # Convert block to string for hashing
            block_str = ''.join(map(str, block.flatten()))
            blocks.append(block_str)
    
    if not blocks:
        return 0.0
        
    counts = Counter(blocks)
    total = len(blocks)
    
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * np.log2(p)
        
    return entropy

def lempel_ziv_complexity(sequence):
    """Calculate Lempel-Ziv complexity of a binary sequence."""
    if len(sequence) == 0:
        return 0
        
    s = ''.join(map(str, sequence.flatten()))
    n = len(s)
    
    if n <= 1:
        return 1
        
    complexity = 1
    i = 1
    
    while i < n:
        j = 0
        max_match = 0
        
        # Find longest match in prefix
        while j < i:
            match_len = 0
            while (i + match_len < n and 
                   j + match_len < i and 
                   s[i + match_len] == s[j + match_len]):
                match_len += 1
            max_match = max(max_match, match_len)
            j += 1
            
        if max_match == 0:
            complexity += 1
            i += 1
        else:
            complexity += 1
            i += max_match + 1
            
    return complexity

def local_entropy_variance(grid, window_size=5):
    """Calculate variance of local entropy measures."""
    h, w = grid.shape
    local_entropies = []
    
    for i in range(window_size//2, h - window_size//2):
        for j in range(window_size//2, w - window_size//2):
            window = grid[i-window_size//2:i+window_size//2+1, 
                         j-window_size//2:j+window_size//2+1]
            local_entropies.append(global_shannon_entropy(window))
    
    return np.var(local_entropies) if local_entropies else 0.0

def analyze_pattern_complexity(game, pattern_name, steps=50):
    """Analyze complexity measures for a specific pattern."""
    game.evolve(steps)
    
    results = {
        'pattern': pattern_name,
        'global_entropy': [],
        'block_entropy': [],
        'lz_complexity': [],
        'local_entropy_var': []
    }
    
    for t, grid in enumerate(game.history[::5]):  # Sample every 5 steps
        results['global_entropy'].append(global_shannon_entropy(grid))
        results['block_entropy'].append(block_entropy(grid, block_size=3))
        results['lz_complexity'].append(lempel_ziv_complexity(grid))
        results['local_entropy_var'].append(local_entropy_variance(grid))
    
    return results

# Define patterns to test
def get_glider():
    """Classic glider pattern."""
    return np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ])

def get_oscillator():
    """Period-2 blinker oscillator."""
    return np.array([
        [1, 1, 1]
    ])

def get_still_life():
    """Block still life."""
    return np.array([
        [1, 1],
        [1, 1]
    ])

def get_random_pattern(size=10, density=0.3):
    """Random pattern for chaos comparison."""
    return (np.random.random((size, size)) < density).astype(int)

def get_pulsar():
    """Period-3 pulsar oscillator."""
    pulsar = np.zeros((17, 17))
    # Pulsar pattern coordinates
    coords = [(2,4), (2,5), (2,10), (2,11),
              (4,2), (4,7), (4,9), (4,14),
              (5,2), (5,7), (5,9), (5,14),
              (7,4), (7,5), (7,10), (7,11),
              (9,4), (9,5), (9,10), (9,11),
              (10,2), (10,7), (10,9), (10,14),
              (11,2), (11,7), (11,9), (11,14),
              (14,4), (14,5), (14,10), (14,11)]
    
    for y, x in coords:
        pulsar[y, x] = 1
    return pulsar

# Run experiments
print("Conway's Game of Life: Advanced Entropy Analysis")
print("=" * 55)

patterns_to_test = [
    ("Glider", get_glider()),
    ("Blinker", get_oscillator()),  
    ("Block", get_still_life()),
    ("Pulsar", get_pulsar()),
    ("Random-1", get_random_pattern(density=0.2)),
    ("Random-2", get_random_pattern(density=0.4)),
    ("Random-3", get_random_pattern(density=0.6))
]

all_results = []

for pattern_name, pattern in patterns_to_test:
    print(f"\nAnalyzing {pattern_name}...")
    
    game = ConwayGameOfLife(size=80)
    pos = (40 - pattern.shape[0]//2, 40 - pattern.shape[1]//2)
    game.set_pattern(pattern, pos)
    
    results = analyze_pattern_complexity(game, pattern_name, steps=100)
    all_results.append(results)
    
    # Print summary statistics
    print(f"  Global Entropy (mean): {np.mean(results['global_entropy']):.3f}")
    print(f"  Block Entropy (mean): {np.mean(results['block_entropy']):.3f}")
    print(f"  LZ Complexity (final): {results['lz_complexity'][-1]}")
    print(f"  Local Entropy Var: {np.mean(results['local_entropy_var']):.6f}")

# Create comprehensive visualization
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Categorize patterns
emergent_patterns = ["Glider", "Blinker", "Block", "Pulsar"]
random_patterns = ["Random-1", "Random-2", "Random-3"]

colors = {'emergent': 'blue', 'random': 'red'}

# Plot 1: Global vs Block Entropy
ax = axes[0, 0]
for results in all_results:
    color = colors['emergent'] if results['pattern'] in emergent_patterns else colors['random']
    ax.scatter(np.mean(results['global_entropy']), 
               np.mean(results['block_entropy']),
               label=results['pattern'], s=100, alpha=0.7, color=color)

ax.set_xlabel('Global Shannon Entropy (mean)')
ax.set_ylabel('Block Entropy (mean)')
ax.set_title('Global vs Block Entropy')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Plot 2: Lempel-Ziv Complexity comparison
ax = axes[0, 1]
patterns = [r['pattern'] for r in all_results]
lz_values = [r['lz_complexity'][-1] for r in all_results]
colors_list = [colors['emergent'] if p in emergent_patterns else colors['random'] for p in patterns]

bars = ax.bar(patterns, lz_values, color=colors_list, alpha=0.7)
ax.set_xlabel('Pattern Type')
ax.set_ylabel('Lempel-Ziv Complexity')
ax.set_title('Algorithmic Complexity Comparison')
ax.tick_params(axis='x', rotation=45)

# Add value labels on bars
for bar, value in zip(bars, lz_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
            str(value), ha='center', va='bottom', fontsize=9)

# Plot 3: Local Entropy Variance
ax = axes[1, 0]
local_var_values = [np.mean(r['local_entropy_var']) for r in all_results]
bars = ax.bar(patterns, local_var_values, color=colors_list, alpha=0.7)
ax.set_xlabel('Pattern Type')
ax.set_ylabel('Local Entropy Variance (mean)')
ax.set_title('Spatial Heterogeneity Analysis')
ax.tick_params(axis='x', rotation=45)

# Plot 4: Time series evolution for selected patterns
ax = axes[1, 1]
selected_patterns = ["Glider", "Pulsar", "Random-2"]
for results in all_results:
    if results['pattern'] in selected_patterns:
        time_points = range(len(results['global_entropy']))
        color = colors['emergent'] if results['pattern'] in emergent_patterns else colors['random']
        ax.plot(time_points, results['global_entropy'], 
                label=f"{results['pattern']} (Global)", color=color, linestyle='-')
        ax.plot(time_points, np.array(results['block_entropy'])/10, 
                label=f"{results['pattern']} (Block/10)", color=color, linestyle='--', alpha=0.7)

ax.set_xlabel('Time Steps (×5)')
ax.set_ylabel('Entropy')
ax.set_title('Temporal Evolution of Entropy Measures')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('conway_entropy_analysis.png', dpi=150, bbox_inches='tight')
print("\nVisualization saved as conway_entropy_analysis.png")

# Statistical analysis
print("\n" + "=" * 60)
print("STATISTICAL DISCRIMINATION ANALYSIS")
print("=" * 60)

# Calculate discrimination metrics
emergent_results = [r for r in all_results if r['pattern'] in emergent_patterns]
random_results = [r for r in all_results if r['pattern'] in random_patterns]

metrics = ['global_entropy', 'block_entropy', 'lz_complexity', 'local_entropy_var']

for metric in metrics:
    emergent_values = []
    random_values = []
    
    for r in emergent_results:
        if metric == 'lz_complexity':
            emergent_values.append(r[metric][-1])  # Final value
        else:
            emergent_values.append(np.mean(r[metric]))
    
    for r in random_results:
        if metric == 'lz_complexity':
            random_values.append(r[metric][-1])  # Final value
        else:
            random_values.append(np.mean(r[metric]))
    
    emergent_mean = np.mean(emergent_values)
    random_mean = np.mean(random_values)
    
    # Cohen's d effect size
    pooled_std = np.sqrt((np.var(emergent_values) + np.var(random_values)) / 2)
    cohens_d = abs(emergent_mean - random_mean) / pooled_std if pooled_std > 0 else float('inf')
    
    print(f"\n{metric.replace('_', ' ').title()}:")
    print(f"  Emergent mean: {emergent_mean:.4f} ± {np.std(emergent_values):.4f}")
    print(f"  Random mean:   {random_mean:.4f} ± {np.std(random_values):.4f}")
    print(f"  Cohen's d:     {cohens_d:.3f} ({'Large' if cohens_d > 0.8 else 'Medium' if cohens_d > 0.5 else 'Small'})")

print("\n" + "=" * 60)
print("HYPOTHESIS VERDICT")
print("=" * 60)

# Determine which measures successfully discriminate
successful_measures = []
discrimination_scores = []

for metric in metrics:
    emergent_values = []
    random_values = []
    
    for r in emergent_results:
        if metric == 'lz_complexity':
            emergent_values.append(r[metric][-1])
        else:
            emergent_values.append(np.mean(r[metric]))
    
    for r in random_results:
        if metric == 'lz_complexity':
            random_values.append(r[metric][-1])
        else:
            random_values.append(np.mean(r[metric]))
    
    pooled_std = np.sqrt((np.var(emergent_values) + np.var(random_values)) / 2)
    if pooled_std > 0:
        cohens_d = abs(np.mean(emergent_values) - np.mean(random_values)) / pooled_std
        discrimination_scores.append(cohens_d)
        if cohens_d > 0.5:  # Medium effect size threshold
            successful_measures.append(metric)

print(f"Measures successfully discriminating (Cohen's d > 0.5): {len(successful_measures)}/4")
print(f"Successful measures: {', '.join(successful_measures)}")

if len(successful_measures) >= 2:
    print("\n✓ HYPOTHESIS CONFIRMED: Advanced entropy measures can distinguish")
    print("  emergent complexity from chaotic configurations in Conway's Game of Life.")
else:
    print("\n✗ HYPOTHESIS CHALLENGED: Limited discrimination ability found.")

print(f"\nOverall discrimination power: {np.mean(discrimination_scores):.3f}")
print(f"Best discriminating measure: {metrics[np.argmax(discrimination_scores)]}")