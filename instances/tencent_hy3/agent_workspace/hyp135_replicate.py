"""Independent replication & methodological audit of HYP-135 (DOSSIER-170).
Pure-python fast loop, closed-form 2x2 max-eigenvalue, env precomputed once per (rho,seed).
"""
import numpy as np, json, math, time

t0=time.time()
rhos = np.linspace(-0.9,0.9,51)
hbetas = np.linspace(0.0,0.5,41)
costs = [0.02,0.05,0.1,0.2,0.3]
T=2000; seeds=[0]

h0=0.3; s=0.9; gamma=0.25
W = (1.3, 0.3)   # wakeful fitness in env state 0 (good) / 1 (bad)

def max_eig(a,b,c,d):
    tr=a+d; det=a*d-b*c
    disc=tr*tr-4*det
    if disc<0: disc=0.0
    return 0.5*(tr+math.sqrt(disc))

def make_envs():
    # env[seed][i] : length-51 list of (rho -> int array T)
    d={}
    for sd in seeds:
        rng=np.random.default_rng(sd)
        for r in rhos:
            psw=0.5*(1-r)
            e=np.zeros(T,dtype=np.int8); e[0]=0
            # vectorized-ish using rng
            u=rng.random(T-1)
            flip=u<psw
            cur=0
            arr=np.empty(T,dtype=np.int8)
            arr[0]=0
            for t in range(1,T):
                if flip[t-1]: cur=1-cur
                arr[t]=cur
            d[(sd,r)]=arr
    return d

ENV=make_envs()

def delta(r,hb,c,cue,seed):
    e=ENV[(seed,r)]
    lyP=0.0; lyS=0.0; maxMS=-1e9
    prev_e=e[0]
    for t in range(T):
        et=e[t]
        Wt=W[et]
        if t==0:
            m=0
        elif cue=='level':
            m=1 if prev_e==1 else 0
        else:
            m=1 if (t>=2 and e[t-2]!=prev_e) else 0
        hP=h0+hb*m
        if hP<0: hP=0.0
        elif hP>1: hP=1.0
        WcP=Wt*(1-c); WcS=Wt
        # P
        lyP+=math.log(max(max_eig((1-hP)*WcP,gamma,hP*WcP,s*(1-gamma)),1e-12))
        # S
        me=max(max_eig((1-h0)*WcS,gamma,h0*WcS,s*(1-gamma)),1e-12)
        lyS+=math.log(me); 
        if me>maxMS: maxMS=me
        prev_e=et
    return lyP/T - lyS/T, lyP/T - maxMS

out={}
for cue in ['level','trans']:
    pw={}
    for c in costs:
        D=np.zeros((len(rhos),len(hbetas)))
        for i,r in enumerate(rhos):
            for j,hb in enumerate(hbetas):
                dC,_=delta(r,hb,c,cue,0)
                D[i,j]=dC
        pw[str(c)]=float((D>0).mean())
        # symmetry at this c
        pos=(D[rhos>1e-9]>0).mean(); neg=(D[rhos<-1e-9]>0).mean()
        pw[str(c)+'_sym+']=float(pos); pw[str(c)+'_sym-']=float(neg)
    out[cue]={'Pwin_frac':{k:v for k,v in pw.items() if not k.endswith('sym')},
              'symmetry':{k:v for k,v in pw.items() if k.endswith('sym')}}
    print(f"cue={cue}")
    print("  P-win frac:",{k:round(v,3) for k,v in pw.items() if not k.endswith('sym')})
    print("  sym +rho / -rho:",{k:round(v,3) for k,v in pw.items() if k.endswith('sym')})

json.dump(out, open('hyp135_replicate.json','w'), indent=2)
print(f"done in {time.time()-t0:.1f}s")
