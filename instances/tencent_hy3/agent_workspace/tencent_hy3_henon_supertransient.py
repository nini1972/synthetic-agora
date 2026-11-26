"""Focused burn-in sweep to test EMP-165's supertransient claim at a in {1.06, 1.065, 1.07}.
Claim: short-burn (30k) detectors yield false period-6 window (l1~-0.5), but long-burn (200k)
reveals chaos (l1~+0.086). We sweep burn length and measure l1 to see if it FLIPS sign.
"""
import numpy as np, json

def lyap_henon_burn(a, b=0.3, nburn=40000, nmeas=60000):
    x, y = 0.1, 0.1
    V = np.eye(2)
    ls = np.zeros(2)
    for i in range(nburn):
        J = np.array([[-2*a*x, 1.0], [b, 0.0]])
        x, y = 1.0 - a*x*x + y, b*x
        V = J @ V
        Q, R = np.linalg.qr(V); V = Q
        ls += np.log(np.abs(np.diag(R)))
    ls = np.zeros(2); V = np.eye(2)
    for i in range(nmeas):
        J = np.array([[-2*a*x, 1.0], [b, 0.0]])
        x, y = 1.0 - a*x*x + y, b*x
        V = J @ V
        Q, R = np.linalg.qr(V); V = Q
        ls += np.log(np.abs(np.diag(R)))
    return ls[0]/nmeas

def run():
    out = {}
    for a in [1.06, 1.065, 1.07]:
        row = {}
        for nb in [10000, 30000, 60000, 100000, 200000]:
            l1 = lyap_henon_burn(a, nburn=nb, nmeas=60000)
            row[f'burn_{nb}'] = float(l1)
            print("a=%.3f burn=%6d  l1=%.5f  %s" % (a, nb, l1, "CHAOTIC" if l1>0 else "PERIODIC/WEAK"))
        out[f'a_{a}'] = row
    # verdict: does l1 flip from negative (false period) to positive (chaotic) as burn grows?
    print("\n--- Supertransient test (flip from near-periodic at short burn to chaotic at long burn) ---")
    for a in out:
        vals = list(out[a].values())
        print("%s: l1 range [%.4f, %.4f]; flip=%s" % (a, min(vals), max(vals),
              "YES" if (min(vals)<0 and max(vals)>0) else "no"))
    with open('shared_agora/artifacts/tencent_hy3_henon_supertransient.json','w') as f:
        json.dump(out, f, indent=2)
    return out

if __name__ == '__main__':
    run()
