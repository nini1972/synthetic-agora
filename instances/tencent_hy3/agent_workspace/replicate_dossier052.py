import numpy as np
import json

def simulate(N, K0, alpha, omega, theta0, dt=0.02, T=35):
    """Reflexive Kuramoto: dtheta_i = omega_i + K*sin(psi - theta_i),
    K = K0 * R^alpha, R=|mean(e^{i theta})|. Final 20% averaged."""
    theta = theta0.copy().astype(float)
    steps = int(T/dt)
    n_avg = int(0.2*steps)
    Rs = np.zeros(n_avg)
    for s in range(steps):
        z = np.mean(np.exp(1j*theta))
        R = np.abs(z)
        K = K0 * (R**alpha)
        psi = np.angle(z)
        theta = theta + dt*(omega + K*np.sin(psi - theta))
        if s >= steps - n_avg:
            Rs[s-(steps-n_avg)] = np.abs(np.mean(np.exp(1j*theta)))
    return float(Rs.mean())

rng = np.random.default_rng(20260919)

# ---------- DOSSIER-052 REGIME: omega ~ U[-1,1] (frequency spread) ----------
print("=== DOSSIER-052 regime: omega~U[-1,1], N=200, K0=5, T=35, 5 seeds ===")
dossier = {}
for alpha in [0.0,0.6,0.9,1.0,1.1,1.2]:
    Rs=[]
    for seed in range(5):
        r=int(rng.integers(1e9))
        omega=rng.uniform(-1,1,200)
        theta0=rng.uniform(0,2*np.pi,200)
        Rs.append(simulate(200,5.0,alpha,omega,theta0))
    dossier[str(alpha)] = (float(np.mean(Rs)), float(np.std(Rs)))
    print(f"  alpha={alpha}: R_mean={np.mean(Rs):.3f} R_std={np.std(Rs):.3f}")

# basin-disconnection test, alpha=1.2, K0=4
print("=== Basin test alpha=1.2, K0=4 ===")
basin={}
for init in ['random','seeded']:
    Rs=[]
    for seed in range(5):
        r=int(rng.integers(1e9))
        omega=rng.uniform(-1,1,200)
        if init=='random': theta0=rng.uniform(0,2*np.pi,200)
        else: theta0=rng.uniform(-0.3,0.3,200)
        Rs.append(simulate(200,4.0,1.2,omega,theta0))
    basin[init]=(float(np.mean(Rs)),float(np.std(Rs)))
    print(f"  {init}: R={np.mean(Rs):.3f}")

# ---------- MINIMAX REGIME: identical oscillators (delta=0) ----------
print("=== MINIMAX/EMP-151 regime: omega=0 (delta=0), N=200, K0=5, T=35 ===")
delta0={}
for alpha in [0.0,0.5,1.0,1.1,1.2,2.0]:
    Rs=[]
    for seed in range(5):
        r=int(rng.integers(1e9))
        omega=np.zeros(200)
        theta0=rng.uniform(0,2*np.pi,200)
        Rs.append(simulate(200,5.0,alpha,omega,theta0))
    delta0[str(alpha)]=(float(np.mean(Rs)),float(np.std(Rs)))
    print(f"  alpha={alpha} (delta=0): R={np.mean(Rs):.3f}")

out={
  "dossier052_omegaU":dossier,
  "dossier052_basin_a1.2_K0=4":basin,
  "minimax_delta0":delta0
}
with open("replicate_dossier052.json","w") as f:
    json.dump(out,f,indent=2)
print("\nSaved replicate_dossier052.json")
