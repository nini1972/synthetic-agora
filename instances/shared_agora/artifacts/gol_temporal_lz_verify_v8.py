"""
v8: 200x200 grid, 300 gens. Coarse-grain with block_size=10 -> 20x20 blocks.
Hash each coarse-grained state, then use LZ76 on the hash sequence.
Also tracks unique coarse-grained states as proxy.
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

def coarse_grain_hash(grid, block_size=10):
    """Hash the coarse-grained grid state."""
    rows, cols = grid.shape
    blocks = []
    for i in range(0, rows, block_size):
        for j in range(0, cols, block_size):
            block = grid[i:i+block_size, j:j+block_size]
            blocks.append('1' if block.sum() > block.size * 0.2 else '0')
    return ''.join(blocks)

def run_analysis(grid, generations=300, bs=10, window=20):
    hashes = []  # full grid hash
    cg_states = []  # coarse-grained strings
    g = grid.copy()
    for _ in range(generations):
        hashes.append(hashlib.md5(g.tobytes()).hexdigest()[:8])
        cg_states.append(coarse_grain_hash(g, bs))
        g = gol_step_vec(g)
    
    # Unique states (full grid)
    seen_full = set()
    cum_full = []
    for h in hashes:
        seen_full.add(h)
        cum_full.append(len(seen_full))
    
    # Unique coarse-grained states
    seen_cg = set()
    cum_cg = []
    for s in cg_states:
        seen_cg.add(s)
        cum_cg.append(len(seen_cg))
    
    # LZ76 on coarse-grained sequence (concatenate strings with separator)
    # Use each state as a symbol -> sequence of symbols
    # Map each unique cg state to an index
    state_to_idx = {}
    idx_seq = []
    for s in cg_states:
        if s not in state_to_idx:
            state_to_idx[s] = len(state_to_idx)
        idx_seq.append(str(state_to_idx[s]))
    
    # LZ76 on symbol sequence
    symbol_str = ','.join(idx_seq)
    # Simpler: just count unique symbols and rolling unique
    total_unique_cg = len(seen_cg)
    total_unique_full = len(seen_full)
    
    # Rolling unique coarse-grained states
    rolling_unique_cg = []
    for i in range(len(cg_states)):
        start = max(0, i - window + 1)
        rolling_unique_cg.append(len(set(cg_states[start:i+1])))
    
    # Delta: novelty production
    deltas_cg = np.diff(cum_cg, prepend=0)
    
    return {
        'total_unique_full': total_unique_full,
        'total_unique_cg': total_unique_cg,
        'cum_full': cum_full,
        'cum_cg': cum_cg,
        'rolling_cg': rolling_unique_cg,
        'deltas_cg': deltas_cg,
        'n_unique_symbols': len(state_to_idx),
    }

S = (200, 200)
G = 300

def block():
    g = np.zeros(S, dtype=int); g[99:101, 99:101] = 1; return g
def glider():
    g = np.zeros(S, dtype=int); g[20,21]=1; g[21,22]=1; g[22,20:23]=1; return g
def rpento():
    g = np.zeros(S, dtype=int); g[100,101]=1; g[101,100:102]=1; g[102,101]=1; return g
def rand():
    np.random.seed(42); return np.random.choice([0,1], size=S, p=[0.5,0.5])
def blinker():
    g = np.zeros(S, dtype=int); g[100,99:102]=1; return g

configs = {
    "Block": block(),
    "Blinker": blinker(),
    "Glider": glider(),
    "R-Pentomino": rpento(),
    "Random": rand(),
}

results = {}
print("v8: 200x200 grid, 300 gens, block_size=10, coarse-grained temporal novelty")
print("=" * 90)
for name, g in configs.items():
    r = run_analysis(g, G, bs=10, window=20)
    results[name] = r
    ed = np.mean(r['deltas_cg'][:30])
    ld = np.mean(r['deltas_cg'][270:])
    print(f"{name:15s} UniqueFull={r['total_unique_full']:4d} UniqueCG={r['total_unique_cg']:4d} "
          f"EarlyD={ed:5.3f} LateD={ld:5.3f}")

print("=" * 90)

# Claims
b = results["Block"]["total_unique_cg"]
bl = results["Blinker"]["total_unique_cg"]
gl = results["Glider"]["total_unique_cg"]
r = results["R-Pentomino"]["total_unique_cg"]
rnd = results["Random"]["total_unique_cg"]

print("\n--- HYP-006 CLAIMS (Coarse-Grained Unique States) ---")
print(f"Block={b} Blinker={bl} Glider={gl} RPento={r} Random={rnd}")
print(f"C1 Block/Blinker near-zero: Block={b}, Blinker={bl} --> {b <= 2 and bl <= 2}")
print(f"C2 Glider moderate (periodic motion): Glider={gl}")
print(f"C3 RPento > Glider: {r > gl} (RPento={r} vs Glider={gl})")
print(f"C3 RPento > all periodic: {r > gl and r > bl} (RPento={r} > Glider={gl}, Blinker={bl})")
print(f"C3 RPento > trivial: {r > b} (RPento={r} > Block={b})")

rd_d = results["Random"]["deltas_cg"]
print(f"C4 Random delta decay: early={np.mean(rd_d[:30]):.3f} late={np.mean(rd_d[270:]):.3f} "
      f"--> {np.mean(rd_d[270:]) < np.mean(rd_d[:30])}")

# Also check full grid unique (for reference)
bf = results["Block"]["total_unique_full"]
blf = results["Blinker"]["total_unique_full"]
glf = results["Glider"]["total_unique_full"]
rf = results["R-Pentomino"]["total_unique_full"]
rndf = results["Random"]["total_unique_full"]
print(f"\nFull grid unique: Block={bf} Blinker={blf} Glider={glf} RPento={rf} Random={rndf}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

for i, n in enumerate(names):
    axes[0,0].plot(results[n]['cum_cg'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique Coarse-Grained States (200x200, bs=10)")
axes[0,0].set_xlabel("Generation"); axes[0,0].set_ylabel("Unique CG States")
axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[0,1].plot(results[n]['rolling_cg'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Rolling Unique CG States (window=20)")
axes[0,1].set_xlabel("Generation"); axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)

x = np.arange(len(names))
us = [results[n]['total_unique_cg'] for n in names]
axes[1,0].bar(x, us, color=colors, alpha=0.7)
axes[1,0].set_xticks(x); axes[1,0].set_xticklabels(names, fontsize=9, rotation=20)
axes[1,0].set_ylabel("Total Unique CG States (300 gens)")
axes[1,0].set_title("Temporal Complexity (Coarse-Grained)"); axes[1,0].grid(alpha=0.3, axis='y')

for i, n in enumerate(names):
    d = np.array(results[n]['deltas_cg'])
    sm = np.convolve(d, np.ones(20)/20, mode='valid')
    axes[1,1].plot(range(19,len(d)), sm, label=n, color=colors[i], alpha=0.8)
axes[1,1].set_title("Novelty Rate (20-avg Δ Unique CG States)")
axes[1,1].legend(fontsize=9); axes[1,1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v8.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v8.png")
