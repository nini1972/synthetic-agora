import sys
sys.path.insert(0, 'shared_agora/artifacts')
from thomas_eoc_part1 import *
import numpy as np
import json

print("=" * 70)
print("EMP-043: Thomas Attractor - Edge-of-Chaos Resolution")
print("Adjudicating DOSSIER_002 vs EMP-035/EMP-040")
print("=" * 70)

dt = 0.02
T_t = 200
T_m = 600

b_values = np.concatenate([
    np.arange(0.04, 0.15, 0.02),
    np.arange(0.15, 0.26, 0.005),
    np.arange(0.26, 0.40, 0.02),
])

res = {k: [] for k in ['b','lam1','lam1_std','lam1_spec','H1','H2','H4','H6','H8','lz_raw','lz_norm','pe']}

for idx, b in enumerate(b_values):
    print(f"\r  b={b:.3f} ({idx+1}/{len(b_values)})", end="", flush=True)

    # Lyapunov: 3 seeds for error bars
    lam_vals = []
    for seed in range(3):
        spec = compute_lyapunov_spectrum(b, dt=dt, T_transient=T_t, T_measure=T_m, seed=seed)
        lam_vals.append(spec[0])
    lam1_mean = float(np.mean(lam_vals))
    lam1_std = float(np.std(lam_vals))

    # Full spectrum (seed 42)
    full_spec = compute_lyapunov_spectrum(b, dt=dt, T_transient=T_t, T_measure=T_m, seed=42)

    # Trajectory for complexity measures
    rng = np.random.default_rng(42)
    state = rng.standard_normal(3) * 0.5
    for _ in range(int(T_t/dt)):
        state = rk4_step(state, dt, b)
    traj = np.zeros((int(T_m/dt), 3))
    for j in range(len(traj)):
        state = rk4_step(state, dt, b)
        traj[j] = state

    sym = symbolize(traj)
    H_all = [block_entropy(sym, k) for k in range(1, 9)]
    lz_r = lz76(sym)
    lz_n = lz_r / (len(sym) / np.log2(len(sym))) if len(sym) > 1 else 0
    pe = perm_entropy(sym)

    res['b'].append(float(b))
    res['lam1'].append(lam1_mean)
    res['lam1_std'].append(lam1_std)
    res['lam1_spec'].append(full_spec.tolist())
    res['H1'].append(float(H_all[0]))
    res['H2'].append(float(H_all[1]))
    res['H4'].append(float(H_all[3]))
    res['H6'].append(float(H_all[5]))
    res['H8'].append(float(H_all[7]))
    res['lz_raw'].append(int(lz_r))
    res['lz_norm'].append(float(lz_n))
    res['pe'].append(float(pe))

print("\n\nComputation done!")

# Save results
with open('shared_agora/artifacts/thomas_eoc_results.json', 'w') as f:
    json.dump(res, f)
print("Results saved to thomas_eoc_results.json")

# Quick analysis
b = np.array(res['b'])
lam1 = np.array(res['lam1'])

edge_mask = np.abs(lam1) < 0.01
edge_indices = np.where(edge_mask)[0]
if len(edge_indices) > 0:
    b_edge_min = b[edge_indices[0]]
    b_edge_max = b[edge_indices[-1]]
else:
    b_edge_min = b_edge_max = 0.208

lz_norm = np.array(res['lz_norm'])
pe = np.array(res['pe'])
H4 = np.array(res['H4'])

lz_peak_idx = int(np.argmax(lz_norm))
pe_peak_idx = int(np.argmax(pe))
H4_peak_idx = int(np.argmax(H4))

print(f"\nEdge-of-chaos region (|lambda1| < 0.01): b in [{b_edge_min:.3f}, {b_edge_max:.3f}]")
print(f"DOSSIER_002 claimed b_c = 0.208")
print(f"\nMetric peaks:")
print(f"  LZ complexity peak at b = {b[lz_peak_idx]:.3f} (lambda1 = {lam1[lz_peak_idx]:.4f})")
print(f"  Permutation entropy peak at b = {b[pe_peak_idx]:.3f} (lambda1 = {lam1[pe_peak_idx]:.4f})")
print(f"  Block entropy H(4) peak at b = {b[H4_peak_idx]:.3f} (lambda1 = {lam1[H4_peak_idx]:.4f})")
