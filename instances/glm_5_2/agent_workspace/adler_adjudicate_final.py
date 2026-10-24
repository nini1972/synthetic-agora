import numpy as np
from scipy import special
import json

K0 = 1.65

# ============================================================
# 1. Deterministic R via exact quadrature (sigma -> 0, dw > 2K)
# ============================================================
def R_det_quad(dw, K, ntheta=200001):
    if dw <= 2*K:
        return 1.0
    th = np.linspace(0, 2*np.pi, ntheta)
    v = dw - 2*K*np.sin(th)
    w = 1.0/v
    Z = np.trapezoid(w, th)
    re = np.trapezoid(w*np.cos(th), th)/Z
    im = np.trapezoid(w*np.sin(th), th)/Z
    return float(np.hypot(re, im))

# ============================================================
# 2. Periodic constant-flux FP: tridiagonal Thomas solve, O(N)
#    Recurrence (n>=1):  K c_{n+1} + (i*dw + D~ n) c_n - K c_{n-1} = 0
#    c_0 = 1, c_{N+1} = 0 (minimal solution).  R = |c_1|.
#    Vectorized over (K, dw) pairs: axes (N, P, M).
# ============================================================
def R_cf_grid(dw_arr, K_arr, sigma, N=400):
    D = 0.5*sigma*sigma
    dws = np.atleast_1d(dw_arr)[None, :]           # (1, M)
    Ks = np.atleast_1d(K_arr)[:, None]             # (P, 1)
    P, M = Ks.size, dws.size
    b_vec = 1j*dws + D*np.arange(1, N+1)[:, None]  # (N, M)
    cp = np.zeros((N, P, M), dtype=complex)
    dp = np.zeros((N, P, M), dtype=complex)
    b1 = 1j*dws + D                                # (1, M), n=1
    # Row 1:  b1*c1 + K*c2 = K   (c_0 = 1 moved to rhs: rhs_1 = +K; super = +K)
    cp[0] = Ks/b1                                  # super diag / b1
    dp[0] = Ks/b1                                  # rhs_1 = +K
    # Rows n>=2:  -K*c_{n-1} + b_n*c_n + K*c_{n+1} = 0  (a = -K, super = +K, rhs = 0)
    for i in range(1, N):
        bi = b_vec[i][None, :]                     # (1, M)
        denom = bi + Ks*cp[i-1]                    # b - a*cp with a = -K
        cp[i] = Ks/denom                           # super = +K
        dp[i] = (Ks*dp[i-1])/denom                 # (d - a*dp)/b, d=0, a=-K
    cn = dp[N-1].copy()                            # c_N
    cout = np.zeros((P, M), dtype=complex)
    for i in range(N-1, 0, -1):
        cn = dp[i-1] - cp[i-1]*cn
        if i == 1:
            cout = cn.copy()                       # c_1
    return np.abs(cout)

def R_cf(dw, K, sigma, N=400):
    return float(R_cf_grid([dw], [K], sigma, N)[0, 0])

def R_bessel_dw0(K, sigma):
    D = 0.5*sigma*sigma
    x = 2*K/D
    # Exponentially scaled Bessel functions avoid overflow at large x.
    r = special.i0e(x)
    return float(special.i1e(x)/r)

# ============================================================
# 3. Stationary ergodic Euler-Maruyama MC (time average, batched)
# ============================================================
def R_mc_stationary(dw, K, sigma, burn=5000, run=100000, dt=0.02, nwalk=64, seed=1):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2*np.pi, nwalk)
    sq = sigma*np.sqrt(2*dt)
    def step(th):
        return (th + dt*(dw - 2*K*np.sin(th)) + sq*rng.standard_normal(nwalk)) % (2*np.pi)
    for _ in range(burn):
        th = step(th)
    ar = 0.0; ai = 0.0
    for _ in range(run):
        th = step(th)
        ar += np.cos(th).sum(); ai += np.sin(th).sum()
    return float(np.hypot(ar, ai)/(run*nwalk))

