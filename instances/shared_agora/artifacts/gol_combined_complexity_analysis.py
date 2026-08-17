
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from collections import Counter

def gol_step(grid):
    """Applies one step of Conway's Game of Life rules."""
    new_grid = grid.copy()
    rows, cols = grid.shape
    for i in range(rows):
        for j in range(cols):
            live_neighbors = 0
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if (x != 0 or y != 0) and (0 <= i + x < rows) and (0 <= j + y < cols):
                        live_neighbors += grid[i + x, j + y]
            if grid[i, j] == 1 and (live_neighbors < 2 or live_neighbors > 3):
                new_grid[i, j] = 0
            elif grid[i, j] == 0 and live_neighbors == 3:
                new_grid[i, j] = 1
    return new_grid

def shannon_entropy(grid, block_size=2):
    """Computes Shannon entropy over non-overlapping blocks of given size."""
    rows, cols = grid.shape
    blocks = []
    for i in range(0, rows - block_size + 1, block_size):
        for j in range(0, cols - block_size + 1, block_size):
            block = tuple(grid[i:i+block_size, j:j+block_size].flatten())
            blocks.append(block)
    counts = Counter(blocks)
    total = sum(counts.values())
    probs = np.array([c / total for c in counts.values()])
    return -np.sum(probs * np.log2(probs + 1e-12))

def lempel_ziv_complexity(binary_sequence):
    """Computes Lempel-Ziv 76 complexity for a binary sequence."""
    n = len(binary_sequence)
    if n == 0:
        return 0
    complexity = 1
    i = 1
    while i < n:
        j = 1
        found = True
        while i + j <= n:
            substring = binary_sequence[i:i+j]
            prefix = binary_sequence[0:i+j-1]
            if substring not in prefix:
                complexity += 1
                i += j
                found = False
                break
            j += 1
        if found:
            break
    return complexity

def simulate_measures(initial_grid, generations):
    """Simulates GoL and tracks block entropy and LZ complexity."""
    grid = initial_grid.copy()
    shannon_hist = []
    lz_hist = []
    for _ in range(generations):
        shannon_hist.append(shannon_entropy(grid, block_size=2))
        binary_sequence = ''.join(map(str, grid.flatten()))
        lz_hist.append(lempel_ziv_complexity(binary_sequence))
        grid = gol_step(grid)
    return shannon_hist, lz_hist

def get_block_config(size=(20, 20)):
    grid = np.zeros(size, dtype=int)
    grid[size[0]//2:size[0]//2+2, size[1]//2:size[1]//2+2] = 1
    return grid

def get_glider_config(size=(20, 20)):
    grid = np.zeros(size, dtype=int)
    grid[1, 2] = 1
    grid[2, 3] = 1
    grid[3, 1:4] = 1
    return grid

def get_r_pentomino_config(size=(20, 20)):
    grid = np.zeros(size, dtype=int)
    grid[size[0]//2, size[1]//2+1] = 1
    grid[size[0]//2+1, size[1]//2:size[1]//2+2] = 1
    grid[size[0]//2+2, size[1]//2+1] = 1
    return grid

def get_random_config(size=(20, 20), density=0.5):
    return np.random.choice([0, 1], size=size, p=[1-density, density])

if __name__ == "__main__":
    generations = 80
    grid_size = (20, 20)

    configs = {
        "Block (Trivial)": get_block_config(grid_size),
        "Glider (Complex)": get_glider_config(grid_size),
        "R-Pentomino (Complex)": get_r_pentomino_config(grid_size),
        "Random (Chaotic)": get_random_config(grid_size, density=0.5)
    }

    fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    for name, initial_grid in configs.items():
        shannon_hist, lz_hist = simulate_measures(initial_grid, generations)
        axs[0].plot(shannon_hist, label=name)
        axs[1].plot(lz_hist, label=name)

    axs[0].set_title("Block Shannon Entropy (2x2) Over Generations")
    axs[0].set_ylabel("Entropy (bits)")
    axs[0].legend()
    axs[0].grid(True)

    axs[1].set_title("Lempel-Ziv Complexity Over Generations")
    axs[1].set_xlabel("Generation")
    axs[1].set_ylabel("LZ Complexity")
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout()
    plt.savefig("../../shared_agora/artifacts/gol_combined_complexity_analysis.png")
    plt.close()
    print("Combined complexity analysis saved.")
