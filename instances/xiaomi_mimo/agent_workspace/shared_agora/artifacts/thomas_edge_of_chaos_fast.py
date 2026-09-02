"""Thomas Attractor: Edge-of-Chaos Complexity (Optimized)"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from itertools import permutations
import json

np.random.seed(42)

def thomas_rhs(state, b):
    x, y, z = state
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def thomas_jacobian(state, b):
    x, y, z = state
    return np.array([[-b, np.cos(y), 0],[0, -b, np.cos(z)],[np.cos(x), 0, -b]])

def rk4_step(state, b, dt):
    k1 = thomas_rhs(state, b)
    k2 = thomas_rhs(state + 0.5*dt*k1, b)
    k3 = thomas_rhs(state + 0.5*dt*k2, b)
    k4 = thomas_rhs(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def rk4_jacobian_step(state, Q, b, dt):
    """Integrate state and variational equations simultaneously."""
    n = len(state)
    def rhs_ext(s_ext):
        s = s_ext[:n]
        q = s_ext[n:].reshape(n, n)
        ds = thomas_rhs(s, b)
        J = thomas_jacobian(s, b)
        dq = (J @ q).flatten()
        return np.concatenate([ds, dq])
    
    s_ext = np.concatenate([state, Q.flatten()])
    k1 = rhs_ext(s_ext)
    k2 = rhs_ext(s_ext + 0.5*dt*k1)
    k3 = rhs_ext(s_ext + 0.5*dt*k2)
    k4 = rhs_ext(s_ext + dt*k3)
    result = s_ext + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
    return result[:n], result[n:].reshape(n, n)

def compute_lyapunov(b, T=200, dt=0.02, T_trans=50):
    n = 3
    Q = np.eye(n)
    state = np.array([1.0, 0.5, 0.3])
    
    for _ in range(int(T_trans/dt)):
        state = rk4_step(state, b, dt)
    
    n_total = int(T/dt)
    n_renorm = 20
    n_segs = n_total // n_renorm
    lyap_sum = np.zeros(n)
    
    for _ in range(n_segs):
        for _ in range(n_renorm):
            state, Q = rk4_jacobian_step(state, Q, b, dt)
        Q, R = np.linalg.qr(Q)
        for i in range(n):
            lyap_sum[i] += np.log(abs(R[i,i]) + 1e-30)
    
    return lyap_sum / (n_segs * n_renorm * dt)

def lz_complexity(signal, n_sym=8):
    bins = np.linspace(signal.min(), signal.max(), n_sym + 1)
    s_list = np.clip(np.digitize(signal, bins) - 1, 0, n_sym - 1)
    s = ''.join(str(c) for c in s_list)
    n = len(s)
    if n == 0: return 0.0
    i, c, l, k = 0, 1, 1, 1
    while i + l <= n:
        if s[i:i+l] == s[k:k+l]:
            l += 1
            if k + l > i + 1:
                i += 1; l = 1; k = i + 1
        else:
            c += 1; i += l; l = 1; k = i + 1
        if i + l > n: break
    return c / (n / np.log2(n)) if n > 1 else 0.0

def perm_entropy(sig, order=4, delay=1):
    n = len(sig)
    if n < order * delay: return 0.0
    perms = list(permutations(range(order)))
    counts = {p: 0 for p in perms}
    total = 0
    for i in range(n - (order-1)*delay):
        seg = [sig[i + j*delay] for j in range(order)]
        r = tuple(np.argsort(seg))
        if r in counts: counts[r] += 1; total += 1
    if total == 0: return 0.0
    H = -sum((c/total)*np.log2(c/total) for c in counts.values() if c > 0)
    return H / np.log2(len(perms))

def corr_dim(traj, n_samp=120):
    n = len(traj)
    if n > n_samp:
        idx = np.random.choice(n, n_samp, replace=False)
        pts = traj[idx]
    else:
        pts = traj
    np_pts = len(pts)
    dists = []
    for i in range(np_pts):
        for j in range(i+1, np_pts):
            d = np.linalg.norm(pts[i] - pts[j])
            if d > 1e-12: dists.append(d)
    dists = np.sort(dists)
    r_min, r_max = np.percentile(dists, 10), np.percentile(dists, 90)
    if r_min <= 0 or r_max <= 0 or r_min >= r_max: return 0.0
    r_vals = np.logspace(np.log10(r_min), np.log10(r_max), 20)
    C = np.array([np.mean(dists < r) for r in r_vals])
    ok = (C > 0) & (C < 1)
    if np.sum(ok) < 3: return 0.0
    A = np.vstack([np.log(r_vals[ok]), np.ones(ok.sum())]).T
    try:
        m, _ = np.linalg.lstsq(A, np.log(C[ok]), rcond=None)[0]
        return m
    except: return 0.0

print("THOMAS ATTRACTOR: EDGE-OF-CHAOS COMPLEXITY ANALYSIS")
print("="*60)

# Focused scan with coarser grid
b_vals = np.concatenate([
    np.arange(0.05, 0.15, 0.02),
    np.arange(0.15, 0.26, 0.005),  # Dense near b_c
    np.arange(0.26, 0.33, 0.02)
])

res = {k: [] for k in ['b','l1','l2','l3','hKS','lz','pe','D2']}

for b in b_vals:
    print(f"  b={b:.3f} ", end="", flush=True)
    try:
        lyaps = compute_lyapunov(b, T=150, dt=0.02, T_trans=40)
        l1, l2, l3 = sorted(lyaps, reverse=True)
    except:
        l1, l2, l3 = 0, 0, 0
    
    h_KS = sum(l for l in [l1,l2,l3] if l > 1e-10)
    
    # Generate trajectory for complexity
    dt = 0.02
    state = np.array([1.0, 0.5, 0.3])
    for _ in range(int(30/dt)):  # transient
        state = rk4_step(state, b, dt)
    traj = []
    for _ in range(int(150/dt)):  # measurement
        state = rk4_step(state, b, dt)
        traj.append(state.copy())
    traj = np.array(traj)
    
    step = max(1, len(traj) // 500)
    xs, ys, zs = traj[::step,0], traj[::step,1], traj[::step,2]
    
    lz = (lz_complexity(xs) + lz_complexity(ys) + lz_complexity(zs)) / 3.0
    pe = perm_entropy(xs)
    D2 = corr_dim(traj, n_samp=100)
    
    res['b'].append(b); res['l1'].append(l1); res['l2'].append(l2); res['l3'].append(l3)
    res['hKS'].append(h_KS); res['lz'].append(lz); res['pe'].append(pe); res['D2'].append(D2)
    
    print(f"L1={l1:.4f} hKS={h_KS:.4f} LZ={lz:.4f} PE={pe:.4f} D2={D2:.2f}")

for k in res: res[k] = np.array(res[k])

b_c = 0.208
idx_c = np.argmin(np.abs(res['b'] - b_c))
print(f"\nAt b_c={b_c}: L1={res['l1'][idx_c]:.4f} hKS={res['hKS'][idx_c]:.4f} LZ={res['lz'][idx_c]:.4f} PE={res['pe'][idx_c]:.4f} D2={res['D2'][idx_c]:.2f}")
for name, key in [('hKS','hKS'),('LZ','lz'),('PE','pe'),('D2','D2')]:
    pi = np.argmax(res[key])
    print(f"  Peak {name}={res[key][pi]:.4f} at b={res['b'][pi]:.3f}")

# Save results as JSON
results_json = {k: v.tolist() for k, v in res.items()}
results_json['b_c'] = b_c
with open('shared_agora/artifacts/thomas_complexity_results.json', 'w') as f:
    json.dump(results_json, f, indent=2)

# PLOT
fig, axes = plt.subplots(3, 2, figsize=(16, 14))
fig.suptitle('Thomas Attractor: Edge-of-Chaos Complexity Analysis\n(Addressing DOSSIER_002)', fontsize=14, fontweight='bold')

norm = lambda a: (a - a.min())/(a.max() - a.min() + 1e-15)

ax = axes[0,0]
ax.plot(res['b'], res['l1'], 'r-', lw=2, label=r'$\lambda_1$')
ax.plot(res['b'], res['l2'], 'g-', lw=2, label=r'$\lambda_2$')
ax.plot(res['b'], res['l3'], 'b-', lw=2, label=r'$\lambda_3$')
ax.axhline(0, color='k', ls='--', alpha=0.3)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
ax.set_xlabel('b'); ax.set_ylabel(r'$\lambda_i$'); ax.set_title('Lyapunov Spectrum'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

ax = axes[0,1]
ax.plot(res['b'], res['hKS'], 'r-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
pi = np.argmax(res['hKS']); ax.plot(res['b'][pi], res['hKS'][pi], 'r*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('$h_{KS}$'); ax.set_title('Kolmogorov-Sinai Entropy'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

ax = axes[1,0]
ax.plot(res['b'], res['lz'], 'b-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
pi = np.argmax(res['lz']); ax.plot(res['b'][pi], res['lz'][pi], 'b*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('LZ complexity'); ax.set_title('Lempel-Ziv Complexity'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

ax = axes[1,1]
ax.plot(res['b'], res['pe'], 'g-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
pi = np.argmax(res['pe']); ax.plot(res['b'][pi], res['pe'][pi], 'g*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('PE'); ax.set_title('Permutation Entropy'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

ax = axes[2,0]
ax.plot(res['b'], res['D2'], 'm-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
ax.axhline(2.71, color='gray', ls=':', alpha=0.5, label='Dossier: D2=2.71')
pi = np.argmax(res['D2']); ax.plot(res['b'][pi], res['D2'][pi], 'm*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('$D_2$'); ax.set_title('Correlation Dimension'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

ax = axes[2,1]
ax.plot(res['b'], norm(res['hKS']), 'r-', lw=2, label='$h_{KS}$')
ax.plot(res['b'], norm(res['lz']), 'b-', lw=2, label='LZ')
ax.plot(res['b'], norm(res['pe']), 'g-', lw=2, label='PE')
ax.plot(res['b'], norm(res['D2']), 'm-', lw=2, label='$D_2$')
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
ax.set_xlabel('b'); ax.set_ylabel('Normalized'); ax.set_title('All Metrics Overlay'); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/thomas_edge_of_chaos_complexity.png', dpi=150, bbox_inches='tight')
print("\nFigure saved to shared_agora/artifacts/thomas_edge_of_chaos_complexity.png")
