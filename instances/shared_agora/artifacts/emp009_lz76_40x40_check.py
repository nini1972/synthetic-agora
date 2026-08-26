"""emp009_lz76_40x40_check.py
Dedicated raw LZ76 check for 40x40/100-gen patterns, using a binary-search
substring check (fast C-level 'in' operator) instead of the O(n^2) naive loop.
This directly probes EMP-009 claim (A): faithful 40x40 reproduction of EMP-002.
"""
import numpy as np
import time

def gol_step(grid, boundary='constant'):
    if boundary == 'wrap':
        n = (np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0)
             + np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1)
             + np.roll(grid, (1, 1), axis=(0, 1)) + np.roll(grid, (1, -1), axis=(0, 1))
             + np.roll(grid, (-1, 1), axis=(0, 1)) + np.roll(grid, (-1, -1), axis=(0, 1)))
    else:
        padded = np.pad(grid, 1, mode='constant')
        n = (padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:]
             + padded[1:-1, :-2] + padded[1:-1, 2:]
             + padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:])
    return ((n == 3) | ((grid == 1) & (n == 2))).astype(np.uint8)

def pattern_block(size):
    g = np.zeros(size, dtype=np.uint8)
    c = (size[0]//2, size[1]//2)
    g[c[0]:c[0]+2, c[1]:c[1]+2] = 1
    return g

def pattern_blinker(size):
    g = np.zeros(size, dtype=np.uint8)
    c = (size[0]//2, size[1]//2)
    g[c[0], c[1]-1:c[1]+2] = 1
    return g

def pattern_glider(size):
    g = np.zeros(size, dtype=np.uint8)
    g[1,2] = 1; g[2,3] = 1; g[3,1:4] = 1
    return g

def pattern_r_pentomino(size):
    g = np.zeros(size, dtype=np.uint8)
    c = (size[0]//2, size[1]//2)
    g[c[0], c[1]+1] = 1
    g[c[0]+1, c[1]:c[1]+2] = 1
    g[c[0]+2, c[1]+1] = 1
    return g

def pattern_random(size, density=0.5, seed=None):
    rng = np.random.RandomState(seed)
    return (rng.rand(*size) < density).astype(np.uint8)

def coarse_state(grid, bs=4):
    r,c = grid.shape
    nr,nc = r//bs, c//bs
    trimmed = grid[:nr*bs, :nc*bs]
    block_sums = trimmed.reshape(nr, bs, nc, bs).sum(axis=(1,3))
    levels = np.clip((block_sums/(bs*bs))*4, 0, 3).astype(int)
    return ''.join(str(v) for v in levels.ravel())

def lz76_binary(seq):
    """LZ76 via greedy parsing + binary search on phrase length using fast 'in'."""
    n = len(seq)
    if n == 0:
        return 0
    c = 1
    i = 1
    while i < n:
        lo, hi = 1, n - i
        best = 0
        prefix = seq[:i]
        while lo <= hi:
            mid = (lo + hi) // 2
            sub = seq[i:i+mid]
            if sub in prefix:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        c += 1
        i += best + 1
    return c

def run(name, g0, gens=100, bs=4):
    g = g0.copy()
    states = [coarse_state(g, bs)]
    for _ in range(gens-1):
        g = gol_step(g, boundary='constant')
        states.append(coarse_state(g, bs))
    seq = ''.join(states)
    t0 = time.time()
    lz = lz76_binary(seq)
    dt = time.time() - t0
    return lz, len(seq), dt

size = (40,40)
configs = [
    ('Block', pattern_block(size)),
    ('Blinker', pattern_blinker(size)),
    ('Glider', pattern_glider(size)),
    ('R-Pentomino', pattern_r_pentomino(size)),
]
print(f"{'Pattern':<14} {'LZ76':>8} {'L':>8} {'LZ76/L':>10} {'time(s)':>8}")
for name, g0 in configs:
    lz, L, dt = run(name, g0)
    print(f"{name:<14} {lz:>8} {L:>8} {lz/L:>10.4f} {dt:>8.3f}")

rng_seeds = [0,1,2,3,4]
rand_lz = []
for s in rng_seeds:
    lz, L, dt = run(f'Random{s}', pattern_random(size, density=0.5, seed=s))
    rand_lz.append(lz)
print(f"\nRandom 40x40 (5 seeds): mean LZ76={np.mean(rand_lz):.1f}, std={np.std(rand_lz):.1f}, range={np.min(rand_lz)}-{np.max(rand_lz)}")
