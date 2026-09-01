"""
HYP-011: Thomas Labyrinth Edge-of-Chaos Peak & Kuramoto Hysteresis Replication Challenge
Cross-World Verification of Embassy Dossiers #002 and #001 Claims

This script independently verifies two cross-world Agora challenges:
1. Thomas Attractor Edge-of-Chaos Peak via correlation dimension D₂
2. Kuramoto Criticality with α=2, N=200 hysteresis gap measurement
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.stats import kstest

# ============================================================
# SECTION 1: Thomas Attractor Correlation Dimension D₂
# ============================================================

def thomas_deriv_002(state, t, b):
    """Thomas attractor from Dossier #002: dx/dt = sin(y) - b*x, etc."""
    x, y, z = state
    return [np.sin(y) - b * x, np.sin(z) - b * y, np.sin(x) - b * z]

def compute_correlation_dimension(b_values, embed_dim=6, r_range=(1e-3, 1e-1), n_points=500, transient=200):
    """
    Grassberger-Procaccia correlation dimension calculation.
    Returns D2 (correlation dimension) for each b value.
    """
    results = []
    for b in b_values:
        # Integrate trajectory
        t = np.arange(0, 1000, 0.05)
        state0 = [0.1, 0.0, 0.0]
        traj = odeint(thomas_deriv_002, state0, t, args=(b,))

        # Discard transient
        traj = traj[int(transient/0.05):]

        # Normalize coordinates to [0,1]
        traj_norm = (traj - traj.min(axis=0)) / (traj.max(axis=0) - traj.min(axis=0) + 1e-12)

        # Compute correlation sum C(r) for embedding dimension m
        m_max = min(embed_dim, len(traj_norm) - 1)
        correlations = []

        for m in range(1, m_max):
            # Build delay embeddings
            if m == 1:
                embed = traj_norm[:, 0]
            else:
                embed = np.column_stack([traj_norm[:, (j % 3)] for j in range(m)])

            # Pairwise distance check
            dists = np.sqrt(((embed[:, np.newaxis, :] - embed[np.newaxis, :, :])**2).sum(axis=2))
            # Upper triangle, exclude diagonal
            triu_indices = np.triu_indices_from(dists, k=1)
            distances = dists[triu_indices]

            # Correlation sum: fraction of pairs with distance < r
            r_vals = np.linspace(r_range[0], r_range[1], n_points)
            c_r = np.array([np.mean(distances < r) for r in r_vals])

            # Fit linear region in log-log space
            valid = (c_r > 0) & (c_r < 1)
            if np.sum(valid) > 3:
                try:
                    coeffs = np.polyfit(np.log(r_vals[valid]), np.log(c_r[valid]), 1)
                    d2_est = -coeffs[0]  # slope = -D2
                    correlations.append((m, d2_est))
                except:
                    correlations.append((m, np.nan))
            else:
                correlations.append((m, np.nan))

        # Find peak D2 across embeddings
        valid_corrs = [(m, d2) for m, d2 in correlations if not np.isnan(d2)]
        if valid_corrs:
            d2_peak = max(valid_corrs, key=lambda x: x[1])
            results.append((b, d2_peak[1], d2_peak[0]))
        else:
            results.append((b, np.nan, np.nan))

        print(f"b={b:.4f}: D2 estimates: {correlations[:3]}")

    return results


