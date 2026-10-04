import numpy as np, os, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

def run_kuramoto(N, K0, alpha=0.6, sigma=0.008, T=2500.0, dt=0.05, seed=0, R_init_uniform=True):
    """EXACT Dossier #009 model:
       dtheta_i = (K0*R^alpha / N) * sum_j sin(theta_j - theta_i) dt + sigma*sqrt(dt)*eta
       identical oscillators (no omega_i), with small noise sigma=0.008.
    """
    rng = np.random.default_rng(seed)
    if R_init_uniform:
        theta = rng.uniform(0, 2*np.pi, N)
    else:
        theta = rng.normal(0, 0.3, N)  # tighter => higher R0
    steps = int(T/dt)
    rec = int(steps*0.5)
    Rstore = np.zeros(rec)
    for step in range(steps):
        z = np.mean(np.exp(1j*theta))
        R = abs(z)
        K = K0 * (R**alpha)
        Z = np.sum(np.exp(1j*theta))
        dtheta = (K/N)*np.imag(Z*np.exp(-1j*theta)) + sigma*rng.normal(0, np.sqrt(dt), N)
        theta = theta + dtheta
        if step >= steps-rec:
            Rstore[step-steps+rec] = R
    return Rstore.mean(), Rstore

if __name__ == "__main__":
    # Feasibility: N=100 and N=600, sweep K0, 6 seeds each.
    Kgrid = [0.05,0.1,0.2,0.3,0.5,0.8,1.0,1.2,1.6,2.0,2.5,3.0]
    for N in [100, 600]:
        print(f"\n=== N={N} (Dossier #009 exact model, sigma=0.008) ===")
        Kc = None
        res = {}
        for K0 in Kgrid:
            rs = [run_kuramoto(N, K0, seed=s)[0] for s in range(6)]
            m = np.mean(rs); res[K0]=m
            if Kc is None and m > 0.5:
                Kc = K0
            print(f"  K0={K0:4.2f}  meanR={m:.3f}  std={np.std(rs):.3f}")
        print(f"  --> estimated K_c(N={N}) ~ {Kc}")
