"""Probe II: mechanism of any first-order transition under K0*R^alpha feedback.
Variables: ALPHA in {0.5,1.0,2.0}; initial condition random vs coherent-seeded.
normal freq width 1. Scan K0. Forward/backward sweep. Determines whether hysteresis
requires (a) small alpha or (b) coherent seed = modeling deviation from dossier."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 200
DT = 0.05
T_TRANS = 30.0
T_MEAS = 30.0
SEED = 999

def run_sweep(om, K0_list, alpha, rng, seed=None, carry=None):
    if seed is not None:
        # coherent clustered initial condition around 0
        th = seed.copy()
    elif carry is not None:
        th = carry
    else:
        th = rng.uniform(0, 2*np.pi, N)
    Ravg = []
    ntrans = int(T_TRANS/DT); nmeas = int(T_MEAS/DT)
    for K0 in K0_list:
        acc = 0.0; cnt = 0
        for step in range(ntrans + nmeas):
            z = np.mean(np.exp(1j*th)); R = abs(z); psi = np.angle(z)
            Keff = K0 * (R**alpha)
            k1 = om + Keff*R*np.sin(psi-th)
            th2 = th + 0.5*DT*k1
            z2=np.mean(np.exp(1j*th2)); R2=abs(z2); p2=np.angle(z2)
            k2 = om + (K0*(R2**alpha))*R2*np.sin(p2-th2)
            th3 = th + 0.5*DT*k2
            z3=np.mean(np.exp(1j*th3)); R3=abs(z3); p3=np.angle(z3)
            k3 = om + (K0*(R3**alpha))*R3*np.sin(p3-th3)
            th4 = th + DT*k3
            z4=np.mean(np.exp(1j*th4)); R4=abs(z4); p4=np.angle(z4)
            k4 = om + (K0*(R4**alpha))*R4*np.sin(p4-th4)
            th = th + (DT/6.0)*(k1+2*k2+2*k3+k4)
            if step >= ntrans:
                acc += abs(np.mean(np.exp(1j*th))); cnt += 1
        Ravg.append(acc/cnt)
    return np.array(K0_list), np.array(Ravg), th

def main():
    grid = np.round(np.arange(0.0, 12.01, 1.0), 2)
    fwd = grid.tolist(); bwd = grid[::-1].tolist()
    rows = []
    fig, axes = plt.subplots(3,2, figsize=(11,11))
    for r, alpha in enumerate([0.5, 1.0, 2.0]):
        rng = np.random.default_rng(SEED + r)
        om = rng.normal(0.0, 1.0, N)
        # random start
        Kf, Rf, th_end = run_sweep(om, fwd, alpha, rng)
        Kb, Rb, _ = run_sweep(om, bwd, alpha, rng, carry=th_end)
        gap = 0.0
        RbK = dict(zip(Kb,Rb))
        for k, rf in zip(Kf, Rf):
            gap = max(gap, rf - RbK.get(k,0.0))
        rows.append(('alpha=%.1f random' % alpha, round(gap,3), 'HYST' if gap>0.1 else 'no'))
        axes[r,0].plot(Kf,Rf,'o-',color='C0'); axes[r,0].plot(Kb,Rb,'s--',color='C3')
        axes[r,0].set_title('alpha=%.1f, random init, gap=%.2f' % (alpha, gap)); axes[r,0].grid(alpha=0.3); axes[r,0].set_xlabel('K0'); axes[r,0].set_ylabel('R')
        # coherent-seeded start
        rng2 = np.random.default_rng(SEED + 100 + r)
        seed = rng2.normal(0.0, 0.3, N)  # clustered -> high initial R
        Kf2, Rf2, th_end2 = run_sweep(om, fwd, alpha, rng2, seed=seed)
        Kb2, Rb2, _ = run_sweep(om, bwd, alpha, rng2, carry=th_end2)
        gap2 = 0.0
        RbK2 = dict(zip(Kb2,Rb2))
        for k, rf in zip(Kf2, Rf2):
            gap2 = max(gap2, rf - RbK2.get(k,0.0))
        rows.append(('alpha=%.1f seeded' % alpha, round(gap2,3), 'HYST' if gap2>0.1 else 'no'))
        axes[r,1].plot(Kf2,Rf2,'o-',color='C0'); axes[r,1].plot(Kb2,Rb2,'s--',color='C3')
        axes[r,1].set_title('alpha=%.1f, coherent-seeded init, gap=%.2f' % (alpha, gap2)); axes[r,1].grid(alpha=0.3); axes[r,1].set_xlabel('K0'); axes[r,1].set_ylabel('R')
    fig.tight_layout(); fig.savefig('kuramoto_arb2.png', dpi=130)
    print('SAVED kuramoto_arb2.png')
    for rrow in rows:
        print(rrow)
    with open('kuramoto_arb2_summary.txt','w') as f:
        for rrow in rows:
            f.write(str(rrow)+'\n')

if __name__ == '__main__':
    main()
