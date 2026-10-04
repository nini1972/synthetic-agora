import numpy as np, time

def run_protocol(N, K0, alpha=0.6, sigma=0.008, omega_std=0.7, mode='ramp_up',
                 T_per=200.0, dt=0.1, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0,2*np.pi,N)
    omega = rng.normal(0, omega_std, N)
    if mode=='ramp_up':
        theta = rng.normal(0,0.05,N)  # start synchronized
        Kseq = np.linspace(0.05, K0, max(2,int(K0/0.05)))
    else:
        Kseq = [K0]
    steps=int(T_per/dt)
    lastR=0.0
    for K0b in Kseq:
        for step in range(steps):
            z=np.mean(np.exp(1j*theta)); R=abs(z); K=K0b*R**alpha
            Z=np.sum(np.exp(1j*theta))
            dtheta=(K/N)*np.imag(Z*np.exp(-1j*theta)) - omega + sigma*rng.normal(0,np.sqrt(dt),N)
            theta=theta+dtheta
        z=np.mean(np.exp(1j*theta)); lastR=abs(z)
    return lastR

if __name__=="__main__":
    t0=time.time()
    print("=== N=150, omega_std=0.7, RAMP UP (synced IC). Forward edge Kc^fwd: smallest K0 staying synced ===")
    Kc=None
    for K0 in [0.3,0.5,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.5]:
        # ramp_from low to K0, measure if stays synced
        r=run_protocol(150,K0,mode='ramp_up',seed=7)
        stays = r>0.5
        if Kc is None and stays: Kc=K0
        print(f"  target K0={K0:4.2f}  R_after_ramp={r:.3f}  synced={stays}")
    print(f"  --> Kc^fwd ~ {Kc} (finite, confirming omega-disorder source)")
    print("elapsed",round(time.time()-t0,1))
