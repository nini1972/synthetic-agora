import numpy as np
def run_cml(r, eps, L=128, T=600, trans=300, seed=42, bc='periodic'):
    rng=np.random.default_rng(seed); x=rng.uniform(0.1,0.9,L)
    for _ in range(trans):
        fx=r*x*(1-x)
        if bc=='periodic':
            x=(1-eps)*fx+eps/2*(np.roll(fx,1)+np.roll(fx,-1))
        else:
            xnew=fp=(1-eps)*fx+eps/2*(np.roll(fx,1)+np.roll(fx,-1))
            xnew[0]=(1-eps)*fx[0]+eps*fx[1]; xnew[-1]=(1-eps)*fx[-1]+eps*fx[-2]
            x=xnew
    frames=[]
    for _ in range(T):
        fx=r*x*(1-x)
        if bc=='periodic':
            x=(1-eps)*fx+eps/2*(np.roll(fx,1)+np.roll(fx,-1))
        else:
            xnew=(1-eps)*fx+eps/2*(np.roll(fx,1)+np.roll(fx,-1))
            xnew[0]=(1-eps)*fx[0]+eps*fx[1]; xnew[-1]=(1-eps)*fx[-1]+eps*fx[-2]
            x=xnew
        frames.append(x.copy())
    return np.array(frames)

def autocorr_period(sig, maxlag=40):
    s=sig-sig.mean(); n=len(s); acf=np.array([np.corrcoef(s[:-l],s[l:])[0,1] if l>0 else 1.0 for l in range(maxlag)])
    # find first positive lag with acf closest to +1 (period)
    cand=[(l,acf[l]) for l in range(1,maxlag) if acf[l]>0.5]
    if cand:
        return min(cand,key=lambda t:-t[1])[0]
    return None

def metrics(frames):
    sm=frames.mean(axis=1); T=len(sm)
    spec=np.abs(np.fft.rfft(sm-sm.mean()))**2; fr=np.fft.rfftfreq(T)
    fpeak=fr[np.argmax(spec[1:])+1]; per=autocorr_period(sm)
    D2=np.mean((frames[2:]-frames[:-2])**2)
    sims=[]
    for lag in range(1,17):
        a,b=frames[:-lag],frames[lag:]; ac=a-a.mean(1,keepdims=True); bc=b-b.mean(1,keepdims=True)
        num=np.sum(ac*bc,1); den=np.sqrt(np.sum(ac**2,1)*np.sum(bc**2,1)+1e-12); sims.append(num/den)
    sims=np.mean(np.array(sims),1); pe=np.mean(sims[1::2]); po=np.mean(sims[0::2])
    return dict(fpeak=fpeak,period=per,D2=D2,parity=max(0,pe-po),pe=pe,po=po)

print("INDEPENDENT REPLICATION (3 seeds) of HYP-126 CML motif-frame separation:")
cands=[('Ordinary',3.8883,0.1030),('Ordinary',3.9050,0.1030),('Resonant',3.8450,0.1307),('Resonant',3.8450,0.1200),('Chaos',4.0,0.2)]
for label,r,eps in cands:
    rs=[metrics(run_cml(r,eps,seed=s)) for s in [11,22,33]]
    fp=np.mean([x['fpeak'] for x in rs]); pe=np.mean([x['period'] for x in rs]); d2=np.mean([x['D2'] for x in rs]); pa=np.mean([x['parity'] for x in rs])
    print(f"  [{label}] r={r},eps={eps}: fpeak={fp:.3f} period~{pe} D2={d2:.4f} parity={pa:.3f}")

print("\nLattice-size & boundary robustness (Resonant r=3.845,eps=0.1307):")
for L in [64,128,256]:
    for bc in ['periodic','fixed']:
        m=metrics(run_cml(3.845,0.1307,L=L,bc=bc,seed=5))
        print(f"  L={L} {bc:8s}: fpeak={m['fpeak']:.3f} period={m['period']} D2={m['D2']:.4f} parity={m['parity']:.3f}")

print("\nParameter scan around resonance (eps fixed 0.1307): does f=0.5 lock only near r=3.845?")
for r in [3.80,3.82,3.845,3.86,3.88,3.90]:
    m=metrics(run_cml(r,0.1307,seed=9))
    print(f"  r={r}: fpeak={m['fpeak']:.3f} D2={m['D2']:.4f} parity={m['parity']:.3f}")
