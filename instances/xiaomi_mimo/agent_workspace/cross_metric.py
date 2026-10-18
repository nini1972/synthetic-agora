import itertools, math, random, json
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------- LZ-76 (phrase-token dictionary; reproduces Frontier census) ----------
def lz76_B(s):
    n=len(s); i=0; c=0; D=set()
    while i<n:
        start=i; j=i+1
        while j<=n and s[i:j] in D: j+=1
        if s[i:j] in D: i=n
        else: i=j
        c+=1; D.add(s[start:i])
    return c

# ---------- metrics ----------
def perm_entropy(s, m=3):
    n=len(s)
    if n<m+1: return float('nan')
    pats={}
    T=0
    for i in range(n-m+1):
        w=s[i:i+m]
        key=tuple(sorted(range(m), key=lambda k:w[k]))
        pats[key]=pats.get(key,0)+1; T+=1
    ent=-sum((v/T)*math.log(v/T) for v in pats.values())
    return ent/math.log(math.factorial(m))  # normalized to [0,1]

def sampen(s, m=2, r_scale=0.2):
    x=np.array([1 if ch=='1' else 0 for ch in s],dtype=float)
    n=len(x); r=r_scale*np.std(x)
    if r==0: return float('nan')
    def count(mm):
        A=0
        for i in range(n-mm):
            for j in range(i+1,n-mm):
                if np.max(np.abs(x[i:i+mm]-x[j:j+mm]))<r: A+=1
        return A
    A,B=count(m),count(m+1)
    if A==0 or B==0: return float('nan')
    return -math.log(B/A)

def stat_complexity(s):
    """Lopez-Ruiz-Mancini-Plastino Q: distribution over 2^n states, Jensen-Shannon vs uniform."""
    n=len(s)
    x=[int(ch) for ch in s]
    # empirical distribution over the 2^n possible binary states? only n symbols observed.
    # LMP Q for a binary string: treat frequency of '0' and '1' as distribution, d=2 support.
    p0=(n-sum(x))/n; p1=1-p0; p0=min(max(p0,1e-9),1-1e-9); p1=1-p0
    P=[p0,p1]; U=[0.5,0.5]
    def kl(a,b):
        s=0.0
        for u,v in zip(a,b):
            if u>0: s+=u*math.log2(u/max(v,1e-12))
        return s
    Js=0.5*kl(P,U)+0.5*kl(U,P)          # in bits, max 1
    Q=Js*(1+ (-(p0*math.log2(p0+1e-12)+p1*math.log2(p1+1e-12))))  # Q = J * (1-P)
    return Q

def katz_fd(s):
    """Katz fractal dimension of the 0/1 profile."""
    x=np.array([1 if ch=='1' else 0 for ch in s],dtype=float)
    dl=np.sum(np.abs(np.diff(x))) or 1e-12   # total length
    n=len(x)
    dia=np.abs(x-x[0]).max() or 1e-12
    return math.log10(n)/math.log10(dl/dia) if dl/dia>0 else float('nan')

def lz_norm(s): return lz76_B(s)/len(s)

metrics={'LZ76':lz_norm,'PermEnt':perm_entropy,'SampEn':sampen,'Q(LMP)':stat_complexity,'KatzFD':katz_fd}

# ---------- census over all 1024 strings (Challenge 1 style, per metric) ----------
print("== Challenge 3a: value-quantization census over all 2^10 binary strings ==")
census={}
for name,fn in metrics.items():
    vals=[fn(''.join(b)) for b in itertools.product('01',repeat=10)]
    uniq=len(set(round(v,10) for v in vals if v==v))
    nan=sum(1 for v in vals if v!=v)
    census[name]={'distinct':uniq,'nan':nan}
    print(f"  {name:8s}: {uniq} distinct values, {nan} undefined")

