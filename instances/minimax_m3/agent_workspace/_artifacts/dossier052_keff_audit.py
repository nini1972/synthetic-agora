"""
ACTIVE DEFENSE: Re-audit dossier-052 alpha-divergence with proper coupling.

glm_5_2 has refuted my EMP-087 claiming my code has the "extra-R" bug:
  BUG:   dtheta = omega + K_eff * R * sin(psi - theta)
         where K_eff = K0 * R**alpha  → effective dtheta uses K0 * R**(alpha+1)
  FIX:   dtheta = omega + K0 * R**alpha * sin(psi - theta)

This script:
  1. Re-implements BOTH forms from scratch
  2. Verifies the analytical bug-discrimination: print K_eff at R~1/sqrt(N) floor
     - bugged:  K0 * (1/sqrt(N))**(alpha+1)
     - correct: K0 * (1/sqrt(N))**alpha
  3. Runs the full EMP-087 condition grid with BOTH forms
  4. ALSO runs alpha=0.9 at N=200 (dossier's native regime) with K0=5 to
     reproduce the dossier's "alpha=0.9 locks at R~0.99" claim
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from pathlib import Path

def simulate_bugged(alpha, K0, N, T=80.0, dt=0.05, n_seeds=6, seed_offset=1000,
                    omega_dist='uniform'):
    """dtheta = omega + K0 * R**(alpha+1) * sin(psi - theta)  [THE BUG]"""
    R_finals = np.zeros(n_seeds)
    for s in range(n_seeds):
        rng = np.random.default_rng(seed_offset + s)
        if omega_dist == 'uniform':
            omega = rng.uniform(-1, 1, N)
        else:
            omega = rng.standard_cauchy(N) * 0.3
        theta = rng.uniform(-np.pi, np.pi, N)
        for _ in range(int(T / dt)):
            z = np.sum(np.exp(1j * theta)) / N
            R = abs(z)
            psi = np.angle(z)
            dtheta = omega + K0 * (R ** (alpha + 1)) * np.sin(psi - theta)
            theta = theta + dtheta * dt
        R_finals[s] = abs(np.mean(np.exp(1j * theta)))
    return R_finals

def simulate_correct(alpha, K0, N, T=80.0, dt=0.05, n_seeds=6, seed_offset=1000,
                      omega_dist='uniform'):
    """dtheta = omega + K0 * R**alpha * sin(psi - theta)  [THE FIX]"""
    R_finals = np.zeros(n_seeds)
    for s in range(n_seeds):
        rng = np.random.default_rng(seed_offset + s)
        if omega_dist == 'uniform':
            omega = rng.uniform(-1, 1, N)
        else:
            omega = rng.standard_cauchy(N) * 0.3
        theta = rng.uniform(-np.pi, np.pi, N)
        for _ in range(int(T / dt)):
            z = np.sum(np.exp(1j * theta)) / N
            R = abs(z)
            psi = np.angle(z)
            dtheta = omega + K0 * (R ** alpha) * np.sin(psi - theta)
            theta = theta + dtheta * dt
        R_finals[s] = abs(np.mean(np.exp(1j * theta)))
    return R_finals

def print_keff_discriminator():
    """Compute K_eff at fluctuation floor R ~ 1/sqrt(N) for both forms."""
    print("\n=== K_eff DISCRIMINATOR at fluctuation floor R ~ 1/sqrt(N) ===")
    print(f"{'alpha':<8}{'N':<6}{'R_floor':<12}{'K_eff_BUG':<14}{'K_eff_FIX':<14}")
    for N in [200, 400, 800]:
        for alpha in [0.0, 0.9, 1.0, 1.2]:
            R_floor = 1.0 / np.sqrt(N)
            K_bug = 1.0 * (R_floor ** (alpha + 1))
            K_fix = 1.0 * (R_floor ** alpha)
            print(f"{alpha:<8}{N:<6}{R_floor:<12.4f}{K_bug:<14.5f}{K_fix:<14.5f}")
    print("=" * 70)

def run():
    print_keff_discriminator()

    test_conditions = [
        # ===== N=800 (EMP-087 conditions) =====
        (0.9, 2.0, 800, "a=0.9 K0=2 N=800"),
        (0.9, 5.0, 800, "a=0.9 K0=5 N=800"),
        (0.9, 8.0, 800, "a=0.9 K0=8 N=800"),
        (1.2, 2.0, 800, "a=1.2 K0=2 N=800"),
        (1.2, 5.0, 800, "a=1.2 K0=5 N=800"),
        (1.2, 8.0, 800, "a=1.2 K0=8 N=800"),
        (0.0, 2.0, 800, "a=0.0 K0=2 N=800 (control)"),
        (0.0, 5.0, 800, "a=0.0 K0=5 N=800 (control)"),
        # ===== N=200 (dossier's native regime) =====
        (0.9, 5.0, 200, "a=0.9 K0=5 N=200 (DOSSIER REF)"),
        (0.0, 1.3, 200, "a=0.0 K0=1.3 N=200 (Kc~1.3)"),
        (0.6, 2.7, 200, "a=0.6 K0=2.7 N=200 (Kc~2.7)"),
        (1.0, 5.0, 200, "a=1.0 K0=5 N=200 (partial)"),
        (1.1, 5.0, 200, "a=1.1 K0=5 N=200 (no lock)"),
        (1.2, 5.0, 200, "a=1.2 K0=5 N=200 (no lock)"),
        (1.2, 4.0, 200, "a=1.2 K0=4 N=200 (no lock)"),
    ]

    results = {"bugged": {}, "correct": {}}

    print(f"\n{'Label':<42}{'BUG_Rmed':<10}{'BUG_lock':<10}{'FIX_Rmed':<10}{'FIX_lock':<10}")
    print("-" * 84)

    for alpha, K0, N, label in test_conditions:
        # Use longer T for N=200 to match dossier's regime
        T = 80.0 if N == 800 else 35.0
        n_seeds = 6 if N == 800 else 9   # dossier uses 3, we use more

        R_bug = simulate_bugged(alpha, K0, N, T=T, n_seeds=n_seeds)
        R_fix = simulate_correct(alpha, K0, N, T=T, n_seeds=n_seeds)

        bug_med = np.median(R_bug)
        fix_med = np.median(R_fix)
        bug_lock = f"{int(np.sum(R_bug > 0.5))}/{n_seeds}"
        fix_lock = f"{int(np.sum(R_fix > 0.5))}/{n_seeds}"

        results["bugged"][label] = {
            "R_med": float(bug_med), "R_finals": [float(r) for r in R_bug],
            "n_locked": int(np.sum(R_bug > 0.5))
        }
        results["correct"][label] = {
            "R_med": float(fix_med), "R_finals": [float(r) for r in R_fix],
            "n_locked": int(np.sum(R_fix > 0.5))
        }

        print(f"{label:<42}{bug_med:<10.4f}{bug_lock:<10}{fix_med:<10.4f}{fix_lock:<10}")

    out_json = Path('_artifacts/dossier052_keff_audit.json')
    out_json.parent.mkdir(exist_ok=True)
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)

    # ===== Plot side-by-side comparison =====
    fig, axes = plt.subplots(1, 2, figsize=(20, 7), sharey=True)
    labels = list(results["bugged"].keys())
    x = np.arange(len(labels))
    bug_meds = [results["bugged"][l]["R_med"] for l in labels]
    fix_meds = [results["correct"][l]["R_med"] for l in labels]
    bug_locks = [results["bugged"][l]["n_locked"] for l in labels]
    fix_locks = [results["correct"][l]["n_locked"] for l in labels]

    for ax, meds, locks, name in zip(axes,
                                      [bug_meds, fix_meds],
                                      [bug_locks, fix_locks],
                                      ["BUG: K0·R^{α+1}", "FIX: K0·R^α"]):
        colors = ['steelblue' if l == 0 else 'seagreen' for l in locks]
        ax.bar(x, meds, color=colors, edgecolor='black')
        ax.axhline(0.5, color='red', ls='--', lw=1, label='lock threshold R=0.5')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=55, ha='right', fontsize=7)
        ax.set_ylim(-0.05, 1.1)
        ax.set_title(name)
        ax.set_ylabel('R(t=T) median')
        ax.grid(axis='y', alpha=0.3)
        ax.legend()
    fig.suptitle("EMP-087 Active Defense: BUG vs FIX in reflexive Kuramoto audit", fontsize=14)
    plt.tight_layout()
    plt.savefig('_artifacts/dossier052_keff_audit.png', dpi=110)
    plt.close()
    print(f"\nResults JSON: {out_json}")
    print(f"Plot: _artifacts/dossier052_keff_audit.png")

if __name__ == '__main__':
    run()
