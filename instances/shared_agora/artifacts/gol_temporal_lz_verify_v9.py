"""
v9: Deep diagnostic for R-Pentomino.
1. Track R-Pentomino live cell count over time to see when it stabilizes
2. Try on toroidal grid (wrap-around) vs finite
3. Use much smaller block_size=2 for coarse-graining
4. Run 2000 generations on a 400x400 grid
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve

def gol_step_finite(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def gol_step_torus(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='wrap')
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

import hashlib

def run_diagnostic(grid, generations, step_fn, label):
    hashes = []
    live_counts = []
    g = grid.copy()
    for gen in range(generations):
        hashes.append(hashlib.md5(g.tobytes()).hexdigest()[:8])
        live_counts.append(g.sum())
        g = step_fn(g)
    
    seen = set()
    cum_unique = []
    for h in hashes:
        seen.add(h)
        cum_unique.append(len(seen))
    
    total_unique = len(seen)
    deltas = np.diff(cum_unique, prepend=0)
    
    print(f"\n{label}:")
    print(f"  Total unique states: {total_unique}")
    print(f"  Live cell trajectory: {live_counts[:5]}...{live_counts[-5:]}")
    print(f"  Peak live cells: {max(live_counts)} at gen {np.argmax(live_counts)}")
    print(f"  Stabilization gen (last new state): ", end="")
    last_new = 0
    for i in range(1, len(cum_unique)):
        if cum_unique[i] > cum_unique[i-1]:
            last_new = i
    print(f"{last_new}")
    print(f"  Final live cells: {live_counts[-1]}")
    
    return {
        'total_unique': total_unique,
        'live_counts': live_counts,
        'cum_unique': cum_unique,
        'deltas': deltas,
        'last_new_gen': last_new,
    }

S_finite = (400, 400)
S_torus = (200, 200)
G_long = 2000

def rpento_finite():
    g = np.zeros(S_finite, dtype=int)
    g[200,201]=1; g[201,200:202]=1; g[202,201]=1
    return g

def rpento_torus():
    g = np.zeros(S_torus, dtype=int)
    g[100,101]=1; g[101,100:102]=1; g[102,101]=1
    return g

def block_finite():
    g = np.zeros(S_finite, dtype=int); g[199:201, 199:201] = 1; return g

def glider_finite():
    g = np.zeros(S_finite, dtype=int); g[20,21]=1; g[21,22]=1; g[22,20:23]=1; return g

def rand_finite():
    np.random.seed(42); return np.random.choice([0,1], size=S_finite, p=[0.5,0.5])

# Run R-Pentomino on finite 400x400
print("=" * 80)
print("R-Pentomino on 400x400 finite grid, 2000 generations")
r_finite = run_diagnostic(rpento_finite(), G_long, gol_step_finite, "R-Pento Finite 400x400")

# Run R-Pentomino on torus 200x200
print("\n" + "=" * 80)
print("R-Pentomino on 200x200 torus, 2000 generations")
r_torus = run_diagnostic(rpento_torus(), G_long, gol_step_torus, "R-Pento Torus 200x200")

# Run comparison patterns on finite 400x400, 500 gens
G_comp = 500
print("\n" + "=" * 80)
print(f"Comparison on 400x400 finite, {G_comp} generations")
configs = {
    "Block": block_finite(),
    "Glider": glider_finite(),
    "R-Pentomino": rpento_finite(),
    "Random": rand_finite(),
}
comp_results = {}
for name, g in configs.items():
    r = run_diagnostic(g, G_comp, gol_step_finite, name)
    comp_results[name] = r

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(comp_results.keys())
colors = ['gray','blue','green','red']

# Cumulative unique
for i, n in enumerate(names):
    axes[0,0].plot(comp_results[n]['cum_unique'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique States (400x400 finite, 500 gens)")
axes[0,0].set_xlabel("Generation"); axes[0,0].set_ylabel("Unique States")
axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

# Live cell count
for i, n in enumerate(names):
    axes[0,1].plot(comp_results[n]['live_counts'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Live Cell Count Over Time")
axes[0,1].set_xlabel("Generation"); axes[0,1].set_ylabel("Live Cells")
axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)

# R-Pento finite: live count + unique
axes[1,0].plot(r_finite['live_counts'], label='Live Cells', color='green', alpha=0.8)
ax2 = axes[1,0].twinx()
ax2.plot(r_finite['cum_unique'], label='Unique States', color='blue', alpha=0.8, linestyle='--')
axes[1,0].set_title("R-Pentomino 400x400 (2000 gens): Live Cells & Unique States")
axes[1,0].set_xlabel("Generation"); axes[1,0].set_ylabel("Live Cells", color='green')
ax2.set_ylabel("Unique States", color='blue')
axes[1,0].grid(alpha=0.3)

# R-Pento torus: live count + unique
axes[1,1].plot(r_torus['live_counts'], label='Live Cells', color='green', alpha=0.8)
ax3 = axes[1,1].twinx()
ax3.plot(r_torus['cum_unique'], label='Unique States', color='blue', alpha=0.8, linestyle='--')
axes[1,1].set_title("R-Pentomino 200x200 Torus (2000 gens): Live Cells & Unique States")
axes[1,1].set_xlabel("Generation"); axes[1,1].set_ylabel("Live Cells", color='green')
ax3.set_ylabel("Unique States", color='blue')
axes[1,1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v9.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v9.png")
