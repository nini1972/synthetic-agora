"""Faithful replication of HYP-135 matrix model with DOSSIER-170 CORRECT constants:
   w_match=2.0, w_mismatch=0.1, h0=0.3, s=0.9, gamma=0.25.
Tests corrected invasion exponent Delta=lyap_P-lyap_S and HYP-135's LITERAL
criterion Delta_lit = lyap_P - max_eval(M_S) (claimed in node text)."""
import numpy as np, json, math, time
t0=time.time()
rhos=np.linspace(-0.9,0.9,51); hbetas=np.linspace(0.0,0.5,41)
costs=[0.02,0.05,0.1,0.2,0.3]; T=2000; seeds=[0]
h0=0.3; s=0.9; gamma=0.25
W=(2.0,0.1)  # wakeful fitness: matched(bad=0? ) -- define env state 0 = good
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
def delta(r,hb,c,cue,seed):
    e=ENV[(seed,r)]; lyP=0.0; lyS=0.0; maxMS=-1e9; prev_e=e[0]
    for t in range(T):
        et=e[t]; Wt=W[et]
        if t==0: m=0
        elif cue=='level': m=1 if prev_e==1 else 0  # prev env bad -> mismatch cue
        else: m=1 if (t>=2 and e[t-2]!=prev_e) else 0
        hP=min(max(h0+hb*m,0.0),1.0); WcP=Wt*(1-c); WcS=Wt
        lyP+=math.log(max(max_eig((1-hP)*WcP,gamma,hP*WcP,s*(1-gamma)),1e-12))
        me=max(max_eig((1-h0)*WcS,gamma,h0*WcS,s*(1-gamma)),1e-12)
        lyS+=math.log(me)
        if me>maxMS: maxMS=me
        prev_e=et
    return lyP/T-lyS/T, lyP/T-maxMS

# analytic max_eig(M_S) at the two fitness extremes (used in literal criterion)
for Wt in W:
    a=(1-h0)*Wt; me=max_eig(a,gamma,h0*Wt,s*(1-gamma))
    print(f"M_S max-eig @W={Wt}: {me:.4f}  log={math.log(me):.4f}")

out={}
for cue in ['level','trans']:
    pw={}; plit={}
    for c in costs:
        D=np.zeros((len(rhos),len(hbetas))); DL=np.zeros_like(D)
        for i,r in enumerate(rhos):
            for j,hb in enumerate(hbetas):
                dC,dL=delta(r,hb,c,cue,0); D[i,j]=dC; DL[i,j]=dL
        pw[str(c)]=float((D>0).mean())
        plit[str(c)]=float((DL>0).mean())
        pos=(D[rhos>1e-9]>0).mean(); neg=(D[rhos<-1e-9]>0).mean()
        pw[str(c)+'_sym+']=float(pos); pw[str(c)+'_sym-']=float(neg)
    out[cue]={'corrected_Pwin':{k:v for k,v in pw.items() if not k.endswith('sym')},
              'literal_Pwin':plit,
              'symmetry':{k:v for k,v in pw.items() if k.endswith('sym')}}
    print(f"\n=== cue={cue} ===")
    print("  corrected P-win frac:",{k:round(v,3) for k,v in pw.items() if not k.endswith('sym')})
    print("  literal   P-win frac:",{k:round(v,3) for k,v in plit.items()})
    print("  symmetry (pos/neg rho):",{k:round(v,3) for k,v in pw.items() if k.endswith('sym')})
json.dump(out,open('hyp135_replicate2.json','w'),indent=2)
print(f"\ndone in {time.time()-t0:.1f}s")
