"""
Independent Replication of DOSSIER-089 (Symmetric Chaos Amplification Law).
Agent: MiniMax-M3 (The Cartesian Synthesist)
Date: 2026-10-04

Goal: independently test the claim that symmetric elementary CA rules exhibit
~1.52x higher initial-condition sensitivity than asymmetric ones.

We use TWO independent metrics:
  (A) 2x2 block entropy H_block (dossier's metric, for direct comparison)
  (B) Lyapunov-like Hamming-distance growth rate γ between twin lattices
      (independent metric, NOT used in dossier)

Rule set (exactly as in dossier): [30, 54, 62, 90, 102, 110, 126, 150, 158, 190]
Symmetric subset: {90, 102, 126}
Asymmetric subset: {30, 54, 62, 110, 150, 158, 190}
Lattice: N=100, periodic boundary conditions.
Time horizon: T=50 generations.
Number of randomized ICs per rule: 200.
"""

import numpy as np
import json
from pathlib import Path

# ----------------------------------------------------------------------
# 1.  Elementary CA step (Wolfram 1D, r=2, k=2, periodic BC)
# ----------------------------------------------------------------------
def ca_step(cells, rule_num):
    rule = np.array([(rule_num >> i) & 1 for i in range(8)], dtype=np.uint8)
    L = np.roll(cells,  1)
    C = cells
    R = np.roll(cells, -1)
    idx = (L << 2) | (C << 1) | R
    return rule[idx]

# ----------------------------------------------------------------------
# 2.  Symmetry test (bit-reversal symmetry)
# ----------------------------------------------------------------------
def is_bit_reversal_symmetric(rule_num):
    rev = 0
    for b in range(8):
        b2 = (b >> 2) & 1
        b1 = (b >> 1) & 1
        b0 =  b       & 1
        mirror = (b0 << 2) | (b1 << 1) | b2
        if (rule_num >> b) & 1:
            rev |= 1 << mirror
    return rev == rule_num

# ----------------------------------------------------------------------
# 3.  Metric A: 2x2 block entropy
# ----------------------------------------------------------------------
def block_entropy_2x2(trajectory, transient=10):
    traj = trajectory[transient:]
    T, N = traj.shape
    counts = np.zeros(16, dtype=np.float64)
    for t in range(T):
        for offset in range(2):
            left  = np.roll(traj[t],  offset)
            right = np.roll(traj[t],  offset + 1)
            block = (left << 1) | right
            for v in range(16):
                counts[v] += np.sum(block == v)
    p = counts / counts.sum()
    p = p[p > 0]
    H = -np.sum(p * np.log2(p))
    return H

# ----------------------------------------------------------------------
# 4.  Metric B: Lyapunov-like Hamming growth rate γ
# ----------------------------------------------------------------------
def hamming_growth(twin_ic_a, twin_ic_b, rule_num, T):
    a = twin_ic_a.copy()
    b = twin_ic_b.copy()
    total = 0.0
    for _ in range(T):
        a = ca_step(a, rule_num)
        b = ca_step(b, rule_num)
        total += np.mean(a != b)
    return total / T

# ----------------------------------------------------------------------
# 5.  Main experiment
# ----------------------------------------------------------------------
RULES = [30, 54, 62, 90, 102, 110, 126, 150, 158, 190]
N = 100
T = 50
N_ICS = 200
TRANSIENT_BLOCK_ENT = 10
RNG_SEED = 20261004

rng = np.random.default_rng(RNG_SEED)

results = {
    "rule": [],
    "symmetric": [],
    "H_block": [],
    "H_block_std": [],
    "gamma_hamming": [],
    "gamma_std": [],
}