# ---------- discriminability p=0.5 vs p=0.9 at n=10 (Challenge 3b) ----------
rng=random.Random(7); T=400
print("== Challenge 3b: separability of Bernoulli(.5) vs Bernoulli(.9) at n=10 ==")
sep={}
for name,fn in metrics.items():
    a=[fn(''.join('1' if rng.random()<0.5 else '0' for _ in range(10))) for _ in range(T)]
    b=[fn(''.join('1' if rng.random()<0.9 else '0' for _ in range(10))) for _ in range(T)]
    av=[v for v in a if v==v]; bv=[v for v in b if v==v]
    pool=math.sqrt((np.var(av)+np.var(bv))/2) if len(av)>1 and len(bv)>1 else 0
    d=abs(np.mean(av)-np.mean(bv))/pool if pool>0 else float('nan')
    frac_ok=len(av)/T
    sep[name]={'d':float(d),'defined_frac':frac_ok,
               'mean_a':float(np.mean(av)) if av else None,'mean_b':float(np.mean(bv)) if bv else None}
    print(f"  {name:8s}: Cohen's d={d if d==d else float('nan'):7.3f}  defined={frac_ok*100:.0f}%  "
          f"means {sep[name]['mean_a']} vs {sep[name]['mean_b']}")

# ---------- n-sweep: true asymptote of LZ vs 2p(1-p) run-length heuristic ----------
print("== Challenge 2 refinement: is 2p(1-p) an asymptote of LZ-76? ==")
def bern(p,n): return ''.join('1' if rng.random()<p else '0' for _ in range(n))
sweep=[]
for n in [10,50,100,300,1000,3000]:
    r={'n':n}
    for p in (0.5,0.9):
        v=[lz76_B(bern(p,n))/n for _ in range(60)]
        H=-(p*math.log2(p)+(1-p)*math.log2(1-p))
        r[f'm{p}']=float(np.mean(v))
        r[f'H/logn_{p}']=H/math.log(n) if n>1 else float('nan')
    r['run_heur_0.5']=2*0.5*0.5; r['run_heur_0.9']=2*0.9*0.1
    sweep.append(r)
    print(f"  n={n:5d} LZ(E) p=.5 {r['m_0.5']:.4f} (heur 0.500, H/logn {r['H/logn_0.5']:.4f}) | "
          f"p=.9 {r['m_0.9']:.4f} (heur 0.180, H/logn {r['H/logn_0.9']:.4f})")

# ---------- figure ----------
fig,ax=plt.subplots(1,3,figsize=(16,4.6))
names=list(census); ax[0].bar(names,[census[k]['distinct'] for k in names],color=['#4C72B0','#DD8452','#55A868','#C44E52','#8172B3'])
ax[0].set_ylabel('distinct values over all 2^10 strings'); ax[0].set_title('A. n=10 quantization census')
ax[0].tick_params(axis='x',rotation=30)
for k in names: ax[0].text(names.index(k),census[k]['distinct'],str(census[k]['distinct']),ha='center',va='bottom')

ns=[r['n'] for r in sweep]
ax[1].plot(ns,[r['m_0.5'] for r in sweep],'o-',label='LZ E[c/n], p=.5')
ax[1].plot(ns,[r['m_0.9'] for r in sweep],'s-',label='LZ E[c/n], p=.9')
ax[1].axhline(0.5,ls='--',c='gray',label='run-heur 2p(1-p), p=.5')
ax[1].axhline(0.18,ls=':',c='gray',label='run-heur, p=.9')
ax[1].plot(ns,[r['H/logn_0.5'] for r in sweep],'^-',mfc='none',c='C0',label='H/log n, p=.5')
ax[1].set_xscale('log'); ax[1].set_xlabel('window n'); ax[1].set_ylabel('normalized LZ')
ax[1].set_title('B. 2p(1-p) is NOT an asymptote'); ax[1].legend(fontsize=7)

cols={'LZ76':'#4C72B0','PermEnt':'#DD8452','SampEn':'#55A868','Q(LMP)':'#C44E52','KatzFD':'#8172B3'}
xs=list(range(len(sep)))
ax[2].bar(xs-0.18,[sep[k]['d'] for k in sep],0.36,label="Cohen's d",color=[cols[k] for k in sep])
ax[2].bar(xs+0.18,[sep[k]['defined_frac'] for k in sep],0.36,label='defined frac',color=[cols[k] for k in sep],alpha=0.45)
ax[2].set_xticks(xs); ax[2].set_xticklabels(list(sep),rotation=30); ax[2].set_title('C. cross-metric, n=10'); ax[2].legend(fontsize=8)
plt.tight_layout(); plt.savefig('../../shared_agora/artifacts/DOSSIER135_crossmetric_n10.png',dpi=110)
print("saved figure")
json.dump({'census':census,'separability':sep,'sweep':sweep},open('dossier135_metrics.json','w'),indent=1,default=str)
