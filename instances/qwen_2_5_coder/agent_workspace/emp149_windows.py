import numpy as np
B = 0.3
def step(a, x, y):
    return 1.0 - a*x*x + y, B*x

def lam1_clean(a, n_burn=60000, n_meas=40000, x0=0.37, y0=0.21):
    x, y = x0, y0
    for _ in range(n_burn):
        x, y = step(a, x, y)
    v1 = np.array([1e-8, 0.0]); v2 = np.array([0.0, 1e-8])
    s1 = 0.0; hist = []
    for _ in range(n_meas):
        x, y = step(a, x, y)
        J = np.array([[-2.0*a*x, 1.0], [B, 0.0]])
        M = J @ np.column_stack([v1, v2])
        Q, R = np.linalg.qr(M)
        s1 += np.log(abs(R[0,0]))
        v1, v2 = Q[:,0], Q[:,1]
        if _ % 5000 == 0:
            hist.append(s1/(_+1))
    return s1/n_meas, hist, x, y

for a in [1.065, 1.10, 1.30, 1.40]:
    L, hist, x, y = lam1_clean(a)
    print(f"a={a}: lam1={L:+.5f}  running={ [f'{h:+.3f}' for h in hist] }  final_pt=({x:.4f},{y:.4f})")

# Check if a=1.30 orbit is periodic: iterate and look for a short return
for a in [1.065, 1.30]:
    x, y = 0.37, 0.21
    seen = {}
    for n in range(200000):
        x, y = step(a, x, y)
        key = (round(x,5), round(y,5))
        if key in seen:
            print(f"a={a}: possible period {n-seen[key]} detected (return after {n} steps)")
            break
        seen[key] = n
    else:
        print(f"a={a}: no exact 5-dp return in 200k steps (chaotic / long period)")
