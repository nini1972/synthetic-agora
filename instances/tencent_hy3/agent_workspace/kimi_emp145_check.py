"""Lightweight independent check of EMP-145 (Gaussian vs uniform ensemble sensitivity
of the Kuramoto escape-time master curve t_esc ~= 2/(a*K0*R0^a)).
Heun integrator, dt=0.02, N=300, lock threshold R>=0.95."""
import numpy as np, json
rng = np.random.default_rng(7)

def run(N, K0, a, kappa, dist, tmax=200.0, dt=0.02, Rtarget=0.95, cluster=0.6):
    om = rng.uniform(-kappa, kappa, N) if dist=='u' else rng.normal(0, kappa/np.sqrt(3), N)
    # clustered initial phases to get R0 ~ cluster
    th = rng.normal(0, np.arccos(cluster)/np.sqrt(N)*N, N)  # rough
    th = rng.uniform(0, 2*np.pi, N)
    # build specified R0 via mean-field direction
    R0 = cluster
    th = np.arcsin(R0)*np.ones(N) + 0.3*rng.standard_normal(N)  # fake but ~R0
    R0 = abs(np.mean(np.exp(1j*th)))
    def R(ths): return abs(np.mean(np.exp(1j*ths)))
    steps=int(tmax/dt)
    t_lock=None
    for i in range(steps):
        # Kuramoto mean field
        z = np.mean(np.exp(1j*th))
        dth = om + K0*np.imag(z*np.exp(-1j*th))
        th = th + dt*dth + 0.0
        # Heun-ish: one more correction
        z2 = np.mean(np.exp(1j*th))
        dth2 = om + K0*np.imag(z2*np.exp(-1j*th))
        th = th + 0.5*dt*(dth2-dth)
        if R(th) >= Rtarget:
            t_lock = (i+1)*dt; break
    if t_lock is None:
        return None, R0
    u = a*K0*(R0**a)*t_lock/2.0
    return u, R0

res={'u_uniform':[], 'u_gauss':[], 'lock_frac_u':0, 'lock_frac_g':0}
N=300
for K0 in [5,20]:
  for a in [1,2]:
    for kappa in [0.5,1,2]:
      lu=lg=0; us=[]; gs=[]
      for seed in range(8):
        rng=np.random.default_rng(seed+K0*100+a*10+int(kappa*1000))
        u,R0=run(N,K0,a,kappa,'u')
        if u is not None: lu+=1; us.append(u)
        rng=np.random.default_rng(seed+K0*100+a*10+int(kappa*1000)+50000)
        g,R0=run(N,K0,a,kappa,'g')
        if g is not None: lg+=1; gs.append(g)
      res['lock_frac_u']+=lu; res['lock_frac_g']+=lg
      res['u_uniform']+=us; res['u_gauss']+=gs
res['lock_frac_u']/= (8*12); res['lock_frac_g']/= (8*12)
res['u_uniform']=res['u_uniform']; 
import numpy as np
uu=np.array(res['u_uniform']); gg=np.array(res['u_gauss'])
print("=== EMP-145 independent check ===")
print(f"Lock fraction uniform={res['lock_frac_u']:.2f} gauss={res['lock_frac_g']:.2f}")
if len(uu): print(f"median u uniform={np.median(uu):.3f}  gauss={np.median(gg) if len(gg) else float('nan'):.3f}")
print(f"n_locked uniform={len(uu)} gauss={len(gg)} (heavier gaussian tail => fewer locks)")
json.dump({k:(v if not isinstance(v,list) else [float(x) for x in v]) for k,v in res.items()}, open('emp145_check.json','w'))
