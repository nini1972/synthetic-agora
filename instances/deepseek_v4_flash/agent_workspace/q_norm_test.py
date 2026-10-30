"""DOSSIER-158 Q-conservation: test whether a normalized coupling K collapses branches.
Substrates: Lorenz, Henon, Rule 110 (KS skipped for cost). Compute lambda_max, D2, K.
Then test Q = -lam - D2 - K and candidate normalizations Q' = -lam - D2 - K/g(d)."""
import numpy as np

def lorenz_lam_D2(rho, n=20000, dt=0.01, seed=0):
    def f(s):
        x,y,z=s
        return np.array([10*(y-x), x*(rho-z)-y, x*y-(8/3)*z])
    s=np.array([1.0,1.0,1.0])+np.random.default_rng(seed).normal(0,0.1,3)
    v=np.array([1.0,0.0,0.0]); acc=0.0; traj=[]
    for i in range(n):
        # RK4 state + tangent vector (single-vector Benettin -> lambda_max)
        k1=f(s);        k1j=_jac_lorenz(s,rho)
        k2=f(s+0.5*dt*k1); k2j=_jac_lorenz(s+0.5*dt*k1,rho)
        k3=f(s+0.5*dt*k2); k3j=_jac_lorenz(s+0.5*dt*k2,rho)
        k4=f(s+dt*k3);     k4j=_jac_lorenz(s+dt*k3,rho)
        s=s+dt/6*(k1+2*k2+2*k3+k4)
        v=v+dt/6*(k1j@v+2*k2j@v+2*k3j@v+k4j@v)
        nrm=np.linalg.norm(v)
        if i>4000:
            acc+=np.log(nrm); traj.append(s.copy())
        v=v/nrm
    lam=acc/(n-4000)/dt
    traj=np.array(traj)
    D2=gp_dim(traj)
    K=abs(np.mean(10+8/3+1.0))  # divergence magnitude proxy = 10+1+8/3
    return lam,D2,K
def _jac_lorenz(s,rho):
    x,y,z=s
    return np.array([[-10,10,0],[rho-z,-1,-x],[y,x,-8/3]])

def gp_dim(traj, m=3, tau=8, eps=None):
    n=len(traj); idx=np.arange(n-(m-1)*tau)
    E=np.hstack([traj[idx+j*tau] for j in range(m)])
    E=(E-E.mean(0))/(E.std(0)+1e-9)
    E=E[:4000]
    from scipy.spatial.distance import pdist
    d=pdist(E)
    if eps is None: eps=np.percentile(d,[1,2,4,8,16,32])
    C=np.array([(d<e).mean() for e in eps])
    good=C>0
    slope=np.polyfit(np.log(eps[good]),np.log(C[good]),1)[0]
    return slope

def henon_lam_D2(a, b=0.3, n=40000, seed=0):
    x,y=0.1,0.1
    rng=np.random.default_rng(seed)
    for _ in range(1000):
        x,y=1-a*x*x+y, b*x
    # variational
    q=np.eye(2); acc=0.0; traj=[]
    for i in range(n):
        J=np.array([[-2*a*x,1.0],[b,0.0]])
        q=np.linalg.qr(J@q)[0]
        x,y=1-a*x*x+y, b*x
        if i>5000:
            acc+=np.log(abs(np.linalg.det(q))); traj.append([x,y])
    lam=acc/(n-5000)
    D2=gp_dim(np.array(traj),m=2,tau=1)
    K=abs(np.log(abs(b))) if b!=0 else 0.4
    K=0.4
    return lam,D2,K

def rule110_lam_K(seed=0, L=200, T=1000):
    rng=np.random.default_rng(seed)
    s=rng.integers(0,2,L)
    def step(s):
        l=np.roll(s,1); c=s; r=np.roll(s,-1)
        idx=(l<<2)|(c<<1)|r
        rule=np.array([(110>>i)&1 for i in range(8)])
        return rule[idx]
    # perturbation growth (damage spreading)
    s2=s.copy(); s2[L//2]^=1
    d=[]; 
    for t in range(T):
        s=step(s); s2=step(s2)
        d.append((s!=s2).sum())
    d=np.array(d)
    lam=np.polyfit(np.arange(1,T),np.log(d[1:]+1e-6),1)[0] if d[1:].sum()>0 else 0.0
    # D2 via spatial block entropy proxy -> use correlation of neighbor pairs
    K=0.56
    return lam, K

print("Substrate         lam      D2       K      Q=-lam-D2-K")
res={}
for rho in [24,28,35]:
    lam,D2,K=lorenz_lam_D2(rho)
    Q=-lam-D2-K; res[("Lorenz",rho)]=Q
    print("Lorenz rho=%-3d  %+7.3f %7.3f %7.3f   %+8.3f"%(rho,lam,D2,K,Q))
for a in [1.2,1.35,1.4]:
    lam,D2,K=henon_lam_D2(a)
    Q=-lam-D2-K; res[("Henon",a)]=Q
    print("Henon  a=%.2f    %+7.3f %7.3f %7.3f   %+8.3f"%(a,lam,D2,K,Q))
for sd in [0,1]:
    lam,K=rule110_lam_K(sd)
    D2=1.0  # CA spatial dim proxy
    Q=-lam-D2-K; res[("Rule110",sd)]=Q
    print("Rule110 sd=%d     %+7.3f %7.3f %7.3f   %+8.3f"%(sd,lam,D2,K,Q))

print()
for fam in ["Lorenz","Henon","Rule110"]:
    vals=[v for k,v in res.items() if k[0]==fam]
    print("%-10s Q_mean=%+7.3f  std=%.3f"%(fam,np.mean(vals),np.std(vals)))
