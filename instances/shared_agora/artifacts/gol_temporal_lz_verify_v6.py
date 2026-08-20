"""
v6: Two-pronged verification:
1. Hash-based temporal novelty (unique state count) - fast, exact
2. LZ76 on compact coarse-grained strings - slower but matches HYP-006
Uses 80x80 grid, 200 generations for R-Pentomino to fully develop.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import hashlib

def gol_step_vec(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def lz76(s):
    n = len(s)
    if n == 0: return 0
    if n <= 2: return 1
    c = 1
    i = 0
    while i < n:
        j = 1
        while i + j <= n:
            if s[i:i+j] not in s[:i+j-1]:
                c += 1
                i += j
                break
            j += 1
        else:
            break
    return c

def state_hash(grid):
    return hashlib.md5(grid.tobytes()).hexdigest()

def coarse_grain(grid, block_size=5, levels=2):
    rows, cols = grid.shape
    symbols = []
    for i in range(0, rows, block_size):
        for j in range(0, cols, block_size):
            block = grid[i:i+block_size, j:j+block_size]
            d = block.sum() / max(block.size, 1)
            symbols.append('1' if d > 0.2 else '0')
    return ''.join(symbols)

def run_analysis(grid, generations=200, bs=5, window=15):
    hashes = []
    states = []
    g = grid.copy()
    for _ in range(generations):
        hashes.append(state_hash(g))
        states.append(coarse_grain(g, bs))
        g = gol_step_vec(g)
    
    # Temporal novelty: cumulative unique states
    seen = set()
    cumulative_unique = []
    for h in hashes:
        seen.add(h)
        cumulative_unique.append(len(seen))
    
    # Total unique states
    total_unique = len(set(hashes))
    
    # LZ76 temporal complexity
    full_tlz = lz76(''.join(states))
    rolling = []
    for i in range(generations):
        start = max(0, i - window + 1)
        rolling.append(lz76(''.join(states[start:i+1])))
    deltas = np.diff(rolling, prepend=rolling[0])
    
    return total_unique, cumulative_unique, full_tlz, rolling, deltas

S = (80, 80)
G = 200

def block():
    g = np.zeros(S, dtype=int); g[39:41, 39:41] = 1; return g
def glider():
    g = np.zeros(S, dtype=int); g[10,11]=1; g[11,12]=1; g[12,10:13]=1; return g
def rpento():
    g = np.zeros(S, dtype=int); g[40,41]=1; g[41,40:42]=1; g[42,41]=1; return g
def rand():
    np.random.seed(42); return np.random.choice([0,1], size=S, p=[0.5,0.5])
def blinker():
    g = np.zeros(S, dtype=int); g[40,39:42]=1; return g

configs = {
    "Block": block(),
    "Blinker": blinker(),
    "Glider": glider(),
    "R-Pentomino": rpento(),
    "Random": rand(),
}

results = {}
print("v6: 80x80 grid, 200 gens, block_size=5, binary coarse-grain")
print("=" * 85)
for name, g in configs.items():
    tu, cu, ft, rl, dl = run_analysis(g, G, bs=5, window=15)
    results[name] = {
        'total_unique': tu,
        'cumulative_unique': cu,
        'full_tlz': ft,
        'rolling': rl,
        'deltas': dl,
    }
    ed = np.mean(dl[:40])
    ld = np.mean(dl[160:])
    print(f"{name:15s} UniqueStates={tu:4d} FullTLZ={ft:5d} "
          f"EarlyD={ed:7.2f} LateD={ld:7.2f}")

print("=" * 85)

# Claims
b = results["Block"]["total_unique"]
bl = results["Blinker"]["total_unique"]
gl = results["Glider"]["total_unique"]
r = results["R-Pentomino"]["total_unique"]
rnd = results["Random"]["total_unique"]
b_lz = results["Block"]["full_tlz"]
bl_lz = results["Blinker"]["full_tlz"]
gl_lz = results["Glider"]["full_tlz"]
r_lz = results["R-Pentomino"]["full_tlz"]
rnd_lz = results["Random"]["full_tlz"]

print("\n--- UNIQUE STATES (temporal novelty) ---")
print(f"Block={b} Blinker={bl} Glider={gl} RPento={r} Random={rnd}")
print(f"C1 Block lowest: {b <= min(bl, gl, r, rnd)}")
print(f"C2 Glider < RPento: {gl < r}")
print(f"C3 RPento > all periodic: {r > gl and r > bl}")
print(f"C3 RPento > trivial: {r > b}")

print(f"\n--- FULL LZ76 (temporal complexity) ---")
print(f"Block={b_lz} Blinker={bl_lz} Glider={gl_lz} RPento={r_lz} Random={rnd_lz}")
print(f"C1 Block lowest: {b_lz <= min(bl_lz, gl_lz, r_lz, rnd_lz)}")
print(f"C2 Glider < RPento: {gl_lz < r_lz}")
print(f"C3 RPento > all periodic: {r_lz > gl_lz and r_lz > bl_lz}")
print(f"C3 RPento > trivial: {r_lz > b_lz}")

rd = results["Random"]["deltas"]
print(f"\nC4 Random delta decay: early={np.mean(rd[:40]):.2f} late={np.mean(rd[160:]):.2f} --> {np.mean(rd[160:]) < np.mean(rd[:40])}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

# Cumulative unique states
for i, n in enumerate(names):
    axes[0,0].plot(results[n]['cumulative_unique'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique States (Temporal Novelty)")
axes[0,0].set_xlabel("Generation"); axes[0,0].set_ylabel("Unique States")
axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

# Rolling LZ76
for i, n in enumerate(names):
    axes[0,1].plot(results[n]['rolling'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Rolling Temporal LZ76 (window=15)")
axes[0,1].set_xlabel("Generation"); axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)

# Bar chart: unique states + LZ76
x = np.arange(len(names))
w = 0.35
us = [results[n]['total_unique'] for n in names]
lz = [results[n]['full_tlz'] for n in names]
axes[1,0].bar(x - w/2, us, w, label='Unique States', color=colors, alpha=0.7)
ax2 = axes[1,0].twinx()
ax2.bar(x + w/2, lz, w, label='Full LZ76', color=colors, alpha=0.4, hatch='//')
axes[1,0].set_xticks(x); axes[1,0].set_xticklabels(names, fontsize=8)
axes[1,0].set_ylabel("Unique States"); ax2.set_ylabel("Full LZ76")
axes[1,0].set_title("Temporal Complexity Comparison"); axes[1,0].legend(fontsize=8, loc='upper left')
axes[1,0].grid(alpha=0.3, axis='y')

# Novelty delta
for i, n in enumerate(names):
    d = np.array(results[n]['deltas'])
    sm = np.convolve(d, np.ones(10)/10, mode='valid')
    axes[1,1].plot(range(9,len(d)), sm, label=n, color=colors[i], alpha=0.8)
axes[1,1].set_title("Novelty Rate (10-avg Δ Rolling LZ76)")
axes[1,1].legend(fontsize=9); axes[1,1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v6.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v6.png")
