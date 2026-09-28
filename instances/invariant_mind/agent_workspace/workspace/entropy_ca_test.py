import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

# Set matplotlib to use Agg for headless environments
plt.switch_backend('Agg')

# Parameters
N = 20  # grid size
steps = 100
H_target = 0.5  # target entropy
alpha = 0.1  # learning rate

# Initialize grid randomly
grid = np.random.choice([0, 1], size=(N, N))

# Rule representation: for simplicity, we represent the rule as a probability vector for the next state
# We'll use a simple rule: each cell's next state depends on the number of neighbors (including itself) that are alive (0 to 9)
# The rule is a vector of 10 probabilities (for 0 to 9 neighbors)
# Initially, set to random probabilities
rule = np.random.rand(10)

# Function to compute Shannon entropy of the grid
def shannon_entropy(grid):
    states, counts = np.unique(grid, return_counts=True)
    probs = counts / counts.sum()
    return -np.sum(probs * np.log2(probs + 1e-10))

# Store entropy over time
entropy_history = []

# Run simulation
for step in range(steps):
    # Compute current entropy
    H = shannon_entropy(grid)
    entropy_history.append(H)
    
    # Update rule: move towards target entropy
    rule = np.clip(rule + alpha * (H_target - H), 0, 1)
    
    # Create next grid
    new_grid = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            # Count neighbors including self (using Moore neighborhood with radius 1)
            total = 0
            for di in [-1,0,1]:
                for dj in [-1,0,1]:
                    ni = (i + di) % N
                    nj = (j + dj) % N
                    total += grid[ni, nj]
            # Apply rule: probability of being alive is rule[total]
            new_grid[i, j] = 1 if np.random.rand() < rule[int(total)] else 0
    grid = new_grid

# Plot final grid
fig, ax = plt.subplots()
cmap = colors.ListedColormap(['white', 'black'])
ax.imshow(grid, cmap=cmap)
ax.set_title(f"Final state after {steps} steps")
plt.savefig('../../shared_agora/artifacts/HYP-074_entropy_ca_evolution.png', bbox_inches='tight')
plt.close()

# Also plot entropy over time
fig, ax = plt.subplots()
ax.plot(entropy_history)
ax.set_xlabel('Time step')
ax.set_ylabel('Shannon entropy')
ax.set_title('Entropy evolution')
plt.savefig('../../shared_agora/artifacts/HYP-074_entropy_history.png', bbox_inches='tight')
plt.close()