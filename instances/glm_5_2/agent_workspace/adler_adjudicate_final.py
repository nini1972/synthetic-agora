import numpy as np

K = 1.65

# ---------- 1. Deterministic dwell-bias rho_det (sigma -> 0 limit) ----------
def rho_det(dw, K):
    if dw <= 2*K:
        return 1.0
    # locked fraction of period: time where |dw - 2K sin| drives forward-slip only
    # slip occurs where dw - 2K sin(theta) > 0, i.e. theta in (a, pi-a) etc.
    s = 2*K/dw
    a = np.arcsin(s)
    # fraction of cycle spent slipping forward through the fast region
    f = (np.pi - 2*a)/np.pi
    return f

# ---------- 2. Exact periodic constant-flux FP: tridiagonal (Thomas) solve ----------
# Recurrence (n>=1):  K c_{n+1} + (i*dw + D_tilde*n) c_n - K c_{n-1} = 0
# (equivalent to deepseek's c_{n+1} = a_n c_n + c_{n-1}, a_n = (dw - i Dn)/(iK)
#  after conjugation; both give identical |c_1|). Boundary: c_0 = 1, c_{N+1} = 0.
def R_cf(dw, K, sigma, N=400):
    D = 0.5*sigma*sigma
    n = np.arange(1, N+1)
    # Thomas algorithm, vectorizable but scalar-loop is fine at N=400
    # a_i (sub) = -K, b_i (diag) = i*dw + D*n_i, c_i (super) = -K, d_i = 0 except d_1 = -K*c_0 = -K
    # forward sweep
    cp = np.zeros(N, dtype=complex); dp = np.zeros(N, dtype=complex)
    b0 = 1j*dw + D*1.0
    cp[0] = -K/b0
    dp[0] = (-K)/b0          # d_1 = -K (from c_0=1 term)
    for i in range(1, N):
        b = 1j*dw + D*(i+1)
        denom = b - (-K)*cp[i-1]
        cp[i] = -K/denom
        dp[i] = (0 - (-K)*dp[i-1])/denom
    # back substitution: c_N = dp[N-1]; c_n = dp[n-1] - cp[n-1]*c_{n+1}
    c = np.zeros(N+1, dtype=complex)
    c[N] = dp[N-1]
    for i in range(N-1, 0, -1):
        c[i] = dp[i-1] - cp[i-1]*c[i+1]
    # c[0] should be 1 by construction; R = |c_1|
    return abs(c[1])

# ---------- 3. Bessel anchor at dw=0: R = I_1(2K/D)/I_0(2K/D) ----------
from scipy import special
def R_bessel_dw0(K, sigma):
    D = 0.5*sigma*sigma
    x = 2*K/D
    return special.i1(x)/special.i0(x)

# ---------- 4. Euler-Maruyama stationary MC (ergodic time average) ----------
def R_mc(dw, K, sigma, burn=20000, run=200000, dt=0.02, seed=1):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi)
    sq = sigma*np.sqrt(2*dt)
    for _ in range(burn):
        theta = (theta + dt*(dw - 2*K*np.sin(theta)) + sq*rng.standard_normal()) % (2*np.pi)
    acc = 0.0 + 0.0j
    for _ in range(run):
        theta = (theta + dt*(dw - 2*K*np.sin(theta)) + sq*rng.standard_normal()) % (2*np.pi)
        acc += np.exp(1j*theta)
    return abs(acc/run)

# ---------- Run adjudication ----------
print("=== dw=0 Bessel anchor vs CF ===")
for sig in [0.05, 0.5]:
    print(f"sigma={sig}: CF={R_cf(0.0,K,sig):.6f}  Bessel={R_bessel_dw0(K,sig):.6f}")

print("\n=== R(dw) at K=1.65, sigma=0.05 (deepseek claimed 0.2287, 0.5704, 0.3884 at dw=4,5,6) ===")
for dw in [4.0, 5.0, 6.0]:
    print(f"dw={dw}: rho_det={rho_det(dw,K):.4f}  CF={R_cf(dw,K,0.05):.4f}  MC={R_mc(dw,K,0.05,run=60000):.4f}")

print("\n=== R(dw) at K=1.65, sigma=0.5 ===")
for dw in [4.0, 5.0, 6.0]:
    print(f"dw={dw}: rho_det={rho_det(dw,K):.4f}  CF={R_cf(dw,K,0.5):.4f}  MC={R_mc(dw,K,0.5,run=60000):.4f}")
