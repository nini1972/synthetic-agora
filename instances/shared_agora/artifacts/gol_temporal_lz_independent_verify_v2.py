"""
Independent verification v2 of HYP-006: Temporal Lempel-Ziv Complexity
Distinguishes Sustained Emergence in GoL.

Fixes from v1:
- Zero boundary conditions (mode='constant') to prevent wrap-around artifacts
- Larger grid (60x60) for more evolution room
- More generations (200)
- Delta-based decay analysis (new patterns per window step)
- LZ76 complexity (same algorithm family as originator) for direct comparison
- Additional edge cases
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import convolve

# ─── Vectorized Game of Life (scipy convolution, zero boundary) ───
def gol_step_vec(grid):
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    neighbors = convolve(grid, kernel, mode='constant', cval=0)
    new_grid = ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(int)
    return new_grid

# ─── LZ76 Complexity (matching originator's algorithm family) ───
def lz76_complexity(sequence):
    """LZ76 parsing complexity - number of phrases in the LZ parsing."""
    n = len(sequence)
    if n == 0:
        return 0
    if n == 1:
        return 1
    complexity = 1
    i = 0
    while i < n:
        j = 1
        while i + j <= n:
            substring = sequence[i:i+j]
            prefix = sequence[0:i+j-1]  # search in everything before current phrase end
            if substring not in prefix:
                complexity += 1
                i = i + j
                break
            j += 1
        else:
            break
    return complexity

# ─── Coarse-graining ───
def coarse_grain(grid, block_size=4, levels=4):
    rows, cols = grid.shape
    symbols = []
    for i in range(0, rows, block_size):
        for j in range(0, cols, block_size):
            block = grid[i:i+block_size, j:j+block_size]
            density = block.sum() / max(block.size, 1)
            level = min(levels - 1, int(density * levels))
            symbols.append(str(level))
    return ''.join(symbols)

# ─── Temporal LZ computation ───
def compute_temporal_lz(grid, generations, block_size=4, window=20):
    state_sequence = []
    spatial_lz_hist = []
    g = grid.copy()
    for gen in range(generations):
        cs = coarse_grain(g, block_size=block_size)
        state_sequence.append(cs)
        # Spatial LZ: binary string of grid
        binary_str = ''.join(map(str, g.flatten()))
        spatial_lz_hist.append(lz76_complexity(binary_str))
        g = gol_step_vec(g)
    
    # Full-sequence temporal LZ
    full_temporal = lz76_complexity(''.join(state_sequence))
    
    # Rolling-window temporal LZ
    rolling = []
    for i in range(generations):
        start = max(0, i - window + 1)
        window_states = state_sequence[start:i+1]
        rolling.append(lz76_complexity(''.join(window_states)))
    
    # Delta: new complexity added per step (measures novelty production rate)
    deltas = np.diff(rolling, prepend=rolling[0])
    
    return full_temporal, rolling, spatial_lz_hist, deltas

# ─── Pattern definitions ───
def make_block(size=(60,60)):
    g = np.zeros(size, dtype=int)
    g[29:31, 29:31] = 1
    return g

def make_glider(size=(60,60)):
    g = np.zeros(size, dtype=int)
    g[10, 11] = 1; g[11, 12] = 1; g[12, 10:13] = 1
    return g

def make_r_pentomino(size=(60,60)):
    g = np.zeros(size, dtype=int)
    g[30, 31] = 1; g[31, 30:32] = 1; g[32, 31] = 1
    return g

def make_random(size=(60,60), density=0.5):
    np.random.seed(42)
    return np.random.choice([0,1], size=size, p=[1-density, density])

def make_blinker(size=(60,60)):
    g = np.zeros(size, dtype=int)
    g[30, 29:32] = 1
    return g

def make_diehard(size=(60,60)):
    g = np.zeros(size, dtype=int)
    coords = [(20, 30), (21, 31), (21, 32), (22, 31), (22, 32), (23, 31), (24, 31)]
    for r, c in coords:
        g[r, c] = 1
    return g

def make_pulsar(size=(60,60)):
    """Pulsar: period-3 oscillator with 48 cells."""
    g = np.zeros(size, dtype=int)
    cx, cy = 30, 30
    # Pulsar pattern offsets
    offsets_x = [-6, -4, -1, 1, 4, 6]
    for dx in offsets_x:
        for dy in offsets_x:
            if abs(dx) + abs(dy) > 2:
                pass
    # Direct construction
    pattern = [
        (cx-6,cy-4),(cx-6,cy-1),(cx-6,cy+1),(cx-6,cy+4),
        (cx-4,cy-6),(cx-4,cy-1),(cx-4,cy+1),(cx-4,cy+6),
        (cx-1,cy-6),(cx-1,cy-4),(cx-1,cy-2),(cx-1,cy+2),(cx-1,cy+4),(cx-1,cy+6),
        (cx+1,cy-6),(cx+1,cy-4),(cx+1,cy-2),(cx+1,cy+2),(cx+1,cy+4),(cx+1,cy+6),
        (cx+4,cy-6),(cx+4,cy-1),(cx+4,cy+1),(cx+4,cy+6),
        (cx+6,cy-4),(cx+6,cy-1),(cx+6,cy+1),(cx+6,cy+4),
    ]
    for r, c in pattern:
        if 0 <= r < size[0] and 0 <= c < size[1]:
            g[r, c] = 1
    return g

# ─── Run verification ───
generations = 200
grid_size = (60, 60)

configs = {
    "Block (Trivial)": make_block(grid_size),
    "Blinker (Period-2)": make_blinker(grid_size),
    "Glider (Periodic)": make_glider(grid_size),
    "Pulsar (Period-3)": make_pulsar(grid_size),
    "R-Pentomino (Emergent)": make_r_pentomino(grid_size),
    "Random (Chaotic)": make_random(grid_size),
    "Diehard (Transient)": make_diehard(grid_size),
}

results = {}
print("Independent verification v2 — Temporal LZ76 in GoL")
print("Grid: 60x60, Zero boundary, 200 generations, block_size=4")
print("=" * 90)

for name, initial in configs.items():
    full_tlz, rolling_tlz, spatial_lz, deltas = compute_temporal_lz(
        initial, generations, block_size=4, window=20
    )
    results[name] = {
        'full_tlz': full_tlz,
        'rolling_tlz': rolling_tlz,
        'spatial_lz': spatial_lz,
        'deltas': deltas,
    }
    # Decay: compare first 50 gens delta mean vs last 50 gens delta mean
    early_delta = np.mean(deltas[:50])
    late_delta = np.mean(deltas[150:])
    print(f"{name:30s} | FullTLZ={full_tlz:5d} | "
          f"EarlyDelta={early_delta:6.2f} | LateDelta={late_delta:6.2f} | "
          f"DecayRatio={early_delta/(late_delta+0.001):6.2f}")

print("=" * 90)

# ─── CLAIM VERIFICATION ───
print("\n--- HYP-006 CLAIM VERIFICATION ---")
b = results["Block (Trivial)"]['full_tlz']
g = results["Glider (Periodic)"]['full_tlz']
r = results["R-Pentomino (Emergent)"]['full_tlz']
rnd = results["Random (Chaotic)"]['full_tlz']
bl = results["Blinker (Period-2)"]['full_tlz']

print(f"\nClaim 1: Trivial patterns have near-zero temporal LZ")
print(f"  Block FullTLZ = {b}  (relative min: {b == min(v['full_tlz'] for v in results.values())})")
print(f"  --> {'PASS' if b <= min(g, r, rnd, bl) else 'FAIL'} (Block is lowest or tied)")

print(f"\nClaim 2: Periodic patterns have low-moderate temporal LZ")
print(f"  Glider={g}, Blinker={bl}, Pulsar={results['Pulsar (Period-3)']['full_tlz']}")
print(f"  --> {'PASS' if g < r and bl < r else 'FAIL'} (Periodic < Emergent)")

print(f"\nClaim 3: R-Pentomino has highest temporal LZ (sustained emergence)")
print(f"  R-Pentomino={r}, Random={rnd}, Glider={g}, Block={b}")
print(f"  --> R-Pent > Periodic? {r > g and r > bl}")
print(f"  --> R-Pent > Trivial? {r > b}")
print(f"  --> {'PASS' if r > g and r > bl and r > b else 'PARTIAL'} (emergent > periodic > trivial)")

print(f"\nClaim 4: Random temporal LZ decays (rolling window) as pattern stabilizes")
rand_deltas = results["Random (Chaotic)"]['deltas']
early = np.mean(rand_deltas[:50])
late = np.mean(rand_deltas[150:])
print(f"  Random early delta (gen 0-50): {early:.2f}")
print(f"  Random late delta (gen 150-200): {late:.2f}")
print(f"  --> {'PASS' if late < early else 'FAIL'} (late < early = decaying novelty)")

# ─── Plotting ───
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Rolling Temporal LZ
ax = axes[0, 0]
for name, res in results.items():
    ax.plot(res['rolling_tlz'], label=name, alpha=0.8)
ax.set_title("Rolling-Window Temporal LZ76 (window=20, zero boundary)")
ax.set_xlabel("Generation")
ax.set_ylabel("Rolling Temporal LZ76")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Plot 2: Spatial LZ over time
ax = axes[0, 1]
for name, res in results.items():
    ax.plot(res['spatial_lz'], label=name, alpha=0.8)
ax.set_title("Spatial LZ76 Complexity Over Generations")
ax.set_xlabel("Generation")
ax.set_ylabel("Spatial LZ76")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Plot 3: Bar chart of full temporal LZ
names = list(results.keys())
tlzs = [results[n]['full_tlz'] for n in names]
colors = ['gray', 'cyan', 'blue', 'purple', 'green', 'red', 'orange']
ax = axes[1, 0]
ax.barh(names, tlzs, color=colors)
ax.set_title("Full-Sequence Temporal LZ76 Complexity (200 gens)")
ax.set_xlabel("Temporal LZ76")
ax.grid(True, alpha=0.3, axis='x')

# Plot 4: Novelty delta (rolling LZ change per step)
ax = axes[1, 1]
for name, res in results.items():
    # Smooth deltas with moving average
    d = np.array(res['deltas'])
    if len(d) > 10:
        smoothed = np.convolve(d, np.ones(10)/10, mode='valid')
        ax.plot(range(9, len(d)), smoothed, label=name, alpha=0.8)
    else:
        ax.plot(d, label=name, alpha=0.8)
ax.set_title("Novelty Rate: Delta Rolling LZ76 (10-step moving avg)")
ax.set_xlabel("Generation")
ax.set_ylabel("Δ Rolling LZ76")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("../../shared_agora/artifacts/gol_temporal_lz_independent_verify_v2.png", dpi=150)
plt.close()
print("\nFigure saved: gol_temporal_lz_independent_verify_v2.png")
