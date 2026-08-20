"""
Empirical stress-test of SYN-009:
A (spatial_LZ, temporal_LZ) phase diagram for a noisy Conway-like 2D CA.

We scan initial density rho and post-update noise epsilon.  Spatial complexity
is the Lempel-Ziv complexity of the final grid (row-major bytes).  Temporal
complexity is the LZ complexity of the coarse-grained state trajectory
(4x4 blocks quantized to 2 bits, 80 generations).

Artifact: ca_spatiotemporal_phase_diagram.png
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

# ---------------------------------------------------------------------------
# Parameters
GRID = 32
T = 80
REPS = 3
BLOCK = 4          # coarse-graining block size
Q = 4              # quantization levels per block -> 2 bits
N_BLOCKS = (GRID // BLOCK) ** 2

DENSITIES = np.linspace(0.05, 0.95, 14)
NOISES = np.linspace(0.0, 0.45, 14)

# ---------------------------------------------------------------------------
# Lempel-Ziv 76 complexity (standard parse)
def lempel_ziv_complexity(seq):
    seq = tuple(seq)
    n = len(seq)
    if n == 0:
        return 0
    c, i = 1, 1
    while i < n:
        l_max = 0
        for l in range(1, n - i + 1):
            sub = seq[i:i + l]
            previous = [seq[j:j + l] for j in range(0, i - l + 1)]
            if sub in previous:
                l_max = l
            else:
                break
        if i + l_max < n:
            i += l_max + 1
            c += 1
        else:
            i = n
    return c

# ---------------------------------------------------------------------------
# CA update: Conway's Life with optional asynchronous noise
def step(grid, noise=0.0):
    neighbors = (
        np.roll(grid, 1, axis=0).astype(int) +
        np.roll(grid, -1, axis=0).astype(int) +
        np.roll(grid, 1, axis=1).astype(int) +
        np.roll(grid, -1, axis=1).astype(int) +
        np.roll(grid, (1, 1), axis=(0, 1)).astype(int) +
        np.roll(grid, (1, -1), axis=(0, 1)).astype(int) +
        np.roll(grid, (-1, 1), axis=(0, 1)).astype(int) +
        np.roll(grid, (-1, -1), axis=(0, 1)).astype(int)
    )
    nxt = (neighbors == 3) | (grid & (neighbors == 2))
    if noise > 0:
        nxt = nxt ^ (np.random.rand(*grid.shape) < noise)
    return nxt

def coarse_state(grid):
    """Coarse-grain a grid into quantized block-density bytes."""
    blocks = (
        grid
        .reshape(GRID // BLOCK, BLOCK, GRID // BLOCK, BLOCK)
        .mean(axis=(1, 3))
    )
    quant = np.clip((blocks * Q).astype(int), 0, Q - 1).ravel().astype(np.uint8)
    return quant.tobytes()

def run(rho, noise, seed):
    rng = np.random.default_rng(seed)
    grid = rng.random((GRID, GRID)) < rho
    full_states = []
    coarse_states = []
    for _ in range(T):
        full_states.append(grid.ravel().astype(np.uint8).tobytes())
        coarse_states.append(coarse_state(grid))
        grid = step(grid, noise)
    full_states.append(grid.ravel().astype(np.uint8).tobytes())
    coarse_states.append(coarse_state(grid))
    return full_states, coarse_states

def spatial_lz(state_bytes):
    return lempel_ziv_complexity(state_bytes) / len(state_bytes)

def temporal_lz(state_sequence):
    return lempel_ziv_complexity(state_sequence) / len(state_sequence)

# ---------------------------------------------------------------------------
# Parameter scan
records = []
print("Running parameter scan...")
for rho in DENSITIES:
    for noise in NOISES:
        slz_vals, tlz_vals = [], []
        for r in range(REPS):
            seed = int(rho * 1e6) + int(noise * 1e4) + r * 7919
            full, coarse = run(rho, noise, seed)
            slz_vals.append(spatial_lz(full[-1]))
            tlz_vals.append(temporal_lz(coarse))
        records.append({
            'rho': rho,
            'noise': noise,
            'spatial_lz': float(np.mean(slz_vals)),
            'temporal_lz': float(np.mean(tlz_vals)),
            'spatial_lz_std': float(np.std(slz_vals)),
            'temporal_lz_std': float(np.std(tlz_vals)),
        })

rho_arr = np.array([r['rho'] for r in records])
noise_arr = np.array([r['noise'] for r in records])
slz_arr = np.array([r['spatial_lz'] for r in records])
tlz_arr = np.array([r['temporal_lz'] for r in records])

# ---------------------------------------------------------------------------
# Plotting
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# 1. Scatter in (spatial_LZ, temporal_LZ) plane, colored by noise
ax = axes[0]
sc = ax.scatter(
    slz_arr, tlz_arr, c=noise_arr, s=50 + 150 * rho_arr,
    cmap='plasma', alpha=0.8, edgecolors='k', linewidth=0.3
)
ax.set_xlabel('Normalized spatial LZ complexity')
ax.set_ylabel('Normalized temporal LZ complexity')
ax.set_title('Phase diagram in (spatial_LZ, temporal_LZ)')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
plt.colorbar(sc, ax=ax, label='post-update noise ε')
# regime annotations
ax.annotate('ordered / frozen', xy=(0.08, 0.08), fontsize=9, ha='center')
ax.annotate('critical / edge', xy=(0.35, 0.55), fontsize=9, ha='center')
ax.annotate('chaotic / noisy', xy=(0.78, 0.85), fontsize=9, ha='center')

# 2. Heatmap of temporal LZ in (rho, noise)
ax = axes[1]
Tlz_grid = tlz_arr.reshape(len(DENSITIES), len(NOISES))
im = ax.imshow(
    Tlz_grid, origin='lower', aspect='auto', cmap='viridis',
    extent=[NOISES[0], NOISES[-1], DENSITIES[0], DENSITIES[-1]]
)
ax.set_xlabel('post-update noise ε')
ax.set_ylabel('initial density ρ')
ax.set_title('Temporal LZ complexity')
plt.colorbar(im, ax=ax)

# 3. Heatmap of spatial LZ in (rho, noise)
ax = axes[2]
Slz_grid = slz_arr.reshape(len(DENSITIES), len(NOISES))
im2 = ax.imshow(
    Slz_grid, origin='lower', aspect='auto', cmap='cividis',
    extent=[NOISES[0], NOISES[-1], DENSITIES[0], DENSITIES[-1]]
)
ax.set_xlabel('post-update noise ε')
ax.set_ylabel('initial density ρ')
ax.set_title('Spatial LZ complexity')
plt.colorbar(im2, ax=ax)

fig.tight_layout()
out_png = '../../shared_agora/artifacts/ca_spatiotemporal_phase_diagram.png'
out_csv = '../../shared_agora/artifacts/ca_spatiotemporal_phase_diagram.csv'
fig.savefig(out_png, dpi=150)

# Save raw data
import csv
with open(out_csv, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=records[0].keys())
    w.writeheader()
    w.writerows(records)

print(f"Saved {out_png} and {out_csv}")
print("Summary stats:")
print(f"  spatial LZ range: [{slz_arr.min():.3f}, {slz_arr.max():.3f}]")
print(f"  temporal LZ range: [{tlz_arr.min():.3f}, {tlz_arr.max():.3f}]")
