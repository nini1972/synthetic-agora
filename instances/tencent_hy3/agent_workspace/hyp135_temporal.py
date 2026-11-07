"""Direct temporal recurrence test of HYP-135 coevolution model.
Tracks 4-state population (P_wakeful, P_dormant, S_wakeful, S_dormant)
under the env sequence, applies cost (1-c) to P only.
Reports final P-fraction (= invaded?) for representative (rho,c)."""
import numpy as np, math
WM,Wm=2.0,0.1; h0=0.3; s=0.9; g=0.25; T=4000
def run(rho,c,cost_model):
    rng=np.random.default_rng(0)
    psw=0.5*(1-rho); env=np.zeros(T,dtype=int); cur=0
    for t in range(1,T):
        if rng.random()<psw: cur=1-cur
        env[t]=cur
    Pw=0.5; Pd=0.5; Sw=0.5; Sd=0.5  # initial equal
    prev=env[0]
    for t in range(T):
        e=env[t]; Wt=WM if e==0 else Wm
        m=1 if prev==1 else 0
        hP=min(max(h0+0.5*m,0.0),1.0)
        cst=(1-c) if cost_model=='every' else (1-c if m==1 else 1.0)
        # P
        nPw=(1-hP)*Wt*cst*Pw + g*Pd
        nPd=hP*Wt*cst*Pw + s*(1-g)*Pd
        # S (no cost, h0)
        nSw=(1-h0)*Wt*Sw + g*Sd
        nSd=h0*Wt*Sw + s*(1-g)*Sd
        tot=nPw+nPd+nSw+nSd
        Pw,nPw=nPw/tot,nPw/tot; Pd=nPd/tot; Sw=nSw/tot; Sd=nSd/tot
        prev=e
    Pf=Pw+Pd
    return Pf
print(f"{'rho':>5} {'c':>5} {'every_P%':>10} {'sense_P%':>10}  verdict")
for rho in [-0.6,0.0,0.6]:
    for c in [0.02,0.05,0.1]:
        pe=run(rho,c,'every'); ps=run(rho,c,'sense')
        v='P invades' if pe>0.5 else ('S excludes P' if pe<0.5 else 'tie')
        print(f"{rho:>5.1f} {c:>5.2f} {pe*100:>9.1f}% {ps*100:>9.1f}%  {v}")
