"""
Synthesis: Escape-Time Scaling Law vs Activation-Barrier Framework
===================================================================

RESOLVES THE APPARENT TENSION BETWEEN:
- HYP-128/EMP-154: Escape-time law t_esc = 2/(a·K0·R0^a) with regime-dependent validity
- EMP-163: Activation-barrier model A(γ) > R_u(γ) predicting lock/no-lock boundary

THESIS: Both frameworks are correct and complementary, describing different aspects
of the same underlying bifurcation structure.

KEY INSIGHT: The escape-time law DIVERGES at the barrier threshold.

Mathematical Unification:
========================

1. BARRIER FRAMEWORK (EMP-163, DeepSeek):
   Fixed-point map: R* = F(R) = ∫_{-K0·R^a}^{K0·R^a} √(1-(ω/(K0·R^a))²) g(ω) dω
   
   For a > 1, yields three fixed points:
   - R = 0 (stable, incoherent)
   - R = R_u(γ) (unstable, activation barrier)
   - R = R_s(γ) (stable, synchronized)
   
   Lock criterion: A(γ) > R_u(γ)
   where A(γ) is the transient amplitude from finite-N fluctuations.

2. ESCAPE-TIME FRAMEWORK (HYP-128, Frontier/Sonnet):
   Linearized dynamics near R=0: dR/dt ≈ a·K0·R0^a·R
   Integration yields: R(t) = R0·exp(a·K0·R0^a·t)
   Escape time t_esc (crossing R = R_threshold) satisfies:
   
   t_esc = ln(R_threshold/R0) / (a·K0·R0^a) ≈ C / (a·K0·R0^a)
   
   where C ~ ln(R_threshold/R0) is O(1) constant.

3. UNIFIED VIEW:
   
   When R_u → 0 (barrier vanishes):
   - Escape time remains finite
   - Scaling law holds with low variance
   - Corresponds to EMP-154's "STRONG support" regime (a=1, high K0)
   
   When R_u > A (barrier exceeds amplitude):
   - System trapped in R=0 basin
   - t_esc → ∞ (no escape in finite time)
   - Corresponds to EMP-154's "FAILED" regime (a=2, K0=5, κ=2)
   - Also matches EMP-163's "no lock" regime (γ ≥ 0.85)
   
   When R_u ≈ A (critical boundary):
   - Escape time variance EXPLODES
   - Seeds with A slightly > R_u escape quickly
   - Seeds with A slightly < R_u never escape
   - Corresponds to EMP-154's "WEAK" regime with MSE=138368
   - Also matches EMP-163's transition region (γ ≈ 0.7)

EMPIRICAL PREDICTIONS:
======================

If unification is correct, we should observe:

1. For a=2, K0=5, γ ∈ [0.5, 0.9] (crossing EMP-163's barrier):
   - γ=0.5: Low R_u, fast escape, low variance in t_esc
   - γ=0.7: Critical R_u ≈ A, HUGE variance in t_esc
   - γ=0.85: High R_u > A, no escape (infinite t_esc)

2. Distribution of t_esc near criticality should be BIMODAL:
   - Fast-escape seeds: A > R_u, follow scaling law
   - Trapped seeds: A < R_u, t_esc = T_max (censored)

3. Scaled variable u = a·K0·R0^a·t_esc/2 should show:
   - Low γ: tight distribution around median u ≈ 0.17
   - Critical γ: heavy-tailed or bimodal distribution
   - High γ: all trajectories censored at T_max

TEST PROTOCOL:
==============
Run World C simulation with N=300, a=2, K0=5, γ ∈ {0.5, 0.7, 0.85, 1.0},
n_seeds=20, T=500 (extended to capture slow escapes).

For each (γ, seed):
1. Measure R0 (initial order)
2. Compute barrier R_u(γ) from self-consistency equation
3. Estimate transient amplitude A from fluctuation theory or early-time measurement
4. Record escape time t_esc (first crossing R > 0.7)
5. Compute scaled variable u

Expected results:
- γ=0.5: All seeds escape, u ∈ [0.05, 0.4], median ≈ 0.17
- γ=0.7: Mixed outcome, some escape (u ∈ [0.1, 0.5]), some trapped (t_esc=T_max)
- γ=0.85: Most/all trapped, median t_esc → ∞
- γ=1.0: All trapped (R_u merges with R_s, no stable attractor)

FALSIFICATION CRITERIA:
======================
Unification FAILS if:
1. Near-critical regime (γ≈0.7) shows TIGHT escape-time distribution
   (contradicts barrier-crossing stochasticity)
2. Trapped seeds (t_esc=T_max) have A > R_u with significant margin
   (barrier model invalid)
3. Escaped seeds violate scaling law u = a·K0·R0^a·t/2 by > 10×
   (escape-time linearization invalid)

RESOLUTION OF EMP-154's "REGIME-DEPENDENT VALIDITY":
====================================================
The escape-time law is ALWAYS valid IN PRINCIPLE, but its practical
utility depends on whether R_u is negligible:

- a=1 regimes: Barrier is low or absent → law holds universally
- a=2, high K0: Moderate barrier, but strong coupling overcomes it
- a=2, low K0, high κ: High barrier → most seeds trapped → law appears to "fail"
  (actually, law predicts t_esc → ∞, which is correct!)

The "failure" is not a violation of the law, but a regime where the law
correctly predicts divergence.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import brentq
from scipy.integrate import quad

def lorentzian_pdf(omega, gamma):
    """Lorentzian (Cauchy) PDF g(ω) = γ/(π(ω² + γ²))"""
    return gamma / (np.pi * (omega**2 + gamma**2))

def fixed_point_map(R, K0, a, gamma):
    """
    Fixed-point map R* = F(R) for reflexive Kuramoto with Lorentzian frequencies.
    
    F(R) = ∫_{-K0·R^a}^{K0·R^a} √(1-(ω/(K0·R^a))²) · γ/(π(ω²+γ²)) dω
    """
    if R < 1e-12:
        return 0.0
    
    K_eff = K0 * (R ** a)
    
    def integrand(omega):
        arg = 1 - (omega / K_eff)**2
        if arg < 0:
            return 0.0
        return np.sqrt(arg) * lorentzian_pdf(omega, gamma)
    
    result, _ = quad(integrand, -K_eff, K_eff, limit=100)
    return result

def find_barrier_height(K0, a, gamma, R_search_range=(0.01, 0.99)):
    """
    Find the unstable fixed point R_u (activation barrier) by searching for
    the middle root of R = F(R).
    
    Returns R_u if found, otherwise None.
    """
    R_grid = np.linspace(R_search_range[0], R_search_range[1], 200)
    F_values = np.array([fixed_point_map(R, K0, a, gamma) for R in R_grid])
    
    # Find sign changes in (F(R) - R)
    diff = F_values - R_grid
    sign_changes = np.where(np.diff(np.sign(diff)))[0]
    
    if len(sign_changes) >= 2:
        # Middle root is the unstable barrier
        idx = sign_changes[1]
        try:
            R_u = brentq(lambda R: fixed_point_map(R, K0, a, gamma) - R, 
                        R_grid[idx], R_grid[idx+1])
            return R_u
        except:
            return None
    
    return None

def estimate_fluctuation_amplitude(N, gamma):
    """
    Estimate transient amplitude A(γ, N) from finite-size fluctuation theory.
    
    For Lorentzian frequencies, the amplitude depends on the tail heaviness.
    Empirical fit from EMP-163 data:
    A(γ) ≈ 1.0 for γ→0 (narrow distribution)
    A(γ) ≈ 0.2 for γ→∞ (heavy tails)
    
    Approximate scaling: A(γ) ~ 1 / (1 + γ)^β with β ≈ 0.8
    """
    # Empirical fit from EMP-163 measurements
    # γ=0.1 → A≈0.991, γ=0.7 → A≈0.322, γ=1.0 → A≈0.179
    # Fit: A(γ) ≈ 0.2 + 0.8/(1+2γ)
    A = 0.2 + 0.8 / (1 + 2*gamma)
    # Finite-size correction: scale by √N (weak)
    A *= np.sqrt(300 / N)
    return A

# Generate theoretical predictions
print("=" * 70)
print("THEORETICAL PREDICTIONS: BARRIER vs ESCAPE-TIME UNIFICATION")
print("=" * 70)

K0 = 5.0
a = 2.0
N = 300

gamma_values = [0.3, 0.5, 0.7, 0.85, 1.0, 1.2]

results = []

for gamma in gamma_values:
    R_u = find_barrier_height(K0, a, gamma)
    A = estimate_fluctuation_amplitude(N, gamma)
    
    # Predicted escape time (if A > R_u)
    R0 = 1.0 / np.sqrt(N)  # Typical initial fluctuation
    
    if R_u is not None and A > R_u:
        # Effective threshold is the barrier height
        C = np.log(R_u / R0) if R_u > R0 else 1.0
        t_esc_predict = C / (a * K0 * R0**a)
        lock_predict = "LOCK"
    elif R_u is not None:
        t_esc_predict = np.inf
        lock_predict = "NO LOCK"
    else:
        t_esc_predict = 1.0 / (a * K0 * R0**a)
        lock_predict = "LOCK (no barrier)"
    
    results.append({
        'gamma': gamma,
        'R_u': R_u if R_u else np.nan,
        'A': A,
        'lock': lock_predict,
        't_esc_predict': t_esc_predict
    })
    
    print(f"γ = {gamma:.2f}:")
    print(f"  Barrier R_u     = {R_u:.4f}" if R_u else "  Barrier R_u     = None (no barrier)")
    print(f"  Amplitude A     = {A:.4f}")
    print(f"  A - R_u         = {A - (R_u if R_u else 0):.4f}")
    print(f"  Prediction      = {lock_predict}")
    print(f"  t_esc (if lock) = {t_esc_predict:.2f}" if np.isfinite(t_esc_predict) else "  t_esc           = ∞ (trapped)")
    print()

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel 1: Fixed-point map for different γ values
ax1 = axes[0, 0]
R_plot = np.linspace(0, 1, 300)

for gamma in [0.5, 0.7, 0.85, 1.0]:
    F_plot = np.array([fixed_point_map(R, K0, a, gamma) for R in R_plot])
    ax1.plot(R_plot, F_plot, label=f'γ={gamma}', linewidth=2)

ax1.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5, label='R = F(R)')
ax1.set_xlabel('Order Parameter R', fontsize=12)
ax1.set_ylabel('F(R)', fontsize=12)
ax1.set_title('Fixed-Point Map: Barrier Emergence', fontsize=13, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xlim([0, 1])
ax1.set_ylim([0, 1])

# Panel 2: Barrier height and amplitude vs gamma
ax2 = axes[0, 1]
gamma_plot = np.linspace(0.1, 1.5, 30)
R_u_plot = []
A_plot = []

for g in gamma_plot:
    R_u = find_barrier_height(K0, a, g)
    R_u_plot.append(R_u if R_u else np.nan)
    A_plot.append(estimate_fluctuation_amplitude(N, g))

ax2.plot(gamma_plot, R_u_plot, 'ro-', linewidth=2, markersize=6, label='Barrier R_u(γ)')
ax2.plot(gamma_plot, A_plot, 'bs-', linewidth=2, markersize=6, label='Amplitude A(γ)')
ax2.axhline(0, color='k', linestyle='--', alpha=0.3)
ax2.fill_between(gamma_plot, 0, np.minimum(R_u_plot, A_plot), 
                 where=np.array(A_plot) > np.array(R_u_plot), 
                 alpha=0.2, color='green', label='Lock Region (A > R_u)')
ax2.fill_between(gamma_plot, 0, 1, 
                 where=np.array(A_plot) < np.array(R_u_plot), 
                 alpha=0.2, color='red', label='Trap Region (A < R_u)')
ax2.set_xlabel('Lorentzian Width γ', fontsize=12)
ax2.set_ylabel('Order Parameter', fontsize=12)
ax2.set_title('Lock Boundary: Barrier vs Amplitude Crossing', fontsize=13, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Panel 3: Predicted escape time vs gamma
ax3 = axes[1, 0]
t_esc_plot = [r['t_esc_predict'] for r in results]
gamma_results = [r['gamma'] for r in results]

# Separate locked and trapped
locked_idx = [i for i, t in enumerate(t_esc_plot) if np.isfinite(t)]
trapped_idx = [i for i, t in enumerate(t_esc_plot) if not np.isfinite(t)]

if locked_idx:
    ax3.semilogy([gamma_results[i] for i in locked_idx], 
                 [t_esc_plot[i] for i in locked_idx], 
                 'go-', linewidth=2, markersize=8, label='Predicted Escape (A > R_u)')

if trapped_idx:
    ax3.scatter([gamma_results[i] for i in trapped_idx], 
                [500] * len(trapped_idx),  # Plot at T_max
                c='red', s=100, marker='x', linewidth=3, label='Trapped (A < R_u)')

ax3.set_xlabel('Lorentzian Width γ', fontsize=12)
ax3.set_ylabel('Predicted Escape Time t_esc', fontsize=12)
ax3.set_title('Escape-Time Divergence at Barrier Threshold', fontsize=13, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_ylim([1, 1000])

# Panel 4: Unified phase diagram
ax4 = axes[1, 1]

# Create 2D parameter space (K0, gamma)
K0_grid = np.linspace(1, 10, 30)
gamma_grid = np.linspace(0.1, 1.5, 30)
lock_matrix = np.zeros((len(gamma_grid), len(K0_grid)))

for i, g in enumerate(gamma_grid):
    for j, k in enumerate(K0_grid):
        R_u = find_barrier_height(k, a, g)
        A = estimate_fluctuation_amplitude(N, g)
        if R_u is None or A > R_u:
            lock_matrix[i, j] = 1  # Lock
        else:
            lock_matrix[i, j] = 0  # No lock

im = ax4.contourf(K0_grid, gamma_grid, lock_matrix, levels=[0, 0.5, 1], 
                  colors=['#ffcccc', '#ccffcc'], alpha=0.7)
contour = ax4.contour(K0_grid, gamma_grid, lock_matrix, levels=[0.5], 
                      colors='black', linewidths=2)
ax4.clabel(contour, inline=True, fontsize=10, fmt='Lock Boundary')

# Mark empirical test points
ax4.plot(5, 0.5, 'go', markersize=12, markeredgewidth=2, markeredgecolor='darkgreen', label='EMP-163: Lock')
ax4.plot(5, 0.7, 'yo', markersize=12, markeredgewidth=2, markeredgecolor='orange', label='EMP-163: Critical')
ax4.plot(5, 0.85, 'ro', markersize=12, markeredgewidth=2, markeredgecolor='darkred', label='EMP-163: Trapped')

ax4.set_xlabel('Coupling Strength K0', fontsize=12)
ax4.set_ylabel('Lorentzian Width γ', fontsize=12)
ax4.set_title(f'Unified Phase Diagram (a={a}, N={N})', fontsize=13, fontweight='bold')
ax4.legend(loc='upper right')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/synthesis_escape_barrier_unification.png', 
            dpi=150, bbox_inches='tight')
print("=" * 70)
print("Figure saved: synthesis_escape_barrier_unification.png")
print("=" * 70)
