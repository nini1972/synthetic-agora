
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from collections import Counter

def gol_step(grid):
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

def spatial_lz(grid):
    binary_sequence = ''.join(map(str, grid.flatten()))
    return lempel_ziv_complexity(binary_sequence)

def coarse_state(grid, block_size=4):
    """Coarse-grain grid into block densities, then hash the pattern."""
    rows, cols = grid.shape
    state = []
    for i in range(0, rows, block_size):
        for j in range(0, cols, block_size):
            block = grid[i:i+block_size, j:j+block_size]
            density = block.sum() / block.size
            # Quantize to 4 levels
            level = int(min(3, np.floor(density * 4)))
            state.append(str(level))
    return ''.join(state)

def temporal_lz(state_sequence):
    """LZ complexity of the sequence of coarse-grained states over time."""
    return lempel_ziv_complexity(''.join(state_sequence))

def rolling_temporal_lz(state_sequence, window=20):
    """Computes temporal LZ in a sliding window over the state sequence."""
    roll = []
    for i in range(len(state_sequence)):
        start = max(0, i - window + 1)
        roll.append(temporal_lz(state_sequence[start:i+1]))
    return roll

def simulate(initial_grid, generations, block_size=4):
    grid = initial_grid.copy()
    spatial_lz_hist = []
    state_sequence = []
    for _ in range(generations):
        spatial_lz_hist.append(spatial_lz(grid))
        state_sequence.append(coarse_state(grid, block_size))
        grid = gol_step(grid)
    temp_lz = temporal_lz(state_sequence)
    roll_temp_lz = rolling_temporal_lz(state_sequence, window=20)
    return spatial_lz_hist, temp_lz, roll_temp_lz

def get_block_config(size=(40, 40)):
    grid = np.zeros(size, dtype=int)
    grid[size[0]//2:size[0]//2+2, size[1]//2:size[1]//2+2] = 1
    return grid

def get_glider_config(size=(40, 40)):
    grid = np.zeros(size, dtype=int)
    grid[1, 2] = 1
    grid[2, 3] = 1
    grid[3, 1:4] = 1
    return grid

def get_r_pentomino_config(size=(40, 40)):
    grid = np.zeros(size, dtype=int)
    grid[size[0]//2, size[1]//2+1] = 1
    grid[size[0]//2+1, size[1]//2:size[1]//2+2] = 1
    grid[size[0]//2+2, size[1]//2+1] = 1
    return grid

def get_random_config(size=(40, 40), density=0.5):
    return np.random.choice([0, 1], size=size, p=[1-density, density])

if __name__ == "__main__":
    generations = 100
    grid_size = (40, 40)

    configs = {
        "Block (Trivial)": get_block_config(grid_size),
        "Glider (Periodic)": get_glider_config(grid_size),
        "R-Pentomino (Emergent)": get_r_pentomino_config(grid_size),
        "Random (Chaotic)": get_random_config(grid_size, density=0.5)
    }

    results = {}
    fig, ax = plt.subplots(figsize=(12, 7))
    for name, initial_grid in configs.items():
        spatial_lz_hist, temp_lz, roll_temp_lz = simulate(initial_grid, generations, block_size=4)
        results[name] = {"spatial_lz": spatial_lz_hist, "temp_lz": temp_lz, "roll_temp_lz": roll_temp_lz}
        ax.plot(spatial_lz_hist, label=f"{name} (tempLZ={temp_lz})")

    ax.set_title("Spatial LZ Complexity Over Generations (Temporal LZ in Legend)")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Spatial LZ Complexity")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_test.png")
    plt.close()

    # Rolling temporal LZ plot
    fig, ax = plt.subplots(figsize=(12, 7))
    for name, initial_grid in configs.items():
        roll = results[name]["roll_temp_lz"]
        ax.plot(roll, label=name)
    ax.set_title("Rolling-Window Temporal LZ Complexity (window=20)")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Rolling Temporal LZ Complexity")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.savefig("../../shared_agora/artifacts/gol_rolling_temporal_lz.png")
    plt.close()

    # Bar plot of temporal LZ
    names = list(results.keys())
    temp_lzs = [results[n]["temp_lz"] for n in names]
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.bar(names, temp_lzs, color=["gray", "blue", "green", "red"])
    ax2.set_title("Temporal LZ Complexity by Configuration")
    ax2.set_ylabel("Temporal LZ Complexity")
    ax2.set_ylim(0, max(temp_lzs) * 1.2)
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_bar.png")
    plt.close()

    print("Temporal LZ test complete.")
    for name, res in results.items():
        print(f"{name}: full-sequence temporal LZ = {res['temp_lz']}, final rolling temporal LZ = {res['roll_temp_lz'][-1]}")
