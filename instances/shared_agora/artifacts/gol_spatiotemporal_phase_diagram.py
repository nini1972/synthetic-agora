#!/usr/bin/env python3
"""Generate a spatial-temporal phase diagram for Conway's Game of Life
using four canonical configurations: Block, Glider, R-pentomino, Random.
Axes:
  x: Spatial disorder (final-frame Lempel-Ziv complexity of the grid).
  y: Temporal predictability (final rolling-window temporal LZ; lower = more predictable).
The script computes spatial LZ per frame and temporal LZ of a coarse-grained
state trajectory (4x4 blocks over 60 generations, rolling window of 20).
It then saves a scatter plot with annotated trajectories for R-pentomino.
Artifact saved as gol_spatiotemporal_phase_diagram.png in ../../shared_agora/artifacts/.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --------------------------------------------------------------
# Lempel-Ziv Complexity (normalized to [0,1])
# Implements the LZ78-style phrase-counting algorithm used in
# EMP-001 / EMP-002 prior Agora work (naive but reliable ranking).
# --------------------------------------------------------------
def lz_complexity(seq):
    """Return normalized LZ complexity in [0,1] for a binary sequence string."""
    if isinstance(seq, list):
        s = ''.join(str(x) for x in seq)
    elif isinstance(seq, np.ndarray):
        s = ''.join(str(int(x)) for x in seq.flat)
    elif isinstance(seq, str):
        s = seq
    else:
        s = str(seq)
    n = len(s)
    if n < 4:
        return 0.0

    # ---- LZ78 phrase counting ----
    # We build phrases greedily: find the longest prefix of the remaining
    # text that has appeared before (as a previously output phrase).
    # The new phrase = longest match + next unique character.
    # We count the number of output phrases (M). Normalized complexity C = M / (n/2 + 1),
    # capped at 1.0.  For small n this yields: ordered ~0.0, random ~1.0.
    text = s
    phrases = 0
    pos = 0
    dict_prefixes = set()  # store previously output phrases
    while pos < n:
        # find longest match in dict_prefixes starting at pos
        max_match = 0
        # look backwards: any earlier substring could match; simple O(n^2) scan:
        # we test lengths from 1 upward while within text and match exists
        # Actually, standard LZ78 builds dictionary incrementally; for simplicity we
        # use the "greedy longest prefix in already-processed text" approach.
        # Processed text = text[:pos]
        # We'll find longest L such that text[pos:pos+L] appears in text[:pos]
        # (with the additional char after the match being unique).
        best_L = 0
        for L in range(1, min(n - pos, n) + 1):
            sub = text[pos:pos+L]
            if sub in text[:pos]:
                best_L = L
            else:
                # first L not found; the new phrase will be of length best_L + 1 (if not at end)
                break
        # output phrase of length best_L + 1 (match + new char), unless we exactly consume
        if pos + best_L + 1 <= n:
            phrases += 1
            pos += best_L + 1
        else:
            # remaining 1..best_L chars count as one final phrase (possibly just a match without trailing new char)
            if pos < n:
                phrases += 1
            break

    # Normalize: complexity = phrases / (n/2 + 1), capped at 1.0
    C = phrases / (n / 2.0 + 1)
    if C > 1.0:
        C = 1.0
    if C < 0.0:
        C = 0.0
    return C


# --------------------------------------------------------------
# Game of Life engine
# --------------------------------------------------------------
def evolve_gol(grid, steps=1):
    """Evolve grid for `steps` generations using 8-neighbour toroidal rules."""
    g = grid.copy()
    for _ in range(steps):
        neigh = (
            np.roll(np.roll(g, 1, axis=0), 1, axis=1) +
            np.roll(np.roll(g, -1, axis=0), 1, axis=1) +
            np.roll(np.roll(g, 1, axis=0), -1, axis=1) +
            np.roll(np.roll(g, -1, axis=0), -1, axis=1) +
            np.roll(np.roll(g, 1, axis=0), 0, axis=1) +
            np.roll(np.roll(g, -1, axis=0), 0, axis=1) +
            np.roll(np.roll(g, 0, axis=0), 1, axis=1) +
            np.roll(np.roll(g, 0, axis=0), -1, axis=1)
        )
        new_g = ((neigh == 3) | ((g == 1) & (neigh == 2))).astype(int)
        g = new_g
    return g


# --------------------------------------------------------------
# Main simulation
# --------------------------------------------------------------
SIZE = 20          # 20x20 grid
STEPS = 100

# Initialise four canonical configurations
# Block (2x2 solid block in corner)
block_grid = np.zeros((SIZE, SIZE), dtype=int)
block_grid[0:2, 0:2] = 1

# Glider (standard)
glider_grid = np.zeros((SIZE, SIZE), dtype=int)
glider = np.array([[0,1,0],[0,0,1],[1,1,1]], dtype=int)
glider_grid[1:4, 1:4] = glider

# R-pentomino (shape)
rp_grid = np.zeros((SIZE, SIZE), dtype=int)
rp = np.array([[1,1,0],[1,0,1],[0,1,0]], dtype=int)
rp_grid[5:8, 5:8] = rp

# Random (fixed seed for reproducibility)
rng = np.random.default_rng(42)
rand_grid = rng.integers(0, 2, size=(SIZE, SIZE))

configs = {
    'Block': block_grid,
    'Glider': glider_grid,
    'R-pentomino': rp_grid,
    'Random': rand_grid,
}

results = {}

for name, grid in configs.items():
    # Evolve and collect spatial LZ per step and state trajectory
    spatial_lzs = []
    temporal_seq = []   # coarse-grained state string each step
    g = grid.copy()
    for t in range(STEPS):
        # spatial LZ on current grid
        spatial_lzs.append(lz_complexity(g))
        # coarse-grain: 4x4 blocks -> binarize by majority vote
        # grid is SIZE x SIZE; divide into 4x4 super-blocks
        nblocks = SIZE // 4
        g4 = g.reshape(nblocks, 4, nblocks, 4).swapaxes(1, 2).reshape((nblocks * nblocks), 4 * 4)
        block_maj = (g4.sum(axis=1) >= 8).astype(int)   # 8/16 threshold => 1
        temporal_seq.append(''.join(str(int(x)) for x in block_maj))
        g = evolve_gol(g, steps=1)

    # --- Temporal LZ metrics ---
    # full-sequence temporal LZ on the coarse-grained sequence joined
    full_temporal_str = ''.join(temporal_seq)
    temporal_lz_full = lz_complexity(full_temporal_str) if full_temporal_str else 0.0

    # rolling-window temporal LZ (window=20 generations)
    window = 20
    rolling_lzs = []
    for i in range(0, len(temporal_seq) - window + 1, 1):
        win_str = ''.join(temporal_seq[i:i+window])
        rolling_lzs.append(lz_complexity(win_str))

    # final rolling LZ = average of last 10 windows (measures predictability at asymptotic time)
    if len(rolling_lzs) >= 10:
        final_rolling_lz = np.mean(rolling_lzs[-10:])
    else:
        final_rolling_lz = np.mean(rolling_lzs) if rolling_lzs else 1.0

    # final spatial LZ (last frame)
    final_spatial_lz = spatial_lzs[-1] if spatial_lzs else 0.0

    results[name] = {
        'final_spatial_lz': final_spatial_lz,
        'final_rolling_lz': final_rolling_lz,
        'spatial_lzs': spatial_lzs,
        'temporal_seq': temporal_seq,
    }
    print(f"{name}: final_spatial_lz={final_spatial_lz:.4f}, final_rolling_lz={final_rolling_lz:.4f}, temporal_lz_full={temporal_lz_full:.4f}")

# --------------------------------------------------------------
# Plot: Spatial vs Temporal phase diagram
# --------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6))
names = list(results.keys())
x = [results[n]['final_spatial_lz'] for n in names]
y = [results[n]['final_rolling_lz'] for n in names]

# plot points
ax.scatter(x, y, s=100, c='darkblue')

# annotate names
for i, name in enumerate(names):
    ax.annotate(name, (x[i], y[i]), textcoords="offset points", xytext=(5, -10), fontsize=10)

# Add trajectory arrow for R-pentomino showing decay from early to late rolling LZ
window = 20
init_rolling_str = ''.join(results['R-pentomino']['temporal_seq'][:window]) if len(results['R-pentomino']['temporal_seq']) >= window else ''
init_rolling_lz = lz_complexity(init_rolling_str) if init_rolling_str else 0.0
ix = results['R-pentomino']['final_spatial_lz']
iy = results['R-pentomino']['final_rolling_lz']
# arrow from initial rolling LZ (computed from first window) to final rolling LZ
ax.annotate('', xy=(ix, iy), xytext=(results['R-pentomino']['spatial_lzs'][0], init_rolling_lz),
            arrowprops=dict(arrowstyle='->', color='red', lw=2))
ax.text(ix, iy + 0.02, 'R-pentomino decay', color='red', fontsize=9, ha='center')

ax.set_xlabel('Spatial LZ Complexity (final frame)')
ax.set_ylabel('Temporal Rolling LZ (last 10 windows; lower = more predictable)')
ax.set_title("Spatial-Temporal Phase Diagram: Conway's Game of Life")
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)
ax.grid(True, alpha=0.3)

out_path = os.path.abspath('../../shared_agora/artifacts/gol_spatiotemporal_phase_diagram.png')
fig.savefig(out_path, dpi=150)
print(f"Plot saved to {out_path}")
plt.close(fig)
print("Done.")