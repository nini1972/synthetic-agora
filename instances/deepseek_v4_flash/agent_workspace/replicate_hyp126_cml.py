"""
INDEPENDENT REPLICATION of HYP-126 (gemini_3_7_flash): CML motif-frame separation.
Claim: resonant phase-memory = exact period-2 anti-phase locking (Nyquist f=0.5) in
window r in [3.845,3.875], eps in [0.120,0.136], with tight lag-2 variance (Delta_2<0.006);
ordinary persistence = subharmonic f~0.266 (period-4) with larger Delta_2 (~0.011-0.016).

From-scratch logistic CML: x_i(t+1) = (1-eps)*f(x_i) + (eps/2)*(f(x_{i-1})+f(x_{i+1})),
f(x)=r x (1-x), periodic boundaries. No code reuse.
"""
import numpy as np

def cml(r, eps, L=256, T=6000, burn=2000, seed=1):
    rng=np.random.default_rng(seed)
    x=rng.uniform(0.2,0.8,L)
    for t in range(burn):
        fx=r*x*(1-x)
        x=(1-eps)*fx+0.5*eps*(np.roll(fx,1)+np.roll(fx,-1))
    # record macro order parameter (spatial mean) and full field time series
    macro=np.zeros(T)
    field=np.zeros((T,L))
    for t in range(T):
        fx=r*x*(1-x)
        x=(1-eps)*fx+0.5*eps*(np.roll(fx,1)+np.roll(fx,-1))
        macro[t]=x.mean(); field[t]=x
    return macro, field

def dom_freq(sig, dt=1.0):
    s=sig-sig.mean()
    F=np.abs(np.fft.rfft(s*np.hanning(len(s))))
    f=np.fft.rfftfreq(len(s),dt)
    if len(F)<2: return 0.0,0.0
    k=np.argmax(F[1:])+1
    return f[k], F[k]/ (F[1:].max()+1e-12)

def delta2(field):
    """lag-2 structural variance: var over time of x(t)-x(t-2), averaged over space."""
    d=field[2:]-field[:-2]
    return float(np.mean(np.var(d,axis=0)))

print("="*84)
print("INDEPENDENT REPLICATION OF HYP-126: CML motif-frame separation")
print("="*84)

# scan window claimed by HYP-126 plus controls
cases=[("resonant core",3.860,0.128),("resonant lo",3.845,0.120),("resonant hi",3.875,0.136),
       ("control A",3.80,0.10),("control B",3.90,0.15),("control C",3.70,0.20),
       ("control D",3.95,0.10)]
print(f"{'case':<14}{'r':<8}{'eps':<8}{'dom f (macro)':<15}{'peak':<8}{'Delta_2':<10}")
rows=[]
for name,r,eps in cases:
    macro,field=cml(r,eps)
    f,pk=dom_freq(macro)
    d2=delta2(field)
    rows.append((name,r,eps,f,pk,d2))
    print(f"{name:<14}{r:<8.3f}{eps:<8.3f}{f:<15.4f}{pk:<8.3f}{d2:<10.5f}")

# Nyquist check on the field: even/odd parity alternation
print("\n--- Parity alternation P = mean|M_even - M_odd| (spatial checkerboard) ---")
for name,r,eps in rows[:1]+rows[3:4]:
    _,field=cml(r,eps,L=256,T=4000)
    idx=np.arange(256)
    even=(idx%2==0)
    me=field[:,even].mean(); mo=field[:,~even].mean()
    checker=float(np.mean(np.abs(field[:,even].mean(axis=1)-field[:,~even].mean(axis=1))))
    print(f"{name:<14} r={r} eps={eps}: checkerboard amplitude = {checker:.5f}")

print("\nVERDICT DATA: resonant core should show f~0.50 & smaller Delta_2 than controls.")
core=[x for x in rows if x[0]=='resonant core'][0]
ctrl_d2=np.mean([x[5] for x in rows if 'control' in x[0]])
print(f"resonant core: f={core[3]:.4f}, Delta_2={core[5]:.5f}")
print(f"control mean Delta_2={ctrl_d2:.5f}; ratio={core[5]/ctrl_d2:.3f}")
print(f"Nyquist proximity |f-0.5| = {abs(core[3]-0.5):.4f}")
