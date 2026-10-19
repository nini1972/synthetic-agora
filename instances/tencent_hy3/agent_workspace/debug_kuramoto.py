import numpy as np
N=300; a=1; K0=5; dt=0.02
rng=np.random.default_rng(0)
theta=rng.uniform(0,2*np.pi,N)
z=np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
print('t=0 R0=',R)
for step in range(10000):
    z=np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
    K_eff=K0*(R**a)
    dtheta=K_eff*R*np.sin(psi-theta)
    theta=theta+dt*dtheta
    if step in [0,9,49,99,499,999,4999,9999]:
        r=np.abs(np.mean(np.exp(1j*theta)))
        print(f'step {step} R={r:.4f} K_eff={K_eff:.4f} max|dtheta|={np.max(np.abs(dt*dtheta)):.4f}')
print('check: is theta collapsing to single value? std(theta)=',np.std(theta))
