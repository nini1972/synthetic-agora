#!/usr/bin/env python3
"""Quick Lorenz invariants verification (HYP-047). Optimized for speed."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def lorenz_rhs(s, sigma, beta, rho):
    x, y, z = s
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y - beta*z])

def lorenz_var(s, sigma, beta, rho):
    x, y, z = s[0], s[1], s[2]
    J = np.array([[-sigma, sigma, 0],[rho-z, -1, -x],[y, x, -beta]])
    V = s[3:].reshape(3,3)
    return np.concatenate([lorenz_rhs(s[:3], sigma, beta, rho), (J@V).flatten()])

def rk4(f, s, dt, *a):
    k1=f(s,*a); k2=f(s+.5*dt*k1,*a); k3=f(s+.5*dt*k2,*a); k4=f(s+dt*k3,*a)
    return s+(dt/6)*(k1+2*k2+2*k3+k4)

lyapunov_var = lorenz_var  # alias defined after function

def lyaps(sigma, beta, rho, dt=0.01, T_trans=100, T_calc=200):
    s = np.concatenate([[1,1,1], np.eye(3).flatten()])
    for _ in range(int(T_trans/dt)):
        s = rk4(lyapunov_var, s, dt, sigma, beta, rho)
        s[3:] = np.eye(3).flatten()
    lyap_sum = np.zeros(3)
    nr = 0
    spr = int(1.0/dt)
    for step in range(int(T_calc/dt)):
        s = rk4(lyapunov_var, s, dt, sigma, beta, rho)
        if (step+1) % spr == 0:
            V = s[3:].reshape(3,3)
            Q, R = np.linalg.qr(V)
            for i in range(3): lyap_sum[i] += np.log(abs(R[i,i]))
            s[3:] = Q.flatten()
            nr += 1
    return np.sort(lyap_sum / (nr*1.0))[::-1]


def kaplan_yorke(ly):
    s = np.sort(ly)[::-1]
    cs = np.cumsum(s)
    for j in range(len(s)-1):
        if cs[j]+s[j+1] < 0: return j + cs[j]/abs(s[j+1])
    return float(len(s))

def box_count(traj):
    data = traj[::10]
    mn, mx = np.min(data,0), np.max(data,0)
    rng = mx - mn
    scs, cnts = [], []
    for bs in [0.5, 1.0, 2.0, 4.0, 8.0]:
        bins = np.maximum(np.ceil(rng/bs).astype(int), 1)
        idx = np.clip(np.floor((data-mn)/bs).astype(int), 0, bins-1)
        nb = len(set(map(tuple, idx)))
        if nb > 10: scs.append(bs); cnts.append(nb)
    if len(scs) < 3: return float('nan')
    slope, _ = np.polyfit(np.log(1/np.array(scs)), np.log(np.array(cnts)), 1)
    return slope

def main():
    sigma, beta = 10.0, 8/3
    rho_vals = [24, 26, 28, 30, 32]
    results = []
    for rho in rho_vals:
        print(f"rho={rho}...", end=" ", flush=True)
        ly = lyaps(sigma, beta, rho)
        D_KY = kaplan_yorke(ly)
        # trajectory for box-counting
        s = np.array([1.0,1,1])
        for _ in range(int(100/0.01)): s = rk4(lorenz_rhs, s, 0.01, sigma, beta, rho)
        n = int(100/0.01)
        traj = np.zeros((n,3))
        for i in range(n): s = rk4(lorenz_rhs, s, 0.01, sigma, beta, rho); traj[i]=s
        D_box = box_count(traj)
        left = np.mean(traj[:,0]<0); right = np.mean(traj[:,0]>0)
        asym = left/right if right>0 else float('inf')
        results.append(dict(rho=rho, l1=ly[0], l2=ly[1], l3=ly[2], D_KY=D_KY, D_box=D_box, asym=asym))
        print(f"l1={ly[0]:.4f} D_KY={D_KY:.4f} D_box={D_box:.3f} asym={asym:.4f}")

    print("\n" + "="*70)
    print(f"{'rho':>5} {'l1':>8} {'l2':>8} {'l3':>8} {'D_KY':>7} {'D_box':>7} {'asym':>7}")
    for r in results:
        print(f"{r['rho']:5} {r['l1']:8.4f} {r['l2']:8.4f} {r['l3']:8.4f} {r['D_KY']:7.4f} {r['D_box']:7.3f} {r['asym']:7.4f}")

    Dk = [r['D_KY'] for r in results]; l1 = [r['l1'] for r in results]; asym = [r['asym'] for r in results]
    print(f"\nHYP-047 targets: D=2.06, lmax=0.9056, asym=1.00")
    print(f"D_KY: {np.mean(Dk):.4f} +/- {np.std(Dk):.4f}")
    print(f"l1:   {np.mean(l1):.4f} +/- {np.std(l1):.4f}")
    print(f"asym: {np.mean(asym):.4f} +/- {np.std(asym):.4f}")

    fig, ax = plt.subplots(1,3,figsize=(15,5))
    rhos = [r['rho'] for r in results]
    ax[0].plot(rhos, Dk, 'bo-', ms=8); ax[0].axhline(2.06, color='r', ls='--'); ax[0].set_title('Kaplan-Yorke D'); ax[0].set_xlabel('rho'); ax[0].grid(alpha=0.3)
    ax[1].plot(rhos, l1, 'bo-', ms=8); ax[1].axhline(0.9056, color='r', ls='--'); ax[1].set_title('lambda_max'); ax[1].set_xlabel('rho'); ax[1].grid(alpha=0.3)
    ax[2].plot(rhos, asym, 'bo-', ms=8); ax[2].axhline(1.0, color='r', ls='--'); ax[2].set_title('Wing Asymmetry'); ax[2].set_xlabel('rho'); ax[2].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('shared_agora/artifacts/lorenz_v2_verify.png', dpi=150)
    print("Saved plot.")

if __name__ == '__main__':
    main()