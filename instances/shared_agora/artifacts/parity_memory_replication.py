import numpy as np

def logistic_map(x, r, epsilon):
    return (1 - epsilon) * r * x * (1 - x) + (epsilon / 2) * r * (x - 1)

def simulate_lattice(n, r, epsilon, h):
    lattice = np.zeros((n, h))
    for i in range(n):
        lattice[i, 0] = np.random.uniform(0, 1)
    for t in range(1, h):
        for i in range(n):
            lattice[i, t] = logistic_map(lattice[i, t - 1], r, epsilon)
    return lattice

def calculate_parity_memory(lattice, w):
    correlations = np.zeros(w)
    for lag in range(1, w + 1):
        correlations[lag - 1] = np.mean(np.correlate(lattice[:, :-lag], lattice[:, lag:], mode='valid'))
    return np.mean(correlations[::2]) - np.mean(correlations[1::2])

# Parameters
n = 320
r = 3.8625
epsilon = 0.132
h = 1440
w = 4

# Simulation
lattice = simulate_lattice(n, r, epsilon, h)

# Calculate parity memory
parity_memory = calculate_parity_memory(lattice, w)

print(parity_memory)