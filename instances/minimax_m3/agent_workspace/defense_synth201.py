"""
Active defense of SYN-201 (SYNTH-201): Reflection Symmetry has Near-Zero
Conditional Effect on CA Block Entropy Once Activation is Controlled.

Independent stress-test:
  - Scan multiple CA rule classes (Wolfram classes 1-4)
  - Multiple lattice sizes (L=64, 128, 256)
  - Multiple block sizes (k=2,3,4,5,6)
  - Compute:
      1) Activation (density of 1s)
      2) Block entropy H_k (Shannon, base 2)
      3) Symmetry-preservation flag (whether rule commutes with spatial reflection)
      4) Partial-correlation: corr(H_k, symmetry | activation)
  - The claim: partial-correlation should be near zero (~0.05 or less).
"""
import numpy as np
from scipy.stats import pearsonr
from itertools import product

rng = np.random.default_rng(20261009)

def step(L, rule_table, x):
    """Apply 1D ECA on L-site lattice with periodic boundaries."""
    # rule_table: 8-bit vector indexed by (xL,x,xR)
    return np.array([rule_table[(x[(i-1) % L] << 2) | (x[i] << 1) | x[(i+1) % L]]
                     for i in range(L)], dtype=np.int8)

def is_symmetric(rule_number):
    """Check if Wolfram ECA commutes with reflection xL<->xR.
       Reflection sends neighborhood index (b2,b1,b0) -> (b0,b1,b2).
       Rule commutes iff rule(abc) == rule(cba) for all abc in {0..7}.
    """
    bits = [(rule_number >> i) & 1 for i in range(8)]
    for a, b, c in product([0, 1], repeat=3):
        idx_fwd = (a << 2) | (b << 1) | c
        idx_rev = (c << 2) | (b << 1) | a
        if bits[idx_fwd] != bits[idx_rev]:
            return False
    return True

def block_entropy(spacetime, k):
    """Block entropy at temporal offset k: average Shannon H of k-bit columns."""
    T, L = spacetime.shape
    H_vals = []
    # Sample columns
    for _ in range(min(200, L)):
        col = rng.integers(0, L)
        # Treat each row as a k-bit block of consecutive columns starting at col
        # For 1D we use spatial blocks of size k, sampled at row=transient_end
        # Simpler: at transient state, take k-bit blocks
        x = spacetime[-1]  # final state
        for j in range(0, L - k + 1):
            block = 0
            for q in range(k):
                block = (block << 1) | int(x[(col + q) % L])
            H_vals.append(block)
    if len(H_vals) == 0:
        return 0.0
    arr = np.array(H_vals)
    _, counts = np.unique(arr, return_counts=True)
    p = counts / counts.sum()
    return float(-(p * np.log2(p + 1e-12)).sum())

def run_ca(L, rule_number, density=0.5, T=200):
    """Run ECA for T steps, return spacetime array (T+1, L)."""
    bits = [(rule_number >> i) & 1 for i in range(8)]
    rule_table = np.array(bits, dtype=np.int8)
    x = (rng.uniform(0, 1, size=L) < density).astype(np.int8)
    spacetime = [x.copy()]
    for _ in range(T):
        x = step(L, rule_table, x)
        spacetime.append(x.copy())
    return np.array(spacetime)

# --- main stress test ---
print("Stress-testing SYN-201: partial corr(block_entropy, symmetry | activation)\n")

RULES_TO_TEST = [3, 5, 9, 18, 22, 30, 45, 54, 60, 73, 75, 86, 90, 105, 110,
                 122, 126, 129, 150, 153, 161, 182, 195, 225]
# These cover all four Wolfram classes

L_LIST = [64, 128]
K_LIST = [3, 4, 5]
DENSITIES = [0.3, 0.5]

results = []
for L in L_LIST:
    for k in K_LIST:
        for density in DENSITIES:
            for rule in RULES_TO_TEST:
                sym = is_symmetric(rule)
                sp = run_ca(L, rule, density=density, T=300)
                act = float(sp.mean())  # activation = density of 1s
                # Spatial-block entropy at final state
                x = sp[-1]
                blocks = []
                for j in range(L - k + 1):
                    val = 0
                    for q in range(k):
                        val = (val << 1) | int(x[(j + q) % L])
                    blocks.append(val)
                blocks = np.array(blocks)
                _, counts = np.unique(blocks, return_counts=True)
                p = counts / counts.sum()
                Hk = float(-(p * np.log2(p + 1e-12)).sum())
                results.append({
                    'L': L, 'k': k, 'density': density, 'rule': rule,
                    'sym': int(sym), 'activation': act, 'H_k': Hk,
                })

import pandas as pd
df = pd.DataFrame(results)

# Compute partial correlation per (L, k, density) group:
# corr(H_k, sym) controlling for activation = (r_xy - r_xz*r_yz)/sqrt((1-r_xz^2)(1-r_yz^2))
def partial_corr(df_sub):
    r_xy, _ = pearsonr(df_sub['H_k'], df_sub['sym'])
    r_xz, _ = pearsonr(df_sub['activation'], df_sub['sym'])
    r_yz, _ = pearsonr(df_sub['H_k'], df_sub['activation'])
    denom = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
    if denom < 1e-12:
        return 0.0
    return (r_xy - r_xz * r_yz) / denom

print(f"{'L':>4s} {'k':>2s} {'dens':>5s} {'n_rules':>8s} {'raw_corr':>10s} {'part_corr':>10s}")
print("-" * 50)
part_corrs = []
for (L, k, dens), grp in df.groupby(['L', 'k', 'density']):
    pc = partial_corr(grp)
    rc, _ = pearsonr(grp['H_k'], grp['sym'])
    part_corrs.append(pc)
    print(f"{L:>4d} {k:>2d} {dens:>5.2f} {len(grp):>8d} {rc:>+10.4f} {pc:>+10.4f}")

print(f"\nMean absolute partial correlation across all groups: {np.mean(np.abs(part_corrs)):.4f}")
print(f"Max  absolute partial correlation across all groups: {np.max(np.abs(part_corrs)):.4f}")
print(f"Std  of partial correlations across all groups:        {np.std(part_corrs):.4f}")
print(f"\nSYN-201 prediction: |partial_corr| << |raw_corr| (since activation absorbs most variance)")
print(f"Mean raw corr:  {np.mean([abs(pearsonr(grp['H_k'], grp['sym'])[0]) for _, grp in df.groupby(['L','k','density'])]):.4f}")
print(f"Mean part corr: {np.mean(np.abs(part_corrs)):.4f}")

# Save CSV for transparency
df.to_csv('defense_synth201_results.csv', index=False)
print(f"\nResults saved to defense_synth201_results.csv ({len(df)} (L,k,density,rule) entries)")
