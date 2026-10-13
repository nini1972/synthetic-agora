import numpy as np, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_sim(N, K, sigma_w=1.0, T=150.0, dt=0.05, n_real=10, seed_base=1000):
    """All-to-all Kuramoto with Gaussian intrinsic freqs.
    Returns (mean stationary R, mean stationary R-fluctuation std) over realizations."""
    nsteps = int(T/dt)
    warm = nsteps//3
    R_means = np.zeros(n_real)
    R_stds  = np.zeros(n_real)
    for r in range(n_real):
        rng = np.random.default_rng(seed_base + r)
        omega = rng.normal(0.0, sigma_w, N)
        theta = rng.uniform(-np.pi, np.pi, N)
        Rrun = np.empty(nsteps-warm)
        for s in range(nsteps):
            z = np.exp(1j*theta)
            Z = z.sum()
            R = abs(Z)/N
            psi = np.angle(Z)
            if s >= warm:
                Rrun[s-warm] = R
            theta = theta + (omega + K*R*np.sin(psi-theta))*dt
        R_means[r] = Rrun.mean()
        R_stds[r]  = Rrun.std()
    return R_means.mean(), R_stds.mean()

# Critical coupling for Gaussian width sigma: K_c^inf = 2*sigma/sqrt(2*pi)? verify:
# Known result: Kc = 2 sigma / sqrt(2 pi) for uniform? Actually for Gaussian density g(omega):
# Kc = 2/(pi g(0)); g(0)=1/(sigma sqrt(2pi)) => Kc = 2 sigma sqrt(2pi)/pi.
sigma = 1.0
Kc_inf = 2*sigma*np.sqrt(2*np.pi)/np.pi
print(f"Theoretical Kc(inf) for Gaussian(sigma=1) = {Kc_inf:.4f}")

Ns = [100, 200, 400, 800, 1600]
results = {}
for N in Ns:
    Ks = np.round(np.linspace(0.6, 2.4, 19), 3)
    Rs = []; stds = []
    for K in Ks:
        m, s = kuramoto_sim(N, K, sigma_w=sigma, n_real=10, seed_base=1000+N+int(K*100))
        Rs.append(m); stds.append(s)
    Rs = np.array(Rs); stds = np.array(stds)
    if np.max(Rs) > 0.5 and np.min(Rs) < 0.5:
        idx = np.where(Rs > 0.5)[0][0]
        KcN = Ks[idx-1] + (0.5-Rs[idx-1])*(Ks[idx]-Ks[idx-1])/(Rs[idx]-Rs[idx-1]) if idx>0 else Ks[idx]
    else:
        KcN = np.nan
    peak_var = np.max(stds**2)
    results[str(N)] = {'Kc_N': round(float(KcN),4) if not np.isnan(KcN) else None,
                       'R_curve': Rs.tolist(), 'K_grid': Ks.tolist(),
                       'peak_var_R': round(float(peak_var),5)}
    print(f"N={N:5d}  Kc(N)={KcN:.4f}  shift={Kc_inf-KcN:.4f}  peakVar(R)={peak_var:.5f}")

Ns_a = np.array([int(n) for n in results if results[n]['Kc_N'] is not None])
shift = np.array([Kc_inf - results[str(n)]['Kc_N'] for n in Ns_a])
logN = np.log(Ns_a); logS = np.log(shift)
gamma, b = np.polyfit(logN, logS, 1)
print(f"FIT shift ~ N^(-gamma): gamma = {-gamma:.3f}")
peakv = np.array([results[str(n)]['peak_var_R'] for n in Ns_a])
delta, bd = np.polyfit(logN, np.log(peakv), 1)
print(f"FIT peakVar(R) ~ N^(-delta): delta = {-delta:.3f}")

out = {'Kc_inf_theory': round(float(Kc_inf),4), 'results': results,
       'gamma_shift': round(float(-gamma),4), 'delta_fluct': round(float(-delta),4)}
os.makedirs('shared_agora/artifacts', exist_ok=True)
with open('shared_agora/artifacts/emp098_fss_replication.json','w') as f:
    json.dump(out, f, indent=2)

plt.figure(figsize=(11,4))
plt.subplot(1,2,1)
for N in Ns_a:
    r = results[str(N)]
    plt.plot(r['K_grid'], r['R_curve'], 'o-', label=f"N={N}", alpha=0.8)
plt.axvline(Kc_inf, color='k', ls='--', label=f'Kc(inf)={Kc_inf:.2f}')
plt.xlabel('K'); plt.ylabel('<R>'); plt.title('Kuramoto order parameter vs K'); plt.legend(fontsize=7); plt.grid(alpha=0.3)
plt.subplot(1,2,2)
plt.loglog(Ns_a, shift, 's-', label=f'shift ~ N^{-gamma:.2f}')
plt.loglog(Ns_a, peakv, '^-', label=f'peakVar ~ N^{-delta:.2f}')
plt.xlabel('N'); plt.ylabel('shift / peakVar'); plt.title('Finite-size scaling'); plt.legend(); plt.grid(True, which='both', alpha=0.3)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/emp098_fss_replication.png', dpi=130)
print("DONE")
