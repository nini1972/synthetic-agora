"""
Independent Monte-Carlo validation of the exact periodic-FP order parameter
R(dw) for the noisy Adler equation. Uses Euler-Maruyama with many walkers.

  dtheta = (dw - 2K sin theta) dt + sigma dW,   R = |<e^{i theta}>|_stationary

Compare against the continued-fraction exact solution R_cf_vectorized.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def R_mc(dw, K, sigma, nwalk=4000, dt=5e-3, nsteps=60000, seed=0):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2*np.pi, nwalk)
    z = 0.0+0.0j
    for _ in range(nsteps):
        th = th + (dw - 2*K*np.sin(th))*dt + sigma*np.sqrt(dt)*rng.standard_normal(nwalk)
        z += np.mean(np.exp(1j*th))
    return abs(z)/nsteps

# reuse exact solver
exec(open('adler_ceiling_corrected.py').read().split('if __name__')[0])

if __name__ == "__main__":
    cases = [(0.0,1.65,0.5),(3.0,1.65,0.5),(6.0,1.65,0.5),(0.0,2.0,0.8),(3.0,2.0,0.8)]
    print(f"{'dw':>5} {'K':>5} {'sig':>5} | {'R_exact(CF)':>12} {'R_MC':>10} {'rel.err':>9}")
    for dw,K,sig in cases:
        Rex = float(R_cf_vectorized(np.array([dw]),np.array([K]),sig,M=800)[0,0])
        Rmc = R_mc(dw,K,sig)
        print(f"{dw:5.1f} {K:5.2f} {sig:5.2f} | {Rex:12.5f} {Rmc:10.5f} {abs(Rmc-Rex)/max(Rex,1e-9):9.3%}")
