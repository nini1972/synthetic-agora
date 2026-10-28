"""Convergence/seed robustness of lambda_max at the 2 discrepant SYN-054 points."""
import numpy as np
def cml_step(x,r,eps):
    f=r*x*(1-x); return (1-eps)*f+0.5*eps*(np.roll(f,1)+np.roll(f,-1))
def lam(r,eps,nburn,nsteps,seed,L=128):
    rng=np.random.default_rng(seed); x=rng.uniform(0.1,0.9,L)
    for _ in range(nburn): x=cml_step(x,r,eps)
    v=rng.standard_normal(L); v/=np.linalg.norm(v); acc=0.0
    for _ in range(nsteps):
        fp=r*(1-2*x)
        Jv=(1-eps)*fp*v+0.5*eps*(np.roll(fp,1)*np.roll(v,1)+np.roll(fp,-1)*np.roll(v,-1))
        nrm=np.linalg.norm(Jv); acc+=np.log(nrm); v=Jv/nrm
        x=cml_step(x,r,eps)
    return acc/nsteps
for name,r,eps,claim in [("res B",3.860,0.136,-0.081),("chaos A",3.900,0.103,+0.337)]:
    print(name, "claimed %+0.3f"%claim)
    for nb,ns in [(20000,60000),(100000,200000)]:
        vals=[lam(r,eps,nburn=nb,nsteps=ns,seed=s) for s in range(3)]
        print("   burn=%d steps=%d -> mean %+0.4f  seeds %s"%(nb,ns,np.mean(vals),["%+0.3f"%v for v in vals]))
    # L dependence
    for L in [64,256]:
        print("   L=%d -> %+0.4f"%(L,lam(r,eps,L=L,nburn=50000,nsteps=100000,seed=7)))
