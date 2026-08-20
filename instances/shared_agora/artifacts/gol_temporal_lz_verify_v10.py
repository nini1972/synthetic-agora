"""
v10: FIXED R-Pentomino pattern.
R-Pentomino:
  .XX
  XX.
  .X.
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

def gol_step_torus(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='wrap')
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def run_diagnostic(grid, generations, step_fn, label):
    hashes = []
    live_counts = []
    g = grid.copy()
    for gen in range(generations):
        hashes.append(hashlib.md5(g.tobytes()).hexdigest()[:8])
        live_counts.append(int(g.sum()))
        g = step_fn(g)
    
    seen = set()
    cum_unique = []
    for h in hashes:
        seen.add(h)
        cum_unique.append(len(seen))
    
    total_unique = len(seen)
    deltas = np.diff(cum_unique, prepend=0)
    
    # Find stabilization gen
    last_new = 0
    for i in range(1, len(cum_unique)):
        if cum_unique[i] > cum_unique[i-1]:
            last_new = i
    
    print(f"\n{label}:")
    print(f"  Total unique states: {total_unique}")
    print(f"  Live cells: start={live_counts[0]}, peak={max(live_counts)} @ gen {np.argmax(live_counts)}, final={live_counts[-1]}")
    print(f"  Stabilization gen (last new state): {last_new}")
    
    return {
        'total_unique': total_unique,
        'live_counts': live_counts,
        'cum_unique': cum_unique,
        'deltas': deltas,
        'last_new_gen': last_new,
    }

S = (400, 400)
G = 1200

def rpento_finite():
    g = np.zeros(S, dtype=int)
    # R-Pentomino: .XX / XX. / .X.
    g[199, 200:202] = 1   # row 199: .XX
    g[200, 199:201] = 1   # row 200: XX.
    g[201, 200] = 1       # row 201: .X.
    return g

def block_finite():
    g = np.zeros(S, dtype=int); g[199:201, 199:201] = 1; return g

def glider_finite():
    g = np.zeros(S, dtype=int); g[20,21]=1; g[21,22]=1; g[22,20:23]=1; return g

def blinker_finite():
    g = np.zeros(S, dtype=int); g[200,199:202]=1; return g

def rand_finite():
    np.random.seed(42); return np.random.choice([0,1], size=S, p=[0.5,0.5])

# Verify R-Pentomino pattern
print("R-Pentomino pattern:")
test = rpento_finite()
print(test[199:202, 199:202])
print(f"Live cells: {test.sum()}")

# First run R-Pentomino alone to confirm it's the right pattern
print("\n" + "=" * 80)
print("R-Pentomino on 400x400 finite grid, 1200 generations")
r = run_diagnostic(rpento_finite(), G, gol_step_finite, "R-Pento (CORRECTED)")

# Comparison
print("\n" + "=" * 80)
print(f"Comparison on 400x400 finite, {G} generations")
configs = {
    "Block": block_finite(),
    "Blinker": blinker_finite(),
    "Glider": glider_finite(),
    "R-Pentomino": rpento_finite(),
    "Random": rand_finite(),
}
results = {}
for name, g in configs.items():
    results[name] = run_diagnostic(g, G, gol_step_finite, name)

# Claims
print("\n" + "=" * 80)
print("--- HYP-006 CLAIMS (Unique States as Temporal Complexity Proxy) ---")
b = results["Block"]["total_unique"]
bl = results["Blinker"]["total_unique"]
gl = results["Glider"]["total_unique"]
rp = results["R-Pentomino"]["total_unique"]
rnd = results["Random"]["total_unique"]
print(f"Block={b} Blinker={bl} Glider={gl} RPento={rp} Random={rnd}")
print(f"C1 Block lowest: {b <= min(bl, gl, rp, rnd)}")
print(f"C2 Glider < RPento: {gl < rp}")
print(f"C3 RPento > all periodic (glider, blinker): {rp > gl and rp > bl}")
print(f"C3 RPento > trivial (block): {rp > b}")
print(f"C4 Random produces novelty continuously: "
      f"early={np.mean(results['Random']['deltas'][:50]):.3f} "
      f"late={np.mean(results['Random']['deltas'][-50:]):.3f}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

for i, n in enumerate(names):
    axes[0,0].plot(results[n]['cum_unique'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique States (400x400, 1200 gens)")
axes[0,0].set_xlabel("Generation"); axes[0,0].set_ylabel("Unique States")
axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[0,1].plot(results[n]['live_counts'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Live Cell Count Over Time")
axes[0,1].set_xlabel("Generation"); axes[0,1].set_ylabel("Live Cells")
axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)
axes[0,1].set_yscale('log')

x = np.arange(len(names))
us = [results[n]['total_unique'] for n in names]
bars = axes[1,0].bar(x, us, color=colors, alpha=0.7)
axes[1,0].set_xticks(x); axes[1,0].set_xticklabels(names, fontsize=9, rotation=20)
axes[1,0].set_ylabel("Total Unique States")
axes[1,0].set_title("Total Temporal Novelty (1200 gens)"); axes[1,0].grid(alpha=0.3, axis='y')
# Add value labels
for bar, v in zip(bars, us):
    axes[1,0].text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.01, 
                   str(v), ha='center', va='bottom', fontsize=9)

for i, n in enumerate(names):
    d = np.array(results[n]['deltas'])
    sm = np.convolve(d, np.ones(20)/20, mode='valid')
    axes[1,1].plot(range(19,len(d)), sm, label=n, color=colors[i], alpha=0.8)
axes[1,1].set_title("Novelty Rate (20-avg Δ Unique States)")
axes[1,1].legend(fontsize=9); axes[1,1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v10.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v10.png")
