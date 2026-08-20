"""
v12: Final comprehensive verification.
- 400x400 grid, 1500 generations
- Corrected R-Pentomino
- Multiple metrics: unique states, live cell variability, stabilization gen
- LZ76 on coarse-grained state symbols
- Separate analysis for transient vs asymptotic phases
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import hashlib
import time

def gol_step(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def coarse_grain(grid, bs=4):
    """Return a string of 0/1 for each block."""
    r, c = grid.shape
    symbols = []
    for i in range(0, r, bs):
        for j in range(0, c, bs):
            block = grid[i:i+bs, j:j+bs]
            symbols.append('1' if block.sum() > block.size * 0.3 else '0')
    return ''.join(symbols)

def lz76_complexity(s):
    """LZ76 on a string of symbols."""
    n = len(s)
    if n == 0: return 0
    c = 1
    i = 0
    while i < n:
        j = 0
        max_match = 0
        while j < i + 1 and i + j < n:
            k = 0
            while i + j + k < n and j + k < i and s[j+k] == s[i+j+k]:
                k += 1
            if k > max_match:
                max_match = k
            j += 1
        i += max_match + 1
        c += 1
    return c

def run_analysis(grid, generations, label, bs=4):
    hashes = []
    live_counts = []
    cg_states = []
    g = grid.copy()
    for gen in range(generations):
        hashes.append(hashlib.md5(g.tobytes()).hexdigest()[:8])
        live_counts.append(int(g.sum()))
        cg_states.append(coarse_grain(g, bs))
        g = gol_step(g)
    
    # Unique states
    seen = set()
    cum_unique = []
    for h in hashes:
        seen.add(h)
        cum_unique.append(len(seen))
    total_unique = len(seen)
    
    # Stabilization
    last_new = 0
    for i in range(1, len(cum_unique)):
        if cum_unique[i] > cum_unique[i-1]:
            last_new = i
    
    # LZ76 on coarse-grained symbols (map each unique CG state to a char)
    cg_to_char = {}
    symbol_seq = []
    for s in cg_states:
        if s not in cg_to_char:
            cg_to_char[s] = chr(65 + len(cg_to_char) % 58)
        symbol_seq.append(cg_to_char[s])
    symbol_str = ''.join(symbol_seq)
    
    # LZ76 for full sequence, first 200, last 200
    lz_full = lz76_complexity(symbol_str)
    lz_early = lz76_complexity(symbol_str[:200]) if len(symbol_str) >= 200 else lz76_complexity(symbol_str)
    lz_late = lz76_complexity(symbol_str[-200:]) if len(symbol_str) >= 200 else lz76_complexity(symbol_str)
    
    # Live cell stats
    live_arr = np.array(live_counts)
    
    print(f"\n{label}:")
    print(f"  Unique states: {total_unique} (stab gen: {last_new})")
    print(f"  LZ76: full={lz_full}, early(0-200)={lz_early}, late(-200:)={lz_late}")
    print(f"  Live: start={live_counts[0]}, peak={max(live_counts)}@{np.argmax(live_counts)}, final={live_counts[-1]}")
    print(f"  Live std: {np.std(live_arr):.2f}")
    print(f"  Unique CG states: {len(cg_to_char)}")
    
    return {
        'total_unique': total_unique,
        'cum_unique': cum_unique,
        'live_counts': live_counts,
        'lz_full': lz_full,
        'lz_early': lz_early,
        'lz_late': lz_late,
        'last_new_gen': last_new,
        'live_std': np.std(live_arr),
        'n_cg_states': len(cg_to_char),
    }

S = (400, 400)
G = 1500

def rpento():
    g = np.zeros(S, dtype=int)
    g[199, 200:202] = 1; g[200, 199:201] = 1; g[201, 200] = 1
    return g

def block():
    g = np.zeros(S, dtype=int); g[199:201, 199:201] = 1; return g

def glider():
    g = np.zeros(S, dtype=int); g[20,21]=1; g[21,22]=1; g[22,20:23]=1; return g

def blinker():
    g = np.zeros(S, dtype=int); g[200,199:202]=1; return g

def rand():
    np.random.seed(42); return np.random.choice([0,1], size=S, p=[0.5,0.5])

configs = {
    "Block": block(),
    "Blinker": blinker(),
    "Glider": glider(),
    "R-Pentomino": rpento(),
    "Random": rand(),
}

print("=" * 80)
print(f"v12: 400x400 grid, {G} generations, bs=4 coarse-grain + LZ76")
print("=" * 80)
results = {}
for name, g in configs.items():
    t0 = time.time()
    results[name] = run_analysis(g, G, name, bs=4)
    print(f"  (took {time.time()-t0:.1f}s)")

print("\n" + "=" * 80)
print("--- HYP-006 CLAIMS VERIFICATION ---")
b = results["Block"]; bl = results["Blinker"]; gl = results["Glider"]
rp = results["R-Pentomino"]; rnd = results["Random"]

print(f"\n{'Pattern':<15} {'Unique':>7} {'LZ_full':>8} {'LZ_early':>9} {'LZ_late':>8} {'LiveStd':>8} {'StabGen':>8}")
print("-" * 70)
for n, r in results.items():
    print(f"{n:<15} {r['total_unique']:>7} {r['lz_full']:>8} {r['lz_early']:>9} {r['lz_late']:>8} {r['live_std']:>8.1f} {r['last_new_gen']:>8}")

print("\n--- Claim Verification ---")
print(f"C1: Block/Blinker trivial (LZ_full ≤ 5): Block={b['lz_full']}, Blinker={bl['lz_full']} --> {b['lz_full'] <= 5 and bl['lz_full'] <= 5}")
print(f"C2: Glider periodic (low LZ, stable live): LZ={gl['lz_full']}, LiveStd={gl['live_std']:.1f} --> moderate LZ expected")
print(f"C3: RPento > Glider (LZ_full): RPento={rp['lz_full']} > Glider={gl['lz_full']} --> {rp['lz_full'] > gl['lz_full']}")
print(f"C3: RPento > all periodic (LZ_full): RPento={rp['lz_full']} > Glider={gl['lz_full']}, Blinker={bl['lz_full']} --> {rp['lz_full'] > max(gl['lz_full'], bl['lz_full'])}")
print(f"C3: RPento > trivial: RPento={rp['lz_full']} > Block={b['lz_full']} --> {rp['lz_full'] > b['lz_full']}")
print(f"C4: Random highest LZ: Random={rnd['lz_full']} >= RPento={rp['lz_full']} --> {rnd['lz_full'] >= rp['lz_full']}")
print(f"C4: Random continuous novelty: stab_gen={rnd['last_new_gen']} (should be {G-1}) --> {rnd['last_new_gen'] >= G-1}")

# Plot
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

for i, n in enumerate(names):
    axes[0,0].plot(results[n]['cum_unique'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique States")
axes[0,0].set_xlabel("Generation"); axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[0,1].plot(results[n]['live_counts'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Live Cell Count")
axes[0,1].set_xlabel("Generation"); axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)
axes[0,1].set_yscale('log')

x = np.arange(len(names))
lz_vals = [results[n]['lz_full'] for n in names]
axes[0,2].bar(x, lz_vals, color=colors, alpha=0.7)
axes[0,2].set_xticks(x); axes[0,2].set_xticklabels(names, fontsize=8, rotation=20)
axes[0,2].set_title("LZ76 Complexity (Full Sequence)"); axes[0,2].grid(alpha=0.3, axis='y')

us = [results[n]['total_unique'] for n in names]
axes[1,0].bar(x, us, color=colors, alpha=0.7)
axes[1,0].set_xticks(x); axes[1,0].set_xticklabels(names, fontsize=8, rotation=20)
axes[1,0].set_title("Total Unique States"); axes[1,0].grid(alpha=0.3, axis='y')

ls = [results[n]['live_std'] for n in names]
axes[1,1].bar(x, ls, color=colors, alpha=0.7)
axes[1,1].set_xticks(x); axes[1,1].set_xticklabels(names, fontsize=8, rotation=20)
axes[1,1].set_title("Live Cell Std Dev"); axes[1,1].grid(alpha=0.3, axis='y')

# LZ early vs late
lz_e = [results[n]['lz_early'] for n in names]
lz_l = [results[n]['lz_late'] for n in names]
w = 0.35
axes[1,2].bar(x - w/2, lz_e, w, label='Early (0-200)', color=[c for c in colors], alpha=0.5)
axes[1,2].bar(x + w/2, lz_l, w, label='Late (1300-1500)', color=[c for c in colors], alpha=1.0)
axes[1,2].set_xticks(x); axes[1,2].set_xticklabels(names, fontsize=8, rotation=20)
axes[1,2].set_title("LZ76: Early vs Late"); axes[1,2].legend(fontsize=8); axes[1,2].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v12.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v12.png")
