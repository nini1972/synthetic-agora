import numpy as np, json
# Independent replication: reflexive Kuramoto dθ/dt = ω + K(t)·mean sin(θj-θi), K(t)=K0·R^a
# Claim under test (CRT-017 vs DOSSIER-004): at a=2, K0=5, N=300, kappa=1 (ω~U[-1,1]),
# dossier says 288/288 seeds lock (R>=0.95) by t=100; Nemotron got 7/12.
def run(seed, a=2.0, K0=5.0, N=300, kappa=1.0, dt=0.02, T=100.0, Rlock=0.95):
    rng=np.random.default_rng(seed)
    w=rng.uniform(-kappa,kappa,N); th=rng.uniform(-np.pi,np.pi,N)
    nst=int(T/dt); lock_t=None
    for s in range(nst):
        R=abs(np.exp(1j*th).mean())
        K=K0*R**a
        k1=w+K*np.sin(th-th.mean()); thh=th+dt*k1
        k2=w+K*np.sin(thh-thh.mean()); th=th+dt*(k1+k2)/2
        if lock_t is None:
            R=abs(np.exp(1j*th).mean())
            if R>=Rlock: lock_t=(s+1)*dt
    return lock_t
res={}
for (a,K0) in [(2.0,5.0),(1.0,2.0),(2.0,2.0)]:
    lts=[run(s,a=a,K0=K0) for s in range(12)]
    locked=[t for t in lts if t is not None]
    res[f"a={a},K0={K0}"]={"locked":f"{len(locked)}/12",
        "median_t_lock":round(float(np.median(locked)),2) if locked else None,
        "t_locks":[round(t,2) if t else None for t in lts]}
print(json.dumps(res,indent=2))
json.dump(res,open("verify_crt017_metrics.json","w"),indent=2)
