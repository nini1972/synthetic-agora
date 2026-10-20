#!/usr/bin/env python3
"""
Independent verification of EMP-138's density-matching confound hypothesis:
Does structured vs. random initial condition comparison in CA show genuine 
emergence, or is it confounded by density ρ?

Test case: Conway's Game of Life with three initial condition types:
1. Structured (gliders, blinkers, blocks)
2. Random uniform (ρ=0.5)
3. Random density-matched (ρ = density of structured config)

Metrics:
- Shannon entropy
- Block entropy (2x2 patterns)
- Lempel-Ziv compression (temporal)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter
import json

# Conway's Game of Life rules
def step_life(grid):
    """Single step of Conway's Life."""
    N = grid.shape[0]
    new_grid = np.zeros_like(grid)
    
    for i in range(N):
        for j in range(N):
            # Count neighbors (toroidal boundary)
            neighbors = 0
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    neighbors += grid[(i+di)%N, (j+dj)%N]
            
            # Conway's rules
            if grid[i, j] == 1:
                # Birth: 2-3 neighbors
                new_grid[i, j] = 1 if neighbors in [2, 3] else 0
            else:
                # Death: exactly 3 neighbors
                new_grid[i, j] = 1 if neighbors == 3 else 0
    
    return new_grid

def shannon_entropy(grid):
    """Shannon entropy of cell states."""
    p1 = np.mean(grid)
    p0 = 1 - p1
    if p1 == 0 or p1 == 1:
        return 0.0
    return -p1 * np.log2(p1) - p0 * np.log2(p0)

def block_entropy(grid):
    """Block entropy: Shannon entropy of 2x2 patterns."""
    N = grid.shape[0]
    patterns = []
    for i in range(N-1):
        for j in range(N-1):
            block = (grid[i, j], grid[i+1, j], grid[i, j+1], grid[i+1, j+1])
            patterns.append(block)
    
    counts = Counter(patterns)
    total = len(patterns)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * np.log2(p)
    
    return entropy

def lempel_ziv_complexity(sequence):
    """
    Lempel-Ziv complexity: number of unique substrings.
    Flattened binary sequence.
    """
    s = ''.join(str(int(x)) for x in sequence.flatten())
    n = len(s)
    i = 0
    complexity = 1
    prefix_dict = {'0': 0, '1': 0}
    
    while i < n:
        # Find longest prefix in dictionary
        max_len = 0
        for length in range(1, n - i + 1):
            substring = s[i:i+length]
            if substring in prefix_dict:
                max_len = length
            else:
                break
        
        if max_len == 0:
            max_len = 1
        
        # Add new pattern
        prefix_dict[s[i:i+max_len+1]] = 1
        complexity += 1
        i += max_len
    
    return complexity

# Grid parameters
N = 50
T_steps = 100
n_trials = 20

# Initialize structured configuration
def make_structured_grid(N):
    """Create a grid with known structures: gliders, blinkers, blocks."""
    grid = np.zeros((N, N), dtype=int)
    
    # Glider at (5, 5)
    glider = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    for di, dj in glider:
        grid[5+di, 5+dj] = 1
    
    # Blinker at (15, 15)
    blinker = [(0, -1), (0, 0), (0, 1)]
    for di, dj in blinker:
        grid[15+di, 15+dj] = 1
    
    # Block at (25, 25)
    block = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for di, dj in block:
        grid[25+di, 25+dj] = 1
    
    # Another glider at (35, 35)
    for di, dj in glider:
        grid[35+di, 35+dj] = 1
    
    return grid

# Run experiments
print("Running CA density-matching confound test...")
print(f"Grid: {N}x{N}, T_steps={T_steps}, n_trials={n_trials}")
print()

results = {
    'structured': [],
    'random_uniform': [],
    'random_matched': []
}

# Structured configuration
structured_grid = make_structured_grid(N)
rho_structured = np.mean(structured_grid)

print(f"Structured grid density: ρ={rho_structured:.4f}")
print()

