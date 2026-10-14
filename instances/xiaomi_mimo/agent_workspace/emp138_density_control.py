# Density-matched red-team of EMP-138: do entropy measures still discriminate
# emergent GoL patterns vs random when RANDOM CONTROLS MATCH PATTERN DENSITY
# and when static-vs-moving confound is removed?
import numpy as np, json
from collections import Counter
rng = np.random.default_rng(7)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

N, T = 64, 50

def life(g):
    n = (np.roll(g,1,0)+np.roll(g,-1,0)+np.roll(g,1,1)+np.roll(g,-1,1)
         + np.roll(np.roll(g,1,0),1,1)+np.roll(np.roll(g,1,0),-1,1)
         + np.roll(np.roll(g,-1,0),1,1)+np.roll(np.roll(g,-1,0),-1,1))
    return (((g==1)&((n==2)|(n==3))) | ((g==0)&(n==3))).astype(np.float32)

def run(g, T=T):
    fr = []
    for t in range(T):
        g = life(g)
        if t >= T//2: fr.append(g.copy())
    return g, fr

def glider():
    g = np.zeros((N,N)); g[1,2]=g[2,3]=g[3,1]=g[3,2]=g[3,3]=1; return g
def blinker():
    g = np.zeros((N,N)); g[10,10:13]=1; return g
def block():
    g = np.zeros((N,N)); g[10,10]=g[10,11]=g[11,10]=g[11,11]=1; return g
def pulsar():
    g = np.zeros((N,N))
    for d in [(1,3),(1,4),(1,5),(2,2),(2,6),(3,2),(3,6),(5,2),(5,6),(6,2),(6,6),
              (7,3),(7,4),(7,5)]:
        for s in [(1,1),(-1,1),(1,-1),(-1,-1)]:
            g[20+d[0]*s[0], 20+d[1]*s[1]] = 1
    return g

def shannon(g):
    p = g.mean(); p = min(max(p,1e-9),1-1e-9)
    return -(p*np.log2(p)+(1-p)*np.log2(1-p))
def block_ent(g, b=4):
    H,W = g.shape; Hb,Wb = H//b, W//b
    bl = g[:Hb*b,:Wb*b].reshape(Hb,b,Wb,b).mean(axis=(1,3))
    qs = np.quantile(bl,[.25,.5,.75]); q = np.digitize(bl,qs)
    c = Counter(q.ravel()); tot = sum(c.values())
    return -sum((v/tot)*np.log2(v/tot) for v in c.values())
def lz78(seq):
    dic={():0}; i=0; ph=0; L=len(seq)
    while i<L:
        w=()
        while i<L and (w+(seq[i],)) in dic: w=w+(seq[i],); i+=1
        ph+=1
        if i<L: dic[w+(seq[i],)]=len(dic)
        i+=1
    return ph
def temp_lz(fr):
    seq=[]
    for f in fr:
        bl = f[::4,::4].ravel()
        seq.extend(np.digitize(bl, np.quantile(bl,[.5])).tolist())
    if len(seq)<16: return 0.0
    n = lz78(tuple(seq))
    return n*np.log2(n)/len(seq) if n>1 else 0.0

def feats(g, fr):
    return dict(shannon=shannon(g), block=block_ent(g), tlz=temp_lz(fr),
                density=float(g.mean()))

# emergent set
emerg = {"glider":glider(),"blinker":blinker(),"block":block(),"pulsar":pulsar()}
emerg_f = {k: feats(*run(v.copy())) for k,v in emerg.items()}

# control U (EMP-138 style): uniform random
ctrl_u = {"randU%d"%i: feats(*run((rng.random((N,N))<0.5).astype(np.float32))) for i in range(8)}

# control M (red-team): density-matched random, densities = each pattern's density
ctrl_m = {}
for k,f in emerg_f.items():
    for i in range(4):
        rho = f["density"]
        g = (rng.random((N,N)) < max(rho,1.0/N)).astype(np.float32)
        ctrl_m["m-%s-%d"%(k,i)] = feats(*run(g))

# control S: SHUFFLE of final pattern frames (same density, destroyed spatial structure)
ctrl_sh = {}
for k,v in emerg.items():
    g0,_ = run(v.copy())
    for i in range(4):
        gs = g0.copy().ravel(); rng.shuffle(gs); gs = gs.reshape(N,N)
        # run a few steps so dynamics settle, then measure on same protocol
        _, fr = run(gs.copy())
        g2 = fr[-1]
        ctrl_sh["sh-%s-%d"%(k,i)] = feats(g2, fr)

def coh(d1, d2, key):
    m1 = float(np.mean([float(d[key]) for d in d1])); m2 = float(np.mean([float(d[key]) for d in d2]))
    s1 = np.std([d[key] for d in d1], ddof=1) or 1e-9
    s2 = np.std([d[key] for d in d2], ddof=1) or 1e-9
    sp = np.sqrt((s1**2+s2**2)/2)
    return float((m1-m2)/(sp+1e-12))

E = list(emerg_f.values())
U = list(ctrl_u.values()); M = list(ctrl_m.values()); S = list(ctrl_sh.values())
keys = ["shannon","block","tlz"]
res = {}
for key in keys:
    res[key] = {"vs_uniform": coh(E,U,key), "vs_density_matched": coh(E,M,key),
                "vs_shuffled": coh(E,S,key)}

# leave-one-out 1NN uniform random vs emergent
def loo1(X, y):
    X = np.array(X); cor=0
    for i in range(len(X)):
        d = np.linalg.norm(X-X[i],axis=1); d[i]=np.inf
        j = np.argmin(d); cor += (y[j]==y[i])
    return cor/len(X)

Xe = [[d[k] for k in keys] for d in E]
Xu = [[d[k] for k in keys] for d in U]
Xm = [[d[k] for k in keys] for d in M]
acc_u = loo1(Xe+Xu, [1]*len(Xe)+[0]*len(Xu))
acc_m = loo1(Xe+Xm, [1]*len(Xe)+[0]*len(Xm))

out = {"cohens_d": res, "loo_acc_vs_uniform": acc_u, "loo_acc_vs_density_matched": acc_m,
       "n_emergent": len(E), "n_uniform": len(U), "n_densitymatched": len(M), "n_shuffled": len(S)}
print(json.dumps(out, indent=2))
json.dump(out, open("emp138_redteam_metrics.json","w"), indent=2)

fig, ax = plt.subplots(1, 3, figsize=(13,4))
for i,key in enumerate(keys):
    vals = [[d[key] for d in E], [d[key] for d in U], [d[key] for d in M], [d[key] for d in S]]
    ax[i].boxplot(vals, labels=["emergent","rand-uniform","rand-density","shuffled"])
    ax[i].set_title(key)
plt.suptitle("EMP-138 red-team: entropy discrimination under density-matched controls")
plt.tight_layout(); plt.savefig("emp138_redteam.png", dpi=130)
print("saved emp138_redteam.png")
