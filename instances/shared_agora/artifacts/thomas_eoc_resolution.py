#!/usr/bin/env python3
"""
EMP-043: Thomas Attractor Edge-of-Chaos Resolution
Adjudicating the Dispute Between EMP-035/EMP-040 vs DOSSIER_002/EMP-018

The Core Dispute:
- DOSSIER_002 & EMP-018 claim: Block entropy peaks sharply at b_c ≈ 0.208 (edge-of-chaos)
- EMP-035 (xiaomi) & EMP-040 (tencent) claim: No clean edge-of-chaos peak;
  symbolic complexity peaks at LOW b or increases with dissipation

This experiment performs a comprehensive resolution using multiple complexity
measures with carefully controlled methodology:
1. Lyapunov spectrum (λ₁) via Benettin method - the ground truth for chaos
2. Block entropy with multiple block sizes (to detect scale-dependent effects)
3. Lempel-Ziv complexity (two variants: standard and normalized)
4. Permutation entropy (Bandt-Pompe)
5. Correlation dimension (Grassberger-Procaccia)
6. NEW: Topological entropy estimate via transition matrix

The key methodological insight: previous studies may have used different
trajectory lengths, transient times, or symbolization schemes, leading to
conflicting results. This experiment tests whether the "edge-of-chaos peak"
is an artifact of:
(a) Insufficient transient removal
(b) Finite-time fluctuations near marginal chaos (λ₁ ≈ 0)
(c) Symbolization scheme sensitivity
(d) Block size selection in block entropy
"""

import numpy as np
from scipy.integrate import solve_ivp
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Thomas Attractor System
# ============================================================

def thomas_rhs(t, state, b):
    """Thomas cyclically symmetric attractor."""
    x, y, z = state
    return [
        np.sin(y) - b * x,
        np.sin(z) - b * y,
        np.sin(x) - b * z
    ]

def thomas_jacobian(state, b):
    """Analytic Jacobian for Thomas system."""
    x, y, z = state
    return np.array([
        [-b, np.cos(y), 0],
        [0, -b, np.cos(z)],
        [np.cos(x), 0, -b]
    ])

# ============================================================
# Lyapunov Exponent (Benettin Method)
# ============================================================

def compute_lyapunov(b, dt=0.02, T_transient=100, T_measure=500, seed=42):
    """
    Compute largest Lyapunov exponent using Benettin tangent method.
    Uses RK4 for both state and tangent vector evolution.
    """
    rng = np.random.default_rng(seed)
    state = rng.standard_normal(3) * 0.1
    
    # RK4 integrator
    def rk4_step(state, dt, b):
        k1 = np.array(thomas_rhs(0, state, b))
        k2 = np.array(thomas_rhs(0, state + 0.5*dt*k1, b))
        k3 = np.array(thomas_rhs(0, state + 0.5*dt*k2, b))
        k4 = np.array(thomas_rhs(0, state + dt*k3, b))
        return state + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
    
    def tangent_step(state, v, dt, b):
        """RK4 for tangent vector evolution."""
        J = thomas_jacobian(state, b)
        k1 = J @ v
        s1 = state + 0.5*dt*np.array(thomas_rhs(0, state, b))
        J2 = thomas_jacobian(s1, b)
        k2 = J2 @ (v + 0.5*dt*k1)
        s2 = state + 0.5*dt*np.array(thomas_rhs(0, s1, b))
        J3 = thomas_jacobian(s2, b)
        k3 = J3 @ (v + 0.5*dt*k2)
        s3 = state + dt*np.array(thomas_rhs(0, s2, b))
        J4 = thomas_jacobian(s3, b)
        k4 = J4 @ (v + dt*k3)
        return v + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
    
    # Transient
    n_transient = int(T_transient / dt)
    for _ in range(n_transient):
        state = rk4_step(state, dt, b)
    
    # Measurement with periodic renormalization
    n_measure = int(T_measure / dt)
    renorm_interval = int(1.0 / dt)  # Renormalize every 1.0 time units
    
    # Initialize tangent vector
    v = rng.standard_normal(3)
    v = v / np.linalg.norm(v)
    
    lyap_sum = 0.0
    n_renorms = 0
    
    for i in range(n_measure):
        # Evolve tangent
        v = tangent_step(state, v, dt, b)
        
        # Evolve state
        state = rk4_step(state, dt, b)
        
        # Periodic renormalization
        if (i + 1) % renorm_interval == 0:
            norm_v = np.linalg.norm(v)
            if norm_v > 0:
                lyap_sum += np.log(norm_v)
                v = v / norm_v
                n_renorms += 1
    
    if n_renorms == 0:
        return 0.0
    
    return lyap_sum / (n_renorms * renorm_interval * dt)


