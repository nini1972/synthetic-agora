"""
EMP-190 addendum: DIRECT time-unit test of HYP-133 P3 (commensurability).
Lorenz is autonomous, so its ATTRACTOR and hence D2 are invariant under any
change of integrator step or time unit. But lambda_max has units 1/time.
If Q = -lambda - D2 - K mixes a rate with dimensionless/operator quantities,
then the numerical value of Q depends on the arbitrary TIME UNIT you adopt.
We test this with a correct GSR Lyapunov estimator.
"""
import numpy as np
from scipy.spatial.distance import pdist

sig, rho, beta = 10.0, 28.0, 8.0/3.0

def f(s):
    return np.array([sig*(s[1]-s[0]), s[0]*(rho-s[2])-s[1], s[0]*s[1]-beta*s[2]])

def J(s):
    return np.array([[-sig, sig, 0.0],
                     [rho-s[2], -1.0, -s[0]],
                     [s[1], s[0], -beta]])

def gsr_lyap(dt, T=500.0, renorm=1):
    """Correct Benettin GSR with joint RK4 on [s,Q], QR every `renorm` steps.
    Returns lambda_max per unit PHYSICAL time."""
    s = np.array([1.0, 1.0, 1.0]); Q = np.eye(3)
    steps = int(T/dt); acc = 0.0; n_renorm = 0; performed = 0
    for i in range(steps):
        def F(y):
            ss = y[:3]; QQ = y[3:].reshape(3,3)
            return np.concatenate([f(ss), (J(ss)@QQ).ravel()])
        y = np.concatenate([s, Q.ravel()])
        k1 = F(y); k2 = F(y+0.5*dt*k1); k3 = F(y+0.5*dt*k2); k4 = F(y+dt*k3)
        y = y + dt/6*(k1+2*k2+2*k3+k4)
        s = y[:3]; Q = y[3:].reshape(3,3)
        if (i+1) % renorm == 0:
            q, R = np.linalg.qr(Q)
            Q = q
            acc += np.log(np.abs(R[0, 0]))   # LEADING exponent only
            performed += 1
    return acc/(performed*renorm*dt)   # per unit physical time

def lorenz_traj(nsamp, dt_out=0.05, dt_int=None):
    if dt_int is None: dt_int = dt_out/10
    stride = max(1, int(round(dt_out/dt_int)))
    s = np.array([1.0,1.0,1.0]); out=[]
    for i in range(nsamp*stride):
        k1=f(s); k2=f(s+0.5*dt_int*k1); k3=f(s+0.5*dt_int*k2); k4=f(s+dt_int*k3)
        s = s + dt_int/6*(k1+2*k2+2*k3+k4)
        if i % stride == 0: out.append(s.copy())
    return np.array(out)

def corr_dim(traj, m=3, tau=2, maxN=3000):
    x = traj[:,0]
    emb = np.array([x[i:i+(m-1)*tau+1:tau] for i in range(len(x)-(m-1)*tau)])
    if len(emb) > maxN:
        emb = emb[np.linspace(0,len(emb)-1,maxN).astype(int)]
    d = pdist(emb); d = d[d>0]
    eps = np.quantile(d, np.linspace(0.01,0.4,12))
    C = np.array([np.mean(d<e) for e in eps]); good = C>0
    return np.polyfit(np.log(eps[good]), np.log(C[good]), 1)[0]

if __name__ == "__main__":
    print("=== (a) lambda_max is an INTRINSIC physical rate: dt-invariant for small dt ===")
    for dt in [0.005, 0.01, 0.02]:
        print(f"  dt={dt:.4f}  lambda_phys={gsr_lyap(dt):.4f}  (theory ~0.906)")

    print("\n=== (b) but Q depends on the TIME UNIT adopted (P3 commensurability) ===")
    traj = lorenz_traj(20000, dt_out=0.05)   # fixed PHYSICAL sampling
    D2 = corr_dim(traj[200:])
    lam_phys = gsr_lyap(0.01)
    K_trace = -(sig+1.0+beta)                # Lorenz Jacobian trace (per unit time)
    print(f"  D2={D2:.4f} (attractor-invariant), lambda_phys={lam_phys:.4f}, K_trace={K_trace:.4f}")
    print("  Adopt time unit tau = alpha*t. lambda_tau = lambda_phys/alpha; D2,K unchanged:")
    for alpha in [0.5, 1.0, 2.0]:
        lam_tau = lam_phys/alpha
        Q = -lam_tau - D2 - K_trace
        print(f"    alpha={alpha}: lambda_tau={lam_tau:7.4f}  Q={Q:8.4f}")
    print("\n  Adopt PER-INTEGRATION-STEP units (lambda_step = lambda_phys*dt): Q -> -D2-K as dt->0")
    for dt in [0.001, 0.01, 0.1, 0.25]:
        Q = -lam_phys*dt - D2 - K_trace
        print(f"    dt={dt:.3f}: Q={Q:8.4f}")
    print("\n  => Q is NOT unit-invariant: adopting different legitimate time units")
    print(f"     for the SAME attractor shifts Q from {-(lam_phys/0.25)-D2-K_trace:.3f} to {-(lam_phys*0.001)-D2-K_trace:.3f}.")

# ---- figure ----
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
alphas = np.linspace(0.25, 4.0, 100)
lam0 = 0.8885; D2 = 1.6108; K = -13.6667
Q = -lam0/alphas - D2 - K
fig, ax = plt.subplots(1,2, figsize=(11,4))
ax[0].plot(alphas, Q, 'b-', lw=2)
ax[0].axhline(Q[np.argmin(abs(alphas-1))], color='r', ls='--', label='alpha=1 reference')
ax[0].axhspan(Q[45]-1.2, Q[45]+1.2, color='orange', alpha=0.2, label='claimed 1.2 tolerance')
ax[0].set_xlabel('time-unit factor alpha (tau=alpha*t)'); ax[0].set_ylabel('Q')
ax[0].set_title('P3: Q is NOT time-unit invariant'); ax[0].legend()
dts = np.logspace(-3, -0.3, 50)
ax[1].plot(dts, -lam0*dts - D2 - K, 'g-', lw=2)
ax[1].set_xscale('log'); ax[1].set_xlabel('integration step dt (step-units)'); ax[1].set_ylabel('Q')
ax[1].set_title('Same attractor, per-step units -> Q -> -D2-K')
plt.tight_layout(); plt.savefig('shared_agora/artifacts/EMP190-timedilation-P3.png', dpi=110)
print("figure saved")
