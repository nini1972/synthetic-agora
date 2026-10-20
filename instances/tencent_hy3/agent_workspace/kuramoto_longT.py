import numpy as np
def sim(N,a,K0,Delta,T=2000.0,dt=0.01,seed=0):
    rng=np.random.default_rng(seed)
    theta=rng.uniform(0,2*np.pi,N)
    if Delta>0:
        U=rng.uniform(1e-6,1-1e-6,N); omega=Delta*np.tan(np.pi*(U-0.5))
    else: omega=np.zeros(N)
    steps=int(T/dt); R_arr=[]
    for _ in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
        Keff=K0*(R**a); theta=theta+dt*(omega+Keff*R*np.sin(psi-theta)); R_arr.append(R)
    R_arr=np.array(R_arr); tail=R_arr[int(0.75*len(R_arr)):]
    return R_arr[-1], bool(np.all(tail>=0.5))

# a=2, Delta=0, long T: do all eventually lock?
print("a=2, Delta=0, T=2000:")
locks=0
for s in range(8):
    f,l=sim(300,2,5,0.0,T=2000.0,seed=s)
    print(f"  seed {s}: R_final={f:.4f} locked={l}")
    locks+=l
print(f"  lock_rate={locks/8:.3f}")

# a=2, Delta=0.5 (barrier): does any escape even at long T?
print("a=2, Delta=0.5, T=2000:")
for s in range(4):
    f,l=sim(300,2,5,0.5,T=2000.0,seed=s)
    print(f"  seed {s}: R_final={f:.4f} locked={l}")
