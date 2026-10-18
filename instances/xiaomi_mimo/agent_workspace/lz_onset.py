import itertools, math, random, json, collections
import numpy as np

# ---------- LZ-76, variant B (dictionary = emitted phrase tokens) -> reproduces 16/128/880 ----------
def lz76_B(s):
    n=len(s); i=0; c=0; D=set()
    while i<n:
        start=i; j=i+1
        while j<=n and s[i:j] in D: j+=1
        if s[i:j] in D: i=n
        else: i=j
        c+=1; D.add(s[start:i])
    return c

def lz76_A(s):   # classic: all substrings of parsed prefix
    n=len(s); i=0; c=0
    while i<n:
        c+=1; j=i+1
        while j<=n and s.find(s[i:j],0,i)>=0: j+=1
        i=j
    return c

# ---------- Challenge 1: exact census ----------
distB=collections.Counter(); distA=collections.Counter()
for bits in itertools.product('01',repeat=10):
    s=''.join(bits); distB[lz76_B(s)]+=1; distA[lz76_A(s)]+=1
print("CENSUS variant B (phrase tokens):", dict(sorted(distB.items())), " target {4:16,5:128,6:880}",
      "MATCH" if dict(sorted(distB.items()))=={4:16,5:128,6:880} else "NO")
print("CENSUS variant A (classic substrings):", dict(sorted(distA.items())))

# exact expected c/n for Bernoulli(p), n=10 (zero sampling error)
for p in (0.5,0.9):
    e=0.0
    for bits in itertools.product('01',repeat=10):
        s=''.join(bits); k=s.count('1')
        w=(p**k)*((1-p)**(10-k)); e+=w*lz76_B(s)/10
    print(f"  exact E[c/n | n=10, p={p}] = {e:.4f}   (asymptote 2p(1-p)={2*p*(1-p):.4f})")

# ---------- Challenge 2: onset of degeneracy ----------
def bern(p,n,rng): return ''.join('1' if rng.random()<p else '0' for _ in range(n))
rng=random.Random(20261015)
ns=[10,20,40,80,100,200,400,800,1600,3200]
T=300
rows=[]
for n in ns:
    row={'n':n}
    for p in (0.5,0.9):
        vals=[lz76_B(bern(p,n,rng))/n for _ in range(T)]
        m=float(np.mean(vals)); sd=float(np.std(vals))
        tgt=2*p*(1-p)
        row[f'mean_{p}']=m; row[f'sd_{p}']=sd
        row[f'relerr_{p}']=abs(m-tgt)/tgt
    # discriminability between the two populations (Cohen's d)
    a=[lz76_B(bern(0.5,n,rng))/n for _ in range(T)]
    b=[lz76_B(bern(0.9,n,rng))/n for _ in range(T)]
    pooled=math.sqrt((np.var(a)+np.var(b))/2)
    row['d']=abs(np.mean(a)-np.mean(b))/pooled if pooled>0 else float('inf')
    row['distinct_at_10']=None
    rows.append(row)
    print(f"n={n:5d}  E[c/n] p=.5 {row['mean_0.5']:.4f} (relerr {row['relerr_0.5']*100:5.1f}%)  "
          f"p=.9 {row['mean_0.9']:.4f} (relerr {row['relerr_0.9']*100:5.1f}%)  d={row['d']:.2f}")

def n_min(key, thr=0.05):
    for r in rows:
        if r[key]<thr: return r['n']
    return None
print("n_min (5% rel. err, p=0.5):", n_min('relerr_0.5'))
print("n_min (5% rel. err, p=0.9):", n_min('relerr_0.9'))

# distinct values achievable at small n (quantization width)
for n in [10,20,40,80,100,200]:
    vals=set()
    for bits in itertools.product('01',repeat=n) if n<=16 else (tuple(rng.choice('01') for _ in range(n)) for _ in range(4000)):
        vals.add(lz76_B(''.join(bits))/n)
    print(f"  n={n}: {len(vals)} distinct c/n values observed (grid step 1/n={1/n:.4f})")

json.dump(rows, open('lz_onset_rows.json','w'), indent=1)
