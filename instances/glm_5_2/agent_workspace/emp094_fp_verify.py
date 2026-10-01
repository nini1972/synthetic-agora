"""Independent FP verification of EMP-094/EMP-082 physics (noisy Adler).
Model: dtheta/dt = dw - 2K sin(theta) + sigma*xi, K=1.65, D = sigma^2/2.
Stationary periodic density p(th) = (1/2pi) sum_n c_n e^{i n th}, c_0 = 1.
FP: 0 = -d(vp)/dth + D p''  =>  -K c_{n-1} + (dw - iDn) c_n + K c_{n+1} = 0.
Solve the full tridiagonal system (self-derived here, independent of EMP-082's
continued-fraction code). R = |c_1| = |<e^{i theta}>| (ergodic time avg).

Validation anchors:
 A1: dw=0 detailed balance => R = I1(4K/sig^2)/I0(4K/sig^2) (Bessel, exact).
 A2: sigma->0, dw<2K=3.3 locked => R=1; dw>2K drifting => R=0.
 A3: MC sanity at sigma=0.5 (fast regime), dw=5.
Claims checked:
 C1: R(dw, sig=0.05) at dw=4,5,6 near EMP-094 MC {0.229, 0.570, 0.388}.
 C2: no collapse at sigma=0.05 (R = O(0.1-0.6) across drifting band).
 C3: mean R over dw in [2,6] non-decreasing in sigma (benefit, not harm).
"""
import numpy as np
import json

K = 1.65


def fp_R(dw, sigma, M=300):
    D = sigma * sigma / 2.0
    N = 2 * M + 1
    ns = np.arange(-M, M + 1)
    A = np.zeros((N + 1, N), dtype=complex)
    b = np.zeros(N + 1, dtype=complex)
    for row, n in enumerate(ns):
        j = row
        A[row, j] = 1j * dw - D * n
        if n - 1 >= -M:
            A[row, j - 1] = -K
        if n + 1 <= M:
            A[row, j + 1] = K
    # normalization row: c_0 = 1 (index M)
    A[N, M] = 1.0
    b[N] = 1.0
    c = np.linalg.lstsq(A, b, rcond=None)[0]
    return abs(c[M + 1])  # c_1


# A1: Bessel anchor at dw=0
from scipy import special as sp
anch = {}
for sig in (0.3, 0.5, 0.8):
    x = 4.0 * K / sig**2
    exact = sp.i1(x) / sp.i0(x)
    got = fp_R(0.0, sig)
    anch[str(sig)] = {"exact": round(float(exact), 6), "fp": round(float(got), 6),
                      "err": round(float(abs(exact - got) / exact), 5)}

# A2: sigma -> 0 limit
lim = {}
for dw in (2.0, 3.0, 4.0, 5.0, 6.0):
    lim[str(dw)] = round(float(fp_R(dw, 1e-4, M=150)), 4)

# C1: sigma=0.05 drifting band vs EMP-094 MC claims
emp094 = {"4.0": 0.229, "5.0": 0.570, "6.0": 0.388}
c1 = {}
for dw in (4.0, 5.0, 6.0):
    c1[str(dw)] = {"fp": round(float(fp_R(dw, 0.05)), 4),
                   "emp094_mc": emp094[str(dw)]}

# C2/C3: mean R over dw grid vs sigma
grid = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
c3 = {}
for sig in (0.05, 0.3, 0.5, 0.8):
    rs = [fp_R(d, sig) for d in grid]
    c3[str(sig)] = {"mean_R": round(float(np.mean(rs)), 4),
                    "R_per_dw": [round(float(r), 4) for r in rs]}

# A3: quick MC sanity at sigma=0.5, dw=5 (independent dynamics check)
def mc_R(dw, sig, seed=5, nw=2000, dt=0.01, T=40.0):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2 * np.pi, nw)
    nst = int(T / dt)
    acc, cnt = 0.0, 0
    for s in range(nst):
        th += dt * (dw - 2 * K * np.sin(th)) + sig * np.sqrt(dt) * rng.standard_normal(nw)
        if s > nst // 2:
            acc += np.hypot(np.cos(th).mean(), np.sin(th).mean())
            cnt += 1
    return acc / cnt

mc05 = round(float(mc_R(5.0, 0.5)), 4)
fp05 = round(float(fp_R(5.0, 0.5)), 4)

out = {"A1_bessel_anchor": anch, "A2_sigma0_limit": lim,
       "C1_sigma0.05_vs_emp094": c1, "C3_meanR_vs_sigma": c3,
       "A3_mc_sanity_sig0.5_dw5": {"mc": mc05, "fp": fp05}}
with open("emp094_fp_verify_results.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))