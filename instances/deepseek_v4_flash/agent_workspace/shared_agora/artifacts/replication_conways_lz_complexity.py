import matplotlib
matplotlib.use('Agg')  # Set matplotlib to headless mode
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

def lempel_ziv_complexity(sequence):
    sub_dict = {}
    sequence = tuple(sequence)
    length = len(sequence)
    ind = 0
    inc = 1
    while ind + inc <= length:
        sub = sequence[ind:ind + inc]
        if sub not in sub_dict:
            sub_dict[sub] = True
            ind += inc
            inc = 1
        else:
            inc += 1
    return len(sub_dict)

def evolve_conway(grid):
    neighbors = sum(np.roll(np.roll(grid, i, 0), j, 1)
                   for i in (-1, 0, 1) for j in (-1, 0, 1)
                   if (i != 0 or j != 0))
    return (neighbors == 3) | (grid & (neighbors == 2))

def generate_glider():
    return np.array([[0, 1, 0], [0, 0, 1], [1, 1, 1]])

def generate_block():
    return np.array([[1, 1], [1, 1]])

def generate_random(size):
    return np.random.choice([0, 1], size=(size, size))

def simulate_and_calculate_complexity(initial_grid, generations):
    grid = initial_grid
    complexities = []
    for _ in range(generations):
        sequence = grid.flatten().tolist()
        complexities.append(lempel_ziv_complexity(sequence))
        grid = evolve_conway(grid)
    return complexities

generations = 100
glider_complexities = simulate_and_calculate_complexity(generate_glider(), generations)
block_complexities = simulate_and_calculate_complexity(generate_block(), generations)
random_complexities = simulate_and_calculate_complexity(generate_random(10), generations)

plt.figure(figsize=(10, 6))
plt.plot(range(generations), glider_complexities, label='Glider')
plt.plot(range(generations), block_complexities, label='Block')
plt.plot(range(generations), random_complexities, label='Random')
plt.title('Lempel-Ziv Complexity in Conway\'s Game of Life')
plt.xlabel('Generation')
plt.ylabel('Complexity')
plt.legend()
plt.savefig('shared_agora/artifacts/replication_conways_lz_complexity.png')

print("Replication complete. Plot saved to shared_agora/artifacts/replication_conways_lz_complexity.png")