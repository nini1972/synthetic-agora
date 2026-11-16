import numpy as np
np.random.seed(0)

def lorenz_rhs(s, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = s
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y-beta*z])

def lorenz_jac(s, sigma, rho, beta):
    x, y, z = s
    return np.array([[-sigma, sigma, 0.0],[rho-z, -1.0, -x],[y, x, -beta]])

def aug_rhs(w, sigma, rho, beta):
    # w = [s(3), Phi(9) row-major]
    s = w[:3]; Phi = w[3:].reshape(3,3)
    ds = lorenz_rhs(s, sigma, rho, beta)
    dPhi = lorenz_jac(s, sigma, rho, beta) @ Phi
    return np.concatenate([ds, dPhi.ravel()])

def rk4_step(f, w, dt, *args):
    k1 = f(w, *args); k2 = f(w+0.5*dt*k1, *args)
    k3 = f(w+0.5*dt*k2, *args); k4 = f(w+dt*k3, *args)
    return w + dt*(k1+2*k2+2*k3+k4)/6.0

def benettin(rho, dt=0.01, T_burn=100.0, T_meas=300.0, sigma=10.0, beta=8.0/3.0):
    w = np.concatenate([[1.0,1.0,20.0], np.eye(3).ravel()])
    for _ in range(int(T_burn/dt)):
        w = rk4_step(aug_rhs, w, dt, sigma, rho, beta)
    lam_sum = 0.0; xs = []
    n = int(T_meas/dt)
    for i in range(n):
        w = rk4_step(aug_rhs, w, dt, sigma, rho, beta)
        Phi = w[3:].reshape(3,3)
        Q, R = np.linalg.qr(Phi)
        lam_sum += np.log(np.abs(R[0,0]))
        w[3:] = Q.ravel()
        if i % 5 == 0: xs.append(w[0].copy())
    return lam_sum/T_meas, np.array(xs)

def d2_gp(xs, m=3, tau=8):
    x = xs - xs.mean()
    emb = np.array([x[i:i+len(x)-2*tau:1] for i in range(0, 2*tau+1, tau)]).T  # crude; do proper below
    # proper Takens
    n = len(x); pts = np.column_stack([x[k*tau:k*tau+n-(m-1)*tau] for k in range(m)])
    from scipy.spatial.distance import pdist
    d = pdist(pts)
    d = d[d>0]
    dmax = d.max(); rs = np.geomspace(dmax*0.02, dmax*0.2, 25)
    C = np.array([(d < r).mean() for r in rs])
    mask = C > 0
    return float(np.polyfit(np.log(rs[mask]), np.log(C[mask]), 1)[0])

for rho in [10.0, 28.0, 50.0]:
    lam, xs = benettin(rho)
    d2 = d2_gp(xs) if lam > 0 else float('nan')
    Q = -(lam + d2) if lam > 0 else float('nan')
    print(f"rho={rho:5.1f}  lam_max={lam:+.4f}  D2={d2:.3f}  Q={Q:.3f}", flush=True)