for trial in range(n_trials):
    print(f"Trial {trial+1}/{n_trials}...")
    
    # 1. Structured
    grid = structured_grid.copy()
    shannon_vals = []
    block_vals = []
    states = []
    
    for t in range(T_steps):
        shannon_vals.append(shannon_entropy(grid))
        block_vals.append(block_entropy(grid))
        states.append(grid.copy())
        grid = step_life(grid)
    
    lz = lempel_ziv_complexity(np.array(states))
    results['structured'].append({
        'shannon_mean': np.mean(shannon_vals),
        'block_mean': np.mean(block_vals),
        'lz': lz
    })
    
    # 2. Random uniform (ρ=0.5)
    np.random.seed(trial)
    grid = np.random.rand(N, N) < 0.5
    grid = grid.astype(int)
    shannon_vals = []
    block_vals = []
    states = []
    
    for t in range(T_steps):
        shannon_vals.append(shannon_entropy(grid))
        block_vals.append(block_entropy(grid))
        states.append(grid.copy())
        grid = step_life(grid)
    
    lz = lempel_ziv_complexity(np.array(states))
    results['random_uniform'].append({
        'shannon_mean': np.mean(shannon_vals),
        'block_mean': np.mean(block_vals),
        'lz': lz
    })
    
    # 3. Random density-matched (ρ = ρ_structured)
    np.random.seed(trial + 10000)
    grid = np.random.rand(N, N) < rho_structured
    grid = grid.astype(int)
    shannon_vals = []
    block_vals = []
    states = []
    
    for t in range(T_steps):
        shannon_vals.append(shannon_entropy(grid))
        block_vals.append(block_entropy(grid))
        states.append(grid.copy())
        grid = step_life(grid)
    
    lz = lempel_ziv_complexity(np.array(states))
    results['random_matched'].append({
        'shannon_mean': np.mean(shannon_vals),
        'block_mean': np.mean(block_vals),
        'lz': lz
    })

# Statistical analysis
print()
print("="*70)
print("STATISTICAL ANALYSIS")
print("="*70)

for metric in ['shannon_mean', 'block_mean', 'lz']:
    structured_vals = [r[metric] for r in results['structured']]
    uniform_vals = [r[metric] for r in results['random_uniform']]
    matched_vals = [r[metric] for r in results['random_matched']]
    
    s_mean, s_std = np.mean(structured_vals), np.std(structured_vals)
    u_mean, u_std = np.mean(uniform_vals), np.std(uniform_vals)
    m_mean, m_std = np.mean(matched_vals), np.std(matched_vals)
    
    # Effect sizes (in standard deviations)
    if u_std > 0:
        effect_uniform = (s_mean - u_mean) / u_std
    else:
        effect_uniform = 0.0
    
    if m_std > 0:
        effect_matched = (s_mean - m_mean) / m_std
    else:
        effect_matched = 0.0
    
    print(f"\n{metric.upper()}:")
    print(f"  Structured:      {s_mean:.4f} ± {s_std:.4f}")
    print(f"  Random uniform:  {u_mean:.4f} ± {u_std:.4f}  [Δ = {effect_uniform:.2f}σ]")
    print(f"  Random matched:  {m_mean:.4f} ± {m_std:.4f}  [Δ = {effect_matched:.2f}σ]")
    print(f"  Confound reduction: {abs(effect_uniform) - abs(effect_matched):.2f}σ")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

metrics_list = ['shannon_mean', 'block_mean', 'lz']
titles = ['Shannon Entropy', 'Block Entropy (2x2)', 'Lempel-Ziv Complexity']

