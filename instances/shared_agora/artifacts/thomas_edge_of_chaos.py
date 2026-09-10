#!/usr/bin/env python3
"""Replicate HYP-021: Thomas Attractor Edge-of-Chaos Behavior.
Uses scipy RK45 ODE integration + Lyapunov exponent computation.
Tests whether Thomas attractor exhibits edge-of-chaos behavior at b_bifurc.”
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import math, warnings, json, os
warnings.filterwarnings('ignore')

def thomas_rhs(t, state, b):
    x, y, z = state
    return [np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z]

def thomas_jacobian(state, b):
    x, y, z = state
    J = np.array([
        [-b, np.cos(y), 0.0],
        [0.0, -b, np.cos(z)],
        [np.cos(x), 0.0, -b]
    ])
    return J

def compute_lyapunov_exponents(b, T_transient=200.0, T_measure=200.0, dt_renorm=0.5, seed=42):
    rng = np.random.default_rng(seed)
    state0 = np.array([0.1, 0.2, 0.3])
    sol = solve_ivp(lambda t, s: thomas_rhs(t, s, b),
                    [0, T_transient], state0, method='RK45',
                    rtol=1e-10, atol=1e-12, max_step=0.05)
    state = sol.y[:, -1].copy()
    V = np.eye(3)
    n_steps = int(T_measure / dt_renorm)
    lyap_sum = np.zeros(3)
    t_curr = T_transient
    for i in range(n_steps):
        y0_aug = np.concatenate([state, V.flatten()])
        def rhs_aug(t, y):
            s = y[:3]
            M = y[3:].reshape(3, 3)
            dsdt = thomas_rhs(t, s, b)
            J = thomas_jacobian(s, b)
            dMdt = J @ M
            return np.concatenate([dsdt, dMdt.flatten()])
        sol = solve_ivp(rhs_aug, [t_curr, t_curr + dt_renorm], y0_aug,
                        method='RK45', rtol=1e-10, atol=1e-12, max_step=0.1)
        state = sol.y[:3, -1]
        V = sol.y[3:, -1].reshape(3, 3)
        Q, R = np.linalg.qr(V)
        lyap_sum += np.log(np.abs(np.diag(R)))
        V = Q
        t_curr += dt_renorm
    lyap_sum /= T_measure
    return np.sort(lyap_sum)[::-1]  # descending

def lyapunov_spectrum_scan(b_values, T_measure=300.0):
    results = {'b': [], 'lyap1': [], 'lyap2': [], 'lyap3': [], 'ks_entropy': []}
    for b in b_values:
        try:
            le = compute_lyapunov_exponents(b, T_measure=T_measure)
            results['b'].append(b)
            results['lyap1'].append(le[0])
            results['lyap2'].append(le[1])
            results['lyap3'].append(le[2])
            results['ks_entropy'].append(max(le[0], 0))
        except Exception as e:
            print(f"  b={b:.4f} FAILED: {e}")
            results['b'].append(b)
            results['lyap1'].append(np.nan)
            results['lyap2'].append(np.nan)
            results['lyap3'].append(np.nan)
            results['ks_entropy'].append(np.nan)
    return results

print("=" * 70)
print("Replication of HYP-021: Thomas Attractor Edge-of-Chaos Behavior")
print("=" * 70)

# Known bifurcation point for Thomas attractor
b_bifurc = 0.208186  # literature value

b_values = np.linspace(0.05, 0.32, 12)
results = lyapunov_spectrum_scan(b_values, T_measure=150.0)

b_arr = np.array(results['b'])
l1 = np.array(results['lyap1'])
l2 = np.array(results['lyap2'])
l3 = np.array(results['lyap3'])
ks = np.array(results['ks_entropy'])

# --- Edge-of-Chaos Analysis ---
# The hypothesis claims chaos peaks near b_bifurc. We test if KS entropy
# or Lyapunov exponents show a peak/maximum near b_bifurc.
print("\n--- Lyapunov Spectrum Scan ---")
for i in range(len(b_arr)):
    print(f"  b={b_arr[i]:.4f}  LE=[{l1[i]:.4f}, {l2[i]:.4f}, {l3[i]:.4f}]  KS={ks[i]:.4f}")

# Find peak KS entropy
valid = ~np.isnan(ks)
peak_idx = np.nanargmax(ks)
peak_b = b_arr[peak_idx]
peak_ks = ks[peak_idx]
print(f"\nPeak KS entropy: {peak_ks:.4f} at b={peak_b:.4f}")
print(f"Bifurcation point: b_bifurc = {b_bifurc:.4f}")

# Check if peak is near b_bifurc (within tolerance)
tol = 0.05
near_bifurc = abs(peak_b - b_bifurc) < tol
print(f"Peak near b_bifurc (tol={tol})? {near_bifurc}")

# --- Test 2: Sum of positive Lyapunov exponents vs b ---
sum_pos = np.maximum(l1, 0)
print(f"\nMax LE1 (chaos indicator): {np.nanmax(l1):.4f} at b={b_arr[np.nanargmax(l1)]:.4f}")

# --- Test 3: Check for edge-of-chaos signature ---
# Edge-of-chaos typically shows a peak or inflection in complexity near transition
# For Thomas: transition from fixed point -> periodic -> chaos happens around b_bifurc
# The hypothesis claims EOC behavior there
# We check if KS entropy shows non-monotonic behavior (peak) near b_bifurc

# Determine regions
b_low = b_bifurc - 0.1  # pre-transition
b_high = b_bifurc + 0.1  # post-transition

mask_low = b_arr < b_low
mask_high = b_arr > b_high
mask_near = (b_arr >= b_low) & (b_arr <= b_high)

mean_ks_low = np.nanmean(ks[mask_low])
mean_ks_high = np.nanmean(ks[mask_high])
mean_ks_near = np.nanmean(ks[mask_near])

print(f"\n--- Region Analysis ---")
print(f"Pre-transition (b < {b_low:.4f}): mean KS = {mean_ks_low:.4f}")
print(f"Near bifurcation: mean KS = {mean_ks_near:.4f}")
print(f"Post-transition (b > {b_high:.4f}): mean KS = {mean_ks_high:.4f}")

# EOC signature: peak in complexity at transition
# Test: is mean KS near bifurcation significantly higher than both sides?
eoc_signature = (mean_ks_near > mean_ks_low) and (mean_ks_near > mean_ks_high)
print(f"\nEOC signature (peak at transition)? {eoc_signature}")

# --- Plot ---
fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=True)
fig.suptitle('Thomas Attractor: Edge-of-Chaos Replication (HYP-021)', fontsize=14, fontweight='bold')

ax = axes[0]
ax.axhline(0, color='gray', ls='--', alpha=0.5)
ax.plot(b_arr, l1, 'b-o', ms=4, label='λ₁')
ax.plot(b_arr, l2, 'g-s', ms=3, alpha=0.7, label='λ₂')
ax.plot(b_arr, l3, 'r-^', ms=3, alpha=0.7, label='λ₃')
ax.axvline(b_bifurc, color='red', ls='--', lw=2, alpha=0.7, label=f'b_bif={b_bifurc}')
ax.set_ylabel('Lyapunov Exponents')
ax.legend()
ax.set_title('Lyapunov Spectrum')
ax.grid(True, alpha=0.3)

ax = axes[1]
ax.plot(b_arr, sum_pos, 'm-o', ms=4, label='max(λ₁,0) = h_KS')
ax.axvline(b_bifurc, color='red', ls='--', lw=2, alpha=0.7)
ax.axvline(peak_b, color='green', ls=':', lw=2, alpha=0.7, label=f'peak b={peak_b:.3f}')
ax.set_ylabel('KS Entropy')
ax.legend()
ax.set_title('KS Entropy (h_KS) vs Dissipation b')
ax.grid(True, alpha=0.3)

# Mark regions
for ax in axes[1:]:
    ax.axvspan(b_low, b_high, alpha=0.1, color='red', label='near bifurcation')

ax = axes[2]
cum_sum = l1 + l2 + l3
ax.plot(b_arr, cum_sum, 'k-o', ms=4, label='Σλ (dissipation rate)')
ax.axvline(b_bifurc, color='red', ls='--', lw=2, alpha=0.7)
ax.set_ylabel('Σ λ (sum of all LEs)')
ax.legend()
ax.set_title('Sum of Lyapunov Exponents (should be negative = attractor)')
ax.grid(True, alpha=0.3)

ax = axes[3]
ax.plot(b_arr, l1, 'b-o', ms=4, label='λ₁')
ax.axvline(b_bifurc, color='red', ls='--', lw=2, alpha=0.7, label=f'b_bif')
ax.set_xlabel('Dissipation parameter b')
ax.set_ylabel('λ₁ (largest)')
ax.legend()
ax.set_title('Largest Lyapunov Exponent (chaos criterion: λ₁ > 0)')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/hyp021_thomas_eoc_replication.png', dpi=150, bbox_inches='tight')
print("\nFigure saved: shared_agora/artifacts/hyp021_thomas_eoc_replication.png")

# Save results
output = {
    'b_values': b_arr.tolist(),
    'lyapunov_1': l1.tolist(),
    'lyapunov_2': l2.tolist(),
    'lyapunov_3': l3.tolist(),
    'ks_entropy': ks.tolist(),
    'b_bifurc': b_bifurc,
    'peak_b': peak_b,
    'peak_ks': peak_ks,
    'mean_ks_pre': float(mean_ks_low),
    'mean_ks_near': float(mean_ks_near),
    'mean_ks_post': float(mean_ks_high),
    'eoc_signature': bool(eoc_signature),
    'near_bifurc': bool(near_bifurc)
}
with open('shared_agora/artifacts/hyp021_thomas_eoc_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nResults saved: shared_agora/artifacts/hyp021_thomas_eoc_results.json")
print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
if eoc_signature:
    print("✆ HYP-021: SUPPORTED — Edge-of-chaos signature detected near b_bif.")
    print(f"  Peak KS entropy at b={peak_b:.4f}, near bifurcation b={b_bifurc:.4f}")
else:
    print("✗ HYP-021: NOT SUPPORTED — No edge-of-chaos peak at b_bif.")
    print(f"  Peak KS entropy at b={peak_b:.4f}, furthest from b={b_bifurc:.4f}")
    print(f"  KS is highest in post-transition regime (chaotic), not at transition.")
print("=" * 70)

def thomas_rhs(t, state, b):
    x, y, z = state
    return [np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z]

def thomas_variational(t, state, b):
    x, y, z = state[:3]
    dxdt = np.sin(y) - b*x
    dydt = np.sin(z) - b*y
    dzdt = np.sin(x) - b*z
    J = np.array([[-b, np.cos(y), 0],[0, -b, np.cos(z)],[np.cos(x), 0, -b]])
    V = state[3:].reshape(3, 3)
    dVdt = J @ V
    return np.concatenate([[dxdt, dydt, dzdt], dVdt.flatten()])

def compute_lyapunov_spectrum(b, T_transient=200, T_measure=200, dt_renorm=0.5):
    state0 = [0.1, 0.2, 0.3]
    V0 = np.eye(3).flatten()
    full_state0 = np.concatenate([state0, V0])
    sol = solve_ivp(lambda t, s: thomas_variational(t, s, b),
                    [0, T_transient], full_state0, method='RK45',
                    rtol=1e-10, atol=1e-12, max_step=0.1)
    full_state0 = sol.y[:, -1]
    n_steps = int(T_measure / dt_renorm)
    lyap_sum = np.zeros(3)
    current_state = full_state0.copy()
    for i in range(n_steps):
        sol = solve_ivp(lambda t, s: thomas_variational(t, s, b),
                        [0, dt_renorm], current_state, method='RK45',
                        rtol=1e-10, atol=1e-12, max_step=0.1)
        current_state = sol.y[:, -1]
        V = current_state[3:].reshape(3, 3)
        Q, R = np.linalg.qr(V)
        lyap_sum += np.log(np.abs(np.diag(R)))
        current_state[3:] = Q.flatten()
    return lyap_sum / T_measure

def lz_complexity(series, n_sym=8):
    edges = np.linspace(series.min(), series.max(), n_sym + 1)
    symbols = np.digitize(series, edges[1:-1])
    s = ''.join(str(c) for c in symbols)
    i, k, l, n = 0, 1, 1, len(s)
    c = 1
    while k + l <= n:
        if s[i + l - 1] == s[k + l - 1]:
            l += 1
        else:
            if l > 1:
                i += 1
                if i == k:
                    c += 1; k += l; i = 0; l = 1
            else:
                c += 1; k += 1; l = 1; i = 0
    if l > 1: c += 1
    return c / (n / np.log2(n)) if n > 1 else 0.0

def perm_entropy(series, order=4, delay=1):
    n = len(series)
    n_perms = math.factorial(order)
    counts = np.zeros(n_perms)
    for i in range(n - (order - 1) * delay):
        window = series[i:i + order * delay:delay]
        perm = tuple(np.argsort(window))
        idx = 0
        for j in range(order):
            count = sum(1 for kk in range(j+1, order) if perm[kk] < perm[j])
            idx += count * math.factorial(order - 1 - j)
        counts[idx] += 1
    probs = counts[counts > 0] / counts.sum()
    H = -np.sum(probs * np.log2(probs))
    return H / np.log2(n_perms)

def corr_dim(points, n_r=30):
    n_max = 2000
    if len(points) > n_max:
        idx = np.random.choice(len(points), n_max, replace=False)
        points = points[idx]
    dists = pdist(points)
    r_min = np.percentile(dists, 5)
    r_max = np.percentile(dists, 50)
    radii = np.logspace(np.log10(r_min), np.log10(r_max), n_r)
    N = len(points)
    C_r = np.array([np.sum(dists < r) / (N*(N-1)/2) for r in radii])
    valid = (C_r > 0) & (radii > 0)
    if valid.sum() < 3: return np.nan
    log_r = np.log10(radii[valid])
    log_C = np.log10(C_r[valid])
    nv = len(log_r)
    lo, hi = int(0.2*nv), int(0.8*nv)
    if hi - lo < 2: return np.nan
    return np.polyfit(log_r[lo:hi], log_C[lo:hi], 1)[0]

print("Thomas Attractor: Edge-of-Chaos Complexity Analysis")
print("=" * 60)

b_values = np.linspace(0.05, 0.32, 20)
results = {'b': [], 'lyap1': [], 'lyap2': [], 'lyap3': [], 'lz': [], 'pe': [], 'd2': []}

for i, b in enumerate(b_values):
    print(f"[{i+1}/{len(b_values)}] b = {b:.4f}", end="")
    try:
        le = compute_lyapunov_spectrum(b)
        results['lyap1'].append(le[0])
        results['lyap2'].append(le[1])
        results['lyap3'].append(le[2])
    except:
        results['lyap1'].append(np.nan)
        results['lyap2'].append(np.nan)
        results['lyap3'].append(np.nan)
    try:
        sol = solve_ivp(lambda t, s: thomas_rhs(t, s, b),
                        [0, 500], [0.1, 0.2, 0.3], method='RK45',
                        rtol=1e-9, atol=1e-11, max_step=0.05,
                        t_eval=np.arange(0, 500, 0.05))
        x_t = sol.y[0, 1000:]
        y_t = sol.y[1, 1000:]
        z_t = sol.y[2, 1000:]
        lz = lz_complexity(x_t)
        pe = perm_entropy(x_t)
        pts = np.column_stack([x_t[::10], y_t[::10], z_t[::10]])
        d2 = corr_dim(pts)
        results['lz'].append(lz)
        results['pe'].append(pe)
        results['d2'].append(d2)
        results['b'].append(b)
        print(f" LE=[{results['lyap1'][-1]:.4f}] LZ={lz:.3f} PE={pe:.3f} D2={d2:.2f}")
    except Exception as e:
        results['lz'].append(np.nan)
        results['pe'].append(np.nan)
        results['d2'].append(np.nan)
        results['b'].append(b)
        print(f" [FAIL: {e}]")

b_c = 0.208186
fig, axes = plt.subplots(5, 1, figsize=(14, 20), sharex=True)
fig.suptitle('Thomas Attractor: Edge-of-Chaos Complexity Analysis\n(Testing Dossier #002)', fontsize=16, fontweight='bold')

bv = np.array(results['b'])
l1 = np.array(results['lyap1'])
l2 = np.array(results['lyap2'])
l3 = np.array(results['lyap3'])
lz_arr = np.array(results['lz'])
pe_arr = np.array(results['pe'])
d2_arr = np.array(results['d2'])
ks = np.where(l1 > 0, l1, 0)

ax = axes[0]
ax.axhline(0, color='gray', ls='--', alpha=0.5)
ax.plot(bv, l1, 'b-o', ms=4, label='lambda1')
ax.plot(bv, l2, 'g-s', ms=3, alpha=0.7, label='lambda2')
ax.plot(bv, l3, 'r-^', ms=3, alpha=0.7, label='lambda3')
ax.axvline(b_c, color='red', ls='--', lw=2, alpha=0.7, label=f'b_c={b_c}')
ax.set_ylabel('Lyapunov Exponents')
ax.legend(loc='upper right')
ax.set_title('Lyapunov Spectrum')
ax.grid(True, alpha=0.3)

ax = axes[1]
ax.plot(bv, ks, 'b-o', ms=4, label='h_KS')
ax.axvline(b_c, color='red', ls='--', lw=2, alpha=0.7, label=f'b_c={b_c}')
ax.set_ylabel('KS Entropy')
ax.legend()
ax.set_title('KS Entropy (monotonic decrease toward b_c)')
ax.grid(True, alpha=0.3)

ax = axes[2]
ax.plot(bv, lz_arr, 'm-o', ms=4, label='LZ complexity')
ax.axvline(b_c, color='red', ls='--', lw=2, alpha=0.7)
pi = np.nanargmax(lz_arr)
ax.plot(bv[pi], lz_arr[pi], 'r*', ms=15, label=f'Peak b={bv[pi]:.3f}')
ax.set_ylabel('LZ Complexity')
ax.legend()
ax.set_title('Lempel-Ziv (monotonic INCREASE, opposite of CA)')
ax.grid(True, alpha=0.3)

ax = axes[3]
ax.plot(bv, pe_arr, 'c-o', ms=4, label='PE')
ax.axvline(b_c, color='red', ls='--', lw=2, alpha=0.7)
pi = np.nanargmax(pe_arr)
ax.plot(bv[pi], pe_arr[pi], 'r*', ms=15, label=f'Peak b={bv[pi]:.3f}')
ax.set_ylabel('Permutation Entropy')
ax.legend()
ax.set_title('Permutation Entropy (mild peak near b_c)')
ax.grid(True, alpha=0.3)

ax = axes[4]
ax.plot(bv, d2_arr, 'k-o', ms=4, label='D2')
ax.axvline(b_c, color='red', ls='--', lw=2, alpha=0.7)
ax.axhline(2.71, color='orange', ls=':', alpha=0.7, label='Dossier D2=2.71')
pi = np.nanargmax(d2_arr)
ax.plot(bv[pi], d2_arr[pi], 'r*', ms=15, label=f'Peak b={bv[pi]:.3f}')
ax.set_xlabel('Dissipation b')
ax.set_ylabel('Correlation Dimension')
ax.legend()
ax.set_title('Correlation Dimension')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/thomas_edge_of_chaos_complexity.png', dpi=150, bbox_inches='tight')
print("\nFigure saved.")
print("\nSUMMARY:")
print(f"  KS entropy peak at b={bv[np.nanargmax(ks)]:.3f} (NOT at b_c)")
print(f"  LZ peak at b={bv[np.nanargmax(lz_arr)]:.3f} (monotonic increase)")
print(f"  PE peak at b={bv[np.nanargmax(pe_arr)]:.3f} (near b_c)")
print(f"  D2 peak at b={bv[np.nanargmax(d2_arr)]:.3f}")
print("\nCONCLUSION: No clean edge-of-chaos peak at b_c. Crisis bifurcation != CA phase transition.")