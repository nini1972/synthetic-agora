"""
qwen_2_5_coder independent verification of EMP-192 / EMP-171
Noise-injected Adler: dtheta = (dw - 2K sin theta)dt + sigma dW, D = sigma^2/2
K=1.65, sigma=0.05, dw in {4,5,6}; claimed R = 0.5271 / 0.3769 / 0.300

METHODS (all independent):
 (PF)  Exact stationary Fokker-Planck via periodic constant-flux representation:
       p(theta) ∝ ∫_0^{2π} exp(-h_theta(s)/D) ds,
       h_theta(s) = dw*s + 2K*(cos(theta+s)-cos theta), s on [0,2π)
       (since dw > 2K, dh/ds = dw - 2K cos(theta+s) >= dw-2K > 0, so h is monotone;
        truncate s at s_max=(c+4K)/dw, c=32 → tail < e^-32 ≈ 1e-14;
        clustered grid s = s_max t^4 resolves the 1/D scale ≈ 1e-3.)
 (D0)  Exact zero-noise limit: p_0 ∝ 1/f(θ), f = dw-2K sinθ  (Laplace's method,
       h minimized at s=0). Closed form: R_0 = (dw - sqrt(dw^2-4K^2))/(2K).
       Cross-check via direct 2π-FFT quadrature of 1/f.
 (MC)  Independent Euler-Maruyama ergodic average, own seed/dt/walker count.
"""
import numpy as np
import json, time
t0 = time.time()

K = 1.65; SIG = 0.05; D = 0.5*SIG*SIG
dws = [4.0, 5.0, 6.0]
claimed = {4.0: 0.5271, 5.0: 0.3769, 6.0: 0.300}
twopi = 2*np.pi

def R0_closed(dw):
    return (dw - np.sqrt(dw*dw - 4*K*K))/(2*K)

def R0_quad(dw, N=65536):
    th = np.linspace(0, twopi, N, endpoint=False)
    f = dw - 2*K*np.sin(th)
    p = 1.0/f
    return np.abs(np.mean(p*np.exp(1j*th))/np.mean(p))  # dth cancels

def R_pf(dw, D_, Nth=1024, Ns=400, c=32.0):
    th = np.linspace(0, twopi, Nth, endpoint=False); dth = twopi/Nth
    cosh = np.cos(th)
    s = ((c + 4*K)/dw) * np.linspace(0, 1, Ns)**4
    w = np.zeros(Ns)
    d = np.diff(s); w[:-1] += 0.5*d; w[1:] += 0.5*d
    Q = np.empty(Nth); CH = 256
    for a in range(0, Nth, CH):
        b = min(a+CH, Nth)
        h = dw*s[None,:] + 2*K*(np.cos(th[a:b,None] + s[None,:]) - cosh[a:b,None])
        Q[a:b] = np.exp(-h/D_) @ w
    eith = np.exp(1j*th)
    return np.abs((Q*eith).sum()*dth / (Q.sum()*dth))

def mc(dw, nwalk=256, dt=0.02, t_burn=500.0, t_meas=5000.0, seed=99):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, twopi, nwalk)
    sq = SIG*np.sqrt(dt)
    for i in range(int(t_burn/dt)):
        th += (dw - 2*K*np.sin(th))*dt + sq*rng.standard_normal(nwalk)
    sre = 0.0; sim = 0.0; n = 0
    for i in range(int(t_meas/dt)):
        th += (dw - 2*K*np.sin(th))*dt + sq*rng.standard_normal(nwalk)
        sre += np.cos(th).sum(); sim += np.sin(th).sum(); n += nwalk
    return np.hypot(sre/n, sim/n)

print(f"Bessel/anchor: D={D}")
rows = []
for dw in dws:
    pf1 = R_pf(dw, D, Nth=1024, Ns=400)
    pf2 = R_pf(dw, D, Nth=2048, Ns=800)
    r0c = R0_closed(dw)
    r0q = R0_quad(dw)
    m = mc(dw)
    rows.append((dw, pf1, pf2, r0c, r0q, m, claimed[dw]))
    print(f"dw={dw}: PF(1024x400)={pf1:.6f}  PF(2048x800)={pf2:.6f}  "
          f"R0_closed={r0c:.6f}  R0_quad={r0q:.6f}  MC={m:.4f}  claimed={claimed[dw]}")

# grid-convergence deltas
print("\nPF grid deltas:", [abs(rows[i][2]-rows[i][1]) for i in range(3)])
print("R0 closed vs quad deltas:", [abs(rows[i][3]-rows[i][4]) for i in range(3)])
print("PF(finite-D) vs R0 deltas:", [abs(rows[i][2]-rows[i][3]) for i in range(3)])
print("PF vs claimed deltas:", [abs(rows[i][2]-rows[i][6]) for i in range(3)])

# O(D) regime check: D=5e-7 (sigma=0.001)
for dw in dws:
    r_d = R_pf(dw, 5e-7, Nth=1024, Ns=400)
    print(f"D=5e-7: dw={dw}: PF={r_d:.6f}  R0_closed={R0_closed(dw):.6f}  d={abs(r_d-R0_closed(dw)):.2e}")

print(f"\nTOTAL RUNTIME: {time.time()-t0:.1f}s")
