
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Use the 'Agg' backend for non-interactive plotting

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

def lempel_ziv_complexity(binary_sequence):
    """
    Computes the Lempel-Ziv complexity of a binary sequence.
    Based on the Lempel-Ziv 76 parsing: count the number of distinct substrings
    that need to be added to a vocabulary to reconstruct the sequence.
    """
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
            # Check if the substring exists in the prefix binary_sequence[0:i+j-1]
            prefix = binary_sequence[0:i+j-1]
            if substring not in prefix:
                complexity += 1
                i += j
                found = False
                break
            j += 1
        if found: # Reached end of string with all substrings found in prefix
            break
    return complexity

def simulate_gol_lz(initial_grid, generations):
    """Simulates GoL and tracks Lempel-Ziv complexity per generation."""
    grid = initial_grid.copy()
    lz_history = []
    for _ in range(generations):
        binary_sequence = ''.join(map(str, grid.flatten()))
        lz_history.append(lempel_ziv_complexity(binary_sequence))
        grid = gol_step(grid)
    return lz_history, grid

# --- Configuration Definitions ---
def get_block_config(size=(10, 10)):
    grid = np.zeros(size, dtype=int)
    grid[4:6, 4:6] = 1
    return grid

def get_glider_config(size=(10, 10)):
    grid = np.zeros(size, dtype=int)
    grid[1, 2] = 1
    grid[2, 3] = 1
    grid[3, 1:4] = 1
    return grid

def get_r_pentomino_config(size=(20, 20)):
    grid = np.zeros(size, dtype=int)
    grid[10, 11] = 1
    grid[11, 10:12] = 1
    grid[12, 11] = 1
    return grid

def get_random_config(size=(20, 20), density=0.5):
    return np.random.choice([0, 1], size=size, p=[1-density, density])

# --- Main Simulation and Plotting ---
if __name__ == "__main__":
    generations = 100
    grid_size = (20, 20)

    configs = {
        "Block (Trivial)": get_block_config(grid_size),
        "Glider (Complex)": get_glider_config(grid_size),
        "R-Pentomino (Complex)": get_r_pentomino_config(grid_size),
        "Random (Chaotic)": get_random_config(grid_size, density=0.5)
    }

    plt.figure(figsize=(12, 8))
    for name, initial_grid in configs.items():
        lz_hist, _ = simulate_gol_lz(initial_grid, generations)
        plt.plot(lz_hist, label=name)

    plt.title("Lempel-Ziv Complexity Over Generations in Conway's Game of Life")
    plt.xlabel("Generation")
    plt.ylabel("Lempel-Ziv Complexity")
    plt.legend()
    plt.grid(True)
    plt.savefig("../../shared_agora/artifacts/gol_lz_complexity_comparison.png")
    plt.close()

    print("Simulation complete. Plot saved to shared_agora/artifacts/gol_lz_complexity_comparison.png")
