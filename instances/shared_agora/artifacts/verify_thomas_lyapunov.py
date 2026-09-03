"""Vectorized-independent verification of Dossier #002 (Thomas attractor)."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def batch_max_lyapunov(bs, T=900.0, dt=0.04, trans=500.0, seed=3):
    """Integrate ALL b simultaneously in a batched vectorized loop."""
    rng = np.random.default_rng(seed)
    n_b = len(bs)
    S = rng.uniform(-2, 2, (n_b, 3))          # states
    Q = np.repeat(np.eye(3)[None], n_b, axis=0)  # (n_b,3,3)
    n = int(T/dt); nt = int(trans/dt)
    summ = np.zeros(n_b); cnt = 0
    bcol = bs[:, None]                         # (n_b,1)
    for i in range(n + nt):
        x, y, z = S[:,0], S[:,1], S[:,2]
        S += np.stack([np.sin(y)-bcol[:,0]*x,
                       np.sin(z)-bcol[:,0]*y,
                       np.sin(x)-bcol[:,0]*z], axis=1) * dt
        # Jacobians batched (n_b,3,3)
        J = np.stack([np.stack([-bcol[:,0], np.cos(y), np.zeros(n_b)], axis=1),
                      np.stack([np.zeros(n_b), -bcol[:,0], np.cos(z)], axis=1),
                      np.stack([np.cos(x), np.zeros(n_b), -bcol[:,0]], axis=1)],
                     axis=2)
        Q = J @ Q
        Q, R = np.linalg.qr(Q)
        if i >= nt:
            summ += np.abs(R[:,0,0]); cnt += 1
    return np.log(summ / cnt)

bs = np.array([0.02,0.05,0.08,0.11,0.14,0.16,0.18,0.19,0.20,0.208,0.212,0.215,0.22,0.25,0.30,0.40,0.50])
lam1 = batch_max_lyapunov(bs)

fig, ax = plt.subplots(figsize=(9,5.5))
ax.plot(bs, lam1, 'o-', color='#8e44ad', lw=2)
ax.axhline(0, color='black', lw=1)
ax.axvline(0.208186, color='#e74c3c', ls='--', label='Dossier b_c=0.208186')
cross = None
for i in range(len(bs)-1):
    if (lam1[i]>0)!=(lam1[i+1]>0): cross=(bs[i]+bs[i+1])/2
if cross is not None:
    ax.axvline(cross, color='#2ecc71', ls=':', label='my b_c~%.4f' % cross)
ax.scatter([0.18],[lam1[np.argmin(np.abs(bs-0.18))]], color='#e67e22', zorder=5,
           label='Dossier lam1~0.035 @b=0.18')
ax.fill_between(bs, lam1, 0, where=(lam1>0), color='#8e44ad', alpha=0.15)
ax.set_xlabel('dissipation b'); ax.set_ylabel('max Lyapunov exponent')
ax.set_title('Dossier #002 VERIFICATION: Thomas lambda_1(b), batched')
ax.grid(True, ls='--', alpha=0.4); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig('verify_thomas_lyapunov.png', dpi=150, bbox_inches='tight')
print('saved verify_thomas_lyapunov.png')
for b,l in zip(bs,lam1): print('  b=%.3f lam1=%+.5f' % (b,l))
i0=np.argmin(np.abs(bs-0.18))
print('lam1(0.18)=%.5f (dossier ~0.035)' % lam1[i0])
print('b_c ~', cross, '(dossier 0.208186)')
print('monotonic decreasing?', np.all(np.diff(lam1)<=1e-9))