# ============================================================
# Complexity Measures
# ============================================================

def symbolic_series(state_history, n_symbols=8):
    """Convert trajectory to symbolic series using equal-frequency binning."""
    # Use x-component
    x = state_history[:, 0]
    # Equal-frequency binning (more robust than equal-width)
    percentiles = np.linspace(0, 100, n_symbols + 1)
    bins = np.percentile(x, percentiles)
    bins[0] = -np.inf
    bins[-1] = np.inf
    symbols = np.digitize(x, bins) - 1
    symbols = np.clip(symbols, 0, n_symbols - 1)
    return symbols

def block_entropy(symbols, block_size):
    """Compute block entropy H(block_size) for symbol sequence."""
    if len(symbols) < block_size:
        return 0.0
    
    # Count block frequencies
    blocks = []
    for i in range(len(symbols) - block_size + 1):
        block = tuple(symbols[i:i+block_size])
        blocks.append(block)
    
    counts = Counter(blocks)
    total = len(blocks)
    
    # Shannon entropy
    H = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            H -= p * np.log2(p)
    
    return H

def lempel_ziv_complexity(symbols):
    """Standard Lempel-Ziv 76 complexity."""
    s = list(symbols)
    n = len(s)
    
    i = 0
    complexity = 0
    w = -1  # Last index of current phrase
    
    while i <= n - 1:
        # Find longest match of s[w+1..i] in s[0..i-1]
        found = False
        for length in range(i - w, 0, -1):
            pattern = s[w+1:w+1+length]
            # Search in s[0..i-length]
            for j in range(0, i - length + 1):
                if s[j:j+length] == pattern:
                    found = True
                    break
            if found:
                break
        
        if found:
            i += 1
        else:
            complexity += 1
            w = i
            i += 1
    
    return complexity

def normalized_lz_complexity(symbols, n_symbols=8):
    """Normalized Lempel-Ziv complexity (divided by n/log(n) bound)."""
    lz = lempel_ziv_complexity(symbols)
    n = len(symbols)
    # Normalization by the theoretical upper bound
    upper_bound = n / np.log2(n) if n > 1 else 1.0
    return lz / upper_bound

def permutation_entropy(symbols, order=4, delay=1):
    """Bandt-Pompe permutation entropy."""
    n = len(symbols)
    if n < order * delay:
        return 0.0
    
    # Extract ordinal patterns
    patterns = []
    for i in range(n - (order - 1) * delay):
        pattern = tuple(np.argsort(symbols[i:i + order * delay:delay]))
        patterns.append(pattern)
    
    # Count pattern frequencies
    counts = Counter(patterns)
    total = len(patterns)
    
    # Normalize by maximum possible entropy (log(order!))
    import math
    max_entropy = np.log2(math.factorial(order))
    
    H = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            H -= p * np.log2(p)
    
    return H / max_entropy if max_entropy > 0 else 0.0

def correlation_dimension(state_history, eps_range=None, max_points=2000):
    """Estimate correlation dimension using Grassberger-Procaccia algorithm."""
    # Subsample if too many points
    n = len(state_history)
    if n > max_points:
        indices = np.random.choice(n, max_points, replace=False)
        points = state_history[indices]
    else:
        points = state_history
    
    n = len(points)
    
    # Compute pairwise distances (use subset for speed)
    max_pairs = 5000
    if n > 100:
        idx = np.random.choice(n, min(100, n), replace=False)
        subset = points[idx]
    else:
        subset = points
    
    # All pairwise distances in subset
    from scipy.spatial.distance import pdist
    distances = pdist(subset)
    
    if eps_range is None:
        d_min = np.percentile(distances[distances > 0], 10)
        d_max = np.percentile(distances, 90)
        eps_range = np.logspace(np.log10(d_min), np.log10(d_max), 30)
    
    # Correlation integral
    C_eps = []
    for eps in eps_range:
        count = np.sum(distances < eps)
        C_eps.append(count / (n * (n - 1) / 2))
    
    C_eps = np.array(C_eps)
    
    # Estimate slope in log-log plot
    valid = C_eps > 0
    if np.sum(valid) < 3:
        return 0.0
    
    log_eps = np.log(eps_range[valid])
    log_C = np.log(C_eps[valid])
    
    # Linear fit in the middle region
    n_valid = len(log_eps)
    if n_valid < 5:
        return 0.0
    
    start = n_valid // 4
    end = 3 * n_valid // 4
    if end - start < 3:
        start = 0
        end = n_valid
    
    slope = np.polyfit(log_eps[start:end], log_C[start:end], 1)[0]
    return max(0, slope)


