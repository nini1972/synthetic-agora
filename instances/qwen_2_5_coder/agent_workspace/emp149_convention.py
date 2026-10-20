import numpy as np

B = 0.3
a = 1.4

def trace(fn, x0, y0, n=30000, tag=""):
    x, y = x0, y0
    xs = [x]; ys = [y]
    for _ in range(n):
        x, y = fn(x, y)
        if abs(x) > 1e6 or abs(y) > 1e6:
            print(f"{tag}: ESCAPED at step {len(xs)}")
            return
        xs.append(x); ys.append(y)
    xs = np.array(xs); ys = np.array(ys)
    print(f"{tag}: x∈[{xs.min():.3f},{xs.max():.3f}] y∈[{ys.min():.3f},{ys.max():.3f}] "
          f"first5x={[round(v,3) for v in xs[:5]]} last5x={[round(v,3) for v in xs[-5:]]}")

# Convention A (classic Henon): x' = 1 - a x^2 + y , y' = b x
A = lambda x, y: (1.0 - a*x*x + y, B*x)
# Convention B: x' = a(1 - x^2) + y , y' = b x
Bf = lambda x, y: (a*(1.0 - x*x) + y, B*x)
# Convention C: x' = a - x^2 + y , y' = b x
Cf = lambda x, y: (a - x*x + y, B*x)

for x0 in [0.37, 0.0, -1.0, 0.5]:
    trace(A, x0, 0.21, tag=f"A x0={x0}")
print("---")
for x0 in [0.37, 0.0]:
    trace(Bf, x0, 0.21, tag=f"B x0={x0}")
    trace(Cf, x0, 0.21, tag=f"C x0={x0}")
