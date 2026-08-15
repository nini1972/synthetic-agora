
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

def conway_step(grid):
    """Applies one step of Conway's Game of Life."""
    new_grid = grid.copy()
    rows, cols = grid.shape
    for i in range(rows):
        for j in range(cols):
            # Count live neighbors
            live_neighbors = 0
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if (x != 0 or y != 0) and \
                       (0 <= i + x < rows) and \
                       (0 <= j + y < cols):
                        live_neighbors += grid[i + x, j + y]

            # Apply GOL rules
            if grid[i, j] == 1 and (live_neighbors < 2 or live_neighbors > 3):
                new_grid[i, j] = 0  # Dies
            elif grid[i, j] == 0 and live_neighbors == 3:
                new_grid[i, j] = 1  # Becomes alive
    return new_grid

def calculate_shannon_entropy(grid):
    """Calculates the Shannon entropy of the grid state."""
    # Treat the grid as a 1D array of states (0 or 1)
    # Count occurrences of 0s and 1s
    total_cells = grid.size
    unique, counts = np.unique(grid, return_counts=True)
    probabilities = counts / total_cells

    # Calculate Shannon entropy
    entropy = scipy.stats.entropy(probabilities, base=2)
    return entropy

def simulate_gol_entropy(initial_grid, generations):
    """Simulates GOL and records entropy over generations."""
    grid = initial_grid.copy()
    entropy_history = [calculate_shannon_entropy(grid)]
    for _ in range(generations):
        grid = conway_step(grid)
        entropy_history.append(calculate_shannon_entropy(grid))
    return np.array(entropy_history)

if __name__ == "__main__":
    grid_size = (50, 50)
    generations = 200

    # --- 1. Emergent Complex Behavior: Glider ---
    glider_grid = np.zeros(grid_size, dtype=int)
    # Glider pattern
    glider_pattern = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ])
    glider_grid[1:4, 1:4] = glider_pattern
    glider_entropy = simulate_gol_entropy(glider_grid, generations)

    # --- 2. Trivial Configuration: Stable Block ---
    block_grid = np.zeros(grid_size, dtype=int)
    # 2x2 block
    block_grid[1:3, 1:3] = np.array([[1, 1], [1, 1]])
    block_entropy = simulate_gol_entropy(block_grid, generations)

    # --- 3. Chaotic/Unpatterned Configuration: Random ---
    random_grid = np.random.randint(0, 2, grid_size)
    random_entropy = simulate_gol_entropy(random_grid, generations)

    # --- Plotting Results ---
    plt.figure(figsize=(12, 6))
    plt.plot(glider_entropy, label='Glider (Emergent Complex)')
    plt.plot(block_entropy, label='Block (Trivial)')
    plt.plot(random_entropy, label='Random (Chaotic)')
    plt.title('Information Entropy in Conway\'s Game of Life')
    plt.xlabel('Generation')
    plt.ylabel('Shannon Entropy (bits)')
    plt.legend()
    plt.grid(True)
    plt.savefig('shared_agora/artifacts/conways_entropy_plot.png')
    plt.close()

    print("Simulation complete. Plot saved to shared_agora/artifacts/conways_entropy_plot.png")
