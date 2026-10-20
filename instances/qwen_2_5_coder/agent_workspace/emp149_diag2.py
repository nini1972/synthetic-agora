import numpy as np
B = 0.3
a = 1.4
def step(x, y):
    return 1.0 - a*x*x + y, B*x

x, y = 0.37, 0.21
v1 = np.array([1e-8, 0.0]); v2 = np.array([0.0, 1e-8])
s1 = s2 = 0.0
for _ in range(20000):
    x, y = step(x, y)
for _ in range(20000):
    x, y = step(x, y)
    J = np.array([[-2.0*a*x, 1.0], [B, 0.0]])
    M = J @ np.column_stack([v1, v2])
    Q, R = np.linalg.qr(M)
    s1 += np.log(abs(R[0,0])); s2 += np.log(abs(R[1,0]) if False else abs(R[1,1]))
    v1, v2 = Q[:,0], Q[:,1]
print(f"TRUE Henon a=1.4:  lam1={s1/20000:+.5f} (expect ~0.419)   lam2={s2/20000:+.5f} (expect ~-1.62)")

# GP quick
x, y = 0.37, 0.21
for _ in range(20000):
    x, y = step(x, y)
pts = []
for _ in range(20000):
    x, y = step(x, y)
    pts.append((x, y))
P = np.array(pts[::4])  # 5000
qs = np.geomspace(0.004, 1.3, 18)
C = []
for q in qs:
    cnt = 0.0
    for i0 in range(0, P.shape[0], 500):
        d = np.sqrt(((P[i0:i0+500, None, :] - P[None, :, :])**2).sum(-1))
        cnt += (d < q).sum()
    C.append(cnt / (P.shape[0]**2))
C = np.array(C)
for q, c in zip(qs, C):
    print(f"q={q:8.5f} C={c:.6f}")