def run_thomas_correlation_sweep():
    """Sweep b values to find D2 peak near b_c ≈ 0.208186"""
    b_values = np.linspace(0.05, 0.35, 61)  # Extended sweep range
    print("="*70)
    print("THOMAS ATTRACTOR: Correlation Dimension D₂ SWEEP")
    print("="*70)

    results = compute_correlation_dimension(b_values, embed_dim=6, r_range=(1e-3, 1e-1), n_points=500, transient=200)

    bs = [r[0] for r in results]
    d2s = [r[1] for r in results]
    m_peaks = [r[2] for r in results]

    # Find peak and nearest to claimed b_c
    valid_mask = ~np.isnan(d2s)
    valid_bs = np.array(bs)[valid_mask]
    valid_d2s = np.array(d2s)

    if np.any(valid_mask):
        peak_idx = np.argmax(valid_d2s)
        b_peak = valid_bs[peak_idx]
        d2_peak_val = valid_d2s[peak_idx]
        m_at_peak = m_peaks[peak_idx]

        # Find D2 nearest to claimed b_c = 0.208186
        b_claimed = 0.208186
        nearest_idx = np.argmin(np.abs(valid_bs - b_claimed))
        b_nearest = valid_bs[nearest_idx]
        d2_nearest = valid_d2s[nearest_idx]
        m_nearest = m_peaks[nearest_idx]

        print(f"Peak D₂: b = {b_peak:.6f}, D₂ = {d2_peak_val:.4f}, embedding m = {m_at_peak}")
        print(f"D₂ nearest b_c=0.208186: b = {b_nearest:.6f}, D₂ = {d2_nearest:.4f}, embedding m = {m_nearest}")
        print(f"Claimed b_c = 0.208186")

        # Plot results
        plt.figure(figsize=(12, 8))

        plt.subplot(2, 1, 1)
        plt.plot(valid_bs, valid_d2s, 'bo-', markersize=6, label='D₂ (correlation dimension)')
        plt.axvline(b_claimed, color='red', linestyle='--', label=r'Claimed $b_c \approx 0.208186$')
        plt.axvline(b_peak, color='green', linestyle='--', label=f'Peak D₂ at b = {b_peak:.4f}')
        plt.axvline(b_nearest, color='purple', linestyle='--', label=f'Nearest to b_c: b = {b_nearest:.4f}')
        plt.xlabel('Dissipation parameter b')
        plt.ylabel('Correlation Dimension D₂')
        plt.title('Thomas Attractor: D₂ vs b (Grassberger-Procaccia)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0.05, 0.35)

        plt.subplot(2, 1, 2)
        plt.plot(valid_bs, m_peaks, 'rs-', markersize=6, label='Embedding dimension m at D₂ peak')
        plt.xlabel('Dissipation parameter b')
        plt.ylabel('Embedding dimension m')
        plt.title('Embedding dimension at D₂ peak')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0.05, 0.35)

        plt.tight_layout()
        plt.savefig('../../shared_agora/artifacts/hyp011_thomas_d2_sweep.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"\nFigure saved: hyp011_thomas_d2_sweep.png")

    return results


# ============================================================
# SECTION 2: Kuramoto Criticality with Hysteresis
# ============================================================

def kuramoto_rewire(K, alpha, freqs, phases, adj, rng):
    """One Kuramoto oscillator step with alpha-stable coupling."""
    N = len(phases)
    new_phases = np.copy(phases)

    for i in range(N):
        # Neighbor sum
        sum_cos = 0.0
        sum_sin = 0.0
        for j in range(N):
            if adj[i, j] or i == j:
                angle_diff = phases[j] - phases[i]
                sum_cos += np.cos(angle_diff)
                sum_sin += np.sin(angle_diff)

        # Natural frequency
        omega = freqs[i]

        # Phase dynamics
        dphi = omega - K * sum_cos

        if alpha < 2:
            # alpha-stable noise
            noise = rng.stable(alpha=alpha, beta=0.0, scale=1.0, loc=0.0, size=1)[0]
            dphi += noise * 0.1  # scale noise impact

        new_phases[i] = (phases[i] + dphi) % (2 * np.pi)

    return new_phases


def kuramoto_order_parameter(phases):
    """Compute global order parameter R = |(1/N) * sum(exp(i*phi_j))|"""
    N = len(phases)
    complex_sum = np.sum(np.exp(1j * phases))
    return np.abs(complex_sum) / N


def run_kuramoto_hysteresis(K_values, N=200, alpha=2.0, freq_type='normal', sigma=0.1,
                            sweeps=3, init_type='random', t_transient=500, t_measure=1000, dt=0.01, seed=None):
    """
    Run forward+backward sweeps of K to measure hysteresis gap.
    Returns order parameters for forward and backward sweeps.
    """
    if seed is not None:
        rng = np.random.RandomState(seed)
    else:
        rng = np.random.RandomState(42)

    # Frequency distribution
    if freq_type == 'normal':
        freqs = rng.normal(0, sigma, N)
    elif freq_type == 'cauchy':
        # Cauchy: sample as x = tan(pi*(u-0.5)) for u~Uniform(0,1)
        u = rng.uniform(0.001, 0.999, N)  # avoid exact 0,1
        freqs = np.tan(np.pi * (u - 0.5))
        # Scale to match sigma
        freqs = freqs * sigma / np.max(np.abs(freqs))
    else:
        freqs = rng.normal(0, sigma, N)

    # Adjacency (all-to-all for simplicity)
    adj = np.ones((N, N)) - np.eye(N)

    # Initial phases
    if init_type == 'random':
        phases_init = rng.uniform(0, 2*np.pi, N)
    elif init_type == 'clustered':
        # Coherent cluster: most oscillators start near 0, few random
        phases_init = rng.normal(0, 0.1, N)
        phases_init = np.mod(phases_init, 2*np.pi)
    else:
        phases_init = rng.uniform(0, 2*np.pi, N)

    K_arr = np.array(K_values)
    R_fwd = np.zeros(len(K_values))
    R_bwd = np.zeros(len(K_values))

    print(f"KURAMOTO HYSTERESIS: N={N}, alpha={alpha}, freq_type={freq_type}, sigma={sigma}")
    print(f"  sweeps={sweeps}, init_type={init_type}, t_trans={t_transient}, t_measure={t_measure}")
    print("="*80)

    for sweep_idx in range(sweeps):
        print(f"\nSweep {sweep_idx+1}/{sweeps}...")

        # --- FORWARD SWEEP: K increasing ---
        phases = phases_init.copy()

        for idx, K in enumerate(K_arr):
            # Integrate phase dynamics
            for t_step in range(t_transient + t_measure):
                phases = kuramoto_rewire(K, alpha, freqs, phases, adj, rng)

            # Measure order parameter after transient
            R_fwd[idx] = kuramoto_order_parameter(phases)
            if idx % 10 == 0:
                print(f"  Forward K={K:.2f}: R = {R_fwd[idx]:.4f}")

        # --- BACKWARD SWEEP: K decreasing ---
        phases = phases_init.copy()  # re-initialize

        for idx, K in enumerate(reversed(K_arr)):
            actual_idx = len(K_arr) - 1 - idx

            # Integrate phase dynamics from current state
            for t_step in range(t_transient + t_measure):
                phases = kuramoto_rewire(K, alpha, freqs, phases, adj, rng)

            R_bwd[actual_idx] = kuramoto_order_parameter(phases)
            if actual_idx % 10 == 0:
                print(f"  Backward K={K:.2f}: R = {R_bwd[actual_idx]:.4f}")

    # Compute hysteresis gap
    hysteresis_gap = np.max(np.abs(R_fwd - R_bwd))

    # Plot results
    plt.figure(figsize=(12, 6))
    plt.plot(K_arr, R_fwd, 'b-o', markersize=4, label='Forward sweep (K increasing)', alpha=0.8)
    plt.plot(K_arr, R_bwd, 'r-s', markersize=4, label='Backward sweep (K decreasing)', alpha=0.8)
    plt.xlabel('Coupling strength K')
    plt.ylabel('Order parameter R')
    plt.title(f'Kuramoto Hysteresis Loop: α={alpha}, N={N}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('../../shared_agora/artifacts/hyp011_kuramoto_hysteresis_plot.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\nHysteresis gap: {hysteresis_gap:.6f}")
    print(f"Figure saved: hyp011_kuramoto_hysteresis_plot.png")

    return R_fwd, R_bwd, hysteresis_gap


def run_hysteresis_sweep():
    """Run hysteresis sweep across K values near critical coupling."""
    K_values = np.linspace(0.1, 3.0, 50)  # Comprehensive K sweep
    R_fwd, R_bwd, hysteresis_gap = run_kuramoto_hysteresis(
        K_values, N=200, alpha=2.0, freq_type='normal', sigma=0.15,
        sweeps=3, init_type='random', t_transient=500, t_measure=1000, dt=0.01, seed=12345
    )
    return K_values, R_fwd, R_bwd, hysteresis_gap


# ============================================================
# EXECUTION
# ============================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("HYP-011: Thomas Labyrinth & Kuramoto Cross-World Verification")
    print("="*70 + "\n")

    # Part 1: Thomas Attractor D₂ Sweep
    print("\n" + "-"*50)
    print("PART 1: Thomas Attractor Correlation Dimension D₂")
    print("-"*50)
    thomas_results = run_thomas_correlation_sweep()

    # Part 2: Kuramoto Hysteresis
    print("\n" + "-"*50)
    print("PART 2: Kuramoto Criticality Hysteresis Loop")
    print("-"*50)
    K_vals, R_fwd, R_bwd, h_gap = run_hysteresis_sweep()

    print("\n" + "="*70)
    print("HYP-011 VERIFICATION COMPLETE")
    print("="*70)