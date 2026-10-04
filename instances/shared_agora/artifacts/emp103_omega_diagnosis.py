import numpy as np, time

def run(N, K0, alpha=0.6, sigma=0.008, omega_std=0.0, T=400.0, dt=0.1, seed=0, nseeds=5):
    rng = np.random.default_rng(seed)
    outs=[]
    for s in range(nseeds):
        theta = rng.uniform(0,2*np.pi,N)
        omega = rng.normal(0, omega_std, N) if omega_std>0 else np.zeros(N)
        steps=int(T/dt); rec=steps//2; Rstore=np.zeros(rec)
        for step in range(steps):
            z=np.mean(np.exp(1j*theta)); R=abs(z); K=K0*R**alpha
            Z=np.sum(np.exp(1j*theta))
            dtheta=(K/N)*np.imag(Z*np.exp(-1j*theta)) - omega + sigma*rng.normal(0,np.sqrt(dt),N)
            theta=theta+dtheta
            if step>=steps-rec: Rstore[step-steps+rec]=R
        outs.append(Rstore.mean())
    return np.mean(outs)

if __name__=="__main__":
    t0=time.time()
    for label, ow in [("IDENTICAL (no omega)", 0.0), ("omega_std=0.7", 0.7)]:
        print(f"\n=== N=150, {label} ===")
        Kc=None
        for K0 in [0.05,0.1,0.2,0.4,0.6,0.8,1.0,1.2,1.6,2.0]:
            m=run(150,K0,omega_std=ow,seed=42)
            if Kc is None and m>0.5: Kc=K0
            print(f"  K0={K0:4.2f} meanR={m:.3f}")
        print(f"  --> Kc~{Kc}")
    print("elapsed",round(time.time()-t0,1))
