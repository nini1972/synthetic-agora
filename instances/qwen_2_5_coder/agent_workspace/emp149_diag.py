import numpy as np

B = 0.3
def henon_step(a, x, y):
    return 1.0 - a * x * x + y, B * y

def benettin(a, n_burn=20000, n_meas=20000, x0=0.37, y0=0.21):
    x, y = x0, y0
    for _ in range(n_burn):
        x, y = henon_step(a, x, y)
    v1 = np.array([1e-8, 0.0]); v2 = np.array([0.0, 1e-8])
    s1 = s2 = 0.0; acc = 0.0
    for _ in range(n_meas):
        x, y = henon_step(a, x, y)
        acc += x * x
        J = np.array([[-2.0 * a * x, 1.0], [0.0, B]])   # FIXED
        M = J @ np.column_stack([v1, v2])
        Q, R = np.linalg.qr(M)
        s1 += np.log(abs(R[0, 0])); s2 += np.log(abs(R[1, 1]))
        v1, v2 = Q[:, 0], Q[:, 1]
    return s1 / n_meas, s2 / n_meas, acc / n_meas

def gp_table(P, qs, chunk=500):
    N = P.shape[0]
    out = []
    for q in qs:
        cnt = 0.0
        for i0 in range(0, N, chunk):
            d = np.sqrt(((P[i0:i0 + chunk, None, :] - P[None, :, :]) ** 2).sum(-1))
            cnt += (d < q).sum()
        out.append(cnt / (N * N))
    return np.array(out)

a = 1.4
lam1, lam2, mx2 = benettin(a)
print(f"FIXED: a=1.4  lam1={lam1:+.5f} (expect ~0.419)  lam2={lam2:+.5f} (expect ~-1.62)")

x, y = 0.37, 0.21
for _ in range(20000):
    x, y = henon_step(a, x, y)
pts = []
for _ in range(10000):
    x, y = henon_step(a, x, y)
    pts.append((x, y))
P = np.array(pts[::2])  # 5000
qs = np.geomspace(0.004, 1.2, 20)
C = gp_table(P, qs)
prev = None
for q, c in zip(qs, C):
    sl = (np.log(c) - np.log(prev)) / (np.log(q) - np.log(qs[list(qs).index(q)-1])) if prev else float('nan')
    print(f"q={q:8.5f}  C={c:.6f}  slope~{sl:6.3f}")
    prev = c
print("K =", a*mx2, " mean_x2=", mx2)
