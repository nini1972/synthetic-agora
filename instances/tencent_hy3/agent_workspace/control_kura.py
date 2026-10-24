import numpy as np
def sim_constant(N,K,omega,theta0,dt=0.02,T=30):
    theta=theta0.copy().astype(float); steps=int(T/dt); n_avg=int(0.2*steps); Rs=np.zeros(n_avg)
    for s in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
        theta=theta+dt*(omega+K*np.sin(psi-theta))
        if s>=steps-n_avg: Rs[s-(steps-n_avg)]=np.abs(np.mean(np.exp(1j*theta)))
    return Rs.mean()
rng=np.random.default_rng(7)
for K in [0.19,0.5,2.0,4.0,6.0]:
    omega=rng.uniform(-1,1,200); theta0=rng.uniform(0,2*np.pi,200)
    R=sim_constant(200,K,omega,theta0)
    print(f"  constant K={K:4.2f}: R_final={R:.4f}  (K_c=4 expected threshold)")
