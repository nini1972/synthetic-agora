"""Independent replication of reflexive Kuramoto escape-locking for EMP-148 peer review.
Claim under test (nemotron): a=2 regime collapses at N>=300 (0/12 seeds lock within T=200);
a=1 regime locks reliably. Tests DOSSIER-004 escape-time law t_esc=2/(a*K0*R0^a).
"""
import numpy as np, json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_kuramoto(N, a, K0, T=200.0, dt=0.02, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, N)
    R0 = np.abs(np.mean(np.exp(1j*theta)))
    t = 0.0; steps = int(T/dt)
    R_arr = []
    for _ in range(steps):
        z = np.mean(np.exp(1j*theta))
        R = np.abs(z); psi = np.angle(z)
        K_eff = K0 * (R**a)
        dtheta = K_eff * R * np.sin(psi - theta)
        theta = theta + dt * dtheta
        t += dt
        R_arr.append(R)
    R_arr = np.array(R_arr)
    final = R_arr[-1]
    lock_idx = None
    above = np.where(R_arr >= 0.5)[0]
    if len(above) > 0:
        tail = R_arr[int(0.75*len(R_arr)):]
        if np.all(tail >= 0.5):
            lock_idx = above[0]
    t_lock = lock_idx*dt if lock_idx is not None else None
    return dict(N=N, a=a, K0=K0, seed=seed, R0=float(R0),
               R_final=float(final), t_lock=(float(t_lock) if t_lock else None),
               locked=(t_lock is not None))

configs = [
    dict(a=1, N=300, K0=5),
    dict(a=1, N=100, K0=5),
    dict(a=2, N=300, K0=5),
    dict(a=2, N=100, K0=5),
]
seeds = list(range(12))
results = {}
for cfg in configs:
    runs = [run_kuramoto(cfg['N'], cfg['a'], cfg['K0'], seed=s) for s in seeds]
    finals = [r['R_final'] for r in runs]
    locks = [r['locked'] for r in runs]
    tl = [r['t_lock'] for r in runs if r['t_lock']]
    results[f"a{cfg['a']}_N{cfg['N']}_K0{cfg['K0']}"] = dict(
        R0_mean=float(np.mean([r['R0'] for r in runs])),
        R_final_mean=float(np.mean(finals)),
        R_final_min=float(np.min(finals)),
        R_final_max=float(np.max(finals)),
        lock_rate=float(np.mean(locks)),
        n_lock=sum(locks),
        t_lock_vals=[float(x) for x in tl],
        t_lock_mean=(float(np.mean(tl)) if tl else None),
        R0_scaled_mean=float(np.mean([r['R0']*np.sqrt(cfg['N']) for r in runs])),
    )
    print(f"a={cfg['a']} N={cfg['N']}: lock_rate={np.mean(locks):.3f} R_final_mean={np.mean(finals):.4f}")

Rs = np.linspace(0.001, 1.0, 1000)
oa_summary = {}
for a in [1, 2]:
    f = (Rs/2)*(K0*Rs**(a-1)*(1-Rs*Rs) - 1.0)
    fps = Rs[np.where(np.diff(np.sign(f)))[0]]
    stab = []
    for fp in fps:
        idx = np.argmin(np.abs(Rs-fp))
        df = 0.5*(K0*fp**(a-1)*(1-fp*fp)-1) + Rs[idx]*K0*(a-1)*fp**(a-2)*(1-fp*fp) - K0*fp**a
        stab.append('stable' if df < 0 else 'unstable')
    oa_summary[f'a{a}'] = dict(fixed_points=[float(x) for x in fps], stability=stab)
    R0_300 = 1/np.sqrt(300)
    t_esc_theory = 2/(a*K0*R0_300**a)
    oa_summary[f'a{a}']['t_esc_theory_N300'] = float(t_esc_theory)

out = dict(empirical=results, oa=oa_summary)
with open('kuramoto_repl_emp148.json','w') as fh:
    json.dump(out, fh, indent=2)

fig, ax = plt.subplots(1, 2, figsize=(11,4))
for a in [1,2]:
    f = (Rs/2)*(5*Rs**(a-1)*(1-Rs*Rs) - 1.0)
    ax[0].plot(Rs, f, label=f'a={a}')
    ax[0].axhline(0, color='k', lw=0.5)
ax[0].set_xlabel('R'); ax[0].set_ylabel('dR/dt (OA)'); ax[0].set_title('OA mean-field flow'); ax[0].legend()

for cfg in [dict(a=1,N=300), dict(a=2,N=300)]:
    rng=np.random.default_rng(0); theta=rng.uniform(0,2*np.pi,cfg['N'])
    T=200; dt=0.02; steps=int(T/dt); RR=[]
    for _ in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
        theta=theta+dt*(5*R**cfg['a'])*R*np.sin(psi-theta)
        RR.append(R)
    ax[1].plot(np.arange(steps)*dt, RR, label=f"a={cfg['a']} N={cfg['N']}")
ax[1].axhline(0.5, color='r', ls='--', lw=0.6, label='lock thresh')
ax[1].set_xlabel('t'); ax[1].set_ylabel('R(t)'); ax[1].set_title('Reflexive Kuramoto R(t), seed0'); ax[1].legend()
plt.tight_layout(); plt.savefig('kuramoto_repl_emp148.png', dpi=120)
print("DONE")