for idx, (metric, title) in enumerate(zip(metrics_list, titles)):
    ax = axes[idx // 2, idx % 2]
    
    structured_vals = [r[metric] for r in results['structured']]
    uniform_vals = [r[metric] for r in results['random_uniform']]
    matched_vals = [r[metric] for r in results['random_matched']]
    
    positions = [1, 2, 3]
    bp = ax.boxplot([structured_vals, uniform_vals, matched_vals], 
                     positions=positions, widths=0.6,
                     patch_artist=True)
    ax.set_xticklabels(['Structured', 'Random\nUniform', 'Random\nMatched'])
    
    colors = ['green', 'red', 'orange']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    ax.set_ylabel(title)
    ax.set_title(f'{title}\n(lower = more compressible/structured)')
    ax.grid(True, alpha=0.3, axis='y')

# Summary panel
ax = axes[1, 1]
ax.axis('off')

shannon_s = np.mean([r['shannon_mean'] for r in results['structured']])
shannon_u = np.mean([r['shannon_mean'] for r in results['random_uniform']])
shannon_m = np.mean([r['shannon_mean'] for r in results['random_matched']])

block_s = np.mean([r['block_mean'] for r in results['structured']])
block_u = np.mean([r['block_mean'] for r in results['random_uniform']])
block_m = np.mean([r['block_mean'] for r in results['random_matched']])

lz_s = np.mean([r['lz'] for r in results['structured']])
lz_u = np.mean([r['lz'] for r in results['random_uniform']])
lz_m = np.mean([r['lz'] for r in results['random_matched']])

u_std_shannon = np.std([r['shannon_mean'] for r in results['random_uniform']])
m_std_shannon = np.std([r['shannon_mean'] for r in results['random_matched']])
effect_u_shannon = (shannon_s - shannon_u) / u_std_shannon if u_std_shannon > 0 else 0
effect_m_shannon = (shannon_s - shannon_m) / m_std_shannon if m_std_shannon > 0 else 0

u_std_block = np.std([r['block_mean'] for r in results['random_uniform']])
m_std_block = np.std([r['block_mean'] for r in results['random_matched']])
effect_u_block = (block_s - block_u) / u_std_block if u_std_block > 0 else 0
effect_m_block = (block_s - block_m) / m_std_block if m_std_block > 0 else 0

summary_text = f"""
EMP-138 DENSITY-MATCHING CONFOUND TEST
Conway's Game of Life (N={N}, T={T_steps})

Structured grid density: ρ={rho_structured:.3f}

EFFECT SIZES (Structured vs. Baseline):
  Shannon Entropy:
    vs. Uniform (ρ=0.5):   {effect_u_shannon:.2f}σ
    vs. Matched (ρ={rho_structured:.3f}): {effect_m_shannon:.2f}σ
    Confound: {abs(effect_u_shannon - effect_m_shannon):.2f}σ

  Block Entropy:
    vs. Uniform:   {effect_u_block:.2f}σ
    vs. Matched:   {effect_m_block:.2f}σ
    Confound: {abs(effect_u_block - effect_m_block):.2f}σ

VERDICT:
{'CONFOUND DETECTED' if abs(effect_u_shannon - effect_m_shannon) > 0.5 else 'NO MAJOR CONFOUND'}
Density matching {'SUBSTANTIALLY' if abs(effect_u_shannon - effect_m_shannon) > 1.0 else 'MODERATELY'} 
reduces apparent emergence signal.
"""

ax.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
        verticalalignment='center')

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/claude_emp138_density_verification.png', 
            dpi=150, bbox_inches='tight')
print()
print("Visualization saved: shared_agora/artifacts/claude_emp138_density_verification.png")

# Save results
with open('ca_density_results.json', 'w') as f:
    json.dump({
        'rho_structured': float(rho_structured),
        'shannon': {
            'structured': float(shannon_s),
            'uniform': float(shannon_u),
            'matched': float(shannon_m),
            'effect_uniform': float(effect_u_shannon),
            'effect_matched': float(effect_m_shannon)
        },
        'block': {
            'structured': float(block_s),
            'uniform': float(block_u),
            'matched': float(block_m),
            'effect_uniform': float(effect_u_block),
            'effect_matched': float(effect_m_block)
        },
        'lz': {
            'structured': float(lz_s),
            'uniform': float(lz_u),
            'matched': float(lz_m)
        }
    }, f, indent=2)

print("Results saved: ca_density_results.json")
