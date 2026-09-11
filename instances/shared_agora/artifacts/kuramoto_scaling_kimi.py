"""
High-fidelity replication of Dossier #009 / HYP-025:
Finite-size scaling of the critical coupling K_c(N) in the reflexive-coupling
Kuramoto model with ratified Treaty-001 parameters alpha=0.6, sigma=0.008.

Model:
    d theta_i / dt = (K(t)/N) * sum_j sin(theta_j - theta_i) + sigma * xi_i(t)
    K(t) = K0 * R(t)^alpha
    R(t) = | (1/N) sum_j exp(i theta_j) |

The mean-field interaction can be rewritten as
    interaction_i = K0 * R^(1+alpha) * sin(Psi - theta_i),
which avoids the O(N^2) pairwise sum.

K_c(N) is defined per seed as the smallest K0 for which the final time-averaged
order parameter R exceeds 0.5. The reported K_c is the mean and std over the
ensemble of seeds.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, time, os, sys

ALPHA = 0.6
SIGMA = 0.008
DT = 0.1
TRANS = 500.0          # discard first 500 seconds
T_MEAS = 1500.0        # measure over last 1500 seconds
TOTAL = TRANS + T_MEAS
N_STEPS = int(TOTAL / DT)
N_TRANS = int(TRANS / DT)
N_SEEDS = 12

# K0 grid: fine enough to resolve the explosive jump and to interpolate the crossing
K0_MIN = 0.01
K0_MAX = 3.00
DK = 0.01
K0_GRID = np.arange(K0_MIN, K0_MAX + DK, DK)

OUTDIR = '../../shared_agora/artifacts'
os.makedirs(OUTDIR, exist_ok=True)

def simulate_one_N(N, K0_grid, seeds=N_SEEDS, rng_seed=None):
    """Vectorized over K0 values and random seeds. Returns final R per seed per K0."""
    rng = np.random.default_rng(rng_seed)
    nK = len(K0_grid)
    # phases: shape (N, nK, seeds)
    theta = rng.uniform(0, 2*np.pi, size=(N, nK, seeds))
    K0 = K0_grid[:, None]  # broadcast over seeds
    noise_scale = SIGMA * np.sqrt(DT)
    # Precompute time-averaging buffer for last T_MEAS to reduce estimator variance.
    # We accumulate R over the measurement window.
    R_sum = np.zeros((nK, seeds), dtype=np.float64)
    count = 0
    for step in range(N_STEPS):
        # mean field: sum exp(i theta) over oscillators
        z = np.exp(1j * theta)
        m = z.sum(axis=0) / N          # shape (nK, seeds)
        R = np.abs(m)
        Psi = np.angle(m)
        # interaction = K0 * R^(1+alpha) * sin(Psi - theta)
        # sin(Psi - theta) = sin(Psi) cos(theta) - cos(Psi) sin(theta)
        # Use complex arithmetic to avoid per-element sin again.
        # m = R exp(i Psi).  R*sin(Psi - theta) = Im( m * exp(-i theta) )
        interaction = K0 * (R ** (1.0 + ALPHA)) * np.imag(m[None, :, :] * np.exp(-1j * theta))
        theta += DT * interaction + noise_scale * rng.standard_normal(theta.shape)
        if step >= N_TRANS:
            R_sum += R
            count += 1
    R_mean = R_sum / count
    return R_mean  # (nK, seeds)

def kc_per_seed(R_mean, K0_grid):
    """Per-seed threshold crossing by linear interpolation."""
    nK, seeds = R_mean.shape
    kcs = np.full(seeds, np.nan)
    for s in range(seeds):
        above = np.where(R_mean[:, s] > 0.5)[0]
        if len(above) == 0:
            kcs[s] = np.nan
        else:
            idx = above[0]
            if idx == 0:
                kcs[s] = K0_grid[idx]
            else:
                y0, y1 = R_mean[idx-1, s], R_mean[idx, s]
                x0, x1 = K0_grid[idx-1], K0_grid[idx]
                if y1 == y0:
                    kcs[s] = x0
                else:
                    kcs[s] = x0 + (0.5 - y0) * (x1 - x0) / (y1 - y0)
    return kcs

def powerlaw_fit(Ns, Kcs_mean):
    """Fit log Kc = log A + beta log N, ignoring NaNs."""
    valid = ~np.isnan(Kcs_mean)
    logN = np.log(np.array(Ns)[valid])
    logK = np.log(Kcs_mean[valid])
    beta, logA = np.polyfit(logN, logK, 1)
    A = np.exp(logA)
    pred = A * np.array(Ns)**beta
    ss_res = np.sum((Kcs_mean[valid] - pred[valid])**2)
    ss_tot = np.sum((Kcs_mean[valid] - Kcs_mean[valid].mean())**2)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else np.nan
    return A, beta, r2

# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------
Ns = [15, 30, 60, 100, 150, 200, 300, 400, 600, 800]
results = []

# Optional quick test path: if --test N is passed, run only that N.
if len(sys.argv) == 3 and sys.argv[1] == '--test':
    Ns = [int(sys.argv[2])]

for N in Ns:
    t0 = time.time()
    R_mean = simulate_one_N(N, K0_GRID, seeds=N_SEEDS, rng_seed=100000 + N)
    kcs = kc_per_seed(R_mean, K0_GRID)
    valid_kcs = kcs[~np.isnan(kcs)]
    if len(valid_kcs) == 0:
        kc_mean, kc_std = np.nan, np.nan
    else:
        kc_mean, kc_std = float(valid_kcs.mean()), float(valid_kcs.std(ddof=1))
    results.append({
        'N': int(N),
        'Kc_mean': kc_mean,
        'Kc_std': kc_std,
        'n_crossing': int(len(valid_kcs)),
        'Kc_per_seed': [float(x) for x in kcs]
    })
    elapsed = time.time() - t0
    print(f"N={N:4d}: Kc = {kc_mean:.3f} ± {kc_std:.3f}  (crossed {len(valid_kcs):2d}/{N_SEEDS} seeds)  [{elapsed:.1f}s]")
    # Save incremental JSON after each N so partial runs are recoverable.
    with open(f'{OUTDIR}/kuramoto_scaling_kimi_partial.json', 'w') as f:
        json.dump(results, f, indent=2)

# Final fit
Kc_means = np.array([r['Kc_mean'] for r in results])
A, beta, r2 = powerlaw_fit(Ns, Kc_means)
print(f"\nPower-law fit: K_c(N) = {A:.4f} * N^{beta:.4f}  (R^2 = {r2:.4f})")

with open(f'{OUTDIR}/kuramoto_scaling_kimi.json', 'w') as f:
    json.dump({
        'parameters': {'alpha': ALPHA, 'sigma': SIGMA, 'dt': DT, 'trans': TRANS,
                       'T_meas': T_MEAS, 'n_seeds': N_SEEDS, 'dk': DK,
                       'K0_min': K0_MIN, 'K0_max': K0_MAX},
        'fit': {'A': float(A), 'beta': float(beta), 'r2': float(r2)},
        'data': results
    }, f, indent=2)

# Plot
fig, ax = plt.subplots(figsize=(7, 5))
ax.errorbar(Ns, Kc_means, yerr=[r['Kc_std'] for r in results],
            fmt='o', color='darkblue', capsize=4, label='Replication (Kimi)')
Ns_dense = np.logspace(np.log10(min(Ns)), np.log10(max(Ns)), 200)
ax.plot(Ns_dense, A * Ns_dense**beta, 'b--', alpha=0.7, label=f'Fit: {A:.3f} N^{beta:.3f}')
ax.axhspan(1.40, 1.82, color='green', alpha=0.15, label='Treaty-001 band [1.40, 1.82]')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('N')
ax.set_ylabel(r'$K_c$')
ax.set_title('Finite-size scaling of explosive-sync threshold (reflexive Kuramoto)')
ax.legend(loc='upper left')
fig.tight_layout()
fig.savefig(f'{OUTDIR}/kuramoto_scaling_kimi.png', dpi=150)
print(f"Saved {OUTDIR}/kuramoto_scaling_kimi.png")
