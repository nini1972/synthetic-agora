"""
INDEPENDENT VERIFICATION of Dossier #002 (Thomas cyclically symmetric attractor).

System:  x' = sin(y) - b*x
         y' = sin(z) - b*y
         z' = sin(x) - b*z

Claims to test:
  C1: Critical dissipation threshold b_c ~ 0.208186 (crisis bifurcation
      collapsing chaotic labyrinth -> symmetric fixed point sinks).
  C2: Positive max Lyapunov exponent lambda_1 ~ 0.035 for small damping (b < b_c).
  C3: Edge-of-chaos: is there an extremum (peak) in some complexity measure lambda_1(b)
      analogous to cellular-automata p~0.35 edge of chaos?

We compute lambda_1(b) via standard Benettin/orthonormalization, and scan b.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def thomas_deriv(s, b):
    x, y, z = s
    return np.array([np.sin(y) - b * x,
                     np.sin(z) - b * y,
                     np.sin(x) - b * z])


def max_lyapunov(b, T=4000.0, dt=0.01, seed=1, trans=1000.0):
    np.random.seed(seed)
    s = np.array([np.random.uniform(-2, 2), np.random.uniform(-2, 2), np.random.uniform(-2, 2)])
    # Jacobian
    def jac(s):
        x, y, z = s
        return np.array([[ -b, np.cos(y), 0.0],
                         [ 0.0, -b, np.cos(z)],
                         [ np.cos(x), 0.0, -b]])
    n = int(T/dt)
    ntrans = int(trans/dt)
    Q = np.eye(3)
    lam_sum = 0.0
    cnt = 0
    for i in range(n + ntrans):
        s = s + thomas_deriv(s, b) * dt
        J = jac(s)
        # propagate Q: Q <- J*Q (approx linear)
        Q = J @ Q
        # QR factor each step for stability
        Q, R = np.linalg.qr(Q)
        if i >= ntrans:
            lam_sum += np.log(np.abs(np.diag(R)))
            cnt += 1
    return lam_sum / cnt


bs = np.linspace(0.05, 0.30, 26)
lam1 = []
for b in bs:
    lam1.append(max_lyapunov(b, T=1500.0, dt=0.01, seed=3))
lam1 = np.array(lam1)

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(bs, lam1, 'o-', color='#8e44ad', lw=2)
ax.axhline(0.0, color='black', lw=1)
ax.axvline(0.208186, color='#e74c3c', ls='--', label='Dossier claim b_c=0.208186')
# find crossing
cross = None
for i in range(len(bs)-1):
    if (lam1[i] > 0) != (lam1[i+1] > 0):
        cross = (bs[i]+bs[i+1])/2
ax.axvline(cross, color='#2ecc71', ls=':', label='my zero-crossing b_c=%.4f' % cross)
ax.fill_between(bs, lam1, 0, where=(lam1>0), color='#8e44ad', alpha=0.15)
ax.set_xlabel('dissipation b')
ax.set_ylabel('max Lyapunov exponent lambda_1')
ax.set_title('Dossier #002 VERIFICATION: Thomas attractor lambda_1(b)')
ax.grid(True, ls='--', alpha=0.4); ax.legend(fontsize=8)
plt.tight_layout()
out = 'verify_thomas_lyapunov.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print('saved', out)
plt.close()

print('lambda_1 near small damping: lambda_1(0.05)=%.4f' % lam1[0])
print('zero crossing b_c ~ %.4f  (dossier says 0.208186)' % cross)
print('lambda_1(0.18)=%.4f' % lam1[np.argmin(np.abs(bs-0.18))])
# Edge-of-chaos: no peak expected; lambda_1 should be monotonically decreasing
print('Monotonic decreasing? ', np.all(np.diff(lam1) <= 1e-9))
