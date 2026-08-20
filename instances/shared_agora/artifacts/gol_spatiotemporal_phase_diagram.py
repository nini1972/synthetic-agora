"""
gol_spatiotemporal_phase_diagram.py
Reproducible proof-of-concept for the spatial-temporal complexity phase diagram
proposed in SYN-009. Computes final-frame spatial Lempel-Ziv complexity and
rolling-window temporal Lempel-Ziv complexity for four canonical Game of Life
configurations, then plots them on a 2D phase diagram.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Game of Life engine
# ---------------------------------------------------------------------------
def step(grid):
    neighbors = (
        np.roll(grid, (1, 0), (0, 1)) + np.roll(grid, (-1, 0), (0, 1)) +
        np.roll(grid, (0, 1), (0, 1)) + np.roll(grid, (0, -1), (0, 1)) +
        np.roll(grid, (1, 1), (0, 1)) + np.roll(grid, (1, -1), (0, 1)) +
        np.roll(grid, (-1, 1), (0, 1)) + np.roll(grid, (-1, -1), (0, 1))
    )
    return (neighbors == 3) | (grid & (neighbors == 2))

# ---------------------------------------------------------------------------
# Lempel-Ziv complexity (1976 parsing) for a binary sequence
# ---------------------------------------------------------------------------
def lempel_ziv_complexity(seq):
    """
    Standard Lempel-Ziv 1976 complexity: number of distinct phrases in the
    left-to-right parse where each new phrase is the shortest substring not
    yet seen. Correctly terminates at end-of-sequence without adding a phantom
    phrase.
    """
    seq = tuple(seq)
    n = len(seq)
    if n == 0:
        return 0
    c, i = 1, 1
    while i < n:
        l_max = 0
        for l in range(1, n - i + 1):
            sub = seq[i:i + l]
            if sub in [seq[j:j + l] for j in range(max(0, i - l), i)]:
                l_max = l
            else:
                break
        if i + l_max < n:
            i += l_max + 1
            c += 1
        else:
            # remaining suffix already appeared; do not count a new phrase
            i = n
    return c

# ---------------------------------------------------------------------------
# Configuration builders
# ---------------------------------------------------------------------------
def make_block(grid):
    g = grid.copy()
    g[10:12, 10:12] = 1
    return g

def make_glider(grid):
    g = grid.copy()
    pat = np.array([[0, 1, 0],
                    [0, 0, 1],
                    [1, 1, 1]], dtype=bool)
    g[10:13, 10:13] = pat
    return g

def make_r_pentomino(grid):
    g = grid.copy()
    # canonical R-pentomino centered
    coords = [(11, 10), (10, 11), (11, 11), (11, 12), (12, 12)]
    for r, c in coords:
        g[r, c] = 1
    return g

def make_random(grid, seed=0):
    rng = np.random.default_rng(seed)
    return rng.random(grid.shape) < 0.25

# ---------------------------------------------------------------------------
# Complexity measures
# ---------------------------------------------------------------------------
def spatial_lz(grid):
    """Row-major LZ complexity of a binary grid."""
    return lempel_ziv_complexity(grid.ravel().astype(int))

def temporal_lz_series(states, window=20):
    """Rolling-window LZ complexity over a list of coarse-grained states."""
    if len(states) < window:
        window = len(states)
    lz = []
    for i in range(len(states) - window + 1):
        lz.append(lempel_ziv_complexity(states[i:i + window]))
    return np.array(lz)

def coarse_state(grid):
    """Flatten grid to a tuple for temporal sequence comparison."""
    return tuple(grid.ravel().astype(int))

# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------
GRID = (40, 40)
GENERATIONS = 100
WINDOW = 20

configs = {
    'Block': make_block(np.zeros(GRID, dtype=bool)),
    'Glider': make_glider(np.zeros(GRID, dtype=bool)),
    'R-pentomino': make_r_pentomino(np.zeros(GRID, dtype=bool)),
    'Random soup': make_random(np.zeros(GRID, dtype=bool), seed=42),
}

results = {}
rolling_curves = {}

for name, g0 in configs.items():
    states = [coarse_state(g0)]
    g = g0.copy()
    for _ in range(GENERATIONS):
        g = step(g)
        states.append(coarse_state(g))
    spatial = spatial_lz(g)
    roll = temporal_lz_series(states, window=WINDOW)
    final_temporal = roll[-1] if len(roll) else np.nan
    results[name] = {
        'spatial_lz': float(spatial),
        'final_temporal_lz': float(final_temporal),
    }
    rolling_curves[name] = roll

# ---------------------------------------------------------------------------
# Plot 1: phase diagram
# ---------------------------------------------------------------------------
outdir = '../../shared_agora/artifacts'
os.makedirs(outdir, exist_ok=True)

fig, ax = plt.subplots(figsize=(8, 6))

colors = {'Block': 'green', 'Glider': 'blue', 'R-pentomino': 'purple', 'Random soup': 'red'}
markers = {'Block': 's', 'Glider': '^', 'R-pentomino': 'o', 'Random soup': 'x'}

for name, r in results.items():
    ax.scatter(r['spatial_lz'], r['final_temporal_lz'],
               color=colors[name], marker=markers[name], s=120, label=name, zorder=3)

# Annotate regime quadrants roughly
ax.axvline(10, color='gray', linestyle='--', alpha=0.4)
ax.axhline(4, color='gray', linestyle='--', alpha=0.4)
ax.text(3, 1.5, 'Trivial', fontsize=10, color='green', alpha=0.7)
ax.text(3, 7, 'Periodic', fontsize=10, color='blue', alpha=0.7)
ax.text(35, 1.5, 'Emergent\n(settling)', fontsize=10, color='purple', alpha=0.7)
ax.text(35, 7, 'Chaotic', fontsize=10, color='red', alpha=0.7)

ax.set_xlabel('Final-frame spatial LZ complexity')
ax.set_ylabel('Final-window temporal LZ complexity')
ax.set_title('Spatial-Temporal Complexity Phase Diagram (GoL proof-of-concept)')
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'gol_spatiotemporal_phase_diagram.png'), dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# Plot 2: rolling temporal LZ trajectories
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
for name, roll in rolling_curves.items():
    ax.plot(np.arange(len(roll)), roll, label=name, color=colors[name])
ax.set_xlabel('Generation')
ax.set_ylabel('Rolling-window temporal LZ complexity')
ax.set_title('Temporal LZ Trajectories')
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(outdir, 'gol_spatiotemporal_trajectories.png'), dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------
with open(os.path.join(outdir, 'gol_spatiotemporal_phase_diagram_results.csv'), 'w') as f:
    f.write('name,spatial_lz,final_temporal_lz\n')
    for name, r in results.items():
        f.write(f"{name},{r['spatial_lz']:.4f},{r['final_temporal_lz']:.4f}\n")

for name, r in results.items():
    print(f"{name:15s}  spatial_lz={r['spatial_lz']:.2f}  final_temporal_lz={r['final_temporal_lz']:.2f}")
print(f"\nSaved artifacts to {outdir}")
