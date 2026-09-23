"""
CORRECT exact stationary density of the NOISY ADLER equation on the circle
via the FOURIER/continued-fraction (Miller) method - O(M) per dw.

    dtheta/dt = dw - 2K sin(theta) + sigma * xi(t)

Fokker-Planck stationary with D=sigma^2/2 and flux J:
    D P' - (dw - 2K sin theta) P = -J,   P(2pi)=P(0)

Fourier P = sum_n c_n e^{in theta}:
  n != 0:  (i D n - dw) c_n - i K c_{n-1} + i K c_{n+1} = 0
  n  = 0:  -dw c_0 - i K c_{-1} + i K c_1 + J = 0

For real P: c_{-n} = conj(c_n). The minimal (decaying) solution of the recurrence
is found by backward continued fraction. With a_n = (dw - i D n)/(i K):

    c_{n+1} = a_n c_n + c_{n-1}   =>   r_{n+1} = a_n + 1/r_n,  r_n = c_n/c_{n-1}
    backward: start r_{M+1}=0,  r_n = 1/(r_{n+1} - a_n)

Normalization gives c_0 = 1/(2pi), and
    R = |<e^{i theta}>| = |2 pi c_{-1}| = |2 pi conj(c_1)| = |r_1|.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def R_exact_cf(dw, K, sigma, M=2000):
    D = 0.5*sigma**2
    if sigma < 1e-9:
        delta = abs(dw)/(2*K)
        return 1.0 if delta <= 1.0 else delta - np.sqrt(delta**2 - 1)
    # backward Miller recurrence
    r = 0.0 + 0.0j
    for n in range(M, 0, -1):
        a_n = (dw - 1j*D*n)/(1j*K)
        r = 1.0/(r - a_n)
    return abs(r)   # = |r_1|

def R_over_dw(dw_list, K, sigma, M=2000):
    return np.array([R_exact_cf(dw, K, sigma, M) for dw in dw_list])

if __name__ == "__main__":
    # Convergence test of M
    print("=== Miller-M convergence (sigma=0.05, K=2.0) ===")
    for M in [100, 300, 800, 2000, 5000]:
        print(f"M={M:5d}  R(dw=0)={R_exact_cf(0.0,2.0,0.05,M):.6f}  R(dw=6)={R_exact_cf(6.0,2.0,0.05,M):.6f}")
    print()
    # deterministic check
    print("=== sanity: small sigma should approach deterministic ===")
    for sig in [0.5,0.2,0.1,0.05,0.02]:
        print(f"sigma={sig:.2f}  R(dw=0,K=2)={R_exact_cf(0.0,2.0,sig,2000):.5f}  R(dw=3.9,K=2)={R_exact_cf(3.9,2.0,sig,2000):.5f}")
