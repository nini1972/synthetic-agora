"""
DIAGNOSTIC: why did the finite-size shift test come back UNRESOLVED?
====================================================================
The bracket (0.2, 60.0) was far too coarse. Predicted shift factors range
0.00007 -> 0.09242, so K_c for alpha>=1.5 sits BELOW K_bracket_lo = 0.2.
The bisection's guard conditions both failed, and I reported "unresolved"
without learning anything. That is a design failure in the test, not a
scientific result. Fix: bracket adaptively, NOT with a fixed span.

Also, the raw predictions are themselves a diagnostic:
  alpha=1.0, N=200: (1.307/sqrt(200))^{2} = 0.0085  -> K_c ~ 0.05
  alpha=1.0, N=1000: (1.307/sqrt(1000))^{2} = 0.0017 -> K_c ~ 0.012
So for alpha>=1.5 K_c collapses toward zero. Either (a) my (c/sqrt N)^{2a}
law is grossly too strong, or (b) the measured K_c values I actually observe
(must-be-locked at K0=1.0, alpha=1.0, N=2000 -> R=0.99) must then be enormous
enormous, which would make the ratio K_c(N)/K_c_inf huge, not small. There is
a sign/structure error in my collapse normalization.
"""
import numpy as np


def rk4_sync(theta, omegas, K0, alpha, T, dt):
    n_steps = int(T / dt)
    def f(th):
        z = np.mean(np.exp(1j*th))
        return omegas + K0*(abs(z)**alpha)*np.sin(np.angle(z) - th)
    for _ in range(n_steps):
        k1 = f(theta); k2 = f(theta + 0.5*dt*k1)
        k3 = f(theta + 0.5*dt*k2); k4 = f(theta + dt*k3)
        theta = theta + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
    return abs(np.mean(np.exp(1j*theta)))


print("="*70)
print("RAW K0 SCAN at fixed N (does locking actually turn on?)")
print("="*70)
for alpha in [1.0, 2.0]:
    for N in [200, 1000]:
        print(f"\n  alpha={alpha}, N={N}")
        for K0 in [0.01, 0.05, 0.1, 0.3, 1.0, 3.0]:
            Rs = []
            for t in range(8):
                rng = np.random.default_rng(4242 + t)
                omegas = rng.standard_cauchy(N)
                th0 = rng.uniform(0, 2*np.pi, N)
                Rs.append(rk4_sync(th0, omegas, K0, alpha, T=40.0, dt=0.02))
            Rm = np.mean(Rs)
            lock = "LOCKED" if Rm > 0.5 else "incoh"
            print(f"    K0={K0:<6} R={Rm:.4f}  ({lock})")