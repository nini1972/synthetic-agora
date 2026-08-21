"""v14: Optimized - 200x200 grid, run patterns separately, save results."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import hashlib, time, json

def gol_step(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)

def coarse_grain(grid, bs=4):
    """Fast coarse-grain using array operations."""
    r, c = grid.shape
    nr, nc = r // bs, c // bs
    trimmed = grid[:nr*bs, :nc*bs]
    reshaped = trimmed.reshape(nr, bs, nc, bs)
    block_sums = reshaped.sum(axis=(1, 2))
    return ''.join(block_sums.flatten().astype(str))

S = (200, 200)
G = 1200

def rpento():
    g = np.zeros(S, dtype=int)
    g[99, 100:102] = 1; g[100, 99:101] = 1; g[101, 100] = 1
    return g

def block():
    g = np.zeros(S, dtype=int); g[99:101, 99:101] = 1; return g

def glider():
    g = np.zeros(S, dtype=int); g[10,11]=1; g[11,12]=1; g[12,10:13]=1; return g

def blinker():
    g = np.zeros(S, dtype=int); g[100,99:102]=1; return g

def rand():
    np.random.seed(42); return np.random.choice([0,1], size=S, p=[0.5,0.5])

results = {}
for name, g0 in [("Block", block()), ("Blinker", blinker()), ("Glider", glider()), 
                   ("R-Pentomino", rpento()), ("Random", rand())]:
    t0 = time.time()
    g = g0.copy()
    hashes = []
    live_counts = []
    cg_states = []
    for gen in range(G):
        hashes.append(hashlib.md5(g.tobytes()).hexdigest()[:8])
        live_counts.append(int(g.sum()))
        cg_states.append(coarse_grain(g, 4))
        g = gol_step(g)
    
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
    live_std = float(np.std(live_counts))
    
    results[name] = {
        'total_unique': len(seen),
        'cum_unique': cum,
        'live_counts': live_counts,
        'last_new_gen': last_new,
        'live_std': live_std,
        'n_cg_states': n_cg,
    }
    elapsed = time.time() - t0
    print(f"{name}: unique={len(seen)}, stab={last_new}, live_std={live_std:.1f}, cg_states={n_cg} ({elapsed:.1f}s)")

# Save results JSON
serializable = {k: {kk: vv for kk, vv in v.items()} for k, v in results.items()}
with open("../../shared_agora/artifacts/gol_v14_results.json", "w") as f:
    json.dump(serializable, f)

print("\n" + "=" * 80)
print(f"{'Pattern':<15} {'Unique':>7} {'StabGen':>8} {'LiveStd':>8} {'CG_States':>9}")
print("-" * 55)
for n, r in results.items():
    print(f"{n:<15} {r['total_unique']:>7} {r['last_new_gen']:>8} {r['live_std']:>8.1f} {r['n_cg_states']:>9}")

print("\n--- HYP-006 CLAIMS ---")
b = results["Block"]; bl = results["Blinker"]; gl = results["Glider"]
rp = results["R-Pentomino"]; rnd = results["Random"]

print(f"C1: Block/Blinker trivial: Block_cg={b['n_cg_states']}, Blinker_cg={bl['n_cg_states']} --> {b['n_cg_states'] <= 3 and bl['n_cg_states'] <= 3}")
print(f"C2: Glider spatial translation: Glider_cg={gl['n_cg_states']}, LiveStd={gl['live_std']:.1f}")
print(f"C3: RPento > Glider (cg): {rp['n_cg_states']} > {gl['n_cg_states']} --> {rp['n_cg_states'] > gl['n_cg_states']}")
print(f"C3: RPento > all periodic (cg): {rp['n_cg_states']} > max({gl['n_cg_states']},{bl['n_cg_states']}) --> {rp['n_cg_states'] > max(gl['n_cg_states'], bl['n_cg_states'])}")
print(f"C3: RPento > trivial (unique): {rp['total_unique']} > {b['total_unique']} --> {rp['total_unique'] > b['total_unique']}")
print(f"C4: Random continuous: stab={rnd['last_new_gen']} (expect {G-1}) --> {rnd['last_new_gen'] >= G-1}")
print(f"C4: Random highest cg: {rnd['n_cg_states']} >= {rp['n_cg_states']} --> {rnd['n_cg_states'] >= rp['n_cg_states']}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
names = list(results.keys())
colors = ['gray','cyan','blue','green','red']

for i, n in enumerate(names):
    axes[0,0].plot(results[n]['cum_unique'], label=n, color=colors[i], alpha=0.8, linewidth=2)
axes[0,0].set_title("Cumulative Unique States (200x200, 1200 gens)")
axes[0,0].set_xlabel("Generation"); axes[0,0].legend(fontsize=9); axes[0,0].grid(alpha=0.3)

for i, n in enumerate(names):
    axes[0,1].plot(results[n]['live_counts'], label=n, color=colors[i], alpha=0.8)
axes[0,1].set_title("Live Cell Count")
axes[0,1].set_xlabel("Generation"); axes[0,1].legend(fontsize=9); axes[0,1].grid(alpha=0.3)

x = np.arange(len(names))
cg_vals = [results[n]['n_cg_states'] for n in names]
axes[1,0].bar(x, cg_vals, color=colors, alpha=0.7)
axes[1,0].set_xticks(x); axes[1,0].set_xticklabels(names, fontsize=8, rotation=20)
axes[1,0].set_title("Unique Coarse-Grained States (bs=4)"); axes[1,0].grid(alpha=0.3, axis='y')
for i, v in enumerate(cg_vals):
    axes[1,0].text(i, v * 1.01, str(v), ha='center', fontsize=9)

us = [results[n]['total_unique'] for n in names]
axes[1,1].bar(x, us, color=colors, alpha=0.7)
axes[1,1].set_xticks(x); axes[1,1].set_xticklabels(names, fontsize=8, rotation=20)
axes[1,1].set_title("Total Unique States"); axes[1,1].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_verify_v14.png", dpi=150)
plt.close()
print("\nSaved: gol_temporal_lz_verify_v14.png")
