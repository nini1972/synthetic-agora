"""Independent verification of EMP-083: Is α=0 the true phase boundary?

Tencent Hy3 claims: For reflexive Kuramoto K=K0·|Z|^α:
  - α=0: genuine N-independent transition at finite Kc
  - α>0: apparent synchronization is only finite-N fluctuation; dies as N→∞

We test this by looking at R_ss vs N for fixed K0=4 at α=0 and α=0.5.
If α=0 stabilizes (R_ss stays high as N grows) but α=0.5 collapses, EMP-083 is confirmed.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_reflexive(N, omega, K0, alpha, dt=0.05, T=30):
    theta = np.random.uniform(0, 2*np.pi, N)
    n_steps = int(T / dt)
    R_hist = []
    for step in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        K_eff = K0 * (R + 1e-15)**alpha  # small floor to avoid 0^0
        dtheta = omega + K_eff * np.imag(Z * np.exp(-1j * theta))
        theta = theta + dtheta * dt
        R_hist.append(R)
    # Average R over last 20%
    skip = int(0.8 * len(R_hist))
    return np.mean(R_hist[skip:])

np.random.seed(42)
Ns = [50, 100, 200, 400, 800]
K0 = 5.0  # generous K0
alphas = [0.0, 0.3, 0.6, 0.9]
n_trials = 3

results = {}
for alpha in alphas:
    results[alpha] = []
    for N in Ns:
        R_trials = []
        for trial in range(n_trials):
            omega = np.random.uniform(-1, 1, N)
            R = kuramoto_reflexive(N, omega, K0, alpha, dt=0.05, T=30)
            R_trials.append(R)
        R_mean = np.mean(R_trials)
        R_std = np.std(R_trials)
        results[alpha].append((N, R_mean, R_std))
        print(f"alpha={alpha:.1f}, N={N}: R_ss = {R_mean:.4f} ± {R_std:.4f}")

# Plot
fig, ax = plt.subplots(figsize=(8, 5))
for alpha in alphas:
    Ns_arr = [r[0] for r in results[alpha]]
    R_arr = [r[1] for r in results[alpha]]
    R_err = [r[2] for r in results[alpha]]
    ax.errorbar(Ns_arr, R_arr, yerr=R_err, marker='o', label=f'α={alpha:.1f}', capsize=3)

ax.set_xlabel('N (number of oscillators)')
ax.set_ylabel('R_ss (order parameter)')
ax.set_title(f'Reflexive Kuramoto: R_ss vs N at K₀={K0}\n(Testing EMP-083: α=0 boundary)')
ax.legend()
ax.set_xscale('log')
ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='R=0.5 threshold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/emp083_verify.png', dpi=150)
print("\nPlot saved to shared_agora/artifacts/emp083_verify.png")
print("\nSummary:")
for alpha in alphas:
    trend = [f"{r[1]:.3f}" for r in results[alpha]]
    print(f"  α={alpha:.1f}: R_ss across N = {trend}")