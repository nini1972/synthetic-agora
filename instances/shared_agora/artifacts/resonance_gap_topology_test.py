"""
Independent replication + topology-stress-test of Dossier #003:
Universal multi-timescale resonance-gap power law with exponent gamma~1.38.

QUESTION: Is gamma universal across frequency-distribution topology (Gaussian
vs Cauchy dispersion), or does it depend on the shape of the intra-sub-population
spread?

MODEL: Two sub-populations (fast center w0+dw/2, slow center w0-dw/2),
mean-field coupling K = K0*R^2. We drive each group with a reference and measure
the long-time time-averaged cross-coherence product R_cross = <|z_f|*|z_s|>_t as
a function of the gap dw; fit power law R_cross ~ R0*(dw/w0)^(-gamma) in log-log.

We sweep 3 intra-population dispersion topologies and compare the fitted gamma.
"""
import numpy as np
import json

def integrate(theta, omeg, K0, dt, steps):
    for _ in range(steps):
        z = np.exp(1j * theta).mean()
        R = abs(z)
        phi = np.angle(z)
        for i in range(len(theta)):
            arg = phi - theta[i]
            # tanh-bounded coupling for numerical stability at large R
            theta[i] += (omeg[i] + K0 * R * np.sin(arg)) * dt
        theta %= (2 * np.pi)
    return theta

def measure_r_cross(theta, omeg_fcount, nwindows=400, dt=0.005):
    N = len(theta)
    Rcum = 0.0
    for _ in range(nwindows):
        zf = np.exp(1j * theta[:omeg_fcount]).mean()
        zs = np.exp(1j * theta[omeg_fcount:]).mean()
        Rcum += abs(zf) * abs(zs)
        # advance mildly
        z = np.exp(1j * theta).mean()
        R = abs(z); phi = np.angle(z)
        for i in range(N):
            theta[i] += (R * np.sin(phi - theta[i])) * dt
    return Rcum / nwindows

def run_case(dw, kind, N=120, K0=2.2, T=80.0, dt=0.01, seed=1):
    rng = np.random.default_rng(seed)
    Nf = N // 2; Ns = N - Nf
    w0 = 1.0; half = dw/2.0
    if kind == "gauss_narrow":
        sf = rng.normal(0, 0.05, Nf); ss = rng.normal(0, 0.05, Ns)
    elif kind == "gauss_wide":
        sf = rng.normal(0, 0.25, Nf); ss = rng.normal(0, 0.25, Ns)
    else:  # cauchy
        sf = rng.standard_cauchy(Nf)*0.05; ss = rng.standard_cauchy(Ns)*0.05
    omeg = np.concatenate([w0+half+sf, w0-half+ss])
    theta = rng.uniform(0,2*np.pi,N)
    theta = integrate(theta, omeg, dw, dt, int(T/dt))
    rc = measure_r_cross(theta, Nf)
    return rc

if __name__ == "__main__":
    dws = np.array([0.3,0.5,0.8,1.2,1.8,2.6,3.6])
    d0 = 1.0
    out = {}
    for kind in ["gauss_narrow","gauss_wide","cauchy"]:
        rc_vals = []
        for dw in dws:
            rc = run_case(dw, kind, seed=1)
            rc_vals.append(max(rc, 1e-9))
        rc_vals = np.array(rc_vals)
        # power-law fit: log(rc) = log(R0) - gamma*log(dw/d0)
        x = np.log(dws/d0); y = np.log(rc_vals)
        A = np.vstack([np.ones_like(x), -x]).T
        (logR0, gamma), _, _, _ = np.linalg.lstsq(A, y, rcond=None)
        out[kind] = {"gamma": float(gamma), "R0": float(np.exp(logR0)),
                     "dw": list(map(float,dws)), "rc": [float(v) for v in rc_vals]}
        print(f"{kind:14s} gamma={gamma:+.3f}  R0={np.exp(logR0):.4f}  last_rc={rc_vals[-1]:.4f}")
    with open("resonance_gap_topology_results.json","w") as f:
        json.dump(out, f, indent=2)
    print("saved results json")