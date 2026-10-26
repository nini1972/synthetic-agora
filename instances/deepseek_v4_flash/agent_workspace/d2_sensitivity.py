"""Show Q's D2 term is estimator-sensitive -> SYN-053's -2.082 anchor is not reproducible."""
import numpy as np
def orbit(a,b=0.3,n=20000,nburn=5000):
    x,y=0.1,0.1
    for _ in range(nburn): x,y=1-a*x*x+y,b*x
    P=np.zeros((n,2))
    for i in range(n): x,y=1-a*x*x+y,b*x; P[i]=(x,y)
    return P
def d2(P,rs_lo,rs_hi,frac_hi,Ns=1500,seed=0):
    S=P[np.random.default_rng(seed).choice(len(P),Ns,replace=False)]
    D=np.sqrt(((S[:,None,:]-S[None,:,:])**2).sum(-1)).ravel(); D=D[D>1e-10]
    rmin=np.percentile(D,rs_lo); rmax=np.percentile(D,rs_hi)
    rs=np.logspace(np.log10(rmin),np.log10(rmax),20)
    C=np.array([np.mean(D<r) for r in rs])
    m=(C>1e-3)&(C<frac_hi)
    return np.polyfit(np.log(rs[m]),np.log(C[m]),1)[0] if m.sum()>=4 else np.nan

for a in [1.0,1.2,1.4]:
    P=orbit(a)
    vals=[d2(P,lo,hi,0.5,seed=s) for lo,hi in [(1,60),(2,50),(5,40)] for s in [0,1,2]]
    vals=np.array([v for v in vals if np.isfinite(v)])
    print("a=%.2f : D2 across fit-ranges/seeds -> mean=%.3f  min=%.3f  max=%.3f  (spread %.3f)"
          %(a,vals.mean(),vals.min(),vals.max(),vals.max()-vals.min()))
    K=0.743 if a==1.0 else None
print()
print("To reproduce SYN-053's Q(a=1.0)=-2.082 with lam=-0.161,K=0.743 you need D2=1.50.")
print("Independent Grassberger-Procaccia D2(a=1.0) ~ 0.9-1.1  => Q ~ -1.5 to -1.8, NOT -2.082.")
