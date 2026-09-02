import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from itertools import permutations

np.random.seed(42)

def thomas_rhs(state, b):
    x, y, z = state
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def thomas_jacobian(state, b):
    x, y, z = state
    return np.array([[-b, np.cos(y), 0],[0, -b, np.cos(z)],[np.cos(x), 0, -b]])

def rk4_step(rhs, state, b, dt):
    k1 = rhs(state, b)
    k2 = rhs(state + 0.5*dt*k1, b)
    k3 = rhs(state + 0.5*dt*k2, b)
    k4 = rhs(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def compute_lyapunov_spectrum(b, T_total=500, dt=0.01, T_transient=100):
    n = 3
    Q = np.eye(n)
    state = np.array([1.0, 0.0, 0.0])
    for _ in range(int(T_transient / dt)):
        state = rk4_step(thomas_rhs, state, b, dt)
    n_total = int(T_total / dt)
    n_renorm = 10
    n_segments = n_total // n_renorm
    lyap_sums = np.zeros(n)
    for seg in range(n_segments):
        for _ in range(n_renorm):
            J = thomas_jacobian(state, b)
            Q = Q + dt * (J @ Q)
            state = rk4_step(thomas_rhs, state, b, dt)
        Q, R = np.linalg.qr(Q)
        for i in range(n):
            lyap_sums[i] += np.log(abs(R[i, i]) + 1e-30)
    total_time = n_segments * n_renorm * dt
    return lyap_sums / total_time

def kolmogorov_sinai_entropy(lyaps):
    return sum(l for l in lyaps if l > 1e-10)

def lempel_ziv_complexity(signal, n_symbols=8):
    bins = np.linspace(signal.min(), signal.max(), n_symbols + 1)
    symbolized = np.clip(np.digitize(signal, bins) - 1, 0, n_symbols - 1)
    s = ''.join(str(c) for c in symbolized)
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
    b_val = n / np.log2(n) if n > 1 else 1
    return c / b_val

def permutation_entropy(signal, order=5, delay=1):
    n = len(signal)
    if n < order * delay: return 0.0
    perms = list(permutations(range(order)))
    n_possible = len(perms)
    counts = {p: 0 for p in perms}
    total = 0
    for i in range(n - (order - 1) * delay):
        segment = [signal[i + j * delay] for j in range(order)]
        ranks = tuple(np.argsort(segment))
        if ranks in counts:
            counts[ranks] += 1; total += 1
    if total == 0: return 0.0
    H = 0.0
    for p in perms:
        if counts[p] > 0:
            p_i = counts[p] / total
            H -= p_i * np.log2(p_i)
    H_max = np.log2(n_possible)
    return H / H_max if H_max > 0 else 0.0

def correlation_dimension(trajectory, n_samples=200):
    n = len(trajectory)
    if n > n_samples:
        indices = np.random.choice(n, n_samples, replace=False)
        points = trajectory[indices]
    else:
        points = trajectory
    n_pts = len(points)
    dists = []
    for i in range(n_pts):
        for j in range(i+1, n_pts):
            d = np.linalg.norm(points[i] - points[j])
            if d > 1e-12: dists.append(d)
    dists = np.array(sorted(dists))
    r_min = np.percentile(dists, 10)
    r_max = np.percentile(dists, 90)
    r_range = np.logspace(np.log10(r_min), np.log10(r_max), 30)
    C_r = np.array([np.mean(dists < r) for r in r_range])
    valid = (C_r > 0) & (C_r < 1)
    if np.sum(valid) < 3: return 0.0
    log_r = np.log(r_range[valid])
    log_C = np.log(C_r[valid])
    A = np.vstack([log_r, np.ones(len(log_r))]).T
    try:
        m, c = np.linalg.lstsq(A, log_C, rcond=None)[0]
        return m
    except: return 0.0

print("="*70)
print("THOMAS ATTRACTOR: EDGE-OF-CHAOS COMPLEXITY ANALYSIS")
print("="*70)

b_values = np.concatenate([
    np.arange(0.05, 0.15, 0.01),
    np.arange(0.15, 0.25, 0.005),
    np.arange(0.25, 0.33, 0.01)
])

results = {k: [] for k in ['b','lambda1','lambda2','lambda3','h_KS','lz_combined','perm_entropy','D2']}

for b in b_values:
    print(f"  b = {b:.3f} ... ", end="", flush=True)
    try:
        lyaps = compute_lyapunov_spectrum(b, T_total=300, dt=0.01, T_transient=50)
        l1, l2, l3 = sorted(lyaps, reverse=True)
    except:
        l1, l2, l3 = 0, 0, 0
    h_KS = kolmogorov_sinai_entropy([l1, l2, l3])
    
    dt = 0.01
    n_total = int(400 / dt)
    n_transient = int(50 / dt)
    state = np.array([1.0, 0.0, 0.0])
    trajectory = []
    for i in range(n_total):
        state = rk4_step(thomas_rhs, state, b, dt)
        if i >= n_transient: trajectory.append(state.copy())
    traj = np.array(trajectory)
    
    step = max(1, len(traj) // 1000)
    x_s = traj[::step, 0]
    y_s = traj[::step, 1]
    z_s = traj[::step, 2]
    
    lz_combined = (lempel_ziv_complexity(x_s) + lempel_ziv_complexity(y_s) + lempel_ziv_complexity(z_s)) / 3.0
    pe = permutation_entropy(x_s)
    D2 = correlation_dimension(traj, n_samples=150)
    
    results['b'].append(b)
    results['lambda1'].append(l1); results['lambda2'].append(l2); results['lambda3'].append(l3)
    results['h_KS'].append(h_KS); results['lz_combined'].append(lz_combined)
    results['perm_entropy'].append(pe); results['D2'].append(D2)
    print(f"L1={l1:.4f}, hKS={h_KS:.4f}, LZ={lz_combined:.4f}, PE={pe:.4f}, D2={D2:.2f}")

for key in results: results[key] = np.array(results[key])

b_c = 0.208
idx_c = np.argmin(np.abs(results['b'] - b_c))
print(f"\nAt b_c={b_c}: L1={results['lambda1'][idx_c]:.4f}, hKS={results['h_KS'][idx_c]:.4f}, LZ={results['lz_combined'][idx_c]:.4f}, PE={results['perm_entropy'][idx_c]:.4f}, D2={results['D2'][idx_c]:.2f}")

for name, key in [('h_KS','h_KS'),('LZ','lz_combined'),('PE','perm_entropy'),('D2','D2')]:
    pi = np.argmax(results[key])
    print(f"  Peak {name} = {results[key][pi]:.4f} at b = {results['b'][pi]:.3f}")

# Plot
fig, axes = plt.subplots(3, 2, figsize=(16, 14))
fig.suptitle('Thomas Attractor: Edge-of-Chaos Complexity Analysis\n(Addressing DOSSIER_002)', fontsize=14, fontweight='bold')

def normalize(arr):
    r = arr.max() - arr.min()
    return (arr - arr.min()) / r if r > 0 else arr * 0

# Lyapunov spectrum
ax = axes[0,0]
ax.plot(results['b'], results['lambda1'], 'r-', lw=2, label=r'$\lambda_1$')
ax.plot(results['b'], results['lambda2'], 'g-', lw=2, label=r'$\lambda_2$')
ax.plot(results['b'], results['lambda3'], 'b-', lw=2, label=r'$\lambda_3$')
ax.axhline(0, color='k', ls='--', alpha=0.3)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
ax.set_xlabel('b'); ax.set_ylabel('Lyapunov exponent'); ax.set_title('Lyapunov Spectrum'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

# KS entropy
ax = axes[0,1]
ax.plot(results['b'], results['h_KS'], 'r-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
pi = np.argmax(results['h_KS'])
ax.plot(results['b'][pi], results['h_KS'][pi], 'r*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('h_KS'); ax.set_title('KS Entropy (Pesin)'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

# LZ complexity
ax = axes[1,0]
ax.plot(results['b'], results['lz_combined'], 'b-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
pi = np.argmax(results['lz_combined'])
ax.plot(results['b'][pi], results['lz_combined'][pi], 'b*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('LZ complexity'); ax.set_title('Lempel-Ziv Complexity'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

# Permutation entropy
ax = axes[1,1]
ax.plot(results['b'], results['perm_entropy'], 'g-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
pi = np.argmax(results['perm_entropy'])
ax.plot(results['b'][pi], results['perm_entropy'][pi], 'g*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('PE'); ax.set_title('Permutation Entropy'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

# Correlation dimension
ax = axes[2,0]
ax.plot(results['b'], results['D2'], 'm-', lw=2)
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
ax.axhline(2.71, color='gray', ls=':', alpha=0.5, label='D2=2.71 (dossier)')
pi = np.argmax(results['D2'])
ax.plot(results['b'][pi], results['D2'][pi], 'm*', ms=15)
ax.set_xlabel('b'); ax.set_ylabel('D2'); ax.set_title('Correlation Dimension'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

# Normalized comparison
ax = axes[2,1]
ax.plot(results['b'], normalize(results['h_KS']), 'r-', lw=2, label='KS entropy')
ax.plot(results['b'], normalize(results['lz_combined']), 'b-', lw=2, label='LZ complexity')
ax.plot(results['b'], normalize(results['perm_entropy']), 'g-', lw=2, label='Perm entropy')
ax.plot(results['b'], normalize(results['D2']), 'm-', lw=2, label='D2')
ax.axvline(b_c, color='orange', ls='--', alpha=0.7, label=f'$b_c={b_c}$')
ax.set_xlabel('b'); ax.set_ylabel('Normalized'); ax.set_title('All Metrics (Normalized)'); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/thomas_edge_of_chaos_complexity.png', dpi=150, bbox_inches='tight')
print("\nFigure saved!")
