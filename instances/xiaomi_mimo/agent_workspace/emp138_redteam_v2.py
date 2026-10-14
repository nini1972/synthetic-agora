# EMP-138 red-team v2 (solid protocol): trajectory-averaged measures, tiled patterns
# so densities are non-trivial, proper pulsar, glider kept in-bounds by re-injection.
import numpy as np, json
from collections import Counter
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rng = np.random.default_rng(7)
N, T, STEP = 96, 60, 25

def life(g):
    n = (np.roll(g,1,0)+np.roll(g,-1,0)+np.roll(g,1,1)+np.roll(g,-1,1)
         + np.roll(np.roll(g,1,0),1,1)+np.roll(np.roll(g,1,0),-1,1)
         + np.roll(np.roll(g,-1,0),1,1)+np.roll(np.roll(g,-1,0),-1,1))
    return (((g==1)&((n==2)|(n==3))) | ((g==0)&(n==3))).astype(np.float32)

def traj(g, T=T, warmup=True):
    fr=[]; rho=[]; t0 = T//3 if warmup else 0
    for t in range(T):
        g = life(g)
        if t >= t0: fr.append(g.copy()); rho.append(g.mean())
    return fr, rho

def place(pattern_fn, ncopy, seed):
    r = np.random.default_rng(seed); g = np.zeros((N,N))
    for _ in range(ncopy):
        p = pattern_fn()
        H, W = p.shape
        y, x = r.integers(0, N-H), r.integers(0, N-W)
        g[y:y+H, x:x+W] = np.maximum(g[y:y+H, x:x+W], p)
    return g

def still():  # block
    return np.array([[1,1],[1,1]], float)
def blink():
    return np.array([[1,1,1]], float)
def pulsar():
    p = np.zeros((13,13)); c = [0,5,7,12]
    for i in [3,4,8,9]:
        p[i, c] = 1; p[c, i] = 1
    return p
def glider():
    g = np.zeros((6,6)); g[0,1]=g[1,2]=g[2,0]=g[2,1]=g[2,2]=1; return g

# --- features (trajectory-averaged) ---
def shannon(fr): 
    out=[]
    for g in fr:
        p=min(max(g.mean(),1e-9),1-1e-9); out.append(-(p*np.log2(p)+(1-p)*np.log2(1-p)))
    return float(np.mean(out))
def blockent(fr, b=4):
    out=[]
    for g in fr:
        Hb,Wb=N//b,N//b; bl=g[:Hb*b,:Wb*b].reshape(Hb,b,Wb,b).mean(axis=(1,3))
        q=np.digitize(bl,np.quantile(bl,[.25,.5,.75])); c=Counter(q.ravel()); tot=sum(c.values())
        out.append(-sum((v/tot)*np.log2(v/tot) for v in c.values()))
    return float(np.mean(out))
def lz78(seq):
    dic={():0}; i=0; ph=0; L=len(seq)
    while i<L:
        w=()
        while i<L and (w+(seq[i],)) in dic: w=w+(seq[i],); i+=1
        ph+=1
        if i<L: dic[w+(seq[i],)]=len(dic)
        i+=1
    return ph
def tlz(fr, b=4):
    seq=[]
    for g in fr:
        Hb,Wb=N//b,N//b; bl=g[:Hb*b,:Wb*b].reshape(Hb,b,Wb,b).mean(axis=(1,3))
        seq.extend(np.digitize(bl,np.quantile(bl,[.5])).ravel().tolist())
    if len(seq)<16: return 0.0
    n=lz78(tuple(seq)); return float(n*np.log2(n)/len(seq)) if n>1 else 0.0
def feats(fr, rho): return dict(shannon=shannon(fr), block=blockent(fr), tlz=tlz(fr), rho=float(np.mean(rho)))

# emergent group: tiled patterns -> non-trivial density
emerg_specs = {"stillx30":(still,30),"blinkx25":(blink,25),
               "pulsarx4":(pulsar,4),"gliderx20":(glider,20)}
E=[]
for i,(name,(fn,nc)) in enumerate(emerg_specs.items()):
    fr, rho = traj(place(fn, nc, 100+i))
    E.append(feats(fr, rho))

def rand_rho(rho, seed):
    r=np.random.default_rng(seed); return (r.random((N,N))<rho).astype(np.float32)

U=[]; M=[]; S=[]
for i in range(10):
    fr,rho = traj(rand_rho(0.5, 500+i)); U.append(feats(fr,rho))
for j,f in enumerate(E):  # density-matched random
    for i in range(5):
        fr,rho = traj(rand_rho(max(f["rho"],1.0/N), 900+10*j+i)); M.append(feats(fr,rho))
for j,(name,(fn,nc)) in enumerate(emerg_specs.items()):  # spatial-shuffle control
    for i in range(5):
        g0 = place(fn, nc, 100+j); gs=g0.ravel().copy(); np.random.default_rng(2000+j*10+i).shuffle(gs)
        fr,rho = traj(gs.reshape(N,N)); S.append(feats(fr,rho))

def coh(a,b,k): 
    a=np.array([float(d[k]) for d in a]); b=np.array([float(d[k]) for d in b])
    sp=np.sqrt((a.std(ddof=1)**2+b.std(ddof=1)**2)/2); return float((a.mean()-b.mean())/(sp+1e-12))
keys=["shannon","block","tlz"]
res={"cohens_d":{k:{"vs_uniform":coh(E,U,k),"vs_density_matched":coh(E,M,k),"vs_shuffled":coh(E,S,k)} for k in keys},
     "density_emergent":[float(d["rho"]) for d in E],
     "density_uniform":float(np.mean([d["rho"] for d in U])),
     "density_matched":[float(d["rho"]) for d in M][:10]}
def loo1(X,y):
    X=np.array(X); c=0
    for i in range(len(X)):
        d=np.linalg.norm(X-X[i],axis=1); d[i]=np.inf; c+=(y[np.argmin(d)]==y[i])
    return c/len(X)
Xe=[[d[k] for k in keys] for d in E]; Xu=[[d[k] for k in keys] for d in U]; Xm=[[d[k] for k in keys] for d in M]
res["loo_acc_vs_uniform"]=loo1(Xe+Xu,[1]*4+[0]*10)
res["loo_acc_vs_density_matched"]=loo1(Xe+Xm,[1]*4+[0]*len(M))
print(json.dumps(res,indent=2)); json.dump(res,open("emp138_redteam_v2_metrics.json","w"),indent=2)
fig,ax=plt.subplots(1,3,figsize=(13,4))
for i,k in enumerate(keys):
    ax[i].boxplot([[float(d[k]) for d in E],[float(d[k]) for d in U],[float(d[k]) for d in M],[float(d[k]) for d in S]],
                  tick_labels=["emergent","rand-.5","rand-density","shuffled"]); ax[i].set_title(k)
plt.suptitle("EMP-138 red-team v2: density-matched controls")
plt.tight_layout(); plt.savefig("emp138_redteam_v2.png",dpi=130); print("saved")
