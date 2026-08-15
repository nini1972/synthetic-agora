
import numpy as np
import matplotlib.pyplot as plt
import math

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

def calculate_shannon_entropy(grid):
    """Calculates the Shannon entropy for a given Game of Life grid."""
    total_cells = grid.size
    live_cells = np.sum(grid)
    
    if total_cells == 0:
        return 0.0

    p_live = live_cells / total_cells

    if p_live == 0 or p_live == 1:
        return 0.0  # Entropy is 0 if all cells are the same state

    # Shannon entropy for a binary system
    entropy = - (p_live * math.log2(p_live) + (1 - p_live) * math.log2(1 - p_live))
    return entropy

def update_grid(grid):
    """Applies Conway's Game of Life rules to update the grid."""
    new_grid = grid.copy()
    rows, cols = grid.shape

    for r in range(rows):
        for c in range(cols):
            # Count live neighbors
            live_neighbors = 0
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (i != 0 or j != 0) and \
                       (0 <= r + i < rows) and \
                       (0 <= c + j < cols):
                        live_neighbors += grid[r + i, c + j]

            # Apply Game of Life rules
            if grid[r, c] == 1:  # Live cell
                if live_neighbors < 2 or live_neighbors > 3:
                    new_grid[r, c] = 0  # Dies
            else:  # Dead cell
                if live_neighbors == 3:
                    new_grid[r, c] = 1  # Becomes alive
    return new_grid

def simulate_gol(initial_grid, generations):
    """Simulates Conway's Game of Life and collects entropy over time."""
    grid = initial_grid.copy()
    entropy_values = []
    
    for _ in range(generations):
        entropy_values.append(calculate_shannon_entropy(grid))
        grid = update_grid(grid)
    entropy_values.append(calculate_shannon_entropy(grid)) # Add entropy for final state
    return entropy_values

def create_glider(rows, cols, r_start, c_start):
    """Creates a glider pattern."""
    grid = np.zeros((rows, cols), dtype=int)
    glider = np.array([[0, 1, 0],
                       [0, 0, 1],
                       [1, 1, 1]])
    grid[r_start:r_start+3, c_start:c_start+3] = glider
    return grid

def create_block(rows, cols, r_start, c_start):
    """Creates a stable 2x2 block pattern."""
    grid = np.zeros((rows, cols), dtype=int)
    block = np.array([[1, 1],
                      [1, 1]])
    grid[r_start:r_start+2, c_start:c_start+2] = block
    return grid

def create_oscillator_blinker(rows, cols, r_start, c_start):
    """Creates a blinker oscillator pattern."""
    grid = np.zeros((rows, cols), dtype=int)
    blinker = np.array([[1, 1, 1]])
    grid[r_start:r_start+1, c_start:c_start+3] = blinker
    return grid

def create_random_grid(rows, cols, density=0.5):
    """Creates a random grid."""
    return np.random.choice([0, 1], size=(rows, cols), p=[1-density, density])

if __name__ == "__main__":
    GRID_SIZE = 50
    GENERATIONS = 100

    # --- Test Cases ---
    
    # 1. Glider (Emergent Complexity)
    glider_grid = create_glider(GRID_SIZE, GRID_SIZE, 1, 1)
    glider_entropy = simulate_gol(glider_grid, GENERATIONS)

    # 2. Block (Trivial/Stable)
    block_grid = create_block(GRID_SIZE, GRID_SIZE, 1, 1)
    block_entropy = simulate_gol(block_grid, GENERATIONS)

    # 3. Blinker (Emergent Complexity/Oscillator)
    blinker_grid = create_oscillator_blinker(GRID_SIZE, GRID_SIZE, 1, 1)
    blinker_entropy = simulate_gol(blinker_grid, GENERATIONS)

    # 4. Random (Chaotic/Unpatterned)
    random_grid = create_random_grid(GRID_SIZE, GRID_SIZE, density=0.3)
    random_entropy = simulate_gol(random_grid, GENERATIONS)

    # 5. Empty Grid (Trivial)
    empty_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
    empty_entropy = simulate_gol(empty_grid, GENERATIONS)

    # 6. Full Grid (Trivial - if it stays full, otherwise might be complex)
    full_grid = np.ones((GRID_SIZE, GRID_SIZE), dtype=int)
    full_entropy = simulate_gol(full_grid, GENERATIONS) # This will quickly die off to empty

    # --- Plotting ---
    plt.figure(figsize=(12, 8))
    plt.plot(glider_entropy, label='Glider (Complex)')
    plt.plot(block_entropy, label='Block (Stable)')
    plt.plot(blinker_entropy, label='Blinker (Oscillator)')
    plt.plot(random_entropy, label='Random (Chaotic)')
    plt.plot(empty_entropy, label='Empty (Trivial)')
    plt.plot(full_entropy, label='Full (Trivial)')

    plt.title('Information Entropy Over Time in Conway\'s Game of Life')
    plt.xlabel('Generation')
    plt.ylabel('Shannon Entropy')
    plt.legend()
    plt.grid(True)
    plt.ylim(0, 1) # Entropy is between 0 and 1 for binary systems
    plt.savefig('../../shared_agora/artifacts/gol_entropy_plot.png')
    plt.close()

    print("Simulation complete. Plot saved to shared_agora/artifacts/gol_entropy_plot.png")
