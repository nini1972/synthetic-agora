import numpy as np, json
from collections import Counter
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
N,T=64,40
def life(g):
    n=(np.roll(g,1,0)+np.roll(g,-1,0)+np.roll(g,1,1)+np.roll(g,-1,1)
       +np.roll(np.roll(g,1,0),1,1)+np.roll(np.roll(g,1,0),-1,1)
       +np.roll(np.roll(g,-1,0),1,1)+np.roll(np.roll(g,-1,0),-1,1))
    return (((g==1)&((n==2)|(n==3)))|((g==0)&(n==3))).astype(np.float32)
def traj(g):
    fr=[]
    for t in range(T):
        g=life(g)
        if t>=T//3: fr.append(g.copy())
    return fr
def shan(g): 
    p=min(max(g.mean(),1e-9),1-1e-9); return -(p*np.log2(p)+(1-p)*np.log2(1-p))
def blockent(g,b=4):
    Hb=Wb=N//b; bl=g[:Hb*b,:Wb*b].reshape(Hb,b,Wb,b).mean(axis=(1,3))
    q=np.digitize(bl,np.quantile(bl,[.25,.5,.75])); c=Counter(q.ravel()); t=sum(c.values())
    return -sum((v/t)*np.log2(v/t) for v in c.values())
def lz78(s):
    d={():0};i=0;ph=0;L=len(s)
    while i<L:
        w=()
        while i<L and (w+(s[i],)) in d: w=w+(s[i],);i+=1
        ph+=1
        if i<L: d[w+(s[i],)]=len(d)
        i+=1
    return ph
def tlz(fr,b=4):
    sq=[]
    for g in fr:
        Hb=Wb=N//b; sq.extend(np.digitize(g[:Hb*b,:Wb*b].reshape(Hb,b,Wb,b).mean(axis=(1,3)),np.quantile(g,[.5])).ravel().tolist())
    if len(sq)<16: return 0.0
    n=lz78(tuple(sq)); return float(n*np.log2(n)/len(sq)) if n>1 else 0.0
def feats(fr):
    return dict(shannon=float(np.mean([shan(g) for g in fr])),
                block=float(np.mean([blockent(g) for g in fr])),
                tlz=tlz(fr),rho=float(np.mean([g.mean() for g in fr])))
def place(pats,seed):
    r=np.random.default_rng(seed); g=np.zeros((N,N))
    for p,H,W in pats:
        y,x=r.integers(0,N-H),r.integers(0,N-W)
        g[y:y+H,x:x+W]=np.maximum(g[y:y+H,x:x+W],p)
    return g
def still(): return np.ones((5,5)),5,5
def blink(): return np.ones((1,3)),1,3
def pulsar():
    p=np.zeros((13,13)); c=[0,5,7,12]
    for i in [3,4,8,9]: p[i,c]=1; p[c,i]=1
    return p,13,13
def glider():
    g=np.zeros((5,5)); g[0,1]=g[1,2]=g[2,0]=g[2,1]=g[2,2]=1; return g,5,5
specs={"still":(still,30),"blink":(blink,25),"pulsar":(pulsar,4),"glider":(glider,20)}
E=[]
for i,(k,(fn,nc)) in enumerate(specs.items()):
    E.append(feats(traj(place([fn() for _ in range(nc)],100+i))))
U=[]
for i in range(10): U.append(feats(traj((np.random.default_rng(50+i).random((N,N))<0.5).astype(np.float32))))
pool=[]
for i in range(150):
    rho0=0.003+0.05*(i/150)
    pool.append(feats(traj((np.random.default_rng(600+i).random((N,N))<rho0).astype(np.float32))))
def strat(E,M_pool,n_per=6,tol=0.02):
    matched=[]
    for e in E:
        cand=[p for p in M_pool if abs(p["rho"]-e["rho"])<=tol]
        if len(cand)>=n_per: matched.extend(cand[:n_per])
        else: matched.extend(cand)
    return matched
M = strat(E,pool)
def coh(a,b,k):
    a=np.array([float(d[k]) for d in a]);b=np.array([float(d[k]) for d in b])
    sp=np.sqrt((a.std(ddof=1)**2+b.std(ddof=1)**2)/2)
    return round(float((a.mean()-b.mean())/(sp+1e-12)),3)
keys=["shannon","block","tlz"]
res={"emergent_rho":[round(d["rho"],4) for d in E],
     "n_matched":len(M),"matched_rho_mean":round(float(np.mean([d["rho"] for d in M])),4),
     "uniform_rho_mean":round(float(np.mean([d["rho"] for d in U])),4),
     "cohens_d":{k:{"vs_uniform":coh(E,U,k),"vs_density_matched":coh(E,M,k)} for k in keys}}
def loo1(X,y):
    X=np.array(X);c=0
    for i in range(len(X)):
        d=np.linalg.norm(X-X[i],axis=1);d[i]=np.inf;c+=(y[np.argmin(d)]==y[i])
    return c/len(X)
Xe=[[d[k] for k in keys] for d in E]; Xu=[[d[k] for k in keys] for d in U]; Xm=[[d[k] for k in keys] for d in M]
res["loo_vs_uniform"]=round(loo1(Xe+Xu,[1]*len(Xe)+[0]*len(Xu)),3)
res["loo_vs_matched"]=round(loo1(Xe+Xm,[1]*len(Xe)+[0]*len(Xm)),3)
res["chance"]=round(len(Xe)/(len(Xe)+len(Xm)),3)
print(json.dumps(res,indent=2)); json.dump(res,open("emp138_v6_metrics.json","w"),indent=2)
fig,ax=plt.subplots(1,3,figsize=(13,4))
for i,k in enumerate(keys):
    ax[i].boxplot([[float(d[k]) for d in E],[float(d[k]) for d in U],[float(d[k]) for d in M]],
                  tick_labels=["emergent","rand-.5","density-matched"]); ax[i].set_title(k)
plt.suptitle("EMP-138 red-team v6: stratified final-density-matched controls")
plt.tight_layout(); plt.savefig("emp138_v6.png",dpi=130); print("saved")
