import numpy as np, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_sim_vec(N, K, sigma_w=1.0, T=40.0, dt=0.1, n_real=8, seed=1000):
    """Vectorized over n_real realizations; returns (mean R, mean std(R)) in stationary window."""
    nsteps = int(T/dt); warm = nsteps//3
    rng = np.random.default_rng(seed)
    omega = rng.normal(0.0, sigma_w, (n_real, N))
    theta = rng.uniform(-np.pi, np.pi, (n_real, N))
    R_means = np.empty(nsteps-warm); R_stds = np.empty(nsteps-warm)
    for s in range(nsteps):
        z = np.exp(1j*theta)
        Z = z.sum(axis=1)
        Rmag = np.abs(Z)/N
        psi = np.angle(Z)
        if s >= warm:
            R_means[s-warm] = Rmag.mean()
            R_stds[s-warm]  = Rmag.std()
        theta = theta + (omega + Rmag[:,None]*K*np.sin(psi[:,None]-theta))*dt
    return R_means.mean(), R_stds.mean()

sigma = 1.0
Kc_inf = 2*sigma*np.sqrt(2*np.pi)/np.pi
print(f"Theoretical Kc(inf) for Gaussian(sigma=1) = {Kc_inf:.4f}")

Ns = [100, 200, 400, 800]
Ks = np.round(np.linspace(1.0, 2.2, 13), 3)
results = {}
for N in Ns:
    Rs = []; stds = []
    for j,K in enumerate(Ks):
        m, s = kuramoto_sim_vec(N, K, sigma_w=sigma, n_real=8, seed=1000+N*100+j)
        Rs.append(m); stds.append(s)
    Rs = np.array(Rs); stds = np.array(stds)
    if np.max(Rs) > 0.5 and np.min(Rs) < 0.5:
        idx = int(np.where(Rs > 0.5)[0][0])
        KcN = Ks[idx-1] + (0.5-Rs[idx-1])*(Ks[idx]-Ks[idx-1])/(Rs[idx]-Rs[idx-1]) if idx>0 else Ks[idx]
    else:
        KcN = np.nan
    peak_var = float(np.max(stds**2))
    results[str(N)] = {'Kc_N': round(float(KcN),4) if not np.isnan(KcN) else None,
                       'R_curve': [round(x,4) for x in Rs.tolist()],
                       'K_grid': Ks.tolist(), 'peak_var_R': round(peak_var,5)}
    print(f"N={N:5d}  Kc(N)={KcN:.4f}  shift={Kc_inf-KcN:.4f}  peakVar(R)={peak_var:.5f}")

Ns_a = np.array([int(n) for n in results if results[n]['Kc_N'] is not None])
shift = np.array([Kc_inf - results[str(n)]['Kc_N'] for n in Ns_a])
g,b = np.polyfit(np.log(Ns_a), np.log(shift), 1)
print(f"FIT shift ~ N^(-gamma): gamma = {-g:.3f}")
peakv = np.array([results[str(n)]['peak_var_R'] for n in Ns_a])
d,bd = np.polyfit(np.log(Ns_a), np.log(peakv), 1)
print(f"FIT peakVar(R) ~ N^(-delta): delta = {-d:.3f}")

out = {'Kc_inf_theory': round(float(Kc_inf),4), 'results': results,
       'gamma_shift': round(float(-g),4), 'delta_fluct': round(float(-d),4)}
os.makedirs('shared_agora/artifacts', exist_ok=True)
with open('shared_agora/artifacts/emp098_fss_replication.json','w') as f:
    json.dump(out, f, indent=2)

plt.figure(figsize=(11,4))
plt.subplot(1,2,1)
for N in Ns_a:
    r = results[str(N)]
    plt.plot(r['K_grid'], r['R_curve'], 'o-', label=f"N={N}", alpha=0.8)
plt.axvline(Kc_inf, color='k', ls='--', label=f'Kc(inf)={Kc_inf:.2f}')
plt.xlabel('K'); plt.ylabel('<R>'); plt.title('Kuramoto order parameter vs K'); plt.legend(fontsize=8); plt.grid(alpha=0.3)
plt.subplot(1,2,2)
plt.loglog(Ns_a, shift, 's-', label=f'shift ~ N^{g:.2f}')
plt.loglog(Ns_a, peakv, '^-', label=f'peakVar ~ N^{d:.2f}')
plt.xlabel('N'); plt.ylabel('shift / peakVar'); plt.title('Finite-size scaling'); plt.legend(); plt.grid(True, which='both', alpha=0.3)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/emp098_fss_replication.png', dpi=130)
print("DONE")
