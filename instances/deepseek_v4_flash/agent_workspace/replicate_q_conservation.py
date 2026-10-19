"""
INDEPENDENT REPLICATION of EMP-149 (Gemini): Is morphospace charge Q = -lambda_max - D2 - K
conserved across Hénon parameter a, or is it a critical edge-of-chaos classifier?

Gemini's claim: Q varies continuously from +0.01 to -2.43 across a in [0.2,1.4], is non-conserved,
and Q≈-2.08 is an artifact of measuring at the period-doubling accumulation onset (a≈1.05-1.20).
We replicate and stress-test.

Setup: Hénon map (x,y) -> (1 - a*x^2 + y, b*x), b=0.3.
Compute per-parameter: lambda_max (Lyapunov via QR / tangent), D2 (correlation dimension via Grassberger-Procaccia), K (some complexity measure).
"""
import numpy as np
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def henon_iter(x, y, a, b=0.3):
    return 1 - a*x*x + y, b*x

def lyapunov_max(a, b=0.3, n=20000, ntrans=2000):
    """Estimate max Lyapunov exponent via tangent-space QR method."""
    x, y = 0.1, 0.1
    # tangent vectors
    J = np.array([[ -2*a*x, 1.0], [b, 0.0]])  # Jacobian
    Q = np.eye(2)
    s = 0.0
    for i in range(ntrans):
        x, y = henon_iter(x, y, a, b)
    # Now accumulate
    for i in range(n):
        x, y = henon_iter(x, y, a, b)
        J = np.array([[-2*a*x, 1.0], [b, 0.0]])
        # multiply J with Q
        A = J @ Q
        Q, R = np.linalg.qr(A)
        s += np.log(np.abs(R[0, 0]) + 1e-12)
    return s / n

def correlation_dimension(a, b=0.3, n=8000, ntrans=1000, max_r_frac=0.1, n_r=30):
    """Grassberger-Procaccia correlation dimension via fixed-reference box counting."""
    x, y = 0.1, 0.1
    for i in range(ntrans):
        x, y = henon_iter(x, y, a, b)
    pts = []
    for i in range(n):
        x, y = henon_iter(x, y, a, b)
        pts.append((x, y))
    pts = np.array(pts)
    # Compute distances from a subsample of reference points
    n_ref = 200
    idx = np.random.default_rng(0).choice(n, n_ref, replace=False)
    ref = pts[idx]
    # Distances
    d = np.sqrt(((pts[:,None,:] - ref[None,:,:])**2).sum(-1))  # n x n_ref
    dmin = d.min()
    dmax = d.max()
    r_vals = np.logspace(np.log10(dmax*1e-3), np.log10(dmax*max_r_frac), n_r)
    C = np.zeros(n_r)
    for k, r in enumerate(r_vals):
        C[k] = np.mean(d < r)
    # slope of log C vs log r in linear regime
    mask = (C > 1e-6) & (C < 0.5)
    if mask.sum() < 3:
        return 0.0
    p = np.polyfit(np.log(r_vals[mask]), np.log(C[mask]), 1)
    return p[0]

def complexity_K(a, b=0.3, n=20000, ntrans=1000):
    """Permutation entropy / approximate complexity proxy for K."""
    x, y = 0.1, 0.1
    for i in range(ntrans):
        x, y = henon_iter(x, y, a, b)
    xser = []
    for i in range(n):
        x, y = henon_iter(x, y, a, b)
        xser.append(x)
    xser = np.array(xser)
    # permutation entropy with embedding 3
    m = 3
    perms = {}
    for i in range(len(xser)-m):
        seg = xser[i:i+m]
        order = tuple(np.argsort(seg))
        perms[order] = perms.get(order, 0) + 1
    total = sum(perms.values())
    probs = np.array(list(perms.values()))/total
    pe = -np.sum(probs*np.log(probs))/np.log(math.factorial(m)) if len(probs)>0 else 0
    # approximate K as normalized permutation entropy scaled
    return pe

a_vals = np.arange(0.2, 1.45, 0.05)
lam = []; D2 = []; K = []
for a in a_vals:
    l = lyapunov_max(a)
    d = correlation_dimension(a)
    k = complexity_K(a)
    lam.append(l); D2.append(d); K.append(k)
lam = np.array(lam); D2 = np.array(D2); K = np.array(K)
Q = -lam - D2 - K

print("="*70)
print("Hénon Q = -lambda_max - D2 - K across a (b=0.3)")
print("="*70)
print(f"{'a':<6}{'lambda_max':<12}{'D2':<10}{'K':<10}{'Q':<10}")
for i,a in enumerate(a_vals):
    print(f"{a:<6.2f}{lam[i]:<12.4f}{D2[i]:<10.4f}{K[i]:<10.4f}{Q[i]:<10.4f}")

print(f"\nQ range: [{Q.min():.3f}, {Q.max():.3f}], std={Q.std():.3f}")
print(f"Correlation of Q with a: {np.corrcoef(a_vals, Q)[0,1]:.3f}")

plt.figure(figsize=(10,4))
plt.subplot(1,2,1)
plt.plot(a_vals, Q, 'o-', label='Q')
plt.axhline(-2.08, color='red', ls='--', label='Q≈-2.08 (legacy)')
plt.xlabel('a'); plt.ylabel('Q'); plt.title('Q vs a: conserved?')
plt.legend(); plt.grid(alpha=0.3)
plt.subplot(1,2,2)
plt.plot(a_vals, lam, 'o-', label='λ_max')
plt.plot(a_vals, D2, 's-', label='D2')
plt.plot(a_vals, K, '^-', label='K')
plt.axhline(0, color='gray', ls=':')
plt.xlabel('a'); plt.ylabel('value'); plt.title('Components')
plt.legend(); plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("replicate_q_conservation.png", dpi=120, bbox_inches='tight')
print("\nSaved replicate_q_conservation.png")
