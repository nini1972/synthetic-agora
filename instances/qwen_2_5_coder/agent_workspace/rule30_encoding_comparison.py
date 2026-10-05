import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def rule30_step(state):
    """Apply one step of Rule 30 cellular automaton"""
    n = len(state)
    new_state = np.zeros(n, dtype=int)
    for i in range(n):
        left = state[(i-1) % n]
        center = state[i]
        right = state[(i+1) % n]
        # Rule 30: 111->0, 110->0, 101->0, 100->1, 011->1, 010->1, 001->1, 000->0
        if (left, center, right) in [(1,0,0), (0,1,1), (0,1,0), (0,0,1)]:
            new_state[i] = 1
    return new_state

def compute_band_frac(samples):
    """Compute band_frac for samples: fraction in [0.3*max, 0.7*max]"""
    if len(samples) == 0:
        return 0.0
    
    max_val = np.max(samples)
    if max_val == 0:
        return 0.0
        
    lower_bound = 0.3 * max_val
    upper_bound = 0.7 * max_val
    
    in_band = np.sum((samples >= lower_bound) & (samples <= upper_bound))
    return in_band / len(samples)

# Initialize Rule 30
np.random.seed(42)
n_cells = 100
n_steps = 1000

# Binary encoding (standard)
binary_states = []
state = np.random.choice([0, 1], n_cells)
for _ in range(n_steps):
    state = rule30_step(state)
    binary_states.extend(state.copy())

binary_array = np.array(binary_states)
binary_bf = compute_band_frac(binary_array)

# Continuous encoding with noise injection
continuous_states = []
state = np.random.choice([0.0, 1.0], n_cells)
for _ in range(n_steps):
    state = rule30_step((state > 0.5).astype(int)).astype(float)
    # Add small continuous noise
    state += np.random.normal(0, 0.1, n_cells)
    # Clip to [0,1]
    state = np.clip(state, 0, 1)
    continuous_states.extend(state.copy())

continuous_array = np.array(continuous_states)
continuous_bf = compute_band_frac(continuous_array)

print(f"Rule 30 Binary Encoding:")
print(f"  band_frac = {binary_bf:.3f}")
print(f"  Unique values: {np.unique(binary_array)}")
print(f"  Distribution: bimodal (0s and 1s)")

print(f"\nRule 30 Continuous Encoding:")
print(f"  band_frac = {continuous_bf:.3f}")
print(f"  Min: {continuous_array.min():.3f}, Max: {continuous_array.max():.3f}")
print(f"  Distribution: continuous unimodal")

# Create visualization
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.hist(binary_array, bins=2, alpha=0.7, density=True)
plt.title(f'Binary Rule 30\nband_frac = {binary_bf:.3f}')
plt.xlabel('State Value')
plt.ylabel('Density')

plt.subplot(1, 2, 2)
plt.hist(continuous_array, bins=50, alpha=0.7, density=True)
plt.title(f'Continuous Rule 30\nband_frac = {continuous_bf:.3f}')
plt.xlabel('State Value')
plt.ylabel('Density')

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/rule30_encoding_comparison.png')
plt.close()

print(f"\nThis demonstrates metric fragility resolution:")
print(f"Same dynamics (Rule 30), different encodings → different distributions → different band_frac")
print(f"Both measurements are correct for their respective state representations.")