"""
DIAGNOSTIC: why does fresh-IC dt=0.1 ignite at K0=0.8 for ALL N?
Track R(t) traces for N=800 vs N=50 at K0=0.8, and test dt sensitivity.
Reflexive mean-field Kuramoto: dtheta/dt = K0*R^(1+alpha)*sin(psi-th) + sigma*xi
"""
import numpy as np

ALPHA = 0.6
SIGMA = 0.008

def trace(N, K0, seed, T, DT, record_every=400):
    r = np.random.default_rng(seed)
    th = r.uniform(0, 2*np.pi, N)
    ns = int(T / DT)
    rec = []
    for t in range(ns):
        c, s_ = np.cos(th), np.sin(th)
        C, S = c.mean(), s_.mean()
        R = np.hypot(C, S)
        psi_s = S / R if R > 1e-12 else 0.0
        psi_c = C / R if R > 1e-12 else 0.0
        Keff = K0 * R**ALPHA * R
        force = Keff * (psi_s * c - psi_c * s_)
        th = th + DT * force + SIGMA * np.sqrt(DT) * r.standard_normal(N)
        if (t + 1) % record_every == 0:
            c, s_ = np.cos(th), np.sin(th)
            rec.append(np.hypot(c.mean(), s_.mean()))
    return np.array(rec)

print("=== R(t) traces, K0 = 0.8, T=400 ===")
for DT in (0.1, 0.05, 0.02):
    for N in (50, 800):
        tr = trace(N, 0.8, 7, 400.0, DT)
        marks = ", ".join(f"t={int((i+1)*400/len(tr))}:{v:.3f}" for i, v in enumerate(tr[:6]))
        print(f"  dt={DT:<5} N={N:<4} R(t): {marks} ... final R={tr[-1]:.4f}")

print()
print("=== same but K0 = 2.0 (for contrast) ===")
for DT in (0.1, 0.05):
    for N in (50, 800):
        tr = trace(N, 2.0, 7, 400.0, DT)
        print(f"  dt={DT:<5} N={N:<4} final R={tr[-1]:.4f}")

print()
print("=== NOISE-OFF test: deterministic only (sigma=0), K0=0.8, N=800, dt=0.1 ===")
r = np.random.default_rng(7)
N, DT, K0 = 800, 0.1, 0.8
th = r.uniform(0, 2*np.pi, N)
for t in range(4000):
    c, s_ = np.cos(th), np.sin(th)
    C, S = c.mean(), s_.mean()
    R = np.hypot(C, S)
    psi_s = S / R if R > 1e-12 else 0.0
    psi_c = C / R if R > 1e-12 else 0.0
    Keff = K0 * R**ALPHA * R
    force = Keff * (psi_s * c - psi_c * s_)
    th = th + DT * force
    if (t + 1) % 800 == 0:
        c, s_ = np.cos(th), np.sin(th)
        print(f"    t={0.1*(t+1):5.0f}  R = {np.hypot(c.mean(), s_.mean()):.4f}  K_eff = {Keff:.2e}")
c, s_ = np.cos(th), np.sin(th)
print(f"    final R = {np.hypot(c.mean(), s_.mean()):.4f}")
