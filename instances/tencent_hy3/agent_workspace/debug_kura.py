import numpy as np
def simulate_traj(N, K0, alpha, omega, theta0, dt=0.02, T=35):
    theta = theta0.copy().astype(float)
    steps = int(T/dt)
    traj=[]
    for s in range(steps):
        z = np.mean(np.exp(1j*theta)); R=np.abs(z); K=K0*(R**alpha); psi=np.angle(z)
        theta = theta + dt*(omega + K*np.sin(psi - theta))
        if s % 100 == 0:
            traj.append((s*dt, R, K))
    return traj

rng=np.random.default_rng(7)
omega=rng.uniform(-1,1,200); theta0=rng.uniform(0,2*np.pi,200)
for alpha in [1.0,1.2]:
    print(f"--- alpha={alpha} ---")
    tr=simulate_traj(200,5.0,alpha,omega,theta0)
    for t,R,K in tr[:20]:
        print(f"  t={t:.1f} R={R:.4f} K={K:.4f}")
    print("  ...")
    for t,R,K in tr[-5:]:
        print(f"  t={t:.1f} R={R:.4f} K={K:.4f}")
