"""
Measure the TRUE escape seed: the maximum transient order parameter R_max reached
during the first epochs, as a function of gamma. Compare with the activation barrier R_u.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sim_track(omega, K0, a, seed, dt=0.05, T=200.0):
    rng=np.random.default_rng(seed); N=len(omega)
    th=rng.uniform(0,2*np.pi,N)
    nsteps=int(T/dt); Rmax=0.0; Rtraj=[]
    def deriv(th):
        z=np.mean(np.exp(1j*th)); R=np.abs(z); Psi=np.angle(z)
        return omega+K0*(R**a)*np.sin(Psi-th)
    for s in range(nsteps):
        k1=deriv(th);k2=deriv(th+0.5*dt*k1);k3=deriv(th+0.5*dt*k2);k4=deriv(th+dt*k3)
        th=th+(dt/6)*(k1+2*k2+2*k3+k4)
        if s%10==0:
            R=np.abs(np.mean(np.exp(1j*th))); Rtraj.append(R); Rmax=max(Rmax,R)
    return Rmax, Rtraj[-1]

K0,a,N=5.0,2.0,300
lorentz=lambda g,x:(1/np.pi)*(g/(x*x+g*g))
print("="*78)
print(f"ESCAPE-SEED MEASUREMENT  a={a}, K0={K0}, N={N} (16 seeds)")
print("="*78)
print(f"{'gamma':<8}{'mean R_max':<14}{'std':<10}{'lock frac':<12}{'R_final':<10}")
gammas=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.85,1.0]
data={}
for g in gammas:
    Rmaxs=[]; locks=0; rfs=[]
    for s in range(16):
        rng=np.random.default_rng(s)
        u=rng.uniform(1e-4,1-1e-4,N)
        om=g*np.tan(np.pi*(u-0.5))
        Rm,Rf=sim_track(om,K0,a,s)
        Rmaxs.append(Rm); rfs.append(Rf)
        if Rf>0.5: locks+=1
    data[g]=(np.mean(Rmaxs),np.std(Rmaxs),locks/16.0,np.mean(rfs))
    print(f"{g:<8}{np.mean(Rmaxs):<14.4f}{np.std(Rmaxs):<10.4f}{str(locks)+'/16':<12}{np.mean(rfs):<10.4f}")

fig,ax=plt.subplots(figsize=(8.5,5.5))
gg=sorted(data); 
ax.errorbar(gg,[data[g][0] for g in gg],yerr=[data[g][1] for g in gg],
            fmt='o-',color='C0',ms=7,capsize=4,label='measured transient R_max (seed)')
ax.plot(gg,[data[g][2] for g in gg],'s--',color='C3',ms=8,label='lock fraction')
ax.set_xlabel("Lorentzian gamma"); ax.set_ylabel("R_max  /  lock fraction")
ax.set_title("Measured transient escape seed R_max collapses with gamma\n(empirical, no theory assumption)")
ax.legend(); ax.grid(alpha=0.3); plt.tight_layout()
plt.savefig('emp153_escape_seed.png',dpi=110)
print("\nSaved emp153_escape_seed.png")
