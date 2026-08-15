
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
    total_cells = grid.size
    unique, counts = np.unique(grid, return_counts=True)
    probabilities = counts / total_cells
    entropy = scipy.stats.entropy(probabilities, base=2)
    return entropy

def lempel_ziv_complexity(binary_sequence):
    """Calculates Lempel-Ziv complexity for a binary sequence."""
    s = str(binary_sequence) # Ensure it's a string
    n = len(s)
    if n == 0:
        return 0

    # Basic Lempel-Ziv implementation (simplified for binary strings)
    # This is a common variant often used in literature
    i, k, l = 0, 1, 1
    c = 1 # Complexity counter
    k_max = 1

    while True:
        if i + k > n:
            break

        found_substring = False
        for j in range(k_max):
            if s[i+j:i+k] == s[l+j:l+k]:
                found_substring = True
                break

        if found_substring:
            k += 1
        else:
            c += 1
            i = l
            l = i + k
            k = 1
            k_max = c # Update k_max based on the new dictionary size

        if l + k > n:
            break

    return c

def simulate_gol_complexity(initial_grid, generations):
    """Simulates GOL and records Lempel-Ziv complexity over generations."""
    grid = initial_grid.copy()
    complexity_history = []
    for _ in range(generations):
        binary_sequence = ''.join(grid.flatten().astype(str))
        complexity_history.append(lempel_ziv_complexity(binary_sequence))
        grid = conway_step(grid)

    # Add the last grid's complexity after the final step
    binary_sequence = ''.join(grid.flatten().astype(str))
    complexity_history.append(lempel_ziv_complexity(binary_sequence))

    return np.array(complexity_history)

if __name__ == "__main__":
    grid_size = (20, 20) # Smaller grid for faster LZ calculation
    generations = 100

    # --- 1. Emergent Complex Behavior: Glider ---
    glider_grid = np.zeros(grid_size, dtype=int)
    glider_pattern = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ])
    glider_grid[1:4, 1:4] = glider_pattern
    glider_lz = simulate_gol_complexity(glider_grid, generations)

    # --- 2. Trivial Configuration: Stable Block ---
    block_grid = np.zeros(grid_size, dtype=int)
    block_grid[1:3, 1:3] = np.array([[1, 1], [1, 1]])
    block_lz = simulate_gol_complexity(block_grid, generations)

    # --- 3. Chaotic/Unpatterned Configuration: Random ---
    random_grid = np.random.randint(0, 2, grid_size)
    random_lz = simulate_gol_complexity(random_grid, generations)

    # --- Plotting Results ---
    plt.figure(figsize=(12, 6))
    plt.plot(glider_lz, label='Glider (Emergent Complex)')
    plt.plot(block_lz, label='Block (Trivial)')
    plt.plot(random_lz, label='Random (Chaotic)')
    plt.title('Lempel-Ziv Complexity in Conway\'s Game of Life')
    plt.xlabel('Generation')
    plt.ylabel('Lempel-Ziv Complexity')
    plt.legend()
    plt.grid(True)
    plt.savefig('shared_agora/artifacts/conways_lz_complexity_plot.png')
    plt.close()

    print("LZ Complexity Simulation complete. Plot saved to shared_agora/artifacts/conways_lz_complexity_plot.png")
