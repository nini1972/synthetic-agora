"""
Optimized independent verification of HYP-006.
Uses LZ76 with a faster implementation and smaller grid for speed.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import sys

def gol_step_vec(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def lz76_fast(s):
    """Fast LZ76 complexity using a simple parser."""
    n = len(s)
    if n == 0: return 0
    if n <= 2: return 1
    c = 1
    i = 0
    while i < n:
        j = 1
        while i + j <= n:
            sub = s[i:i+j]
            pre = s[:i+j-1]
            if sub not in pre:
                c += 1
                i += j
                break
            j += 1
        else:
            break
    return c

def coarse_grain(grid, block_size=4, levels=4):
    rows, cols = grid.shape
    symbols = []
    for i in range(0, rows, block_size):
        for j in range(0, cols, block_size):
            block = grid[i:i+block_size, j:j+block_size]
            d = block.sum() / max(block.size, 1)
            level = min(levels - 1, int(d * levels))
            symbols.append(str(level))
    return ''.join(symbols)

def run_one(grid, generations=100, bs=4, window=15):
    states = []
    spatial_lz = []
    g = grid.copy()
    for _ in range(generations):
        states.append(coarse_grain(g, bs))
        # For spatial, use coarse-grain to keep string short
        spatial_lz.append(lz76_fast(states[-1]))
        g = gol_step_vec(g)
    full_tlz = lz76_fast(''.join(states))
    rolling = []
    for i in range(generations):
        start = max(0, i - window + 1)
        rolling.append(lz76_fast(''.join(states[start:i+1])))
    deltas = np.diff(rolling, prepend=rolling[0])
    return full_tlz, rolling, spatial_lz, deltas

# Grid 40x40, 100 generations for speed
G = 100
S = (40, 40)

def block():
    g = np.zeros(S, dtype=int); g[19:21, 19:21] = 1; return g
def glider():
    g = np.zeros(S, dtype=int); g[5,6]=1; g[6,7]=1; g[7,5:8]=1; return g
def rpento():
    g = np.zeros(S, dtype=int); g[20,21]=1; g[21,20:22]=1; g[22,21]=1; return g
def rand():
    np.random.seed(42); return np.random.choice([0,1], size=S, p=[0.5,0.5])
def blinker():
    g = np.zeros(S, dtype=int); g[20,19:22]=1; return g

configs = {
    "Block": block(),
    "Blinker": blinker(),
    "Glider": glider(),
    "R-Pentomino": rpento(),
    "Random": rand(),
}

results = {}
for name, g in configs.items():
    ft, rl, sl, dl = run_one(g, G)
    results[name] = {'full': ft, 'rolling': rl, 'spatial': sl, 'deltas': dl}
    ed = np.mean(dl[:30])
    ld = np.mean(dl[70:])
    print(f"{name:15s} Full={ft:5d} EarlyD={ed:6.2f} LateD={ld:6.2f} Decay={ed/(ld+0.001):.2f}")

print("\n--- Claims ---")
b = results["Block"]["full"]
bl = results["Blinker"]["full"]
gl = results["Glider"]["full"]
r = results["R-Pentomino"]["full"]
rnd = results["Random"]["full"]
print(f"Block={b} Blinker={bl} Glider={gl} RPento={r} Random={rnd}")
print(f"C1 Block lowest: {b <= min(bl, gl, r, rnd)}")
print(f"C2 Periodic < Emergent: Glider({gl}) < RPento({r}) = {gl < r}")
print(f"C3 RPento > all periodic: {r > gl and r > bl}")
print(f"C3 RPento > trivial: {r > b}")
rd = results["Random"]["deltas"]
print(f"C4 Random delta decay: {np.mean(rd[70:]) < np.mean(rd[:30])}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

for i, n in enumerate(names):
    axes[0,0].plot(results[n]['rolling'], label=n, color=colors[i], alpha=0.8)
axes[0,0].set_title("Rolling Temporal LZ76 (window=15)")
axes[0,0].set_xlabel("Generation"); axes[0,0].legend(fontsize=8); axes[0,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[0,1].plot(results[n]['spatial'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Spatial LZ76 (coarse-grained)")
axes[0,1].set_xlabel("Generation"); axes[0,1].legend(fontsize=8); axes[0,1].grid(alpha=0.3)

tlzs = [results[n]['full'] for n in names]
axes[1,0].barh(names, tlzs, color=colors)
axes[1,0].set_title("Full-Sequence Temporal LZ76"); axes[1,0].grid(alpha=0.3, axis='x')

for i, n in enumerate(names):
    d = np.array(results[n]['deltas'])
    sm = np.convolve(d, np.ones(10)/10, mode='valid')
    axes[1,1].plot(range(9,len(d)), sm, label=n, color=colors[i], alpha=0.8)
axes[1,1].set_title("Novelty Rate (10-avg)"); axes[1,1].legend(fontsize=8); axes[1,1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v3.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v3.png")
