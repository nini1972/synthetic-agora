"""Diagnostic: why does faithful matrix give P-wins=0% while dossier claims 94%?
Test cost models and print invasion exponent for representative (rho,hbeta,c).
Cost models:
  'every' : WcP = Wt*(1-c) for ALL t (natural reading of 'fitness scaled by (1-c)')
  'sense' : WcP = Wt*(1-c) only when m=1 (cost paid only when sensing/adjusting)
"""
import numpy as np, math, time
t0=time.time()
rhos=np.linspace(-0.9,0.9,19); hbetas=[0.0,0.25,0.5]; costs=[0.02,0.05,0.1,0.3]
T=3000; seeds=[0]
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
def delta(r,hb,c,cue,cost_model):
    e=ENV[(0,r)]; lyP=0.0; lyS=0.0; prev_e=e[0]
    for t in range(T):
        et=e[t]; Wt=W[et]
        if t==0: m=0
        elif cue=='level': m=1 if prev_e==1 else 0
        else: m=1 if (t>=2 and e[t-2]!=prev_e) else 0
        hP=min(max(h0+hb*m,0.0),1.0)
        if cost_model=='every': WcP=Wt*(1-c)
        else: WcP=Wt*(1-c) if m==1 else Wt
        WcS=Wt
        lyP+=math.log(max(max_eig((1-hP)*WcP,gamma,hP*WcP,s*(1-gamma)),1e-12))
        lyS+=math.log(max(max_eig((1-h0)*WcS,gamma,h0*WcS,s*(1-gamma)),1e-12))
        prev_e=et
    return lyP/T-lyS/T

for cost_model in ['every','sense']:
    print(f"\n##### cost_model={cost_model} #####")
    for cue in ['level','trans']:
        pw={}
        for c in costs:
            cnt=0;N=0
            for r in rhos:
                for hb in hbetas:
                    if delta(r,hb,c,cue,cost_model)>0: cnt+=1
                    N+=1
            pw[str(c)]=round(cnt/N,3)
        print(f" cue={cue}  P-win frac:",pw)
# detailed table for 'sense' model at c=0.05 over a rho grid
print("\nDetailed Delta (sense model, c=0.05, hbeta=0.5, cue=level):")
for r in [-0.8,-0.4,0,0.4,0.8]:
    d=delta(r,0.5,0.05,'level','sense')
    print(f"  rho={r:+.1f}  Delta(lyapP-lyapS)={d:+.4f}  -> {'P wins' if d>0 else 'S wins'}")
print(f"\ntime {time.time()-t0:.1f}s")
