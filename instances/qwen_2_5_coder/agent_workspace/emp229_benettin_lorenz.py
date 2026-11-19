"""
Qwen local replication of EMP-229 (poolside_laguna):
  Lorenz system sigma=10, rho=28, beta=8/3
  Benettin QR algorithm for the full Lyapunov spectrum.
  Literature benchmark: lambda_max = 0.9056 (Grassberger & Procaccia 1983).
  EMP-229 reported lambda_max = 0.8880 and Q = -(lambda_max + D2) ~ -2.95,
  vs HYP-222's claimed Q ~ -270 (an alleged ~90x 'dynamical invariant' signal).
"""
import numpy as np
from scipy.linalg import qr

SIG, RHO, BETA = 10.0, 28.0, 8.0/3.0


def make_rk4(dt):
    def s(x, y, z):
        def f(a, b, c):
            return SIG*(b-a), a*(RHO-c)-b, a*b-BETA*c
        k1x, k1y, k1z = f(x, y, z)
        k2x, k2y, k2z = f(x+0.5*dt*k1x, y+0.5*dt*k1y, z+0.5*dt*k1z)
        k3x, k3y, k3z = f(x+0.5*dt*k2x, y+0.5*dt*k2y, z+0.5*dt*k2z)
        k4x, k4y, k4z = f(x+dt*k3x, y+dt*k3y, z+dt*k3z)
        return (x + dt/6*(k1x+2*k2x+2*k3x+k4x),
                y + dt/6*(k1y+2*k2y+2*k3y+k4y),
                z + dt/6*(k1z+2*k2z+2*k3z+k4z))
    return s


def benettin(dt, n_steps, n_renorm_steps=20, transient=10000):
    step = make_rk4(dt)
    x, y, z = 1.0, 1.0, 1.0
    for _ in range(transient):
        x, y, z = step(x, y, z)

    V = np.eye(3)
    n = 0
    Lcum = np.zeros(3)
    lam_hist = []
    for s in range(n_steps):
        x, y, z = step(x, y, z)
        J = np.array([[-SIG, SIG, 0.0],
                      [RHO - 2.0*z, -1.0, -x],
                      [y, x, -BETA]])
        V = V + dt*(J @ V)
        n += 1
        if n % n_renorm_steps == 0:
            Q, R = qr(V)
            d = np.sign(np.diag(R)); d[d == 0] = 1.0
            for i in range(3):
                Q[:, i] *= d[i]
            Lcum += np.log(np.abs(np.diag(R)))
            V = Q @ V
        if s and s % (n_steps // 10) == 0:
            lam_hist.append((n*dt, Lcum/(n*dt)))
    return Lcum/(n*dt), n*dt, lam_hist


def main():
    lam, T, hist = benettin(dt=0.01, n_steps=2_000_000)
    print("QWEN BENETTIN REPLACEMENT of EMP-229 (Lorenz 10/28/8/3)")
    print(f"time integrated (units): {T:,.0f}")
    print("lyapunov spectrum (Benettin QR, dt=0.01, renorm=20):")
    for i, li in enumerate(lam):
        print(f"  lambda_{i} = {li:+.4f}")
    print("\nConvergence (t, lambda_max):")
    for t, lm in hist:
        print(f"  t={t:7.1f}  lambda_max={lm:.4f}")

    LIT = 0.9056
    D2_LIT = 2.06
    print(f"\nlambda_max (this run)      : {lam[0]:.4f}")
    print(f"lambda_max (lit GP1983)    : {LIT:.4f}   deviation: {100*(lam[0]-LIT)/LIT:+.2f}%")
    print(f"lambda_max (EMP-229 pool)  : 0.8880   deviation: {100*(0.8880-LIT)/LIT:+.2f}%")
    print(f"lambda_max (HYP-222 implied if Q=-270 with D2=2.06): {-270+2.06:.1f}  <-- absurd, would require lambda_max ~ -268")

    Q_emp  = -(lam[0] + D2_LIT)
    Q_lit  = -(LIT + D2_LIT)
    Q_pool = -(0.8880 + D2_LIT)
    print(f"\nQ = -(lambda_max + D2):")
    print(f"  this run : {Q_emp:+.3f}")
    print(f"  lit      : {Q_lit:+.3f}")
    print(f"  EMP-229  : {Q_pool:+.3f}")
    print(f"  HYP-222 claimed: ~ -270   (ratio to this run: {270/abs(Q_emp):.1f}x)")

    print("\ndt-robustness (Benettin, same algorithm, 5,000 time units each):")
    for dt in (0.005, 0.01, 0.02):
        l2, T2, _ = benettin(dt=dt, n_steps=int(5000/dt))
        print(f"  dt={dt}: lambda_max = {l2[0]:+.4f}  (dev vs lit: {100*(l2[0]-LIT)/LIT:+.2f}%)")


if __name__ == "__main__":
    main()
