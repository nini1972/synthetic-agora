import numpy as np
def trace(N,K0,alpha,omega,theta0,dt=0.02,steps=300):
    theta=theta0.copy().astype(float)
    for s in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); K=K0*(R**alpha); psi=np.angle(z)
        theta=theta+dt*(omega+K*np.sin(psi-theta))
        if s%10==0:
            print(f"  step {s:4d} t={s*dt:.2f} R={R:.4f} K={K:.4f}")
rng=np.random.default_rng(7)
omega=rng.uniform(-1,1,200); theta0=rng.uniform(0,2*np.pi,200)
print("alpha=1.2 K0=5 N=200 fine trace (first 30 prints = 300 steps):")
trace(200,5.0,1.2,omega,theta0)
