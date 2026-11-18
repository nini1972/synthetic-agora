import numpy as np
from scipy.linalg import expm
from scipy.spatial.distance import pdist
np.random.seed(42)

def lorenz_rhs(s, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = s
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y-beta*z])
def lorenz_jac(s, sigma, rho, beta):
    x, y, z = s
    return np.array([[-sigma, sigma, 0.0],[rho-z, -1.0, -x],[y, x, -beta]])
def rk4_step(f, s, dt, *args):
    k1 = f(s, *args); k2 = f(s+0.5*dt*k1, *args)
    k3 = f(s+0.5*dt*k2, *args); k4 = f(s+dt*k3, *args)
    return s + dt*(k1+2*k2+2*k3+k4)/6.0

def benettin_expm(rho, dt=0.01, T_burn=200.0, T_meas=2000.0, sigma=10.0, beta=8.0/3.0):
    """Matrix-exponential Benettin: exact linearization per step, QR every step."""
    s = np.array([1.0,1.0,20.0]); Phi = np.eye(3)
    for _ in range(int(T_burn/dt)):
        J = lorenz_jac(s, sigma, rho, beta)
        s = rk4_step(lorenz_rhs, s, dt, sigma, rho, beta)
        Phi = expm(J*dt) @ Phi
        Q, R = np.linalg.qr(Phi); Phi = Q
    lam = np.zeros(3); xs = []
    n = int(T_meas/dt)
    for i in range(n):
        J = lorenz_jac(s, sigma, rho, beta)
        s = rk4_step(lorenz_rhs, s, dt, sigma, rho, beta)
        Phi = expm(J*dt) @ Phi
        Q, R = np.linalg.qr(Phi)
        lam += np.log(np.abs(np.diag(R))); Phi = Q
        if i % 10 == 0: xs.append(s.copy())
    return lam/T_meas, np.array(xs)

def d2_gp(xs, m=3, tau=8):
    x = xs[:,0] - xs[:,0].mean(); n = len(x)
    pts = np.column_stack([x[k*tau:k*tau+n-(m-1)*tau] for k in range(m)])
    d = pdist(pts); d = d[d>0]
    dmax = d.max(); rs = np.geomspace(dmax*0.02, dmax*0.25, 30)
    C = np.array([(d < r).mean() for r in rs]); mask = C > 1e-4
    return float(np.polyfit(np.log(rs[mask]), np.log(C[mask]), 1)[0])

print("=== Lorenz rho-sweep: matrix-exponential Benettin + GP D2 ===")
print(f"{'rho':>6} {'lam_max':>8} {'D2':>6} {'Q(K=0)':>8}  regime")
for rho in [10.0, 14.0, 18.0, 22.0, 24.0, 24.74, 28.0, 35.0, 42.0, 50.0]:
    lam, xs = benettin_expm(rho)
    if lam[0] > 0.05:
        d2 = d2_gp(xs); Q = -(lam[0] + d2)
        print(f"{rho:6.2f} {lam[0]:+8.4f} {d2:6.3f} {Q:8.3f}  chaotic", flush=True)
    else:
        print(f"{rho:6.2f} {lam[0]:+8.4f} {'nan':>6} {'nan':>8}  non-chaotic", flush=True)
