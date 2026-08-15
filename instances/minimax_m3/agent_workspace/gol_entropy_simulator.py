
import numpy as np
import matplotlib
matplotlib.use('Agg') # Use the 'Agg' backend for non-interactive plotting
import matplotlib.pyplot as plt

def initialize_grid(size, pattern='random', density=0.5, custom_pattern=None):
    """Initializes a Game of Life grid."""
    if pattern == 'random':
        return np.random.choice([0, 1], size=(size, size), p=[1-density, density])
    elif pattern == 'glider':
        grid = np.zeros((size, size), dtype=int)
        # Glider pattern
        # . # .
        # . . #
        # # # #
        if size >= 5: # Ensure there's space for the glider
            grid[1, 2] = 1
            grid[2, 3] = 1
            grid[3, 1] = 1
            grid[3, 2] = 1
            grid[3, 3] = 1
        return grid
    elif pattern == 'block':
        grid = np.zeros((size, size), dtype=int)
        # 2x2 block (stable)
        # # #
        # # #
        if size >= 2:
            grid[1, 1] = 1
            grid[1, 2] = 1
            grid[2, 1] = 1
            grid[2, 2] = 1
        return grid
    elif pattern == 'oscillator': # Blinker
        grid = np.zeros((size, size), dtype=int)
        # . # .
        # . # .
        # . # .
        if size >= 3:
            grid[1, 2] = 1
            grid[2, 2] = 1
            grid[3, 2] = 1
        return grid
    elif pattern == 'custom' and custom_pattern is not None:
        grid = np.zeros((size, size), dtype=int)
        # Place custom pattern in the center
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

def update_grid(grid):
    """Applies Game of Life rules to update the grid."""
    new_grid = grid.copy()
    size = grid.shape[0]

    for i in range(size):
        for j in range(size):
            # Count live neighbors
            live_neighbors = 0
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if (x != 0 or y != 0): # Exclude the cell itself
                        neighbor_row = (i + x) % size # Toroidal wrapping
                        neighbor_col = (j + y) % size
                        live_neighbors += grid[neighbor_row, neighbor_col]

            # Apply Game of Life rules
            if grid[i, j] == 1: # Live cell
                if live_neighbors < 2 or live_neighbors > 3:
                    new_grid[i, j] = 0 # Dies
            else: # Dead cell
                if live_neighbors == 3:
                    new_grid[i, j] = 1 # Becomes live
    return new_grid

def calculate_shannon_entropy(grid):
    """
    Calculates the Shannon entropy of the grid based on the probability of live/dead cells.
    H = - sum(p_i * log2(p_i))
    """
    total_cells = grid.size
    live_cells = np.sum(grid)
    dead_cells = total_cells - live_cells

    p_live = live_cells / total_cells
    p_dead = dead_cells / total_cells

    entropy = 0.0
    if p_live > 0:
        entropy -= p_live * np.log2(p_live)
    if p_dead > 0:
        entropy -= p_dead * np.log2(p_dead)
    return entropy

def simulate_game_of_life(grid_size, pattern_type, generations, density=0.5, custom_pattern=None):
    """Simulates Game of Life and records entropy."""
    grid = initialize_grid(grid_size, pattern=pattern_type, density=density, custom_pattern=custom_pattern)
    entropy_history = []
    grid_history = [grid.copy()]

    for _ in range(generations):
        entropy_history.append(calculate_shannon_entropy(grid))
        grid = update_grid(grid)
        grid_history.append(grid.copy()) # Store grid for potential visualization

    entropy_history.append(calculate_shannon_entropy(grid)) # Entropy of final state
    return entropy_history, grid_history

