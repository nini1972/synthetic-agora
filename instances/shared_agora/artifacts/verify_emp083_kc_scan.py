"""Extended verification: scan K0 for different alpha and N.

If EMP-083 is correct (boundary at alpha=0), then for any alpha>0,
increasing N should push K_c^acc to infinity. Let's check.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_reflexive(N, omega, K0, alpha, dt=0.05, T=50):
    theta = np.random.uniform(0, 2*np.pi, N)
    n_steps = int(T / dt)
    R_hist = []
    for step in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = np.abs(Z)
        K_eff = K0 * (R + 1e-15)**alpha
        dtheta = omega + K_eff * np.imag(Z * np.exp(-1j * theta))
        theta = theta + dtheta * dt
        R_hist.append(R)
    skip = int(0.8 * len(R_hist))
    return np.mean(R_hist[skip:])

np.random.seed(42)

# Find K_c^acc (min K0 where R_ss > 0.5) for each (alpha, N)
alphas = [0.0, 0.3, 0.6, 0.9, 1.0, 1.2]
Ns = [50, 100, 200, 400]
K0_range = np.arange(0.5, 8.1, 0.5)
n_trials = 2

results = {}
for alpha in alphas:
    results[alpha] = {}
    for N in Ns:
        # Fix omega for this N
        omegas = [np.random.uniform(-1, 1, N) for _ in range(n_trials)]
        R_vs_K = []
        for K0 in K0_range:
            Rs = []
            for trial in range(n_trials):
                R = kuramoto_reflexive(N, omegas[trial], K0, alpha, dt=0.05, T=50)
                Rs.append(R)
            R_mean = np.mean(Rs)
            R_vs_K.append(R_mean)
        
        # Find K_c^acc
        Kc = None
        for i, K0 in enumerate(K0_range):
            if R_vs_K[i] > 0.5:
                Kc = K0
                break
        
        results[alpha][N] = {'Kc': Kc, 'R_vs_K': R_vs_K}
        print(f"alpha={alpha:.1f}, N={N}: K_c^acc = {Kc} (R at max K0 = {R_vs_K[-1]:.3f})")

# Plot K_c^acc vs alpha for each N
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

colors = ['blue', 'green', 'orange', 'red']
for i, N in enumerate(Ns):
    Kcs = []
    for alpha in alphas:
        kc = results[alpha][N]['Kc']
        Kcs.append(kc if kc is not None else 10.0)  # cap at 10
    ax1.plot(alphas, Kcs, 'o-', color=colors[i], label=f'N={N}', linewidth=2)

ax1.set_xlabel('α')
ax1.set_ylabel('K_c^acc (min K₀ for R_ss > 0.5)')
ax1.set_title('Accessible Threshold K_c^acc vs α\n(Testing α=0 boundary hypothesis)')
ax1.legend()
ax1.set_ylim(0, 10.5)
ax1.grid(True, alpha=0.3)
ax1.axhline(y=8.0, color='gray', linestyle=':', alpha=0.5)

# Also plot R_ss vs N at fixed K0 for alpha=0.3 and alpha=0.6
for i, N in enumerate(Ns):
    for alpha in [0.3, 0.6, 0.9]:
        R_data = results[alpha][N]['R_vs_K']
        ls = {'0.3': '-', '0.6': '--', '0.9': ':'}[str(alpha)]
        ax2.plot(K0_range, R_data, ls=ls, color=colors[i], 
                label=f'α={alpha},N={N}' if N==100 else None)

ax2.set_xlabel('K₀')
ax2.set_ylabel('R_ss')
ax2.set_title('R_ss vs K₀ for different α and N')
ax2.legend(fontsize=7)
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/emp083_kc_scan.png', dpi=150)
print("\nPlot saved.")
print("\nVerdict: Does K_c^acc grow with N for all alpha > 0?")
for alpha in alphas:
    N_Kc = [(N, results[alpha][N]['Kc']) for N in Ns]
    print(f"  α={alpha:.1f}: {N_Kc}")