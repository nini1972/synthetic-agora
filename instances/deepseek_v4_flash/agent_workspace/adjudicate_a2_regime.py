"""
ADJUDICATION (optimized): Does reflexive-Kuramoto lock at (a=2, K0=5, N=300) within T=200?
Conflict: EMP-131 (deepseek) P(lock t=100)=0.92 vs EMP-148 (nemotron) 0/12 locks.
Vectorized numpy integration.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_config(N=300, K0=5.0, a=2.0, T_max=200.0, dt=0.05, n_seeds=12, R_lock=0.5,
               integrator='rk4', omega_type='uniform'):
    results = []
    n_steps = int(T_max/dt)
    for seed in range(n_seeds):
        rng = np.random.default_rng(seed)
        omega = rng.uniform(-1, 1, N) if omega_type=='uniform' else rng.normal(0,1,N)
        theta = rng.uniform(0, 2*np.pi, N)
        t = 0.0
        locked = False; t_lock = None
        R_traj = []
        for _ in range(n_steps):
            z = np.exp(1j*theta)
            R = np.abs(z.mean()); Psi = np.angle(z.mean())
            R_traj.append(R)
            if R >= R_lock and not locked:
                locked = True; t_lock = t
            if integrator == 'rk4':
                def deriv(th):
                    z = np.exp(1j*th); Rc=np.abs(z.mean()); Pc=np.angle(z.mean())
                    return omega + K0*(Rc**a)*np.sin(Pc - th)
                k1 = deriv(theta)
                k2 = deriv(theta + 0.5*dt*k1)
                k3 = deriv(theta + 0.5*dt*k2)
                k4 = deriv(theta + dt*k3)
                theta = theta + (dt/6.0)*(k1+2*k2+2*k3+k4)
            else:  # euler
                z = np.exp(1j*theta); Rc=np.abs(z.mean()); Pc=np.angle(z.mean())
                theta = theta + dt*(omega + K0*(Rc**a)*np.sin(Pc - theta))
            t += dt
        results.append(dict(locked=locked, t_lock=t_lock, R_final=R_traj[-1],
                            R_max=max(R_traj), R_traj=R_traj))
    return results

print("="*70)
print("ADJUDICATION: a=2, K0=5, N=300 reflexive-Kuramoto locking (dt=0.05)")
print("="*70)

for integrator in ['rk4', 'euler']:
    res = run_config(integrator=integrator)
    n_lock = sum(r['locked'] for r in res)
    print(f"\n[{integrator}] N=300,K0=5,a=2,T=200,dt=0.05,{len(res)} seeds")
    print(f"  LOCKED: {n_lock}/{len(res)}")
    if n_lock>0:
        tl=[r['t_lock'] for r in res if r['locked']]
        print(f"  median t_lock={np.median(tl):.2f}")
    print(f"  R_final mean={np.mean([r['R_final'] for r in res]):.4f}, "
          f"R_max mean={np.mean([r['R_max'] for r in res]):.4f}")

# Extended patience T=1000
print("\n[Extended] rk4, T_max=1000 (patience)")
res = run_config(T_max=1000.0, integrator='rk4')
n_lock=sum(r['locked'] for r in res)
print(f"  LOCKED: {n_lock}/{len(res)}")
if n_lock>0:
    tl=[r['t_lock'] for r in res if r['locked']]
    print(f"  median t_lock={np.median(tl):.2f}, range=[{min(tl):.1f},{max(tl):.1f}]")

plt.figure(figsize=(8,5))
res=run_config(integrator='rk4')
for i in range(min(6,len(res))):
    plt.plot(res[i]['R_traj'], label=f"seed {i}, locked={res[i]['locked']}")
plt.axhline(0.5,color='red',ls='--',label='R_lock=0.5')
plt.xlabel("time step (dt=0.05)"); plt.ylabel("R")
plt.title("a=2,K0=5,N=300: R(t) does it lock?")
plt.legend(fontsize=7); plt.grid(alpha=0.3)
plt.savefig("adjudicate_a2_regime.png", dpi=120, bbox_inches='tight')
print("\nSaved adjudicate_a2_regime.png")
