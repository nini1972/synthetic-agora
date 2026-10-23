"""
REFINEMENT / ADVERSARIAL TEST of HYP-126.
Observation from first pass: the SPATIAL-MEAN (macro) dominant frequency is 0.5 (Nyquist)
for almost ALL (r,eps) probed, including controls outside the claimed window.
=> f=0.5 on the macro mode is NOT a sufficient discriminator.

Test the sharper claim: does a CHECKERBOARD parity order parameter (site-even vs site-odd)
+ tight lag-2 variance Delta_2 uniquely flag the claimed resonant window r in [3.845,3.875],
eps in [0.120,0.136]?
"""
import numpy as np

def cml(r, eps, L=256, T=5000, burn=2000, seed=1):
    rng=np.random.default_rng(seed)
    x=rng.uniform(0.2,0.8,L)
    for t in range(burn):
        fx=r*x*(1-x); x=(1-eps)*fx+0.5*eps*(np.roll(fx,1)+np.roll(fx,-1))
    field=np.zeros((T,L))
    for t in range(T):
        fx=r*x*(1-x); x=(1-eps)*fx+0.5*eps*(np.roll(fx,1)+np.roll(fx,-1)); field[t]=x
    return field

def metrics(field):
    T,L=field.shape
    macro=field.mean(axis=1)
    def domf(s):
        s=s-s.mean(); F=np.abs(np.fft.rfft(s*np.hanning(len(s))))
        f=np.fft.rfftfreq(len(s)); k=np.argmax(F[1:])+1; return f[k]
    fm=domf(macro)
    # checkerboard parity order parameter: alternating spatial sum
    idx=np.arange(L); sign=(-1.0)**idx
    check=field@sign/L
    fc=domf(check)
    # lag-2 structural variance
    d2=float(np.mean(np.var(field[2:]-field[:-2],axis=0)))
    # checkerboard amplitude (rms)
    amp=float(np.std(check))
    return fm,fc,d2,amp

print("="*90)
print("ADVERSARIAL TEST OF HYP-126: is the resonant window UNIQUELY flagged?")
print("="*90)
print(f"{'case':<14}{'r':<7}{'eps':<7}{'f_macro':<9}{'f_check':<9}{'Delta_2':<10}{'check_amp':<11}")
cases=[("core",3.860,0.128),("lo",3.845,0.120),("hi",3.875,0.136),
       ("ctl A",3.80,0.10),("ctl B",3.90,0.15),("ctl C",3.70,0.20),
       ("ctl D",3.95,0.10),("ctl E",3.83,0.13),("ctl F",3.89,0.13)]
res=[]
for name,r,eps in cases:
    fm,fc,d2,amp=metrics(cml(r,eps))
    res.append((name,r,eps,fm,fc,d2,amp))
    print(f"{name:<14}{r:<7.3f}{eps:<7.3f}{fm:<9.3f}{fc:<9.3f}{d2:<10.5f}{amp:<11.5f}")

core=[x for x in res if x[0]=='core'][0]
ctls=[x for x in res if 'ctl' in x[0]]
print("\n--- SUMMARY ---")
print(f"core Delta_2 = {core[5]:.5f} ; control Delta_2 range = "
      f"[{min(c[5] for c in ctls):.5f}, {max(c[5] for c in ctls):.5f}]")
print(f"core check_amp = {core[6]:.5f} ; control check_amp range = "
      f"[{min(c[6] for c in ctls):.5f}, {max(c[6] for c in ctls):.5f}]")
sep = core[5] < min(c[5] for c in ctls)
print(f"Delta_2 cleanly separates core from ALL controls? {sep}")
