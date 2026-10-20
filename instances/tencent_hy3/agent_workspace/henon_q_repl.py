"""Independent replication of Hénon morphospace Q = -lam - D2 - K (HYP-120 / EMP-149).
Test claim: Q is NOT universal constant ~-2.08; it varies across a and can sign-flip.
"""
import numpy as np, json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def henon_lyap(a, b=0.3, n=50000, burn=10000):
    x, y = 0.1, 0.1
    for _ in range(burn):
        x, y = 1 - a*x*x + y, b*x
    x1, y1 = x, y
    dx, dy = 1e-8, 0.0
    lam = 0.0; nrm = 0
    for i in range(n):
        x, y = 1 - a*x*x + y, b*x
        jxx = -2*a*x1; jxy = 1.0; jyx = b; jyy = 0.0
        ndx = jxx*dx + jxy*dy
        ndy = jyx*dx + jyy*dy
        x1, y1 = x, y
        dx, dy = ndx, ndy
        d = np.sqrt(dx*dx + dy*dy)
        lam += np.log(d)
        dx /= d; dy /= d
        nrm += 1
    return lam/nrm

def corr_dim(xs, m=2, rvals=None, subsample=1500):
    N=len(xs); M=N-(m-1)
    emb=np.array([xs[i:i+m] for i in range(M)])
    if M>subsample:
        idx=np.random.default_rng(0).choice(M,subsample,replace=False)
        emb=emb[idx]
    # pairwise distances (numpy, no scipy)
    D=np.sqrt(((emb[:,None,:]-emb[None,:,:])**2).sum(-1))
    np.fill_diagonal(D, np.inf)
    if rvals is None:
        rvals=np.logspace(-3,0,15)
    C=np.array([np.mean(D<r) for r in rvals])
    mask=(rvals>0.01)&(rvals<0.3)&(C>0)
    if mask.sum()<3: mask=(C>0)
    lr=np.polyfit(np.log(rvals[mask]),np.log(C[mask]),1)
    return lr[0]

def henon_K(a, b=0.3, n=40000, burn=5000):
    x, y = 0.1, 0.1
    for _ in range(burn):
        x, y = 1 - a*x*x + y, b*x
    sxx=0.0
    for _ in range(n):
        x, y = 1 - a*x*x + y, b*x
        sxx+=x*x
    return a*(sxx/n)   # K = a*<x^2>

as_=np.round(np.arange(0.4,1.41,0.05),2)
rows=[]
for a in as_:
    lam=henon_lyap(a)
    xs=[]
    x,y=0.1,0.1
    for _ in range(5000):
        x,y=1-a*x*x+y,0.3*x
        xs.append(x)
    xs=np.array(xs)
    D2=corr_dim(xs,m=2)
    K=henon_K(a)
    Q=-lam-D2-K
    rows.append(dict(a=float(a),lam_max=float(lam),D2=float(D2),K=float(K),Q=float(Q)))
    print(f"a={a:.2f} lam={lam:.3f} D2={D2:.3f} K={K:.3f} Q={Q:.3f}")

with open('henon_q_repl.json','w') as fh:
    json.dump(rows,fh,indent=2)

A=np.array([r['a'] for r in rows]); Q=np.array([r['Q'] for r in rows])
fig,ax=plt.subplots(1,2,figsize=(11,4))
ax[0].plot(A,Q,'o-')
ax[0].axhline(-2.08,color='r',ls='--',label='claimed universal Q=-2.08')
ax[0].axhline(0,color='k',lw=0.5)
ax[0].set_xlabel('Hénon a'); ax[0].set_ylabel('Q'); ax[0].set_title('Morphospace Q vs a'); ax[0].legend()
ax[1].plot(A,[r['lam_max'] for r in rows],label='lam')
ax[1].plot(A,[r['D2'] for r in rows],label='D2')
ax[1].plot(A,[r['K'] for r in rows],label='K')
ax[1].set_xlabel('Hénon a'); ax[1].set_ylabel('value'); ax[1].set_title('Q components'); ax[1].legend()
plt.tight_layout(); plt.savefig('henon_q_repl.png',dpi=120)
print("DONE")
