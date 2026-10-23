"""
2D PARAMETER-PLANE SCAN for HYP-126 adversarial test.
Map Delta_2(r,eps) and checkerboard amplitude over the region containing the claimed
resonant window (r in [3.845,3.875], eps in [0.120,0.136]).
If HYP-126 is right, the window should appear as a distinct basin/ridge in Delta_2 or checkerboard.
"""
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt

def cml_metrics(r,eps,L=128,T=3000,burn=1500,seed=2):
    rng=np.random.default_rng(seed); x=rng.uniform(0.2,0.8,L)
    for _ in range(burn):
        fx=r*x*(1-x); x=(1-eps)*fx+0.5*eps*(np.roll(fx,1)+np.roll(fx,-1))
    F=np.zeros((T,L))
    for t in range(T):
        fx=r*x*(1-x); x=(1-eps)*fx+0.5*eps*(np.roll(fx,1)+np.roll(fx,-1)); F[t]=x
    d2=float(np.mean(np.var(F[2:]-F[:-2],axis=0)))
    idx=np.arange(L); sign=(-1.0)**idx
    check=F@sign/L
    amp=float(np.std(check))
    # spectral entropy of checkerboard (low => coherent)
    c=check-check.mean(); P=np.abs(np.fft.rfft(c*np.hanning(len(c))))**2
    P=P/ (P.sum()+1e-12); ent=-np.sum(P*np.log(P+1e-12))/np.log(len(P)+1e-12)
    return d2,amp,ent

rs=np.linspace(3.78,3.93,22); epss=np.linspace(0.08,0.20,18)
D2=np.zeros((len(epss),len(rs))); AMP=np.zeros_like(D2); ENT=np.zeros_like(D2)
for i,e in enumerate(epss):
    for j,r in enumerate(rs):
        d2,amp,ent=cml_metrics(r,e)
        D2[i,j]=d2; AMP[i,j]=amp; ENT[i,j]=ent
    print(f"eps={e:.3f} done")

fig,axs=plt.subplots(1,3,figsize=(16,5))
for ax,Z,ttl in zip(axs,[D2,AMP,ENT],
        [r'$\Delta_2$ (lag-2 struct. var)', 'checkerboard amplitude', 'checkerboard spectral entropy']):
    im=ax.imshow(Z,origin='lower',aspect='auto',extent=[rs[0],rs[-1],epss[0],epss[-1]],
                 cmap='viridis')
    # overlay claimed window
    ax.plot([3.845,3.875,3.875,3.845,3.845],[0.120,0.120,0.136,0.136,0.120],'r-',lw=2)
    ax.set_xlabel('r'); ax.set_ylabel('eps'); ax.set_title(ttl); plt.colorbar(im,ax=ax)
plt.suptitle("HYP-126 adversarial scan: red box = claimed resonant window",y=1.02)
plt.tight_layout(); plt.savefig('hyp126_scan.png',dpi=105,bbox_inches='tight')

# Quantify: is the window a local minimum of Delta_2?
win=(rs>=3.845)&(rs<=3.875); we=(epss>=0.120)&(epss<=0.136)
core_d2=D2[np.ix_(we,win)].mean()
glob_min=np.unravel_index(np.argmin(D2),D2.shape)
print("\n"+"="*80)
print(f"core-window mean Delta_2 = {core_d2:.5f}")
print(f"global min Delta_2 = {D2[glob_min]:.5f} at r={rs[glob_min[1]]:.3f}, eps={epss[glob_min[0]]:.3f}")
print(f"global min inside claimed window? {(rs[glob_min[1]]>=3.845 and rs[glob_min[1]]<=3.875 and epss[glob_min[0]]>=0.120 and epss[glob_min[0]]<=0.136)}")
# rank of window in sorted Delta_2
flat=np.sort(D2.flatten())
print(f"window mean Delta_2 percentile = {100*np.mean(flat<core_d2):.1f}%")
print(f"fraction of plane with Delta_2 < 0.006 (the claimed threshold): {100*np.mean(D2<0.006):.1f}%")
print(f"fraction of plane with Delta_2 < core_d2: {100*np.mean(D2<core_d2):.1f}%")
print("Saved hyp126_scan.png")
