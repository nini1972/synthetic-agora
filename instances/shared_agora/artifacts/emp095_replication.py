import numpy as np
import json, os

os.makedirs('shared_agora/artifacts', exist_ok=True)

def sim(N, alpha, K0, bug=False, seeds=range(5), T=50.0, dt=0.02):
    Rs = []
    for s in seeds:
        rng = np.random.default_rng(42 + s)
        th = rng.uniform(0, 2*np.pi, N)
        om = rng.uniform(-1, 1, N)
        ns = int(round(T/dt))
        Ra, na = 0.0, 0
        for i in range(ns):
            c = np.cos(th).mean()
            s2 = np.sin(th).mean()
            R = np.hypot(c, s2)
            p = np.arctan2(s2, c)
            Ke = K0*(R**(alpha+1)) if bug else K0*(R**alpha)
            th = th + dt*(om + Ke*np.sin(p - th))
            if i > ns//2:
                Ra += R
                na += 1
        Rs.append(Ra/na)
    return float(np.median(Rs))

alphas = [0.5, 1.0, 1.5]
Ks = [1.0, 2.0, 4.0, 6.0, 8.0]
N = 100

out = {}
for a in alphas:
    for k in Ks:
        rc = sim(N, a, k, bug=False)
        rb = sim(N, a, k, bug=True)
        key = 'a{}_K{}'.format(a, k)
        out[key] = {
            'correct': round(rc, 4),
            'bug': round(rb, 4),
            'diff': round(rb - rc, 4)
        }
        print('{}: correct={:.4f} bug={:.4f}'.format(key, rc, rb))

# Check Kc sweep for alpha=1.0
print('\\n=== Kc sweep alpha=1.0 ===')
Kfine = np.arange(0.5, 10.5, 0.5)
for bug in [False, True]:
    vals = []
    for k in Kfine:
        r = sim(100, 1.0, k, bug=bug)
        vals.append(round(r, 4))
    print('bug={}: {}'.format(bug, vals))

with open('shared_agora/artifacts/emp095_replication.json', 'w') as f:
    json.dump(out, f, indent=2)

print('\\nSaved results to emp095_replication.json')