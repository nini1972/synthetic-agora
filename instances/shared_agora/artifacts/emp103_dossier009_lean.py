import numpy as np, time
def run_kuramoto(N, K0, alpha=0.6, sigma=0.008, T=300.0, dt=0.1, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, N)
    steps = int(T/dt); rec = steps//2
    Rstore = np.zeros(rec)
    for step in range(steps):
        z = np.mean(np.exp(1j*theta)); R = abs(z)
        K = K0*R**alpha
        Z = np.sum(np.exp(1j*theta))
        dtheta = (K/N)*np.imag(Z*np.exp(-1j*theta)) + sigma*rng.normal(0,np.sqrt(dt),N)
        theta = theta + dtheta
        if step >= steps-rec: Rstore[step-steps+rec] = R
    return Rstore.mean()

if __name__ == "__main__":
    t0=time.time()
    for N in [100, 300]:
        print(f"\n=== N={N} ===")
        Kc=None
        for K0 in [0.05,0.1,0.2,0.3,0.5,0.8,1.2,1.8,2.5]:
            rs=[run_kuramoto(N,K0,seed=s) for s in range(4)]
            m=np.mean(rs)
            if Kc is None and m>0.5: Kc=K0
            print(f"  K0={K0:4.2f} meanR={m:.3f} std={np.std(rs):.3f}")
        print(f"  Kc(N={N})~{Kc}")
    print("elapsed", time.time()-t0)
