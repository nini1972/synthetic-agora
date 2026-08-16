
import numpy as np
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
from collections import Counter

# --- Game of Life Core Functions (Optimized with numpy for speed) ---
def update_grid(grid):
    """Applies Game of Life rules using numpy convolution."""
    size = grid.shape[0]
    # Count neighbors using toroidal wrapping
    live_neighbors = np.zeros_like(grid)
    for x in [-1, 0, 1]:
        for y in [-1, 0, 1]:
            if x == 0 and y == 0:
                continue
            # Roll the grid and add to live_neighbors
            live_neighbors += np.roll(np.roll(grid, x, axis=0), y, axis=1)

    # Apply rules
    # 1. Live cell with 2 or 3 neighbors survives
    survive = ((grid == 1) & ((live_neighbors == 2) | (live_neighbors == 3)))
    # 2. Dead cell with exactly 3 neighbors becomes live
    born = ((grid == 0) & (live_neighbors == 3))

    new_grid = (survive | born).astype(int)
    return new_grid

def initialize_grid(size, pattern='random', density=0.5, custom_pattern=None):
    """Initializes a Game of Life grid."""
    if pattern == 'random':
        return np.random.choice([0, 1], size=(size, size), p=[1-density, density])
    elif pattern == 'glider':
        grid = np.zeros((size, size), dtype=int)
        if size >= 5:
            grid[1, 2] = 1
            grid[2, 3] = 1
            grid[3, 1] = 1
            grid[3, 2] = 1
            grid[3, 3] = 1
        return grid
    elif pattern == 'block':
        grid = np.zeros((size, size), dtype=int)
        if size >= 2:
            grid[1, 1] = 1
            grid[1, 2] = 1
            grid[2, 1] = 1
            grid[2, 2] = 1
        return grid
    elif pattern == 'oscillator': # Blinker
        grid = np.zeros((size, size), dtype=int)
        if size >= 3:
            grid[1, 2] = 1
            grid[2, 2] = 1
            grid[3, 2] = 1
        return grid
    elif pattern == 'custom' and custom_pattern is not None:
        grid = np.zeros((size, size), dtype=int)
        start_row = (size - custom_pattern.shape[0]) // 2
        start_col = (size - custom_pattern.shape[1]) // 2
        if start_row >= 0 and start_col >= 0 and \
           start_row + custom_pattern.shape[0] <= size and \
           start_col + custom_pattern.shape[1] <= size:
            grid[start_row : start_row + custom_pattern.shape[0],
                 start_col : start_col + custom_pattern.shape[1]] = custom_pattern
        return grid
    else:
        return np.zeros((size, size), dtype=int)

# --- Advanced Entropy Measures ---

def calculate_spatial_block_entropy(grid, block_size=2):
    """
    Calculates Shannon entropy based on frequency of non-overlapping k x k blocks.
    """
    size = grid.shape[0]
    if size < block_size:
        return 0.0

    # Truncate to a multiple of block_size
    rows = (size // block_size) * block_size
    cols = (size // block_size) * block_size

    # Extract blocks: Reshape grid to (rows/block_size, block_size, cols/block_size, block_size)
    # Then transpose to get blocks clearly.
    try:
        view = grid[:rows, :cols].reshape(
            rows // block_size, block_size,
            cols // block_size, block_size
        )
        # Move axes to group by block: (n_blocks_rows, n_blocks_cols, block_size, block_size)
        view = view.transpose(0, 2, 1, 3)
        # Flatten each block
        blocks = view.reshape(-1, block_size * block_size)
    except ValueError:
        # Fallback if reshape fails (e.g., size not divisible)
        return 0.0

    if blocks.shape[0] == 0:
        return 0.0

    # Convert each block to a unique integer representation
    # Treat blocks as binary vectors
    weights = 2 ** np.arange(block_size * block_size)[::-1]
    block_ids = np.dot(blocks, weights)

    # Calculate Shannon entropy of these block IDs
    counts = Counter(block_ids)
    total = sum(counts.values())
    probabilities = np.array([c / total for c in counts.values()])
    entropy = -np.sum(probabilities * np.log2(probabilities))
    return entropy

def lempel_ziv_complexity(s):
    """
    Calculates Lempel-Ziv complexity (LZ76) for a string.
    Counts the number of distinct phrases in the factorization.
    Logic: Is the next symbol part of any already established phrase in the current prefix?
    """
    n = len(s)
    if n == 0:
        return 0
    i = 0
    c = 1
    l = 1
    while i + l < n:
        # Check if s[i+l] is found in the substring s[i:i+l]
        # If yes, extend the current phrase length l.
        # If no, a new phrase begins.
        if s[i+l] in s[i:i+l]:
            l += 1
        else:
            c += 1
            i = i + l
            l = 1
    return c

# --- Simulation and Plotting ---
def simulate_and_measure(grid_size, pattern_type, generations, density=0.5, custom_pattern=None, block_size=2):
    grid = initialize_grid(grid_size, pattern=pattern_type, density=density, custom_pattern=custom_pattern)
    block_entropy_hist = []
    lz_hist = []

    for _ in range(generations):
        block_entropy_hist.append(calculate_spatial_block_entropy(grid, block_size=block_size))
        s = "".join(map(str, grid.flatten()))
        lz_hist.append(lempel_ziv_complexity(s))
        grid = update_grid(grid)

    # Final state
    block_entropy_hist.append(calculate_spatial_block_entropy(grid, block_size=block_size))
    s = "".join(map(str, grid.flatten()))
    lz_hist.append(lempel_ziv_complexity(s))

    return block_entropy_hist, lz_hist

if __name__ == "__main__":
    grid_size = 50
    generations = 50
    block_size = 2

    # Define test cases
    test_cases = {
        "Empty (Trivial)": ('empty', None),
        "Block (Trivial)": ('block', None),
        "Chaotic Random": ('random', 0.5),
        "Blinker (Complex)": ('oscillator', None),
        "Glider (Complex)": ('glider', None)
    }

    results = {}

    for name, (p_type, density) in test_cases.items():
        be_hist, lz_hist = simulate_and_measure(grid_size, p_type, generations, density=density, block_size=block_size)
        results[name] = (be_hist, lz_hist)
        avg_be = np.mean(be_hist)
        avg_lz = np.mean(lz_hist)
        print(f"{name}: Avg Block Entropy = {avg_be:.4f}, Avg LZ Complexity = {avg_lz:.4f}")

    # Plotting
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # Block Entropy Plot
    for name, (be_hist, _) in results.items():
        linewidth = 2 if "Complex" in name else 1
        linestyle = '--' if "Trivial" in name else '-'
        axes[0].plot(be_hist, label=f"{name} (Avg: {np.mean(be_hist):.2f})", linewidth=linewidth, linestyle=linestyle)
    axes[0].set_ylabel(f'Spatial Block Entropy ({block_size}x{block_size})')
    axes[0].set_title('Advanced Entropy Measures in Game of Life')
    axes[0].legend()
    axes[0].grid(True)

    # LZ Complexity Plot
    for name, (_, lz_hist) in results.items():
        linewidth = 2 if "Complex" in name else 1
        linestyle = '--' if "Trivial" in name else '-'
        axes[1].plot(lz_hist, label=f"{name} (Avg: {np.mean(lz_hist):.2f})", linewidth=linewidth, linestyle=linestyle)
    axes[1].set_xlabel('Generation')
    axes[1].set_ylabel('Lempel-Ziv Complexity')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    save_path = '../../shared_agora/artifacts/advanced_entropy_gol.png'
    plt.savefig(save_path)
    plt.close()
    print(f"\nPlot saved to: {save_path}")
