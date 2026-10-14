import numpy as np
from scipy import special

def R_cf(dw, K, D, N=600):
    # vectorized-over-nothing backward scan; but do scan over a vector of n
    r = np.array(K / (D * N + 1j * dw), dtype=complex)
    # backward iteration via cumulative approach: iterate r = K/((i dw + D n) + K r)
    for n in range(N - 1, 0, -1):
        r = K / ((1j * dw + D * n) + K * r)
    return abs(r)

def R_cf_vec(dw, K, D, N=600):
    # faster: iterate with numpy scalar ops is same speed; use float trick:
    # r_n = K/((i dw + D n) + K r_{n+1}). Do in C-like loop but with plain floats via numpy complex
    r = K / (D * N + 1j * dw)
    inv = 1.0 / K
    for n in range(N - 1, 0, -1):
        r = inv / ((1j * dw + D * n) * inv + r)
    return abs(r)

def R_det(dw, K):
    f = dw - 2*K
    return 1.0 if f < 0 else (dw - np.sqrt(dw*dw - (2*K)**2)) / (2*K)

def R_mc(dw, K, sigma, nwalk=60000, dt=0.1, T=2000.0, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, nwalk)
    nsteps = int(T/dt)
    sq = sigma*np.sqrt(2*dt)
    for _ in range(nsteps):
        theta = (theta + dt*(dw - 2*K*np.sin(theta)) + sq*rng.standard_normal(nwalk)) % (2*np.pi)
    return abs(np.mean(np.exp(1j*theta)))

if __name__ == "__main__":
    K = 1.65
    dws = [3.0, 4.0, 5.0, 6.0]
    print("deterministic dwell-bias R:", [round(R_det(d,K),4) for d in dws])
    for sig in [1e-3, 5e-3, 1e-2, 5e-2]:
        D = sig*sig/2
        print(f"sigma={sig}: ", [round(R_cf_vec(d,K,D),4) for d in dws])
    sig0=0.5; D0=sig0**2/2
    print(f"dw=0 sig=0.5: CF={R_cf_vec(0.0,K,D0):.6f} Bessel={special.i1(K/D0)/special.i0(K/D0):.6f}")
    for sig, dw in [(0.05,4.0),(0.05,5.0),(0.05,6.0),(0.5,5.0),(0.2,3.0)]:
        D=sig*sig/2
        print(f"sig={sig} dw={dw}: CF={R_cf_vec(dw,K,D):.4f} MC={R_mc(dw,K,sig):.4f}")
