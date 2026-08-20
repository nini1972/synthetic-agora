"""
v11: Refined analysis.
1. Run R-Pentomino to 1500 gens (past known ~1103 stabilization point)
2. Compare Glider vs R-Pentomino using:
   - Total unique states (should diverge: glider is periodic with period 4*grid_width)
   - Live cell trajectory (R-Pento varies, glider is constant)
   - State recurrence time (avg time between repeats)
3. For LZ76: use short symbol sequences (coarse-grained state -> symbol)
4. Also use a per-generation "pattern complexity" via live cell count variance
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import hashlib

def gol_step_finite(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def run_analysis(grid, generations, step_fn, label):
    hashes = []
    live_counts = []
    live_changes = []  # |Δ live cells| per gen
    g = grid.copy()
    prev_live = int(g.sum())
    for gen in range(generations):
        hashes.append(hashlib.md5(g.tobytes()).hexdigest()[:8])
        cur_live = int(g.sum())
        live_counts.append(cur_live)
        live_changes.append(abs(cur_live - prev_live))
        prev_live = cur_live
        g = step_fn(g)
    
    seen = set()
    cum_unique = []
    for h in hashes:
        seen.add(h)
        cum_unique.append(len(seen))
    total_unique = len(seen)
    
    last_new = 0
    for i in range(1, len(cum_unique)):
        if cum_unique[i] > cum_unique[i-1]:
            last_new = i
    
    # Rolling unique (window=50)
    window = 50
    rolling_unique = []
    for i in range(len(hashes)):
        s = max(0, i - window + 1)
        rolling_unique.append(len(set(hashes[s:i+1])))
    
    # Live cell variance in windows
    rolling_live_var = []
    for i in range(len(live_counts)):
        s = max(0, i - window + 1)
        rolling_live_var.append(np.var(live_counts[s:i+1]))
    
    print(f"\n{label}:")
    print(f"  Total unique states: {total_unique}")
    print(f"  Stabilization gen: {last_new}")
    print(f"  Live cells: start={live_counts[0]}, peak={max(live_counts)} @ {np.argmax(live_counts)}, final={live_counts[-1]}")
    print(f"  Avg |Δ live cells|: {np.mean(live_changes):.2f}")
    print(f"  Live cell std (all): {np.std(live_counts):.2f}")
    
    return {
        'total_unique': total_unique,
        'live_counts': live_counts,
        'live_changes': live_changes,
        'cum_unique': cum_unique,
        'rolling_unique': rolling_unique,
        'rolling_live_var': rolling_live_var,
        'last_new_gen': last_new,
        'std_live': np.std(live_counts),
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
print(f"400x400 finite grid, {G} generations")
results = {}
for name, g in configs.items():
    results[name] = run_analysis(g, G, gol_step_finite, name)

print("\n" + "=" * 80)
print("--- HYP-006 CLAIMS ---")
b = results["Block"]; bl = results["Blinker"]; gl = results["Glider"]
rp = results["R-Pentomino"]; rnd = results["Random"]

print(f"\nTotal unique states:")
print(f"  Block={b['total_unique']} Blinker={bl['total_unique']} "
      f"Glider={gl['total_unique']} RPento={rp['total_unique']} Random={rnd['total_unique']}")

print(f"\nStabilization gen:")
print(f"  Block={b['last_new_gen']} Blinker={bl['last_new_gen']} "
      f"Glider={gl['last_new_gen']} RPento={rp['last_new_gen']} Random={rnd['last_new_gen']}")

print(f"\nLive cell std (variability):")
print(f"  Block={b['std_live']:.1f} Blinker={bl['std_live']:.1f} "
      f"Glider={gl['std_live']:.1f} RPento={rp['std_live']:.1f} Random={rnd['std_live']:.1f}")

print(f"\nAvg |Δ live cells| (dynamics):")
print(f"  Block={np.mean(b['live_changes']):.1f} Blinker={np.mean(bl['live_changes']):.1f} "
      f"Glider={np.mean(gl['live_changes']):.1f} RPento={np.mean(rp['live_changes']):.1f} "
      f"Random={np.mean(rnd['live_changes']):.1f}")

print(f"\nClaim verification:")
print(f"C1 Block/Blinker trivial (lowest complexity): {b['total_unique'] <= 2 and bl['total_unique'] <= 2}")
print(f"C2 Glider periodic (stable dynamics): Glider std={gl['std_live']:.1f}, |Δ|={np.mean(gl['live_changes']):.1f}")
print(f"C3 RPento complex (highest non-random complexity):")
print(f"   RPento > Glider (unique states after stabilization): "
      f"RPento stab={rp['last_new_gen']}, Glider stab={gl['last_new_gen']}")
print(f"   RPento > all periodic on dynamics: RPento_std={rp['std_live']:.1f} > Glider_std={gl['std_live']:.1f} --> {rp['std_live'] > gl['std_live']}")
print(f"   RPento > trivial: RPento_unique={rp['total_unique']} > Block={b['total_unique']} --> {rp['total_unique'] > b['total_unique']}")
print(f"C4 Random continuous novelty: Random_stab={rnd['last_new_gen']} (should be {G-1}) --> {rnd['last_new_gen'] >= G-1}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

for i, n in enumerate(names):
    axes[0,0].plot(results[n]['cum_unique'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique States (400x400, 1500 gens)")
axes[0,0].set_xlabel("Generation"); axes[0,0].set_ylabel("Unique States")
axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[0,1].plot(results[n]['live_counts'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Live Cell Count Over Time")
axes[0,1].set_xlabel("Generation"); axes[0,1].set_ylabel("Live Cells")
axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[1,0].plot(results[n]['rolling_unique'], label=n, color=colors[i], alpha=0.8)
axes[1,0].set_title("Rolling Unique States (window=50)")
axes[1,0].set_xlabel("Generation"); axes[1,0].legend(fontsize=9); axes[1,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[1,1].plot(results[n]['rolling_live_var'], label=n, color=colors[i], alpha=0.8)
axes[1,1].set_title("Rolling Live Cell Variance (window=50)")
axes[1,1].set_xlabel("Generation"); axes[1,1].legend(fontsize=9); axes[1,1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v11.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v11.png")
