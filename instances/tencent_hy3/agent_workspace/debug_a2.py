import numpy as np
np.set_printoptions(suppress=True)

# Deterministic OA flow for a=2, K0=5
def oa_R(R):
    return 0.5*R*(5*R**(2-1)*(1-R*R) - 1.0)  # a=2
print("OA deterministic dR/dt (a=2):")
for R in [0.05,0.09,0.15,0.219,0.3,0.5,0.9]:
    print(f"  R={R:.3f}  dR/dt={oa_R(R):+.4f}")

# Finite-N simulation, trace, several dt and integrators
def sim(N,a,K0,T,dt,seed,integrator='euler'):
    rng=np.random.default_rng(seed)
    theta=rng.uniform(0,2*np.pi,N)
    steps=int(T/dt)
    Rs=[]
    for s in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
        Keff=K0*(R**a)
        if integrator=='euler':
            theta=theta+dt*(Keff*R*np.sin(psi-theta))
        elif integrator=='rk4':
            def f(th):
                zz=np.mean(np.exp(1j*th)); Rr=np.abs(zz); pp=np.angle(zz)
                return K0*(Rr**a)*Rr*np.sin(pp-th)
            k1=f(theta); k2=f(theta+0.5*dt*k1); k3=f(theta+0.5*dt*k2); k4=f(theta+dt*k3)
            theta=theta+(dt/6.0)*(k1+2*k2+2*k3+k4)
        Rs.append(R)
    return np.array(Rs)

for dt in [0.02,0.005,0.001]:
    Rs=sim(300,2,5,200,dt,0,'euler')
    print(f"\nEuler dt={dt}: R_final={Rs[-1]:.4f}  R@50={Rs[min(50,len(Rs)-1)]:.4f}  R@500={Rs[min(500,len(Rs)-1)]:.4f}  R@5000={Rs[min(5000,len(Rs)-1)]:.4f}")
    # when does it first exceed 0.3?
    cross=np.where(Rs>0.3)[0]
    print("   first cross 0.3 at step", cross[0] if len(cross)>0 else "NEVER")

Rs=sim(300,2,5,200,0.005,0,'rk4')
print(f"\nRK4 dt=0.005: R_final={Rs[-1]:.4f}  R@500={Rs[min(500,len(Rs)-1)]:.4f}  R@5000={Rs[min(5000,len(Rs)-1)]:.4f}")
cross=np.where(Rs>0.3)[0]
print("   first cross 0.3 at step", cross[0] if len(cross)>0 else "NEVER")

# Also seed 0 vs seed 5
for seed in [0,5]:
    Rs=sim(300,2,5,200,0.02,seed,'euler')
    print(f"Euler seed={seed} dt=0.02: R_final={Rs[-1]:.4f}")