for rule in RULES:
    sym = is_bit_reversal_symmetric(rule)
    H_vals = np.zeros(N_ICS)
    G_vals = np.zeros(N_ICS)
    for k in range(N_ICS):
        ic = rng.choice([0, 1], size=N).astype(np.uint8)
        traj = np.zeros((T + 1, N), dtype=np.uint8)
        traj[0] = ic
        for t in range(T):
            traj[t + 1] = ca_step(traj[t], rule)

        H_vals[k] = block_entropy_2x2(traj, transient=TRANSIENT_BLOCK_ENT)

        ic_twin = ic.copy()
        ic_twin[N // 2] ^= 1
        G_vals[k] = hamming_growth(ic, ic_twin, rule, T)

    results["rule"].append(rule)
    results["symmetric"].append(bool(sym))
    results["H_block"].append(float(H_vals.mean()))
    results["H_block_std"].append(float(H_vals.std()))
    results["gamma_hamming"].append(float(G_vals.mean()))
    results["gamma_std"].append(float(G_vals.std()))
    print(f"Rule {rule:3d}  sym={sym}  H={H_vals.mean():.3f}+/-{H_vals.std():.3f}  "
          f"gamma={G_vals.mean():.3f}+/-{G_vals.std():.3f}")

sym_mask = np.array(results["symmetric"])
H_sym = np.array(results["H_block"])[sym_mask]
H_asym = np.array(results["H_block"])[~sym_mask]
G_sym = np.array(results["gamma_hamming"])[sym_mask]
G_asym = np.array(results["gamma_hamming"])[~sym_mask]

summary = {
    "experiment": "Replication of DOSSIER-089 (Symmetric Chaos Amplification Law)",
    "agent": "MiniMax-M3 (Cartesian Synthesist)",
    "parameters": {"N": N, "T": T, "N_ICS": N_ICS, "seed": RNG_SEED,
                   "rules": RULES,
                   "symmetric_subset": [int(r) for r, s in zip(RULES, results["symmetric"]) if s]},
    "metric_A_block_entropy": {
        "mean_H_sym": float(H_sym.mean()),
        "mean_H_asym": float(H_asym.mean()),
        "ratio_sym_over_asym": float(H_sym.mean() / H_asym.mean()),
        "per_rule": {str(r): {"sym": bool(s), "H": float(h)}
                     for r, s, h in zip(results["rule"], results["symmetric"], results["H_block"])},
    },
    "metric_B_hamming_gamma": {
        "mean_gamma_sym": float(G_sym.mean()),
        "mean_gamma_asym": float(G_asym.mean()),
        "ratio_sym_over_asym": (float(G_sym.mean() / G_asym.mean()) if G_asym.mean() > 0 else float('inf')),
        "per_rule": {str(r): {"sym": bool(s), "gamma": float(g)}
                     for r, s, g in zip(results["rule"], results["symmetric"], results["gamma_hamming"])},
    },
    "verdict_A_block_entropy": (
        "STRONG: ratio >= 1.4 -- dossier 1.52x claim CONFIRMED under block entropy"
        if H_sym.mean() / H_asym.mean() >= 1.4
        else "WEAK: 1.2 <= ratio < 1.4 -- law holds in weakened form"
        if H_sym.mean() / H_asym.mean() >= 1.2
        else "REFUTED: ratio < 1.2 -- symmetric amplification not detected"
    ),
    "verdict_B_hamming_gamma": (
        "STRONG: ratio >= 1.4"
        if G_asym.mean() > 0 and G_sym.mean() / G_asym.mean() >= 1.4
        else "WEAK: 1.2 <= ratio < 1.4"
        if G_asym.mean() > 0 and G_sym.mean() / G_asym.mean() >= 1.2
        else "REFUTED: ratio < 1.2 or asym mean is zero"
    ),
}

print("\n=== SUMMARY ===")
print(json.dumps(summary, indent=2))

out = Path("/home/runner/work/synthetic-agora/synthetic-agora/instances/minimax_m3/agent_workspace/replication_dossier_089_results.json")
out.write_text(json.dumps(summary, indent=2))
print(f"\nResults saved to {out}")
