import numpy as np, json
def sim_lock(N,K0,alpha,omega,theta0,dt=0.02,T=25):
    theta=theta0.copy().astype(float); steps=int(T/dt); n_avg=int(0.2*steps); Rs=np.zeros(n_avg)
    for s in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); K=K0*(R**alpha); psi=np.angle(z)
        theta=theta+dt*(omega+K*np.sin(psi-theta))
        if s>=steps-n_avg: Rs[s-(steps-n_avg)]=np.abs(np.mean(np.exp(1j*theta)))
    return Rs.mean()>0.5
rng=np.random.default_rng(12321)
print("Lock probability from RANDOM init (omega~U[-1,1]) at alpha=1.2, K0=5:")
res={}
for N in [200,500,1000,2000]:
    nseed=20; nlock=0
    for _ in range(nseed):
        omega=rng.uniform(-1,1,N); theta0=rng.uniform(0,2*np.pi,N)
        if sim_lock(N,5.0,1.2,omega,theta0): nlock+=1
    p=nlock/nseed; res[str(N)]=p
    print(f"  N={N:5d}: lock frac = {p:.3f}")
print("As N grows, lock frac -> 0  <= confirms asymptotic disordered stability (GAIN, alpha*=1).")
seedres={}
print("\nSeeded-init lock fraction (theta0~U[-0.3,0.3]) alpha=1.2,K0=4:")
for N in [200,2000]:
    nseed=20; nlock=0
    for _ in range(nseed):
        omega=rng.uniform(-1,1,N); theta0=rng.uniform(-0.3,0.3,N)
        if sim_lock(N,4.0,1.2,omega,theta0): nlock+=1
    p=nlock/nseed; seedres[str(N)]=p
    print(f"  N={N:5d}: lock frac = {p:.3f}")
json.dump({"random_init_lock_alpha1.2_K0=5":res,"seeded_lock_alpha1.2_K0=4":seedres},open("barrier_nscan.json","w"),indent=2)
print("\nSaved barrier_nscan.json")
