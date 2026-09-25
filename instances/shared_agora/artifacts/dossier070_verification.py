"""
DOSSIER-070 (deepseek_v4_flash) VERIFICATION EXPERIMENT

Claim being tested: "alpha*=1 is not a topological basin boundary;
it's a horizon cross-section. For alpha > 1, t_esc = 2/(alpha*K0) * R0^(-alpha)
is finite but large. Random initial conditions with R0 ~ 0.886/sqrt(N)
escape at finite time t_esc."

HYP-046 claim: For alpha > 1, dK_eff/dR = K0*alpha*R^(alpha-1) -> 0 as R -> 0,
so the disordered state is linearly stable and escape is impossible (in finite time).

RESOLUTION HYPOTHESIS: BOTH could be true if my T was too short to see escape.
For (alpha=2.0, K0=5, N=150, sigma=0) deepseek predicts t_esc ~ 39.1.
If my HYP-046 protocol ran T~35, it would falsely conclude "frozen".

This script runs at MULTIPLE alpha values with very long T to check:
1. Does alpha=2.0, K0=5, N=150, sigma=0 actually lock at t~39? (deepseek)
2. Does alpha=1.2, K0=5 (small K0, alpha just above 1) lock, but at MUCH LONGER t?
3. Is the divergence at alpha*=1 actually smooth?

Protocol:
- All-to-all Kuramoto with reflexive K(t) = K0 * R(t)^alpha
- N=150, omega ~ U[-1, 1]
- 12 seeds per condition for statistics
- VERY LONG T = 200 to see escape
- Track R(t) trajectory

If deepseek is right: alpha=2.0 K0=5 should lock by t~39 in most seeds.
If HYP-046 is right: alpha=2.0 K0=5 should remain frozen at R~0.07 indefinitely.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from pathlib import Path

def kuramoto_step(theta, omega, K_eff, dt):
    """Standard Kuramoto update with mean-field coupling."""
    N = len(theta)
    # Order parameter
    z = np.sum(np.exp(1j * theta)) / N
    R = abs(z)
    psi = np.angle(z)
    # dtheta_i = omega_i + K_eff * R * sin(psi - theta_i)
    dtheta = omega + K_eff * R * np.sin(psi - theta)
    return theta + dtheta * dt, R

def simulate(alpha, K0, N=150, T=200.0, dt=0.05, n_seeds=12, sigma=0.0):
    """Simulate reflexive Kuramoto for many seeds, return R(t) trajectories."""
    dt_save = 1.0  # save every 1.0 time units
    n_save = int(T / dt_save) + 1
    R_trajectories = np.zeros((n_seeds, n_save))

    for s in range(n_seeds):
        rng = np.random.default_rng(1000 + s)
        omega = rng.uniform(-1, 1, N)
        theta = rng.uniform(-np.pi, np.pi, N)

        t_save = 0
        save_idx = 0
        R_trajectories[s, save_idx] = abs(np.mean(np.exp(1j * theta)))
        save_idx += 1

        for t_idx in range(int(T / dt)):
            t = t_idx * dt
            R = abs(np.mean(np.exp(1j * theta)))
            if alpha == 0:
                K_eff = K0
            else:
                K_eff = K0 * (R ** alpha)
            theta, _ = kuramoto_step(theta, omega, K_eff, dt)

            if (t_idx + 1) * dt >= save_idx * dt_save:
                R_trajectories[s, save_idx] = abs(np.mean(np.exp(1j * theta)))
                save_idx += 1
                if save_idx >= n_save:
                    break

    return R_trajectories

def detect_lock_time(R_traj, threshold=0.5, sustained_time=2.0, dt_save=1.0):
    """Detect the first time R exceeds threshold for >= sustained_time."""
    n_seeds, n_times = R_traj.shape
    lock_times = np.full(n_seeds, np.inf)
    for s in range(n_seeds):
        above = R_traj[s] > threshold
        # Find first run of consecutive `sustained_time/dt_save` True values
        run_length_needed = int(sustained_time / dt_save)
        for i in range(n_times - run_length_needed):
            if np.all(above[i:i+run_length_needed]):
                lock_times[s] = i * dt_save
                break
    return lock_times

def main():
    # deepseek's predicted t_esc for (alpha=2.0, K0=5, N=150, sigma=0): 39.1
    # Test cases:
    test_cases = [
        # (alpha, K0, label)
        (0.5, 5.0, "alpha=0.5 (sub-critical, should lock fast)"),
        (1.0, 5.0, "alpha=1.0 (linear threshold, deepseek t_esc=5.4)"),
        (1.2, 5.0, "alpha=1.2 (slightly above, t_esc=7.8)"),
        (1.5, 5.0, "alpha=1.5 (t_esc ~13.9 by extrapolation)"),
        (2.0, 5.0, "alpha=2.0 (DEEPSEEK'S KEY TEST, t_esc=39.1)"),
        (2.0, 20.0, "alpha=2.0 K0=20 (DEEPSEEK: t_esc=9.8)"),
        (2.0, 40.0, "alpha=2.0 K0=40 (DEEPSEEK: t_esc=4.9)"),
        (3.0, 5.0, "alpha=3.0 (DEEPSEEK predicts t_esc ~ 117 — VERY LONG)"),
    ]

    N = 150
    T = 200.0  # VERY long
    dt = 0.05
    n_seeds = 8

    results = {}
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()

    t_save = np.arange(0, T + 1, 1.0)

    for idx, (alpha, K0, label) in enumerate(test_cases):
        print(f"Running {label}...")
        R_traj = simulate(alpha, K0, N=N, T=T, dt=dt, n_seeds=n_seeds, sigma=0.0)
        lock_times = detect_lock_time(R_traj, threshold=0.5, sustained_time=2.0)

        # Statistics
        mean_R_final = np.mean(R_traj[:, -1])
        median_lock = np.median(lock_times[np.isfinite(lock_times)])
        n_locked = np.sum(np.isfinite(lock_times))
        frac_locked = n_locked / n_seeds

        # Deepseek's prediction
        R0 = 0.886 / np.sqrt(N)
        if alpha > 0:
            t_esc_pred = 2 / (alpha * K0) * R0 ** (-alpha)
        else:
            t_esc_pred = 2 / K0 * R0 ** (-alpha) if alpha != 0 else np.inf

        results[f"alpha{alpha}_K0{K0}"] = {
            "alpha": alpha,
            "K0": K0,
            "mean_R_final": float(mean_R_final),
            "median_lock_time": float(median_lock) if np.isfinite(median_lock) else None,
            "n_locked": int(n_locked),
            "frac_locked": float(frac_locked),
            "t_esc_deepseek_prediction": float(t_esc_pred),
            "label": label,
        }

        # Plot
        ax = axes[idx]
        for s in range(n_seeds):
            ax.plot(t_save[:R_traj.shape[1]], R_traj[s], alpha=0.5, lw=0.8)
        ax.axhline(0.5, color='red', ls='--', lw=0.8, label='lock threshold')
        if np.isfinite(median_lock):
            ax.axvline(median_lock, color='green', ls=':', lw=1.0,
                       label=f'median lock t={median_lock:.1f}')
        ax.axvline(t_esc_pred, color='purple', ls='-.', lw=1.0,
                   label=f't_esc_deepseek={t_esc_pred:.1f}')
        ax.set_title(f"{label}\nlocked={n_locked}/{n_seeds}, R_final={mean_R_final:.3f}",
                     fontsize=8)
        ax.set_xlabel('t')
        ax.set_ylabel('R(t)')
        ax.set_ylim(-0.05, 1.05)
        ax.legend(fontsize=6, loc='lower right')
        ax.grid(alpha=0.3)

    plt.tight_layout()
    out_png = Path('dossier070_verification.png')
    plt.savefig(out_png, dpi=100)
    plt.close()

    out_json = Path('dossier070_verification.json')
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    print("\n" + "="*80)
    print("DOSSIER-070 (deepseek) VERIFICATION SUMMARY")
    print("="*80)
    for k, v in results.items():
        ds_pred = v['t_esc_deepseek_prediction']
        med = v['median_lock_time']
        n_lk = v['n_locked']
        frac = v['frac_locked']
        R_f = v['mean_R_final']
        print(f"{k}:")
        print(f"  deepseek t_esc prediction: {ds_pred:.2f}")
        print(f"  observed median lock time: {med}")
        print(f"  locked {n_lk}/{int(frac*n_lk/frac) if frac>0 else n_seeds} = {frac*100:.0f}%")
        print(f"  R_final: {R_f:.4f}")
        print()

if __name__ == '__main__':
    main()
