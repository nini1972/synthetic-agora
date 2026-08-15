
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
                new_grid[i, j] = 0  # Underpopulation or Overpopulation
            elif grid[i, j] == 0 and live_neighbors == 3:
                new_grid[i, j] = 1  # Reproduction
    return new_grid

def calculate_information_entropy(grid):
    """Calculates the information entropy of the GoL grid."""
    # Treat the grid as a flattened array of states (0 or 1)
    # Count occurrences of 0s and 1s
    total_cells = grid.size
    if total_cells == 0:
        return 0.0

    counts = np.bincount(grid.flatten(), minlength=2)
    p0 = counts[0] / total_cells
    p1 = counts[1] / total_cells

    entropy = 0.0
    if p0 > 0:
        entropy -= p0 * np.log2(p0)
    if p1 > 0:
        entropy -= p1 * np.log2(p1)
    return entropy

def simulate_gol_and_entropy(initial_grid, generations):
    """Simulates GoL and tracks entropy over generations."""
    grid = initial_grid.copy()
    entropy_history = []
    for _ in range(generations):
        entropy_history.append(calculate_information_entropy(grid))
        grid = gol_step(grid)
    return entropy_history, grid

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

def get_random_config(size=(20, 20), density=0.3):
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
        entropy_hist, _ = simulate_gol_and_entropy(initial_grid, generations)
        plt.plot(entropy_hist, label=name)

    plt.title("Information Entropy Over Generations in Conway's Game of Life")
    plt.xlabel("Generation")
    plt.ylabel("Information Entropy (bits)")
    plt.legend()
    plt.grid(True)
    plt.savefig("../../shared_agora/artifacts/gol_entropy_comparison.png")
    plt.close()

    print("Simulation complete. Plot saved to shared_agora/artifacts/gol_entropy_comparison.png")
