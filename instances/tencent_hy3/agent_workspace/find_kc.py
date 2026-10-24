import numpy as np
def sim_constant(N,K,omega,theta0,dt=0.02,T=40):
    theta=theta0.copy().astype(float); steps=int(T/dt); n_avg=int(0.2*steps); Rs=np.zeros(n_avg)
    for s in range(steps):
        z=np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
        theta=theta+dt*(omega+K*np.sin(psi-theta))
        if s>=steps-n_avg: Rs[s-(steps-n_avg)]=np.abs(np.mean(np.exp(1j*theta)))
    return Rs.mean()
rng=np.random.default_rng(7)
print("Locate K_c for omega~U[-1,1] (expect ~2? from K_c=2g(0)^{-1}... test):")
for K in [0.5,1.0,1.27,1.5,2.0,3.0]:
    Rs=[]
    for _ in range(4):
        omega=rng.uniform(-1,1,200); theta0=rng.uniform(0,2*np.pi,200)
        Rs.append(sim_constant(200,K,omega,theta0))
    print(f"  K={K:4.2f}: R_final={np.mean(Rs):.4f}")

# barrier test: start from partial coherence, see if it climbs or decays for alpha>0
def sim_gain(N,K0,alpha,r0_init,dt=0.02,T=40):
    theta=rng.uniform(0,2*np.pi,N).astype(float)
    # enforce initial R ~ r0_init by clustering
    # simpler: just start random; instead test monotonicity by scanning R_eff
    return None
print("\nConclusion expected: K_c~2 (U[-1,1] gamma=1 => K_c=2gamma=2).")
print("If K_c~2, then K0=5 is strongly supercritical; barrier R*=(Kc/K0)^(1/alpha).")
print("alpha=1.2: R*=(2/5)^(1/1.2)=(0.4)^0.833=0.46. random R0~0.07<0.46 => SHOULD decay.")
print("Yet sim climbs -> suggests gain barrier is NOT a simple decay trap here; need finer probe.")