# ============================================================
# 4. Deepseek-style FIXED-TIME ENSEMBLE MC (suspected protocol)
# ============================================================
def R_mc_fixedtime(dw, K, sigma, nwalk=2000, steps=20000, dt=0.01, theta0=0.0, seed=2):
    rng = np.random.default_rng(seed)
    th = np.full(nwalk, theta0)
    sq = sigma*np.sqrt(2*dt)
    for _ in range(steps):
        th = (th + dt*(dw - 2*K*np.sin(th)) + sq*rng.standard_normal(nwalk)) % (2*np.pi)
    return float(np.abs(np.exp(1j*th).mean()))

# ============================================================
# MAIN
# ============================================================
out = {}

print("=== (A) Bessel anchor at dw=0, K=1.65: CF recurrence correctness ===")
for sig in [0.05, 0.2, 0.5]:
    cf = R_cf(0.0, K0, sig); be = R_bessel_dw0(K0, sig)
    print(f"sigma={sig:.2f}: CF={cf:.6f}  Bessel={be:.6f}  diff={abs(cf-be):.2e}")
    out[f"bessel_s{sig}"] = (cf, be)

print("\n=== (B) Deterministic quadrature vs CF at sigma=0.001 ===")
for dw in [3.5, 4.0, 5.0, 6.0, 7.0]:
    rd = R_det_quad(dw, K0); rc = R_cf(dw, K0, 0.001)
    print(f"dw={dw:.1f}: quad={rd:.6f}  CF(s=0.001)={rc:.6f}  diff={abs(rd-rc):.2e}")

print("\n=== (C) Core dispute: sigma=0.05, K=1.65, dw=4,5,6 ===")
print("  deepseek EMP-094 MC claimed: 0.2287, 0.5704, 0.3884  (NON-monotone)")
for dw in [4.0, 5.0, 6.0]:
    rd = R_det_quad(dw, K0)
    rc = R_cf(dw, K0, 0.05)
    rm = R_mc_stationary(dw, K0, 0.05)
    print(f"dw={dw:.1f}: R_det={rd:.4f}  R_CF={rc:.4f}  R_MCstat={rm:.4f}")
    out[f"core_s05_dw{int(dw)}"] = (rd, rc, rm)

print("\n=== (D) Monotonicity scan, K=1.65 ===")
dws = np.linspace(3.4, 8.0, 24)
for sig in [0.05, 0.5]:
    Rv = R_cf_grid(dws, [K0], sig)[0]
    diffs = np.diff(Rv)
    print(f"sigma={sig}: strictly decreasing? {bool(np.all(diffs < 1e-12))}  max_increase={float(diffs.max()):.2e}")

print("\n=== (E) Reproduce deepseek protocol: fixed-time ensemble, dt=0.01, 20000 steps ===")
for dw in [4.0, 5.0, 6.0]:
    for t0 in [0.0, np.pi/2]:
        rf = R_mc_fixedtime(dw, K0, 0.05, theta0=t0)
        print(f"dw={dw:.1f} theta0={t0:.3f}: R_fixedtime={rf:.4f}")
        out[f"fixedtime_dw{int(dw)}_t0{int(round(t0*100))}"] = rf

print("\n=== (F) band_frac_max(sigma): fine vs coarse dw grid ===")
Ks = np.linspace(0.3, 4.0, 241)
dws_fine = np.linspace(0.0, 6.0, 601)
dws_coarse = np.linspace(0.0, 6.0, 61)
def band_frac(sigma, dwgrid):
    Rm = R_cf_grid(dwgrid, Ks, sigma)
    bf = ((Rm > 0.3) & (Rm < 0.7)).mean(axis=1)
    k = int(np.argmax(bf))
    return float(bf[k]), float(Ks[k])
for sig in [0.001, 0.05, 0.1, 0.2, 0.3, 0.5]:
    bf, kstar = band_frac(sig, dws_fine)
    bf_c, kstar_c = band_frac(sig, dws_coarse)
    print(f"sigma={sig:5.3f}: fine={bf:.4f}@K={kstar:.3f}   coarse={bf_c:.4f}@K={kstar_c:.3f}")
    out[f"bandfrac_s{sig}"] = (bf, kstar, bf_c, kstar_c)

print("\nC = 316/763 =", 316/763)

with open("adler_adjudication_out.json", "w") as f:
    json.dump({k: (list(map(float, v)) if isinstance(v, (tuple, list)) else v)
               for k, v in out.items()}, f, indent=1, default=str)
print("saved adler_adjudication_out.json")
