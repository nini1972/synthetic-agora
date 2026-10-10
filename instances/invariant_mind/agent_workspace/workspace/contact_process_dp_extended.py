import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class ContactProcess:
    """2D contact process simulation for directed-percolation criticality"""
    def __init__(self, N, a=0.5):
        self.N = N
        self.a = a  # Survival probability
        self.grid = np.zeros((N, N), dtype=int)
        
    def step(self, b):
        """Synchronous update with birth probability b * live_neighbors"""
        new_grid = np.zeros_like(self.grid)
        # Count neighbors
        neighbors = sum(np.roll(self.grid, shift, axis=axis)
                       for shift in (-1, 1) for axis in (0, 1))
        
        # Survival rule
        survivors = (self.grid == 1) & (np.random.random(self.grid.shape) < self.a)
        # Birth rule
        births = (self.grid == 0) & (np.random.random(self.grid.shape) < b * neighbors)
        
        new_grid[survivors | births] = 1
        self.grid = new_grid
        return np.mean(self.grid)

    def simulate_soup(self, b, steps=250):
        """Branch A: Start from random soup"""
        self.grid = (np.random.random((self.N, self.N)) < 0.3).astype(int)
        densities = []
        for _ in range(steps):
            densities.append(self.step(b))
        return np.mean(densities[-50:])

    def simulate_seed(self, b, steps=100):
        """Branch B: Start from central seed"""
        self.grid = np.zeros((self.N, self.N), dtype=int)
        self.grid[self.N//2, self.N//2] = 1
        for _ in range(steps):
            density = self.step(b)
        return density > 0

# Parameter sweep for different grid sizes
sizes = [64, 96, 128]
results = {}

for N in sizes:
    print(f"Starting simulations for N={N}...")
    b_values = np.linspace(0.20, 0.28, 17)
    trials = 15
    
    # Branch A results
    rhoA = []
    print("\tBranch A simulation...")
    for b in b_values:
        print(f"\t\tb={b:.4f}")
        cp = ContactProcess(N)
        rhoA.append(np.mean([cp.simulate_soup(b) for _ in range(trials)]))
    
    # Branch B results
    Psurv = []
    print("\tBranch B simulation...")
    for b in b_values:
        print(f"\t\tb={b:.4f}")
        cp = ContactProcess(N)
        Psurv.append(np.mean([int(cp.simulate_seed(b)) for _ in range(trials)]))
    
    # Find critical points
    b_c_A = None
    b_c_B = None
    
    try:
        # Find first b where density > 0.05
        idx = np.where(np.array(rhoA) > 0.05)[0]
        if len(idx) > 0:
            b_c_A = b_values[idx[0]]
        
        # Find first b where survival probability > 0
        idx = np.where(np.array(Psurv) > 0)[0]
        if len(idx) > 0:
            b_c_B = b_values[idx[0]]
    except:
        pass
    
    # Store results
    results[N] = {
        'b_values': b_values.tolist(),
        'rhoA': rhoA,
        'Psurv': Psurv,
        'b_c_A': b_c_A,
        'b_c_B': b_c_B
    }
    
    # Plot results for this size
    plt.figure(figsize=(10, 6))
    plt.plot(b_values, rhoA, 'o-', label='Branch A: Soup density')
    plt.plot(b_values, Psurv, 's-', label='Branch B: Seed survival probability')
    if b_c_A:
        plt.axvline(b_c_A, color='r', linestyle='--', label=f'Branch A threshold: {b_c_A:.4f}')
    if b_c_B:
        plt.axvline(b_c_B, color='b', linestyle=':', label=f'Branch B threshold: {b_c_B:.4f}')
    plt.xlabel('Birth probability (b)')
    plt.ylabel('Order parameter')
    plt.title(f'Contact Process: DP Critical Point (N={N})')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'../../shared_agora/artifacts/contact_process_dp_critical_N{N}.png')

# Save all results
import json
with open('workspace/cp_results_extended.json', 'w') as f:
    json.dump(results, f)

# Finite-size scaling analysis
plt.figure(figsize=(10, 6))
for N, data in results.items():
    if data['b_c_A']:
        plt.plot(N, data['b_c_A'], 'ro', label=f'Branch A Threshold (N={N})')
    if data['b_c_B']:
        plt.plot(N, data['b_c_B'], 'bs', label=f'Branch B Threshold (N={N})')

plt.xlabel('System Size (N)')
plt.ylabel('Critical Birth Probability (b_c)')
plt.title('Finite-Size Scaling of Directed-Percolation Critical Point')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/finite_size_scaling_dp_critical.png')