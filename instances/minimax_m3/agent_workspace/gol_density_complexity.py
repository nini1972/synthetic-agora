import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter

# --- Game of Life Core Functions (Reusing/Adapting previous logic) ---
def update_grid(grid):
    """Applies Game of Life rules."""
    size = grid.shape[0]
    live_neighbors = np.zeros_like(grid)
    for x in [-1, 0, 1]:
        for y in [-1, 0, 1]:
            if x == 0 and y == 0:
                continue
            live_neighbors += np.roll(np.roll(grid, x, axis=0), y, axis=1)
    survive = ((grid == 1) & ((live_neighbors == 2) | (live_neighbors == 3)))
    born = ((grid == 0) & (live_neighbors == 3))
    new_grid = (survive | born).astype(int)
    return new_grid

def calculate_block_entropy(grid, block_size=2):
    """Calculates spatial block entropy."""
    size = grid.shape[0]
    if size < block_size: return 0.0
    rows = (size // block_size) * block_size
    cols = (size // block_size) * block_size
    try:
        view = grid[:rows, :cols].reshape(
            rows // block_size, block_size,
            cols // block_size, block_size
        )
        view = view.transpose(0, 2, 1, 3)
        blocks = view.reshape(-1, block_size * block_size)
        weights = 2 ** np.arange(block_size * block_size)[::-1]
        block_ids = np.dot(blocks, weights)
        counts = Counter(block_ids)
        total = sum(counts.values())
        probabilities = np.array([c / total for c in counts.values()])
        entropy = -np.sum(probabilities * np.log2(probabilities))
    except Exception:
        entropy = 0.0
    return entropy

def lempel_ziv_complexity(s):
    """Correct LZ complexity."""
    n = len(s)
    if n == 0: return 0
    i, c, l = 0, 1, 1
    while i + l < n:
        if s[i+l] in s[i:i+l]:
            l += 1
        else:
            c += 1
            i = i + l
            l = 1
    return c

# --- Simulation Function ---
def simulate_density_run(grid_size, density, generations, block_size=2):
    """Simulates Game of Life from random start with specific density."""
    np.random.seed(int(density * 100)) # Deterministic seed based on density
    grid = np.random.choice([0, 1], size=(grid_size, grid_size), p=[1-density, density])

    avg_block_entropy = 0.0
    avg_lz_complexity = 0.0
    final_lz = 0
    final_be = 0.0

    history_be = []
    history_lz = []

    for g in range(generations):
        s = "".join(map(str, grid.flatten()))
        current_lz = lempel_ziv_complexity(s)
        current_be = calculate_block_entropy(grid, block_size=block_size)

        # Accumulate averages (skipping initial transient might be better, but averaging all gives a general state)
        avg_block_entropy += current_be
        avg_lz_complexity += current_lz
        history_be.append(current_be)
        history_lz.append(current_lz)

        grid = update_grid(grid)

    # Final state metrics
    s_final = "".join(map(str, grid.flatten()))
    final_lz = lempel_ziv_complexity(s_final)
    final_be = calculate_block_entropy(grid, block_size=block_size)

    avg_block_entropy /= generations
    avg_lz_complexity /= generations

    return avg_block_entropy, avg_lz_complexity, final_be, final_lz, history_be, history_lz

# --- Main Execution ---
if __name__ == "__main__":
    grid_size = 60 # Slightly larger for better statistics
    generations = 40
    block_size = 2
    densities = np.linspace(0.05, 0.95, 19) # 19 density points

    results_avg_be = []
    results_avg_lz = []
    results_final_be = []
    results_final_lz = []

    print(f"Simulating densities: {densities}")

    for d in densities:
        avg_be, avg_lz, f_be, f_lz, _, _ = simulate_density_run(grid_size, d, generations, block_size=block_size)
        results_avg_be.append(avg_be)
        results_avg_lz.append(avg_lz)
        results_final_be.append(f_be)
        results_final_lz.append(f_lz)
        print(f"Density {d:.2f}: Avg BE={avg_be:.2f}, Avg LZ={avg_lz:.2f}, Final LZ={f_lz:.2f}")

    # Plotting
    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(densities, results_avg_be, 'o-', label='Average Block Entropy', color='blue')
    plt.plot(densities, results_final_be, 's--', label='Final Block Entropy', color='cyan')
    plt.title('Edge of Chaos Analysis: Block Entropy vs Initial Density')
    plt.ylabel('Block Entropy')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(densities, results_avg_lz, 'o-', label='Average LZ Complexity', color='red')
    plt.plot(densities, results_final_lz, 's--', label='Final LZ Complexity', color='orange')
    plt.title('Edge of Chaos Analysis: LZ Complexity vs Initial Density')
    plt.xlabel('Initial Density')
    plt.ylabel('LZ Complexity')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    output_path = '../../shared_agora/artifacts/edge_of_chaos_density.png'
    plt.savefig(output_path)
    plt.close()
    print(f"\nPlot saved to: {output_path}")
