import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt

def run_cml(r, eps, L=128, T=600, trans=300, seed=42):
    rng=np.random.default_rng(seed); x=rng.uniform(0.1,0.9,L)
    for _ in range(trans):
        fx=r*x*(1-x); x=(1-eps)*fx+eps/2*(np.roll(fx,1)+np.roll(fx,-1))
    fr=[]
    for _ in range(T):
        fx=r*x*(1-x); x=(1-eps)*fx+eps/2*(np.roll(fx,1)+np.roll(fx,-1)); fr.append(x.copy())
    return np.array(fr)

def metrics(frames):
    sm=frames.mean(axis=1); spec=np.abs(np.fft.rfft(sm-sm.mean()))**2; fr=np.fft.rfftfreq(len(sm))
    fpeak=fr[np.argmax(spec[1:])+1]
    D2=np.mean((frames[2:]-frames[:-2])**2)
    sims=[]
    for lag in range(1,17):
        a,b=frames[:-lag],frames[lag:]; ac=a-a.mean(1,keepdims=True); bc=b-b.mean(1,keepdims=True)
        num=np.sum(ac*bc,1); den=np.sqrt(np.sum(ac**2,1)*np.sum(bc**2,1)+1e-12); sims.append(np.mean(num/den))
    pe=np.mean(sims[1::2]); po=np.mean(sims[0::2])
    return fpeak,max(0,pe-po),D2

# Three labeled regimes + scan
regimes=[('Ordinary',3.8883,0.1030),('Resonant',3.8450,0.1307),('Chaos',4.0000,0.2000)]
fig,axs=plt.subplots(1,3,figsize=(13,4))
labels=[];fp=[];pa=[];d2=[]
for lab,r,e in regimes:
    f,p,d=metrics(run_cml(r,e,seed=7)); labels.append(lab);fp.append(f);pa.append(p);d2.append(d)
axs[0].bar(labels,fp,color=['C0','C2','C3']);axs[0].axhline(0.5,ls='--',c='k',lw=1);axs[0].set_title('Peak FFT freq (Nyquist=0.5)');axs[0].set_ylim(0,0.6)
axs[1].bar(labels,pa,color=['C0','C2','C3']);axs[1].set_title('Parity index (even-odd sim)')
axs[2].bar(labels,d2,color=['C0','C2','C3']);axs[2].set_title('Lag-2 drift D2 (lower=locked)')
plt.tight_layout(); plt.savefig('../../shared_agora/artifacts/hyp126_replication.png',dpi=110)

# Resonance band scan
rs=np.linspace(3.78,3.95,18); fps=[];pars=[];d2s=[]
for r in rs:
    f,p,d=metrics(run_cml(r,0.1307,seed=3)); fps.append(f);pars.append(p);d2s.append(d)
plt.figure(figsize=(7,4))
plt.plot(rs,fps,'o-',label='fpeak');plt.axhline(0.5,ls='--',c='k');plt.axvline(3.845,ls=':',c='gray')
plt.xlabel('r (eps=0.1307)');plt.ylabel('fpeak');plt.title('Resonant Nyquist lock is a BROAD band (fpeak=0.5)');plt.legend();plt.grid(0.3)
plt.tight_layout();plt.savefig('../../shared_agora/artifacts/hyp126_resonance_band.png',dpi=110)
print('saved plots; fpeak by regime:',fp)
