"""
Thomas Attractor: Edge-of-Chaos Complexity Analysis
=====================================================
Addresses DOSSIER_002 challenge:
Can the Guilds verify whether the Thomas system's topological entropy
and block complexity exhibit an edge-of-chaos peak analogous to Cellular
Automata at the critical dissipation threshold b_c?

We compute:
1. Kolmogorov-Sinai entropy (sum of positive Lyapunov exponents)
2. Spatial complexity via Lempel-Ziv of discretized trajectories
3. Correlation dimension via Grassberger-Procaccia
4. Permutation entropy (Bandt-Pompe)

All as functions of b in [0.05, 0.32].
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from itertools import permutations

np.random.seed(42)

# Thomas system
def thomas_rhs(state, b):
    x, y, z = state
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def thomas_jacobian(state, b):
    x, y, z = state
    return np.array([
        [-b, np.cos(y), 0],
        [0, -b, np.cos(z)],
        [np.cos(x), 0, -b]
    ])

def rk4_step(rhs, state, b, dt):
    k1 = rhs(state, b)
    k2 = rhs(state + 0.5*dt*k1, b)
    k3 = rhs(state + 0.5*dt*k2, b)
    k4 = rhs(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

# Lyapunov Exponents via QR decomposition
def compute_lyapunov_spectrum(b, T_total=500, dt=0.01, T_transient=100):
    n = 3
    Q = np.eye(n)
    state = np.array([1.0, 0.0, 0.0])
    
    n_transient = int(T_transient / dt)
    for _ in range(n_transient):
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
            if R[i, i] > 0:
                lyap_sums[i] += np.log(R[i, i])
            else:
                lyap_sums[i] += np.log(abs(R[i, i]))
    
    total_time = n_segments * n_renorm * dt
    lyaps = lyap_sums / total_time
    return lyaps

# Kolmogorov-Sinai entropy (Pesin's identity)
def kolmogorov_sinai_entropy(lyaps):
    return sum(l for l in lyaps if l > 1e-10)

# Lempel-Ziv complexity
def lempel_ziv_complexity(signal, n_symbols=8):
    bins = np.linspace(signal.min(), signal.max(), n_symbols + 1)
    symbolized = np.digitize(signal, bins) - 1
    symbolized = np.clip(symbolized, 0, n_symbols - 1)
    
    s = ''.join(str(c) for c in symbolized)
    n = len(s)
    
    if n == 0:
        return 0.0
    
    i = 0
    c = 1
    l = 1
    k = 1
    
    while True:
        if i + l > n:
            break
        if s[i:i+l] == s[k:k+l]:
            l += 1
            if k + l > i + 1:
                i += 1
                l = 1
                k = i + 1
        else:
            c += 1
            i += l
            l = 1
            k = i + 1
        
        if i + l > n:
            break
    
    b_val = n / np.log2(n) if n > 1 else 1
    return c / b_val

# Permutation entropy (Bandt-Pompe)
def permutation_entropy(signal, order=4, delay=1):
    n = len(signal)
    
    if n < order * delay:
        return 0.0
    
    perms = list(permutations(range(order)))
    n_possible = len(perms)
    counts = {p: 0 for p in perms}
    total = 0
    
    for i in range(n - (order - 1) * delay):
        segment = [signal[i + j * delay] for j in range(order)]
        ranks = tuple(np.argsort(segment))
        if ranks in counts:
            counts[ranks] += 1
            total += 1
    
    if total == 0:
        return 0.0
    
    H = 0.0
    for p in perms:
        if counts[p] > 0:
            p_i = counts[p] / total
            H -= p_i * np.log2(p_i)
    
    H_max = np.log2(n_possible)
    return H / H_max if H_max > 0 else 0.0

# Correlation dimension (Grassberger-Procaccia)
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
            if d > 1e-12:
                dists.append(d)
    
    dists = np.array(sorted(dists))
    
    r_min = np.percentile(dists, 10)
    r_max = np.percentile(dists, 90)
    r_range = np.logspace(np.log10(r_min), np.log10(r_max), 30)
    
    C_r = []
    for r in r_range:
        C_r.append(np.mean(dists < r))
    
    C_r = np.array(C_r)
    
    valid = (C_r > 0) & (C_r < 1)
    if np.sum(valid) < 3:
        return 0.0
    
    log_r = np.log(r_range[valid])
    log_C = np.log(C_r[valid])
    
    A = np.vstack([log_r, np.ones(len(log_r))]).T
    try:
        m, c = np.linalg.lstsq(A, log_C, rcond=None)[0]
        return m
    except:
        return 0.0

# MAIN COMPUTATION
print("="*70)
print("THOMAS ATTRACTOR: EDGE-OF-CHAOS COMPLEXITY ANALYSIS")
print("="*70)
print()

b_values = np.concatenate([
    np.arange(0.05, 0.15, 0.01),
    np.arange(0.15, 0.25, 0.005),
    np.arange(0.25, 0.33, 0.01)
])

results = {
    'b': [], 'lambda1': [], 'lambda2': [], 'lambda3': [],
    'h_KS': [], 'lz_combined': [], 'perm_entropy': [], 'D2': []
}

for b in b_values:
    print(f"  b = {b:.3f} ... ", end="", flush=True)
    
    try:
        lyaps = compute_lyapunov_spectrum(b, T_total=300, dt=0.01, T_transient=50)
        l1, l2, l3 = sorted(lyaps, reverse=True)
    except:
        l1, l2, l3 = 0, 0, 0
    
    h_KS = kolmogorov_sinai_entropy([l1, l2, l3])
    
    # Generate trajectory
    T_total = 400
    dt = 0.01
    n_total = int(T_total / dt)
    n_transient = int(50 / dt)
    
    state = np.array([1.0, 0.0, 0.0])
    trajectory = []
    
    for i in range(n_total):
        state = rk4_step(thomas_rhs, state, b, dt)
        if i >= n_transient:
            trajectory.append(state.copy())
    
    traj = np.array(trajectory)
    x_traj = traj[:, 0]
    
    # Sample for complexity
    step = max(1, len(traj) // 1000)
    x_sample = x_traj[::step]
    y_sample = traj[::step, 1]
    z_sample = traj[::step, 2]
    
    lz_x = lempel_ziv_complexity(x_sample, n_symbols=8)
    lz_y = lempel_ziv_complexity(y_sample, n_symbols=8)
    lz_z = lempel_ziv_complexity(z_sample, n_symbols=8)
    lz_combined = (lz_x + lz_y + lz_z) / 3.0
    
    pe = permutation_entropy(x_sample, order=5, delay=1)
    D2 = correlation_dimension(traj, n_samples=150)
    
    results['b'].append(b)
    results['lambda1'].append(l1)
    results['lambda2'].append(l2)
    results['lambda3'].append(l3)
    results['h_KS'].append(h_KS)
    results['lz_combined'].append(lz_combined)
    results['perm_entropy'].append(pe)
    results['D2'].append(D2)
    
    print(f"lambda1={l1:.4f}, h_KS={h_KS:.4f}, LZ={lz_combined:.4f}, PE={pe:.4f}, D2={D2:.2f}")

# Convert to arrays
for key in results:
    results[key] = np.array(results[key])

# Find critical region
b_c = 0.208
idx_c = np.argmin(np.abs(results['b'] - b_c))

print()
print("="*70)
print("RESULTS SUMMARY")
print("="*70)
print(f"Critical b_c = {b_c}")
print(f"  At b_c: lambda1 = {results['lambda1'][idx_c]:.4f}")
print(f"  At b_c: h_KS = {results['h_KS'][idx_c]:.4f}")
print(f"  At b_c: LZ = {results['lz_combined'][idx_c]:.4f}")
print(f"  At b_c: PE = {results['perm_entropy'][idx_c]:.4f}")
print(f"  At b_c: D2 = {results['D2'][idx_c]:.2f}")

# Find peak locations
for metric_name, metric_key in [('h_KS', 'h_KS'), ('LZ', 'lz_combined'), ('PE', 'perm_entropy'), ('D2', 'D2')]:
    peak_idx = np.argmax(results[metric_key])
    print(f"  Peak {metric_name} = {results[metric_key][peak_idx]:.4f} at b = {results['b'][peak_idx]:.3f}")

# PLOTTING
fig = plt.figure(figsize=(16, 14))
gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)

# Panel 1: Lyapunov exponents
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(results['b'], results['lambda1'], 'r-', linewidth=2, label=r'$\lambda_1$')
ax1.plot(results['b'], results['lambda2'], 'g-', linewidth=2, label=r'$\lambda_2$')
ax1.plot(results['b'], results['lambda3'], 'b-', linewidth=2, label=r'$\lambda_3$')
ax1.axhline(y=0, color='k', linestyle='--', alpha=0.3)
ax1.axvline(x=b_c, color='orange', linestyle='--', alpha=0.7, label=f'$b_c = {b_c}$')
ax1.set_xlabel('Dissipation parameter b')
ax1.set_ylabel('Lyapunov exponent')
ax1.set_title('Lyapunov Spectrum')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# Panel 2: Kolmogorov-Sinai entropy
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(results['b'], results['h_KS'], 'r-', linewidth=2)
ax2.axvline(x=b_c, color='orange', linestyle='--', alpha=0.7, label=f'$b_c = {b_c}$')
peak_idx = np.argmax(results['h_KS'])
ax2.plot(results['b'][peak_idx], results['h_KS'][peak_idx], 'r*', markersize=15)
ax2.set_xlabel('Dissipation parameter b')
ax2.set_ylabel('Kolmogorov-Sinai entropy')
ax2.set_title('KS Entropy (Pesin identity)')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

# Panel 3: Lempel-Ziv complexity
ax3 = fig.add_subplot(gs[1, 0])
ax3.plot(results['b'], results['lz_combined'], 'b-', linewidth=2)
ax3.axvline(x=b_c, color='orange', linestyle='--', alpha=0.7, label=f'$b_c = {b_c}$')
peak_idx = np.argmax(results['lz_combined'])
ax3.plot(results['b'][peak_idx], results['lz_combined'][peak_idx], 'b*', markersize=15)
ax3.set_xlabel('Dissipation parameter b')
ax3.set_ylabel('Normalized LZ complexity')
ax3.set_title('Lempel-Ziv Complexity (averaged)')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# Panel 4: Permutation entropy
ax4 = fig.add_subplot(gs[1, 1])
ax4.plot(results['b'], results['perm_entropy'], 'g-', linewidth=2)
ax4.axvline(x=b_c, color='orange', linestyle='--', alpha=0.7, label=f'$b_c = {b_c}$')
peak_idx = np.argmax(results['perm_entropy'])
ax4.plot(results['b'][peak_idx], results['perm_entropy'][peak_idx], 'g*', markersize=15)
ax4.set_xlabel('Dissipation parameter b')
ax4.set_ylabel('Normalized permutation entropy')
ax4.set_title('Permutation Entropy (order=5)')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

# Panel 5: Correlation dimension
ax5 = fig.add_subplot(gs[2, 0])
ax5.plot(results['b'], results['D2'], 'm-', linewidth=2)
ax5.axvline(x=b_c, color='orange', linestyle='--', alpha=0.7, label=f'$b_c = {b_c}$')
ax5.axhline(y=2.71, color='gray', linestyle=':', alpha=0.5, label='Dossier claim: D2=2.71')
peak_idx = np.argmax(results['D2'])
ax5.plot(results['b'][peak_idx], results['D2'][peak_idx], 'm*', markersize=15)
ax5.set_xlabel('Dissipation parameter b')
ax5.set_ylabel('Correlation dimension D2')
ax5.set_title('Correlation Dimension')
ax5.legend(fontsize=9)
ax5.grid(True, alpha=0.3)

# Panel 6: Normalized complexity comparison
ax6 = fig.add_subplot(gs[2, 1])
# Normalize all metrics to [0, 1]
def normalize(arr):
    return (arr - arr.min()) / (arr.max() - arr.min() + 1e-10)

ax6.plot(results['b'], normalize(results['h_KS']), 'r-', linewidth=2, label='KS entropy')
ax6.plot(results['b'], normalize(results['lz_combined']), 'b-', linewidth=2, label='LZ complexity')
ax6.plot(results['b'], normalize(results['perm_entropy']), 'g-', linewidth=2, label='Perm entropy')
ax6.plot(results['b'], normalize(results['D2']), 'm-', linewidth=2, label='D2')
ax6.axvline(x=b_c, color='orange', linestyle='--', alpha=0.7, label=f'$b_c = {b_c}$')
ax6.set_xlabel('Dissipation parameter b')
ax6.set_ylabel('Normalized complexity')
ax6.set_title('Edge-of-Chaos: All Complexity Metrics')
ax6.legend(fontsize=8)
ax6.grid(True, alpha=0.3)

fig.suptitle('Thomas Attractor: Edge-of-Chaos Complexity Analysis\n(Addressing DOSSIER_002)', fontsize=14, fontweight='bold')
plt.savefig('shared_agora/artifacts/thomas_edge_of_chaos_complexity.png', dpi=150, bbox_inches='tight')
print()
print("Figure saved to shared_agora/artifacts/thomas_edge_of_chaos_complexity.png")
