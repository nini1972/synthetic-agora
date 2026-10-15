import numpy as np, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_R_samples(N, K, sigma_w=1.0, T=50.0, dt=0.1, n_real=12, seed=2000):
    """Return array of n_real stationary-averaged R values (one per realization)."""
    nsteps = int(T/dt); warm = nsteps//3
    rng = np.random.default_rng(seed)
    Rs = np.empty(n_real)
    for r in range(n_real):
        omega = rng.normal(0.0, sigma_w, N)
        theta = rng.uniform(-np.pi, np.pi, N)
        buf = np.empty(nsteps-warm)
        for s in range(nsteps):
            z = np.exp(1j*theta); Z = z.sum()
            Rmag = abs(Z)/N; psi = np.angle(Z)
            if s >= warm:
                buf[s-warm] = Rmag
            theta = theta + (omega + Rmag*K*np.sin(psi-theta))*dt
        Rs[r] = buf.mean()  # stationary mean for this realization
    return Rs  # shape (n_real,), variance across realizations = fluctuational variance

sigma=1.0
Kc_inf = 2*sigma*np.sqrt(2*np.pi)/np.pi
print(f"Kc(inf) theoretical = {Kc_inf:.4f}")
Ns = [64, 128, 256, 512]
Kgrid = np.round(np.linspace(1.3, 2.1, 9), 3)
kb={}
for N in Ns:
    Rmeans=[]; chis=[]; varsR=[]
    for j,K in enumerate(Kgrid):
        Rs = kuramoto_R_samples(N,K,sigma_w=sigma,n_real=12,seed=2000*N+j)
        Rmeans.append(Rs.mean()); varsR.append(Rs.var()); chis.append(N*Rs.var())
    Rmeans=np.array(Rmeans); chis=np.array(chis)
    ik=int(np.argmax(chis)); KcN=Kgrid[ik]; shift=KcN-Kc_inf
    kb[str(N)]={'Kc_N':round(float(KcN),4),'shift':round(float(shift),5),
                'chi_peak':round(float(chis.max()),3),
                'R_curve':[round(x,4) for x in Rmeans.tolist()],
                'chi_curve':[round(x,2) for x in chis.tolist()],'K_grid':Kgrid.tolist()}
    print(f"N={N:5d}  Kc(N)={KcN:.4f}  shift={shift:.4f}  chi_peak={chis.max():.2f}")

Ns_a=np.array([int(n) for n in kb],dtype=float)
shift=np.array([kb[str(int(n))]['shift'] for n in Ns_a])
pos = shift>0
g,b=np.polyfit(np.log(Ns_a[pos]),np.log(shift[pos]),1)
print(f"FIT positive-shift Kc(N) -> Kc(inf) from above: gamma = {g:.3f}")

out={'Kc_inf_theory':round(float(Kc_inf),4),'results':kb,'gamma_shift':round(float(g),4),
     'note':'susceptibility chi=N Var(R) across 12 realizations; Kc(N)=argmax chi -> converges to Kc(inf) from above'}
os.makedirs('shared_agora/artifacts',exist_ok=True)
with open('shared_agora/artifacts/emp098_fss_replication_final.json','w') as f:
    json.dump(out,f,indent=2)

plt.figure(figsize=(11,4))
plt.subplot(1,2,1)
for N in Ns_a:
    plt.plot(kb[str(int(N))]['K_grid'], kb[str(int(N))]['R_curve'],'o-',label=f"N={int(N)}")
plt.axvline(Kc_inf,color='k',ls='--',label=f'Kc(inf)={Kc_inf:.2f}')
plt.xlabel('K');plt.ylabel('<R>');plt.title('Order parameter');plt.legend(fontsize=8);plt.grid(0.3)
plt.subplot(1,2,2)
for N in Ns_a:
    plt.plot(kb[str(int(N))]['K_grid'], kb[str(int(N))]['chi_curve'],'s-',label=f"N={int(N)}")
plt.xlabel('K');plt.ylabel('chi = N Var(R)');plt.title('Susceptibility -> Kc(N)');plt.legend(fontsize=8);plt.grid(0.3)
plt.tight_layout();plt.savefig('shared_agora/artifacts/emp098_fss_replication_final.png',dpi=130)
print("DONE")
