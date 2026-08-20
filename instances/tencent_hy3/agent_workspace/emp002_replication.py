import numpy as np, zlib, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt

def lempel_ziv_complexity(s):
    n=len(s)
    if n==0: return 0
    c=1; i=1
    while i<n:
        j=1; found=True
        while i+j<=n:
            if s[i:i+j] not in s[0:i+j-1]:
                c+=1; i+=j; found=False; break
            j+=1
        if found: break
    return c

def coarse_state(grid, bs=4):
    rows,cols=grid.shape; st=[]
    for i in range(0,rows,bs):
        for j in range(0,cols,bs):
            d=grid[i:i+bs,j:j+bs].sum()/(bs*bs)
            st.append(str(int(min(3,np.floor(d*4)))))
    return ''.join(st)

def gol_step_vec(grid, toroidal=False):
    rows,cols=grid.shape; nw=np.zeros_like(grid)
    for di in(-1,0,1):
        for dj in(-1,0,1):
            if di==0 and dj==0: continue
            if toroidal:
                sh=np.roll(grid,(di,dj),axis=(0,1))
            else:
                s=np.zeros_like(grid)
                si=np.arange(rows)+di; sj=np.arange(cols)+dj
                vi=(si>=0)&(si<rows); vj=(sj>=0)&(sj<cols)
                s[np.ix_(si[vi],sj[vj])]=grid[np.ix_(vi,vj)]
                sh=s
            nw+=sh
    new=np.zeros_like(grid)
    new[(grid==1)&((nw==2)|(nw==3))]=1
    new[(grid==0)&(nw==3)]=1
    return new

def lz_zlib(seq): return len(zlib.compress(''.join(seq).encode('ascii'),9))
def rolling(seq, fn, window=20):
    # FIX: join the windowed slice into a single string BEFORE applying fn,
    # mirroring kimi_code's temporal_lz(''.join(state_sequence)).
    out=[]
    for i in range(len(seq)):
        out.append(fn(''.join(seq[max(0,i-window+1):i+1])))
    return out

def rolling_last(seq, fn, window=20):
    # cheap: only the final rolling-window value (settling probe)
    return fn(''.join(seq[max(0,len(seq)-window+1):]))

def simulate(grid, gens, bs=4, toroidal=False, use_naive=False):
    g=grid.copy(); ss=[]
    for _ in range(gens):
        ss.append(coarse_state(g,bs)); g=gol_step_vec(g,toroidal)
    if use_naive:
        tl=lempel_ziv_complexity(''.join(ss)); rl=rolling(ss,lempel_ziv_complexity)
    else:
        tl=lz_zlib(ss); rl=rolling(ss,lz_zlib)
    return ss,tl,rl

def simulate_last(grid, gens, bs=4, toroidal=False, use_naive=False):
    g=grid.copy(); ss=[]
    for _ in range(gens):
        ss.append(coarse_state(g,bs)); g=gol_step_vec(g,toroidal)
    if use_naive:
        tl=lempel_ziv_complexity(''.join(ss)); rl=rolling_last(ss,lempel_ziv_complexity)
    else:
        tl=lz_zlib(ss); rl=rolling_last(ss,lz_zlib)
    return ss,tl,rl

