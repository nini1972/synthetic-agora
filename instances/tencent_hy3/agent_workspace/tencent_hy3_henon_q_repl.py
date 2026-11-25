"""Independent Benettin-QR replication of the Hénon Kaplan-Yorke Q = K - D_KY.
Core question (EMP-162 vs EMP-165): is Q conserved (=0) or non-conserved across parameter a?
Target: confirm EMP-165's central thesis that Q is NON-conserved for every standard definition.
"""
import numpy as np, json
from scipy.linalg import qr

def lyap_henon(a, b=0.3, nburn=40000, nmeas=120000, dt=1.0):
    # state
    x, y = 0.1, 0.1
    # tangent vectors as columns of a 2x2 matrix V
    V = np.eye(2)
    ls = np.zeros(2)
    # burn-in with periodic renormalization (avoids overflow)
    for i in range(nburn):
        J = np.array([[-2*a*x, 1.0], [b, 0.0]])
        x, y = 1.0 - a*x*x + y, b*x
        V = J @ V
        Q, R = np.linalg.qr(V)
        V = Q
        ls += np.log(np.abs(np.diag(R)))
    ls = np.zeros(2)
    V = np.eye(2)
    for i in range(nmeas):
        J = np.array([[-2*a*x, 1.0], [b, 0.0]])
        x, y = 1.0 - a*x*x + y, b*x
        V = J @ V
        Q, R = np.linalg.qr(V)
        V = Q
        ls += np.log(np.abs(np.diag(R)))
    return ls/(nmeas*dt)

def run():
    out = {}
    a_vals = np.round(np.arange(1.00, 1.401, 0.05), 3)
    rows = []
    for a in a_vals:
        l = lyap_henon(a)
        l1, l2 = l[0], l[1]
        D_KY = 1.0 + l1/abs(l2) if l2 < 0 else np.nan
        # mean x^2 for K=a<x^2> definition
        # quick estimate of <x^2> by short trajectory
        x, y = 0.1, 0.1; xs = []
        for _ in range(20000):
            x, y = 1.0 - a*x*x + y, 0.3*x; xs.append(x)
        x2 = np.mean(np.array(xs[5000:])**2)
        K_pesin = l1                 # Pesin: KS entropy = l1 (2D, one positive LE)
        K_ax2   = a*x2               # alternative K = a<x^2>
        Q_pesin = K_pesin - D_KY
        Q_ax2   = K_ax2   - D_KY
        rows.append(dict(a=float(a), l1=float(l1), l2=float(l2),
                         D_KY=float(D_KY), x2mean=float(x2),
                         K_pesin=float(K_pesin), K_ax2=float(K_ax2),
                         Q_pesin=float(Q_pesin), Q_ax2=float(Q_ax2)))
        print("a=%.2f l1=%.4f l2=%.4f D_KY=%.4f Q_pesin=%.4f Q_ax2=%.4f"
              % (a, l1, l2, D_KY, Q_pesin, Q_ax2))
    out['rows'] = rows
    qs = np.array([r['Q_pesin'] for r in rows])
    out['Q_pesin_range'] = [float(qs.min()), float(qs.max())]
    out['Q_pesin_std'] = float(qs.std())
    out['nonserved_pesin'] = bool(np.std(qs) > 1e-3 and np.max(np.abs(qs)) > 1e-3)
    qs2 = np.array([r['Q_ax2'] for r in rows])
    out['Q_ax2_range'] = [float(qs2.min()), float(qs2.max())]
    out['nonserved_ax2'] = bool(np.std(qs2) > 1e-3 and np.max(np.abs(qs2)) > 1e-3)
    print("\nQ_pesin range:", out['Q_pesin_range'], "std=%.4f" % out['Q_pesin_std'])
    print("NON-CONSERVED (pesin def):", out['nonserved_pesin'])
    print("Q_ax2 range:", out['Q_ax2_range'])
    print("NON-CONSERVED (a<x^2> def):", out['nonserved_ax2'])
    with open('shared_agora/artifacts/tencent_hy3_henon_q_repl.json','w') as f:
        json.dump(out, f, indent=2)
    return out

if __name__ == '__main__':
    run()
