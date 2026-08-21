"""v13: Optimized - use bs=8 coarse-grain, only track key metrics, no LZ76."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import hashlib, time

def gol_step(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def coarse_grain(grid, bs=8):
    r, c = grid.shape
    symbols = []
    for i in range(0, r, bs):
        for j in range(0, c, bs):
            block = grid[i:i+bs, j:j+bs]
            symbols.append('1' if block.sum() > 0 else '0')
    return ''.join(symbols)

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

results = {}
print(f"400x400 grid, {G} gens, bs=8")
for name, g0 in configs.items():
    t0 = time.time()
    g = g0.copy()
    hashes = []
    live_counts = []
    cg_states = []
    for gen in range(G):
        hashes.append(hashlib.md5(g.tobytes()).hexdigest()[:8])
        live_counts.append(int(g.sum()))
        cg_states.append(coarse_grain(g, 8))
        g = gol_step(g)
    elapsed = time.time() - t0
    
    seen = set()
    cum = []
    for h in hashes:
        seen.add(h)
        cum.append(len(seen))
    last_new = 0
    for i in range(1, len(cum)):
        if cum[i] > cum[i-1]:
            last_new = i
    
    n_cg = len(set(cg_states))
    live_std = np.std(live_counts)
    
    results[name] = {
        'total_unique': len(seen),
        'cum_unique': cum,
        'live_counts': live_counts,
        'last_new_gen': last_new,
        'live_std': live_std,
        'n_cg_states': n_cg,
        'cg_states': cg_states,
    }
    print(f"  {name}: unique={len(seen)}, stab={last_new}, live_std={live_std:.1f}, cg_states={n_cg} ({elapsed:.1f}s)")

# Print comparison table
print("\n" + "=" * 80)
print(f"{'Pattern':<15} {'Unique':>7} {'StabGen':>8} {'LiveStd':>8} {'CG_States':>9}")
print("-" * 55)
for n, r in results.items():
    print(f"{n:<15} {r['total_unique']:>7} {r['last_new_gen']:>8} {r['live_std']:>8.1f} {r['n_cg_states']:>9}")

print("\n--- HYP-006 CLAIMS ---")
b = results["Block"]; bl = results["Blinker"]; gl = results["Glider"]
rp = results["R-Pentomino"]; rnd = results["Random"]

print(f"C1: Block/Blinker trivial: Block_cg={b['n_cg_states']}, Blinker_cg={bl['n_cg_states']} --> {b['n_cg_states'] <= 3 and bl['n_cg_states'] <= 3}")
print(f"C2: Glider spatial translation only: Glider_cg={gl['n_cg_states']}, LiveStd={gl['live_std']:.1f}")
print(f"C3: RPento > Glider: cg RPento={rp['n_cg_states']} vs Glider={gl['n_cg_states']} --> {rp['n_cg_states'] > gl['n_cg_states']}")
print(f"C3: RPento > periodic: cg RPento={rp['n_cg_states']} > Glider={gl['n_cg_states']}, Blinker={bl['n_cg_states']} --> {rp['n_cg_states'] > max(gl['n_cg_states'], bl['n_cg_states'])}")
print(f"C3: RPento > trivial: unique RPento={rp['total_unique']} > Block={b['total_unique']} --> {rp['total_unique'] > b['total_unique']}")
print(f"C4: Random continuous novelty: stab={rnd['last_new_gen']} (expect {G-1}) --> {rnd['last_new_gen'] >= G-1}")
print(f"C4: Random highest complexity: cg Random={rnd['n_cg_states']} >= RPento={rp['n_cg_states']} --> {rnd['n_cg_states'] >= rp['n_cg_states']}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

for i, n in enumerate(names):
    axes[0,0].plot(results[n]['cum_unique'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique States (400x400, 1500 gens)")
axes[0,0].set_xlabel("Generation"); axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[0,1].plot(results[n]['live_counts'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Live Cell Count")
axes[0,1].set_xlabel("Generation"); axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)

x = np.arange(len(names))
cg_vals = [results[n]['n_cg_states'] for n in names]
axes[1,0].bar(x, cg_vals, color=colors, alpha=0.7)
axes[1,0].set_xticks(x); axes[1,0].set_xticklabels(names, fontsize=8, rotation=20)
axes[1,0].set_title("Unique Coarse-Grained States (bs=8)"); axes[1,0].grid(alpha=0.3, axis='y')
for i, v in enumerate(cg_vals):
    axes[1,0].text(i, v * 1.01, str(v), ha='center', fontsize=9)

ls = [results[n]['live_std'] for n in names]
axes[1,1].bar(x, ls, color=colors, alpha=0.7)
axes[1,1].set_xticks(x); axes[1,1].set_xticklabels(names, fontsize=8, rotation=20)
axes[1,1].set_title("Live Cell Std Dev"); axes[1,1].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v13.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v13.png")
