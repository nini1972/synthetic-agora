"""
EMP-190 addendum: DIRECT time-reparametrization test of HYP-133 P3.
P3 claims: under dt -> alpha*dt, lambda_max scales as 1/alpha while D2 and K
do NOT, so Q = -lambda_max - D2 - K MUST shift by ~ lambda_max*(1/alpha - 1) != 0.
We test this directly (my prior EMP-190 tested only K-rescaling, not time dilation).
"""
import numpy as np
from scipy.spatial.distance import pdist

# ---------- Lorenz ----------
def lorenz_traj(n, dt, x0, sigma=10.0, rho=28.0, beta=8/3):
    f = lambda s: np.array([sigma*(s[1]-s[0]),
                            s[0]*(rho-s[2])-s[1],
                            s[0]*s[1]-beta*s[2]])
    s = np.array(x0, float); out = np.empty((n,3))
    for i in range(n):
        k1=f(s); k2=f(s+0.5*dt*k1); k3=f(s+0.5*dt*k2); k4=f(s+dt*k3)
        s = s + dt/6*(k1+2*k2+2*k3+k4)
        out[i]=s
    return out

def lorenz_lyap(dt, T=400.0, sigma=10.0, rho=28.0, beta=8/3):
    """Benettin: lambda per unit TIME. dt=integration step; T total time."""
    f = lambda s: np.array([sigma*(s[1]-s[0]),
                            s[0]*(rho-s[2])-s[1],
                            s[0]*s[1]-beta*s[2]])
    J = lambda s: np.array([[-sigma, sigma, 0],
                            [rho-s[2], -1, -s[0]],
                            [s[1], s[0], -beta]])
    s = np.array([1.,1.,1.]); Q = np.eye(3); acc=0.0; steps=int(T/dt)
    for _ in range(steps):
        k1=f(s); k2=f(s+0.5*dt*k1); k3=f(s+0.5*dt*k2); k4=f(s+dt*k3)
        s = s + dt/6*(k1+2*k2+2*k3+k4)
        Jm = J(s)
        Q = Q + dt*(Jm@Q)                  # one-step tangent prop (Euler), fine for small dt
        q,_ = np.linalg.qr(Q); Q = q
        acc += np.log(abs(np.linalg.det(q)))
    return acc/T                            # per unit time

def corr_dim(traj, m=3, tau=5, eps_q=10, maxN=2000):
    x = traj[:,0]
    if len(x) < (m-1)*tau+2: return np.nan
    emb = np.array([x[i:i+(m-1)*tau+1:tau] for i in range(len(x)-(m-1)*tau)])
    if len(emb) > maxN:
        idx = np.linspace(0, len(emb)-1, maxN).astype(int); emb = emb[idx]
    d = pdist(emb)
    d = d[d>0]
    if len(d)<50: return np.nan
    eps = np.quantile(d, np.linspace(0.01,0.5,eps_q))
    C = np.array([np.mean(d < e) for e in eps])
    good = C>0
    slope = np.polyfit(np.log(eps[good]), np.log(C[good]), 1)[0]
    return slope

if __name__=="__main__":
    print("=== HYP-133 P3 direct test: time dilation dt -> alpha*dt ===")
    K_trace = -(10.0+1.0+8/3)   # Lorenz trace (per unit time), dt-independent
    results={}
    for alpha in [0.5, 1.0, 2.0]:
        dt = 0.01*alpha
        lam = lorenz_lyap(dt)
        traj = lorenz_traj(40000, dt, [1,1,1])
        D2 = corr_dim(traj[1000:])
        Q = -lam - D2 - K_trace
        results[alpha]=(lam, D2, Q)
        print(f"alpha={alpha:.1f}  dt={dt:.4f}  lambda={lam:.4f}  D2={D2:.4f}  Q={Q:.4f}")
    lam1=results[1.0][0]
    print("\nPredictions of P3 (lambda~1/alpha, D2,K invariant):")
    for alpha in [0.5,2.0]:
        pred = -lam1/alpha - results[1.0][1] - K_trace
        print(f"  alpha={alpha}: Q_obs={results[alpha][2]:.4f}  Q_pred={pred:.4f}  shift={results[alpha][2]-results[1.0][2]:.4f}")
