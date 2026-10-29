"""Figure: L-dependence of CML lambda_max near the transition (SYN-054 refinement)."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np
def cml_step(x,r,eps):
    f=r*x*(1-x); return (1-eps)*f+0.5*eps*(np.roll(f,1)+np.roll(f,-1))
def lam(r,eps,nburn,nsteps,seed,L):
    rng=np.random.default_rng(seed); x=rng.uniform(0.1,0.9,L)
    for _ in range(nburn): x=cml_step(x,r,eps)
    v=rng.standard_normal(L); v/=np.linalg.norm(v); acc=0.0
    for _ in range(nsteps):
        fp=r*(1-2*x)
        Jv=(1-eps)*fp*v+0.5*eps*(np.roll(fp,1)*np.roll(v,1)+np.roll(fp,-1)*np.roll(v,-1))
        acc+=np.log(np.linalg.norm(Jv)); v=Jv/np.linalg.norm(Jv)
        x=cml_step(x,r,eps)
    return acc/nsteps

Ls=[32,64,128,256]
pts=[("resonant B (r=3.860,eps=0.136)",3.860,0.136,-0.081,'o'),
     ("chaotic A (r=3.900,eps=0.103)",3.900,0.103,+0.337,'s')]
fig,ax=plt.subplots(figsize=(8,5.5))
for name,r,eps,claim,mk in pts:
    means=[];errs=[]
    for L in Ls:
        vals=[lam(r,eps,6000,24000,s,L) for s in range(3)]
        means.append(np.mean(vals)); errs.append(np.std(vals))
    ax.errorbar(Ls,means,yerr=errs,marker=mk,label=name)
    ax.axhline(claim,ls='--',alpha=0.5)
    ax.text(Ls[-1],claim+0.01,"claimed %+0.3f"%claim,fontsize=8,ha='right')
ax.axhline(0,color='k',lw=1)
ax.set_xlabel("lattice size L"); ax.set_ylabel(r"$\lambda_{max}$ (maximal spatiotemporal Lyapunov)")
ax.set_title("SYN-054 refinement: CML $\\lambda_{max}$ is finite-size (L) dependent\nnear the transition — numeric anchors need L-scaling error bars")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("syn054_Ldependence.png",dpi=110)
print("saved syn054_Ldependence.png")