def block(s):
    g=np.zeros(s,int); g[s[0]//2:s[0]//2+2,s[1]//2:s[1]//2+2]=1; return g
def glider(s):
    g=np.zeros(s,int); g[1,2]=1; g[2,3]=1; g[3,1:4]=1; return g
def rpent(s):
    g=np.zeros(s,int); g[s[0]//2,s[1]//2+1]=1; g[s[0]//2+1,s[1]//2:s[1]//2+2]=1; g[s[0]//2+2,s[1]//2+1]=1; return g
def rnd(s,d=0.3,seed=0):
    return np.random.default_rng(seed).choice([0,1],size=s,p=[1-d,d])
def gun(s):
    g=np.zeros(s,int)
    pts=[(5,1),(5,2),(6,1),(6,2),(5,11),(6,11),(7,11),(4,12),(8,12),(3,13),(9,13),(3,14),(9,14),(6,15),(4,16),(8,16),(5,17),(6,17),(7,17),(6,18),(3,21),(4,21),(5,21),(3,22),(4,22),(5,22),(2,23),(6,23),(1,25),(2,25),(6,25),(7,25),(3,35),(4,35),(3,36),(4,36)]
    for (r,c) in pts:
        if 0<=r<s[0] and 0<=c<s[1]: g[r,c]=1
    return g

ART="/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts"
def run():
    res={}
    gs=(40,40); G=100
    print("=== (A) 40x40/100gen faithful reproduction (LZ76 naive) ===")
    for nm,g in [("Block",block(gs)),("Glider",glider(gs)),("R-Pentomino",rpent(gs)),("Random",rnd(gs,0.5,1))]:
        ss,tl,rl=simulate(g,G,use_naive=True)
        print(f"  {nm:12s} tempLZ={tl:6d} finalRoll={rl[-1]:4d}")

    print("=== (B) zlib(LZ77) proxy validation vs naive LZ76 (40x40) ===")
    for nm,g in [("Block",block(gs)),("Glider",glider(gs)),("R-Pentomino",rpent(gs)),("Random",rnd(gs,0.5,1))]:
        gg=g.copy(); ss=[]
        for _ in range(G): ss.append(coarse_state(gg)); gg=gol_step_vec(gg)
        nv=lempel_ziv_complexity(''.join(ss)); zb=lz_zlib(ss)
        print(f"  {nm:12s} naive={nv:6d} zlib={zb:6d} ratio={zb/max(nv,1):.3f}")

    print("=== (C/D/E) 100x100/300gen scale-out (zlib proxy) ===")
    gs2=(100,100); G2=300
    cls=[("Block",block(gs2)),("Glider",glider(gs2)),("R-Pentomino",rpent(gs2)),("GliderGun",gun(gs2))]
    for nm,g in cls:
        ss,tl,rl=simulate(g,G2); L=len(''.join(ss))
        print(f"  {nm:12s} tempLZ={tl:7d} finalRoll={rl[-1]:6d} norm={tl/L:.4f} L={L}")

    print("  Random 5 seeds OPEN BC:")
    rs=[]; rsr=[]
    for seed in range(5):
        ss,tl,rl=simulate_last(rnd(gs2,0.3,seed),G2); L=len(''.join(ss)); rs.append(tl); rsr.append(rl)
        print(f"    seed{seed} tempLZ={tl:7d} finalRoll={rl:6d} norm={tl/L:.4f}")
    rm=np.mean(rs); print(f"    RANDOM mean={rm:.1f}")
    print("  Random 5 seeds TOROIDAL BC:")
    ts=[]; tsr=[]
    for seed in range(5):
        ss,tl,rl=simulate_last(rnd(gs2,0.3,seed),G2,toroidal=True); ts.append(tl); tsr.append(rl)
        print(f"    seed{seed} tempLZ={tl:7d} finalRoll={rl:6d}")
    tm=np.mean(ts); print(f"    TOROIDAL mean={tm:.1f}")

    fig,ax=plt.subplots(figsize=(11,6))
    for nm,g in [("Block",block(gs)),("Glider",glider(gs)),("R-Pentomino",rpent(gs)),("Random",rnd(gs,0.5,1))]:
        ss,tl,rl=simulate(g,G,use_naive=True)
        ax.plot(rl,label=f"{nm} (fin={rl[-1]})")
    ax.set_title("Replication 40x40/100gen openBC: Rolling Temporal LZ [LZ76 naive]")
    ax.set_xlabel("Generation"); ax.set_ylabel("Rolling Temp LZ (w=20)"); ax.legend(); ax.grid(True); plt.tight_layout()
    plt.savefig(f"{ART}/emp002_rep_40x40_rolling.png"); plt.close()

    fig,ax=plt.subplots(figsize=(11,6))
    for nm,g in cls:
        ss,tl,rl=simulate(g,G2)
        ax.plot(rl,label=f"{nm} (fin={rl[-1]})")
    ax.set_title("Scale-out 100x100/300gen openBC: Rolling Temporal LZ [LZ77 proxy]")
    ax.set_xlabel("Generation"); ax.set_ylabel("Rolling Temp LZ (w=20)"); ax.legend(); ax.grid(True); plt.tight_layout()
    plt.savefig(f"{ART}/emp002_rep_100x100_rolling.png"); plt.close()

    fig,ax=plt.subplots(figsize=(10,6))
    seeds=list(range(5))
    ax.bar([s-0.2 for s in seeds],rs,width=0.4,label="OPEN",color="red")
    ax.bar([s+0.2 for s in seeds],ts,width=0.4,label="TOROIDAL",color="orange")
    ax.set_title("Random soup tempLZ(zlib): boundary-condition sensitivity")
    ax.set_xlabel("Seed"); ax.set_ylabel("Full-sequence Temp LZ (zlib bytes)"); ax.legend(); ax.grid(True); plt.tight_layout()
    plt.savefig(f"{ART}/emp002_rep_boundary_test.png"); plt.close()

    fig,ax=plt.subplots(figsize=(11,6))
    L100=(100//4)*(100//4)*300
    norms=[simulate(block(gs2),G2)[1]/L100, simulate(glider(gs2),G2)[1]/L100,
           simulate(rpent(gs2),G2)[1]/L100, simulate(gun(gs2),G2)[1]/L100, rm/L100]
    names=["Block","Glider","R-Pentomino","GliderGun","Random(mean)"]
    ax.bar(names,norms,color=["gray","blue","green","purple","red"])
    ax.set_title("Normalised Temporal LZ (zlib/L): scale-invariant discrimination")
    ax.set_ylabel("Normalised Temporal LZ (bytes/symbol)"); plt.xticks(rotation=15,ha="right"); ax.grid(True); plt.tight_layout()
    plt.savefig(f"{ART}/emp002_rep_norm_bar.png"); plt.close()
    print("DONE: artifacts written.")

run()

