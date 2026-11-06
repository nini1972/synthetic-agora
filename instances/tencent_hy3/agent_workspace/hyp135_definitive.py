"""Definitive test of HYP-135 matrix (DOSSIER-170 constants).
Report MAX invasion exponent Delta=lyap_P-lyap_S over full grid + location.
Tests cost_model 'every' and 'sense', cue='level' (most informative), seeds=3.
"""
import numpy as np, math, time
t0=time.time()
rhos=np.linspace(-0.9,0.9,51); hbetas=np.linspace(0.0,0.5,21)
T=2000; seeds=[0,1,2]; c=0.05
h0=0.3; s=0.9; gamma=0.25; W=(2.0,0.1)
def max_eig(a,b,c,d):
    tr=a+d; det=a*d-b*c; disc=tr*tr-4*det
    if disc<0: disc=0.0
    return 0.5*(tr+math.sqrt(disc))
ENV={}
for sd in seeds:
    rng=np.random.default_rng(sd)
    for r in rhos:
        psw=0.5*(1-r); e=np.zeros(T,dtype=np.int8); cur=0
        for t in range(1,T):
            if rng.random()<psw: cur=1-cur
            e[t]=cur
        ENV[(sd,r)]=e
def delta(r,hb,c,cost_model):
    best=0
    for sd in seeds:
        e=ENV[(sd,r)]; lyP=0.0; lyS=0.0; prev_e=e[0]
        for t in range(T):
            et=e[t]; Wt=W[et]
            m=1 if prev_e==1 else 0
            hP=min(max(h0+hb*m,0.0),1.0)
            WcP=Wt*(1-c) if (cost_model=='every' or m==1) else Wt
            lyP+=math.log(max(max_eig((1-hP)*WcP,gamma,hP*WcP,s*(1-gamma)),1e-12))
            lyS+=math.log(max(max_eig((1-h0)*Wt,gamma,h0*Wt,s*(1-gamma)),1e-12))
            prev_e=et
        d=lyP/T-lyS/T
        if d>best: best=d
    return best
for cost_model in ['every','sense']:
    D=np.zeros((len(rhos),len(hbetas)))
    for i,r in enumerate(rhos):
        for j,hb in enumerate(hbetas):
            D[i,j]=delta(r,hb,c,cost_model)
    Pwin=(D>0).mean()
    amax=np.unravel_index(np.argmax(D),D.shape)
    print(f"\ncost_model={cost_model} cue=level c=0.05  (51x21 grid, 3 seeds)")
    print(f"  P-win frac = {Pwin:.4f}")
    print(f"  max Delta  = {D.max():.4f}  at rho={rhos[amax[0]]:.2f}, hbeta={hbetas[amax[1]]:.2f}")
    print(f"  mean Delta = {D.mean():.4f}   min Delta = {D.min():.4f}")
    # fraction of rho>0 that P wins:
    pos=(D[rhos>1e-9]>0).mean(); neg=(D[rhos<-1e-9]>0).mean()
    print(f"  among rho>0: P-win={pos:.3f}; among rho<0: P-win={neg:.3f}")
print(f"\ndone in {time.time()-t0:.1f}s")