# Example Usage and Plotting
if __name__ == "__main__":
    grid_size = 50
    generations = 100
    patterns_to_test = {
        "empty": initialize_grid(grid_size, pattern='empty'),
        "block": initialize_grid(grid_size, pattern='block'),
        "blinker": initialize_grid(grid_size, pattern='oscillator'),
        "glider": initialize_grid(grid_size, pattern='glider'),
        "random_sparse": initialize_grid(grid_size, pattern='random', density=0.2),
        "random_dense": initialize_grid(grid_size, pattern='random', density=0.7),
    }

    results = {}
    for name, initial_grid_pattern in patterns_to_test.items():
        # Using 'custom' pattern type to pass the pre-initialized grid
        entropy, _ = simulate_game_of_life(grid_size, pattern_type='custom', generations=generations, custom_pattern=initial_grid_pattern)
        results[name] = entropy
        print(f"Pattern: {name}, Avg Entropy: {np.mean(entropy):.4f}, Max Entropy: {np.max(entropy):.4f}")

    # Plotting the entropy history
    plt.figure(figsize=(12, 7))
    for name, entropy_data in results.items():
        plt.plot(entropy_data, label=f'{name} (Avg: {np.mean(entropy_data):.2f})')

    plt.title('Shannon Entropy over Generations for Different Game of Life Patterns')
    plt.xlabel('Generation')
    plt.ylabel('Shannon Entropy')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/entropy_gol_patterns.png')
    plt.close()

    # --- Refined approach for different types of patterns with clear definition ---
    print("\n--- Testing specific categories for the hypothesis ---")

    # Trivial: Empty (all zeros)
    empty_grid_entropy, _ = simulate_game_of_life(grid_size, pattern_type='empty', generations=generations)
    print(f"Empty Grid - Avg Entropy: {np.mean(empty_grid_entropy):.4f}, Max Entropy: {np.max(empty_grid_entropy):.4f}")

    # Trivial: Stable Block
    block_grid_entropy, _ = simulate_game_of_life(grid_size, pattern_type='block', generations=generations)
    print(f"Stable Block - Avg Entropy: {np.mean(block_grid_entropy):.4f}, Max Entropy: {np.max(block_grid_entropy):.4f}")

    # Chaotic: Random initial state (high density)
    random_chaotic_entropy, _ = simulate_game_of_life(grid_size, pattern_type='random', generations=generations, density=0.6)
    print(f"Chaotic Random - Avg Entropy: {np.mean(random_chaotic_entropy):.4f}, Max Entropy: {np.max(random_chaotic_entropy):.4f}")

    # Emergent Complex: Blinker
    blinker_entropy, _ = simulate_game_of_life(grid_size, pattern_type='oscillator', generations=generations)
    print(f"Blinker (Oscillator) - Avg Entropy: {np.mean(blinker_entropy):.4f}, Max Entropy: {np.max(blinker_entropy):.4f}")

    # Emergent Complex: Glider
    glider_entropy, _ = simulate_game_of_life(grid_size, pattern_type='glider', generations=generations)
    print(f"Glider - Avg Entropy: {np.mean(glider_entropy):.4f}, Max Entropy: {np.max(glider_entropy):.4f}")

    # Plotting for the hypothesis categories
    plt.figure(figsize=(12, 7))
    plt.plot(empty_grid_entropy, label=f'Empty Grid (Avg: {np.mean(empty_grid_entropy):.2f})', linestyle='--')
    plt.plot(block_grid_entropy, label=f'Stable Block (Avg: {np.mean(block_grid_entropy):.2f})', linestyle='--')
    plt.plot(random_chaotic_entropy, label=f'Chaotic Random (Avg: {np.mean(random_chaotic_entropy):.2f})')
    plt.plot(blinker_entropy, label=f'Blinker (Oscillator) (Avg: {np.mean(blinker_entropy):.2f})', linewidth=2)
    plt.plot(glider_entropy, label=f'Glider (Avg: {np.mean(glider_entropy):.2f})', linewidth=2)

    plt.title('Shannon Entropy over Generations for Hypothesis Categories in Game of Life')
    plt.xlabel('Generation')
    plt.ylabel('Shannon Entropy')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/entropy_gol_hypothesis_categories.png')
    plt.close()
