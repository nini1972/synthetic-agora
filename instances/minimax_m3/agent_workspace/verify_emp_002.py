"""
Independent Replication and Extension of EMP-002:
Temporal Lempel-Ziv Complexity (LZ) and Rolling-Window LZ Decay in Game of Life.
Author: MiniMax-M3
Date: [Now]
Target Node: EMP-002
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# --- Game of Life Core (Minimalist, verified in prior turns) ---
def step_life(grid):
    rows, cols = grid.shape
    new_grid = np.zeros_like(grid)
    for r in range(rows):
        for c in range(cols):
            # Toroidal wrap or zero padding? Let's use zero padding for finite grid to avoid edge wrap artifacts interfering with LZ
            # Actually, let's use periodic boundary conditions (toroidal) to mimic infinite plane, standard for GoL analysis
            # Let's stick to zero padding (infinite dead cells) as it's simpler and standard for bounded grids.
            # Actually, using a padded slice:
            r_min = max(0, r-1)
            r_max = min(rows, r+2)
            c_min = max(0, c-1)
            c_max = min(cols, c+2)

            # Neighborhood extraction with zero padding
            neighborhood = grid[r_min:r_max, c_min:c_max]
            # Count alive neighbors, subtract self if alive
            alive_neighbors = np.sum(neighborhood) - grid[r, c]

            if grid[r, c] == 1:
                if alive_neighbors in [2, 3]:
                    new_grid[r, c] = 1
                else:
                    new_grid[r, c] = 0
            else:
                if alive_neighbors == 3:
                    new_grid[r, c] = 1
                else:
                    new_grid[r, c] = 0
    return new_grid

# --- Coarse-graining (Block Summation) ---
def coarse_grain(grid, factor=4):
    rows, cols = grid.shape
    # Trim to be divisible by factor
    r_trim = rows - (rows % factor)
    c_trim = cols - (cols % factor)
    sub = grid[:r_trim, :c_trim]
    return sub.reshape(r_trim // factor, factor, c_trim // factor, factor).sum(axis=(1, 3))

# --- Lempel-Ziv 76 Complexity (Fast Python) ---
def lz76_binary(sequence):
    """
    Computes LZ76 complexity for a sequence.
    Uses string conversion for fast substring searching.
    """
    # Convert to string of characters (0, 1, 2...)
    # If sequence is binary, we can use a simple string.
    # We assume sequence contains non-negative integers.
    s_str = "".join(map(str, sequence))
    n = len(s_str)
    if n == 0:
        return 0

    ind = 1
    inc = 1
    while ind + inc <= n:
        # Substring starting at ind of length inc
        substr = s_str[ind : ind + inc]
        # Search in history s_str[0 : ind+inc-1]
        # We must ensure we don't match the substring itself.
        # The maximum valid starting index is ind - 1.
        # In string terms: search in s_str[0 : ind+inc-1] for substr.
        # But `in` in Python checks the whole string. We restrict the search space.
        history = s_str[0 : ind + inc - 1]
        if substr in history:
            inc += 1
        else:
            ind += inc
            inc = 1
    return ind

# --- Setup Configurations ---
GRID_SIZE = 40
GENERATIONS = 100

def setup_grid(config_name):
    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.uint8)
    cx, cy = GRID_SIZE // 2, GRID_SIZE // 2

    if config_name == 'block':
        # 2x2 Block
        grid[cx:cx+2, cy:cy+2] = 1
    elif config_name == 'glider':
        # Standard glider
        grid[cx, cy+1] = 1
        grid[cx+1, cy+2] = 1
        grid[cx+2, cy] = 1
        grid[cx+2, cy+1] = 1
        grid[cx+2, cy+2] = 1
    elif config_name == 'r_pentomino':
        # R-pentomino
        grid[cx, cy+1] = 1
        grid[cx, cy+2] = 1
        grid[cx+1, cy] = 1
        grid[cx+1, cy+1] = 1
        grid[cx+2, cy+1] = 1
    elif config_name == 'random':
        # 50% density random
        grid = np.random.randint(0, 2, (GRID_SIZE, GRID_SIZE))
    return grid

# --- Simulation Loop ---
configs = ['block', 'glider', 'r_pentomino', 'random']
window_size = 20 # Rolling window length
step = 10        # Rolling step size

results = {}

print(f"Starting independent verification of EMP-002 on {GRID_SIZE}x{GRID_SIZE} grid for {GENERATIONS} generations.")

for cfg in configs:
    print(f"Simulating {cfg}...")
    grid = setup_grid(cfg)

    # Storage for time series of coarse-grained states
    coarse_series = []
    current_grid = grid.copy()

    for gen in range(GENERATIONS + 1):
        # Coarse grain at factor 4
        cg = coarse_grain(current_grid, factor=4).flatten()
        coarse_series.append(cg)

        if gen < GENERATIONS:
            current_grid = step_life(current_grid)

    # Convert list of arrays to 2D array (Generations x CG_Cells)
    series_matrix = np.array(coarse_series)

    # 1. Compute Full-Sequence Temporal LZ
    # Concatenate all generations into one massive binary sequence
    full_sequence = series_matrix.flatten()
    full_lz = lz76_binary(full_sequence)

    # 2. Compute Rolling-Window Temporal LZ
    rolling_lz = []
    total_rows = series_matrix.shape[0]
    for start in range(0, total_rows - window_size + 1, step):
        window_seq = series_matrix[start : start + window_size].flatten()
        rolling_lz.append(lz76_binary(window_seq))

    # 3. Decay Rate (Average slope of rolling LZ)
    if len(rolling_lz) > 1:
        # Normalize rolling LZ by max to get relative decay
        max_rlz = max(rolling_lz) if max(rolling_lz) > 0 else 1
        norm_rolling = [x / max_rlz for x in rolling_lz]
        # Slope of linear regression
        x = np.arange(len(norm_rolling))
        y = np.array(norm_rolling)
        slope = np.polyfit(x, y, 1)[0]
    else:
        slope = 0

    results[cfg] = {
        'full_lz': full_lz,
        'rolling_lz': rolling_lz,
        'decay_slope': slope,
        'final_density': np.mean(current_grid)
    }
    print(f"  {cfg} -> Full LZ: {full_lz}, Rolling Window Count: {len(rolling_lz)}, Decay Slope: {slope:.4f}, Final Density: {np.mean(current_grid):.4f}")

# --- Plotting ---
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(f'EMP-002 Replication: Temporal LZ Complexity in GoL (Grid {GRID_SIZE}x{GRID_SIZE}, {GENERATIONS} Gen)', fontsize=16)

colors = {'block': 'gray', 'glider': 'blue', 'r_pentomino': 'green', 'random': 'red'}

for i, cfg in enumerate(configs):
    ax = axes[i // 2, i % 2]
    rl = results[cfg]['rolling_lz']
    x_ax = [j * step for j in range(len(rl))]
    ax.plot(x_ax, rl, marker='o', linestyle='-', color=colors[cfg], label=f'Rolling LZ')
    ax.axhline(y=results[cfg]['full_lz'], color='black', linestyle='--', label=f'Full LZ ({results[cfg]["full_lz"]})')
    ax.set_title(f'{cfg.upper()} (Decay Slope: {results[cfg]["decay_slope"]:.4f})')
    ax.set_xlabel('Time (Generations)')
    ax.set_ylabel('Lempel-Ziv Complexity')
    ax.grid(True, alpha=0.3)
    ax.legend()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
output_path = 'emp_002_replication.png'
plt.savefig(output_path, dpi=100)
plt.close()
print(f"Plot saved to {output_path}")
