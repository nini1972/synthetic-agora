import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree

DT = 0.01

def f(state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = state
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y-beta*z])

def J(state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = state
    return np.array([[-sigma, sigma, 0.0],
                     [rho - z, -1.0, -x],
                     [y, x, -beta]])

def rk4_state(x, dt, sigma, rho, beta):
    k1 = f(x, sigma, rho, beta)
    k2 = f(x + 0.5*dt*k1, sigma, rho, beta)
    k3 = f(x + 0.5*dt*k2, sigma, rho, beta)
    k4 = f(x + dt*k3, sigma, rho, beta)
    return x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def benettin(sigma=10.0, rho=28.0, beta=8.0/3.0, dt=DT, T_burn=2000.0,
             T_meas=1500.0, renorm=10):
    x = np.array([1.0, 1.0, 1.0])
    n_burn = int(T_burn/dt)
    for _ in range(n_burn):
        x = rk4_state(x, dt, sigma, rho, beta)
    U = np.eye(3)
    log_sum = np.zeros(3)
    n_steps = int(T_meas/dt)
    n_renorms = 0
    xs, ys, zs = [], [], []
    for i in range(n_steps):
        xa = x + 0.5*dt*f(x, sigma, rho, beta)
        xb = x + 0.5*dt*f(xa, sigma, rho, beta)
        xc = x + dt*f(xb, sigma, rho, beta)
        x = rk4_state(x, dt, sigma, rho, beta)
        Ja, Jb, Jc, Jx = J(xa, sigma, rho, beta), J(xb, sigma, rho, beta), J(xc, sigma, rho, beta), J(x, sigma, rho, beta)
        m1 = Ja @ U
        m2 = Jb @ (U + 0.5*dt*m1)
        m3 = Jc @ (U + 0.5*dt*m2)
        m4 = Jx @ (U + dt*m3)
        U = U + (dt/6.0)*(m1 + 2*m2 + 2*m3 + m4)
        if (i+1) % renorm == 0:
            Q, R = np.linalg.qr(U)
            diag = np.abs(np.diag(R))
            log_sum += np.log(diag)
            U = Q
            n_renorms += 1
        if i % 10 == 0:
            xs.append(x[0]); ys.append(x[1]); zs.append(x[2])
    total_time = n_renorms * renorm * dt
    lyap = log_sum / total_time
    lyap.sort()
    cum = 0.0; DKY = 2.0
    if lyap[0] >= 0 and lyap[1] >= 0:
        DKY = 3.0
    elif lyap[0] >= 0 and lyap[1] < 0:
        DKY = 1.0
    elif lyap[0] + lyap[1] >= 0:
        DKY = 2.0 + (lyap[0]+lyap[1])/(-lyap[2])
    else:
        DKY = 1.0 + lyap[0]/abs(lyap[1])
    return np.array(lyap), DKY, np.array([xs, ys, zs])

def grassberger_procaccia(series, eps_list=None, plot=True, tag=''):
    if eps_list is None:
        eps_list = np.logspace(-2.5, 0.2, 30)
    n = len(series)
    pts = series.reshape(n, 1)
    tree = cKDTree(pts)
    C = np.zeros(len(eps_list))
    for i, eps in enumerate(eps_list):
        idx = tree.query_ball_point(pts, eps)
        cnt = sum(len(lst) - 1 for lst in idx)
        C[i] = cnt / (n*(n-1))
    mask = (C > 1e-4) & (C < 0.2) & np.isfinite(C)
    D2 = np.polyfit(np.log(eps_list[mask]), np.log(C[mask]), 1)[0] if mask.sum() > 3 else np.nan
    if plot:
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        ax[0].plot(eps_list, C, 'o-'); ax[0].set_xscale('log'); ax[0].set_yscale('log')
        ax[0].set_xlabel('epsilon'); ax[0].set_ylabel('C(eps)'); ax[0].set_title('Correlation sum')
        ax[1].plot(np.log(eps_list), np.log(C), 'o-')
        ax[1].axvspan(np.log(eps_list[mask][0]), np.log(eps_list[mask][-1]), alpha=0.15, color='green')
        ax[1].set_xlabel('ln eps'); ax[1].set_ylabel('ln C'); ax[1].set_title(f'D2 = {D2:.3f}')
        plt.tight_layout()
        plt.savefig(f'shared_agora/artifacts/lorenz_qmetric_gp{tag}.png', dpi=120); plt.close()
    return D2, eps_list, C, mask

print("="*64)
print("CLEAN LORENZ Q-METRIC  (Benettin + Grassberger-Procaccia)")
print("="*64)
for rho in [28.0, 50.0]:
    lyap, DKY, traj = benettin(rho=rho)
    print(f"\n=== rho = {rho} ===")
    print(f"Lyapunov (ascending): {np.round(lyap,4)}")
    print(f"Kaplan-Yorke D_KY   : {DKY:.4f}")
    D2, _, _, _ = grassberger_procaccia(traj[2], tag=f'_rho{int(rho)}')
    print(f"Correlation D_2     : {D2:.4f}")
    lam_max = lyap[-1]
    Q = -(lam_max + D2)
    Q_full = -np.sum(lyap)
    print(f"lambda_max          : {lam_max:.4f}")
    print(f"Q = -(lam_max+D2)   : {Q:.4f}")
    print(f"Q_full=-(sum lyap)  : {Q_full:.4f}")
    print(f"lit benchmark Q_true~ -2.97 (lambda1=0.9056, D2=2.06)")
