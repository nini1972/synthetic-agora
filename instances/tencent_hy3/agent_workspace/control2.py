import numpy as np
def sim_gak(N,K0,alpha,omega,theta0,dt=0.02,T=40):
    theta=theta0.copy().astype(float); steps=int(T/dt); n_avg=int(0.2*steps); Rs=np.zeros(n_avg)
    for s in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); K=K0*(R**alpha); psi=np.angle(z)
        theta=theta+dt*(omega+K*np.sin(psi-theta))
        if s>=steps-n_avg: Rs[s-(steps-n_avg)]=np.abs(np.mean(np.exp(1j*theta)))
    return Rs.mean()
rng=np.random.default_rng(7)
print("CORRECT GAK sim. U[-1,1], N=200, random init. K_c(std)=1.27.")
print("alpha=1 (standard):")
for K0 in [0.5,1.0,5.0]:
    Rs=[sim_gak(200,K0,1.0,rng.uniform(-1,1,200),rng.uniform(0,2*np.pi,200)) for _ in range(3)]
    print(f"  K0={K0}: R={np.mean(Rs):.3f}")
print("alpha=1.2 (sublinear gain; GAIN predicts disordered STABLE for any K0):")
for K0 in [0.5,1.0,2.0,5.0]:
    Rs=[sim_gak(200,K0,1.2,rng.uniform(-1,1,200),rng.uniform(0,2*np.pi,200)) for _ in range(3)]
    print(f"  K0={K0}: R={np.mean(Rs):.3f}")
print("alpha=0.5 (superlinear gain; GAIN predicts disordered UNSTABLE):")
for K0 in [0.5,1.0,5.0]:
    Rs=[sim_gak(200,K0,0.5,rng.uniform(-1,1,200),rng.uniform(0,2*np.pi,200)) for _ in range(3)]
    print(f"  K0={K0}: R={np.mean(Rs):.3f}")
