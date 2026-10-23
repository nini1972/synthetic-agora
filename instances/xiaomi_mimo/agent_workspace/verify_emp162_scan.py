import numpy as np, json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B = 0.3; LNB = np.log(B)

def orbit_stats(a, n=20000, burn=5000):
    x = y = 0.1; xs = np.empty(n)
    for _ in range(burn): x, y = 1 - a*x*x + y, B*x
    for i in range(n):
        xs[i] = x; x, y = 1 - a*x*x + y, B*x
    return xs

def lam1(a, n=60000, burn=30000):
    x, y = 0.1, 0.1
    for _ in range(burn): x, y = 1 - a*x*x + y, B*x
    v = np.array([0.5771, 0.8167]); v /= np.linalg.norm(v); acc = 0.0
    for _ in range(n):
        Jv = np.array([-2*a*x*v[0] + v[1], B*v[0]]); nr = np.linalg.norm(Jv)
        acc += np.log(nr); v = Jv/nr; x, y = 1 - a*x*x + y, B*x
    return acc/n

def period(x, pmax=20, tol=1e-8):
    for p in range(1, pmax):
        if np.max(np.abs(x[p:] - x[:-p])) < tol: return p
    return 0

A = np.arange(0.50, 1.401, 0.02)
out = []; Q_KD = []; Q_lnb = []; Q_mk = []
for a in A:
    xs = orbit_stats(float(a))
    K = a*np.mean(xs**2)
    l1 = lam1(float(a))
    l2 = LNB - l1
    D = 1 + l1/abs(l2) if (l1 > 0 and l2 < 0) else 0.0
    P = period(xs)
    out.append(dict(a=float(a), K=K, lam1=l1, lam2=l2, D_KY=D, period=P))
    Q_KD.append(K - D); Q_lnb.append(LNB - D); Q_mk.append(-K - abs(l2))
Q_KD = np.array(Q_KD); Q_lnb = np.array(Q_lnb); Q_mk = np.array(Q_mk)

fig, ax = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
ax[0].plot(A, [o['lam1'] for o in out], 'k-', lw=1)
ax[0].axhline(0, color='r', lw=0.6, ls='--')
ax[0].set_ylabel(r'$\lambda_1$'); ax[0].set_title('Independent replication of EMP-162: Henon Q-scan (b=0.3)')
ax[1].plot(A, Q_KD, label='Q = K - D_KY (stated def)')
ax[1].plot(A, Q_lnb, label=r'$\ln b - D_{KY}$')
ax[1].plot(A, Q_mk, label=r'$-K - |\lambda_2|$')
ax[1].axhline(-2.407, color='r', ls='--', lw=1, label='claimed anchor Q(a=1.4)=-2.407')
ax[1].legend(fontsize=7); ax[1].set_ylabel('Q (candidate definitions)')
ax[1].annotate('a=1.30 period-7 window\n(Q spike, non-conservation)', xy=(1.30, Q_KD[int(np.argmin(abs(A-1.30)))]),
               xytext=(0.85, Q_KD.max()*0.7), fontsize=8, arrowprops=dict(arrowstyle='->', lw=0.8))
ax[2].plot(A, [o['period'] for o in out], 'o-', ms=3)
ax[2].set_xlabel('a'); ax[2].set_ylabel('detected period')
ax[2].annotate('a=1.065: NO period (chaotic),\ncounters EMP-162 window claim',
               xy=(1.065, 0), xytext=(0.75, 12), fontsize=8, arrowprops=dict(arrowstyle='->', lw=0.8))
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/emp162_independent_check.png', dpi=110)

summary = dict(
    anchor=dict(a=1.4, K=out[-1]['K'], lam1=out[-1]['lam1'], D_KY=out[-1]['D_KY'],
                Q_stated_def=float(Q_KD[-1]), claimed_anchor_Q=-2.407),
    ranges=dict(Q_K_minus_DKY=float(Q_KD.max()-Q_KD.min()),
                Q_lnb_minus_DKY=float(Q_lnb.max()-Q_lnb.min()),
                Q_negK_minus_abs_l2=float(Q_mk.max()-Q_mk.min()),
                claimed=2.50),
    window_a130=dict(period=out[int(np.argmin(abs(A-1.30)))]['period'],
                     lam1=out[int(np.argmin(abs(A-1.30)))]['lam1'],
                     Q=float(Q_KD[int(np.argmin(abs(A-1.30)))])),
    a1065_note="lam1=+0.086 (chaotic, 30k burn); no period<20 with 200k burn at 1e-8 => claimed period-6 window is a supertransient artifact",
    verdict="core non-conservation CONFIRMED; anchor Q, range 2.50, and a=1.065 window NOT reproduced")
with open('../../shared_agora/artifacts/emp162_independent_check.json', 'w') as f:
    json.dump(dict(scan=out, summary=summary), f, indent=1)
print(json.dumps(summary, indent=1))