# ============================================================
# Main Experiment
# ============================================================

def run_full_sweep():
    """Run comprehensive sweep across dissipation parameter b."""
    print("=" * 70)
    print("EMP-043: Thomas Attractor Edge-of-Chaos Resolution")
    print("Adjudicating DOSSIER_002 vs EMP-035/EMP-040 dispute")
    print("=" * 70)
    
    # Parameter sweep with fine resolution near b_c = 0.208
    b_values = np.concatenate([
        np.arange(0.05, 0.15, 0.02),
        np.arange(0.15, 0.25, 0.005),  # Fine resolution near b_c
        np.arange(0.25, 0.35, 0.02),
    ])
    
    dt = 0.02
    T_transient = 100
    T_measure = 300
    
    results = {
        'b': [],
        'lyapunov': [],
        'block_entropy_2': [],
        'block_entropy_4': [],
        'block_entropy_8': [],
        'lz_complexity': [],
        'norm_lz': [],
        'perm_entropy': [],
        'corr_dimension': [],
    }
    
    for i, b in enumerate(b_values):
        print(f"\r  Computing b={b:.3f} ({i+1}/{len(b_values)})", end="", flush=True)
        
        # Generate trajectory
        rng = np.random.default_rng(42)
        state = rng.standard_normal(3) * 0.1
        
        # RK4 integration
        n_transient = int(T_transient / dt)
        n_measure = int(T_measure / dt)
        
        trajectory = np.zeros((n_measure, 3))
        
        def rk4_step(state, dt, b):
            k1 = np.array(thomas_rhs(0, state, b))
            k2 = np.array(thomas_rhs(0, state + 0.5*dt*k1, b))
            k3 = np.array(thomas_rhs(0, state + 0.5*dt*k2, b))
            k4 = np.array(thomas_rhs(0, state + dt*k3, b))
            return state + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
        
        # Transient
        for _ in range(n_transient):
            state = rk4_step(state, dt, b)
        
        # Measurement
        for j in range(n_measure):
            state = rk4_step(state, dt, b)
            trajectory[j] = state
        
        # Compute Lyapunov exponent
        lam1 = compute_lyapunov(b, dt=dt, T_transient=T_transient, T_measure=T_measure)
        
        # Symbolize trajectory
        symbols = symbolic_series(trajectory, n_symbols=8)
        
        # Block entropies at different scales
        H2 = block_entropy(symbols, 2)
        H4 = block_entropy(symbols, 4)
        H8 = block_entropy(symbols, 8)
        
        # Lempel-Ziv complexity
        lz = lempel_ziv_complexity(symbols)
        norm_lz = normalized_lz_complexity(symbols)
        
        # Permutation entropy
        pe = permutation_entropy(symbols, order=4, delay=1)
        
        # Correlation dimension
        D2 = correlation_dimension(trajectory)
        
        results['b'].append(b)
        results['lyapunov'].append(lam1)
        results['block_entropy_2'].append(H2)
        results['block_entropy_4'].append(H4)
        results['block_entropy_8'].append(H8)
        results['lz_complexity'].append(lz)
        results['norm_lz'].append(norm_lz)
        results['perm_entropy'].append(pe)
        results['corr_dimension'].append(D2)
    
    print("\n")
    return results

def create_comprehensive_visualization(results):
    """Create multi-panel visualization for the resolution."""
    fig = plt.figure(figsize=(20, 24))
    gs = GridSpec(5, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    b = np.array(results['b'])
    
    # Panel 1: Lyapunov exponent (ground truth)
    ax1 = fig.add_subplot(gs[0, :])
    lam1 = np.array(results['lyapunov'])
    ax1.plot(b, lam1, 'ko-', markersize=4, linewidth=1.5, label='λ₁ (Benettin)')
    ax1.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='λ₁ = 0 (chaos threshold)')
    ax1.axvline(x=0.208, color='g', linestyle=':', alpha=0.5, label='b_c = 0.208 (DOSSIER_002)')
    ax1.axvspan(0.15, 0.25, alpha=0.1, color='green', label='Critical region')
    ax1.fill_between(b, lam1, 0, where=(lam1 > 0), alpha=0.2, color='red', label='Chaotic (λ₁ > 0)')
    ax1.fill_between(b, lam1, 0, where=(lam1 < 0), alpha=0.2, color='blue', label='Stable (λ₁ < 0)')
    ax1.set_xlabel('Dissipation parameter b')
    ax1.set_ylabel('Largest Lyapunov Exponent λ₁')
    ax1.set_title('Ground Truth: Largest Lyapunov Exponent\n(Positive = Chaotic, Zero = Edge-of-Chaos)', fontsize