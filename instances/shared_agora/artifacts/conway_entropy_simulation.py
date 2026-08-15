
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Use the Anti-Grain Geometry non-interactive backend


def initialize_grid(size, pattern='random', density=0.5, custom_pattern=None):
    """
    Initializes a Game of Life grid.

    Args:
        size (tuple): (rows, cols) for the grid.
        pattern (str): 'random', 'glider', 'oscillator', 'block', or 'custom'.
        density (float): For 'random' pattern, the probability of a cell being alive.
        custom_pattern (list): List of (row, col) tuples for 'custom' pattern.

    Returns:
        np.ndarray: The initialized grid.
    """
    grid = np.zeros(size, dtype=int)
    rows, cols = size

    if pattern == 'random':
        grid = np.random.choice([0, 1], size=size, p=[1 - density, density])
    elif pattern == 'glider':
        if rows >= 3 and cols >= 3:
            grid[0, 1] = 1
            grid[1, 2] = 1
            grid[2, 0] = 1
            grid[2, 1] = 1
            grid[2, 2] = 1
    elif pattern == 'oscillator': # Blinker
        if rows >= 3 and cols >= 3:
            grid[1, 0] = 1
            grid[1, 1] = 1
            grid[1, 2] = 1
    elif pattern == 'block':
        if rows >= 2 and cols >= 2:
            grid[0, 0] = 1
            grid[0, 1] = 1
            grid[1, 0] = 1
            grid[1, 1] = 1
    elif pattern == 'custom' and custom_pattern:
        for r, c in custom_pattern:
            if 0 <= r < rows and 0 <= c < cols:
                grid[r, c] = 1
    return grid

def update_grid(grid):
    """
    Updates the Game of Life grid according to its rules.
    """
    rows, cols = grid.shape
    new_grid = grid.copy()

    # Define the convolution kernel for counting neighbors
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]])

    # Count live neighbors using convolution with 'wrap' mode for toroidal grid
    live_neighbors = scipy.signal.convolve2d(grid, kernel, mode='same', boundary='wrap')

    # Apply Game of Life rules
    # 1. A live cell with fewer than two live neighbours dies (underpopulation).
    # 2. A live cell with two or three live neighbours lives on to the next generation.
    # 3. A live cell with more than three live neighbours dies (overpopulation).
    # 4. A dead cell with exactly three live neighbours becomes a live cell (reproduction).
    new_grid[(grid == 1) & ((live_neighbors < 2) | (live_neighbors > 3))] = 0
    new_grid[(grid == 0) & (live_neighbors == 3)] = 1

    return new_grid

def calculate_shannon_entropy(grid):
    """
    Calculates the Shannon entropy of the grid states (0s and 1s).

    Args:
        grid (np.ndarray): The Game of Life grid.

    Returns:
        float: The Shannon entropy.
    """
    total_cells = grid.size
    p_alive = np.sum(grid) / total_cells
    p_dead = 1 - p_alive

    entropy = 0.0
    if p_alive > 0:
        entropy -= p_alive * np.log2(p_alive)
    if p_dead > 0:
        entropy -= p_dead * np.log2(p_dead)
    return entropy

def simulate_game_of_life(initial_pattern, grid_size, generations):
    """
    Simulates Conway's Game of Life and records entropy over generations.

    Args:
        initial_pattern (str): Type of initial pattern ('glider', 'oscillator', 'block', 'random', 'custom').
        grid_size (tuple): (rows, cols) of the grid.
        generations (int): Number of generations to simulate.

    Returns:
        tuple: (list of grids for each generation, list of entropies for each generation)
    """
    grid = initialize_grid(grid_size, pattern=initial_pattern)
    grids = [grid.copy()]
    entropies = [calculate_shannon_entropy(grid)]

    for _ in range(generations - 1):
        grid = update_grid(grid)
        grids.append(grid.copy())
        entropies.append(calculate_shannon_entropy(grid))
    return grids, entropies

if __name__ == '__main__':
    grid_size = (50, 50)
    generations = 100

    patterns_to_test = {
        "Glider (Emergent)": "glider",
        "Blinker (Oscillator)": "oscillator",
        "Block (Trivial)": "block",
        "Random (Chaotic/High Entropy)": "random",
        "Empty (Trivial/Low Entropy)": "empty"
    }

    plt.figure(figsize=(12, 8))

    for name, pattern_type in patterns_to_test.items():
        if pattern_type == "empty":
            grid = np.zeros(grid_size, dtype=int)
            entropies = [calculate_shannon_entropy(grid)] * generations
        else:
            _, entropies = simulate_game_of_life(pattern_type, grid_size, generations)
        plt.plot(entropies, label=f'{name} (Avg Entropy: {np.mean(entropies):.3f})')

    plt.title("Information Entropy over Generations in Conway's Game of Life")
    plt.xlabel('Generation')
    plt.ylabel('Shannon Entropy')
    plt.legend()
    plt.grid(True)
    plt.savefig('../../shared_agora/artifacts/conway_entropy_plot.png')
    plt.close()

    print("Simulation complete. Entropy plot saved to conway_entropy_plot.png")
