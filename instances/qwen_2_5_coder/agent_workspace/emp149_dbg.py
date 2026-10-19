import numpy as np
B = 0.3
a = 1.4
def step(x, y):
    return 1.0 - a * x * x + y, B * y

x, y = 0.37, 0.21
xs = []
for _ in range(30000):
    x, y = step(x, y)
    if len(xs) < 6 or len(xs) % 5000 == 0:
        xs.append(x)
print("x samples:", [f"{v:.4f}" for v in xs])
print("x range:", min(x for x in [xs[0]]), "current:", x, y)

# full orbit stats
x, y = 0.37, 0.21
buf = []
for _ in range(30000):
    x, y = step(x, y)
    buf.append((x, y))
buf = np.array(buf)
print("x range over orbit:", buf[:, 0].min(), buf[:, 0].max())
print("y range over orbit:", buf[:, 1].min(), buf[:, 1].max())
P = buf[::2]
# min and mean pairwise distance on 5000 pts
d = np.sqrt(((P[None, :, :] - P[:, None, :]) ** 2).sum(-1))
dmin = d.min()
print("min pairwise dist:", dmin)
print("C(0.004) exact:", (d < 0.004).mean())
print("C(0.05):", (d < 0.05).mean())
print("C(0.1):", (d < 0.1).mean())
# test one QR step manually
x0, y0 = buf[-1]
J = np.array([[-2.0 * a * x0, 1.0], [0.0, B]])
print("J at last point:", J.tolist(), "eig:", np.linalg.eigvals(J))
v1 = np.array([1.0, 0.0]); v2 = np.array([0.0, 1.0])
M = J @ np.column_stack([v1, v2])
Q, R = np.linalg.qr(M)
print("R diag:", np.abs(np.diag(R)), " svd:", np.linalg.svd(M, compute_uv=False))
