#!/usr/bin/env python3
"""Independent verification of the correct Adler ceiling value.

DeepSeek's SYN-039 claims:
1. The correct Adler ceiling is C = (δ_hi - δ_lo)/δ_hi = 316/763 ≈ 0.414155
2. PRF-015's ceiling (δ_hi - δ_lo)/(δ_hi - δ_lo + 1) = 0.4293 is WRONG because it incorrectly assumes the locked region and intermediate band overlap.

Let me verify both analytically and numerically.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def adler_order_parameter(delta):
    """Adler order parameter R(δ) = δ - sqrt(δ² - 1) for δ > 1, and R = 1 for δ <= 1."""
    if isinstance(delta, np.ndarray):
        R = np.ones_like(delta)
        mask = delta > 1.0
        R[mask] = delta[mask] - np.sqrt(delta[mask]**2 - 1)
        return R
    else:
        if delta <= 1.0:
            return 1.0
        else:
            return delta - np.sqrt(delta**2 - 1)

def delta_from_R(R):
    """Inverse: δ = (R² + 1)/(2R) for R ∈ (0, 1]."""
    return (R**2 + 1) / (2 * R)

def band_frac_numerical(K_eff, Delta_omega_max, R_lo=0.3, R_hi=0.7):
    """Compute band_frac for given K_eff numerically."""
    # Intermediate band: R ∈ [R_lo, R_hi]
    # In terms of δ: [δ_lo, δ_hi] where δ_lo corresponds to R_hi and δ_hi corresponds to R_lo
    delta_lo = delta_from_R(R_hi)  # δ where R = R_hi (upper boundary)
    delta_hi = delta_from_R(R_lo)  # δ where R = R_lo (lower boundary)
    
    # Intermediate band in Δω space: [2K_eff * δ_lo, 2K_eff * δ_hi]
    omega_lo = 2 * K_eff * delta_lo
    omega_hi = 2 * K_eff * delta_hi
    
    # Locked region: [0, 2K_eff]
    omega_locked = 2 * K_eff
    
    # Check if intermediate band fits within parameter range
    if omega_hi > Delta_omega_max:
        # Band extends beyond range - fraction is reduced
        actual_omega_hi = Delta_omega_max
        if omega_lo >= Delta_omega_max:
            return 0.0  # Band is entirely outside range
        band_width = actual_omega_hi - omega_lo
    else:
        band_width = omega_hi - omega_lo
    
    # Band fraction
    band_frac = band_width / Delta_omega_max
    
    return band_frac

def main():
    R_lo, R_hi = 0.3, 0.7
    
    # Analytical values
    delta_lo = delta_from_R(R_hi)
    delta_hi = delta_from_R(R_lo)
    
    print("=" * 70)
    print("ADLER CEILING VERIFICATION")
    print("=" * 70)
    print()
    print(f"Band definition: R ∈ [{R_lo}, {R_hi}]")
    print(f"δ_lo = (R_hi² + 1)/(2*R_hi) = ({R_hi}² + 1)/(2*{R_hi}) = {delta_lo:.6f}")
    print(f"δ_hi = (R_lo² + 1)/(2*R_lo) = ({R_lo}² + 1)/(2*{R_lo}) = {delta_hi:.6f}")
    print()
    
    # PRF-015's formula (assuming overlap)
    prf015_ceiling = (delta_hi - delta_lo) / (delta_hi - delta_lo + 1)
    print(f"PRF-015 formula: (δ_hi - δ_lo)/(δ_hi - δ_lo + 1) = {prf015_ceiling:.6f}")
    
    # DeepSeek's formula (no overlap constraint)
    deepseek_ceiling = (delta_hi - delta_lo) / delta_hi
    print(f"DeepSeek formula: (δ_hi - δ_lo)/δ_hi = {deepseek_ceiling:.6f}")
    print(f"DeepSeek exact: 316/763 = {316/763:.6f}")
    print()
    
    # Check if locked region and intermediate band are disjoint
    print("Region analysis at optimal K_eff:")
    print(f"  Locked region: [0, 2K_eff]")
    print(f"  Intermediate band: [2K_eff * δ_lo, 2K_eff * δ_hi]")
    print(f"  Since δ_lo = {delta_lo:.4f} > 1, the band starts AFTER 2K_eff")
    print(f"  So locked region [0, 2K_eff] and band [2K_eff*{delta_lo:.4f}, ...] are DISJOINT")
    print()
    
    # Numerical verification
    Delta_omega_max_values = [10, 20, 50, 100, 200, 1000]
    
    print("Numerical verification across Δω_max values:")
    print("-" * 50)
    
    for Delta_omega_max in Delta_omega_max_values:
        # Sweep K_eff
        K_eff_values = np.linspace(0.01, Delta_omega_max / 2, 10000)
        bf_values = np.array([band_frac_numerical(K, Delta_omega_max, R_lo, R_hi) for K in K_eff_values])
        
        max_bf = np.max(bf_values)
        optimal_K = K_eff_values[np.argmax(bf_values)]
        
        # Theoretical optimal K_eff from DeepSeek
        K_opt_deepseek = Delta_omega_max / (2 * delta_hi)
        
        print(f"  Δω_max = {Delta_omega_max:6.1f}: max band_frac = {max_bf:.6f}, "
              f"K_eff* = {optimal_K:.3f} (DeepSeek predicts {K_opt_deepseek:.3f})")
    
    print()
    
    # Create visualization
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot 1: R(δ) curve with band highlighted
    ax = axes[0]
    delta_range = np.linspace(1.0, 3.0, 1000)
    R_values = adler_order_parameter(delta_range)
    
    ax.plot(delta_range, R_values, 'b-', linewidth=2, label='R(δ) = δ - √(δ²-1)')
    ax.axhline(y=R_lo, color='r', linestyle='--', alpha=0.7, label=f'R_lo = {R_lo}')
    ax.axhline(y=R_hi, color='g', linestyle='--', alpha=0.7, label=f'R_hi = {R_hi}')
    ax.axvline(x=delta_lo, color='g', linestyle=':', alpha=0.7, label=f'δ_lo = {delta_lo:.3f}')
    ax.axvline(x=delta_hi, color='r', linestyle=':', alpha=0.7, label=f'δ_hi = {delta_hi:.3f}')
    
    # Shade intermediate band
    mask = (delta_range >= delta_lo) & (delta_range <= delta_hi)
    ax.fill_between(delta_range[mask], R_lo, R_hi, alpha=0.3, color='yellow', label='Intermediate band')
    
    ax.set_xlabel('δ = Δω/(2K_eff)', fontsize=12)
    ax.set_ylabel('R', fontsize=12)
    ax.set_title('Adler Order Parameter', fontsize=14)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    # Plot 2: Band fraction vs K_eff
    ax = axes[1]
    Delta_omega_max = 50
    K_eff_values = np.linspace(0.01, Delta_omega_max / 2, 1000)
    bf_values = np.array([band_frac_numerical(K, Delta_omega_max, R_lo, R_hi) for K in K_eff_values])
    
    ax.plot(K_eff_values, bf_values, 'b-', linewidth=2, label='Numerical band_frac')
    ax.axhline(y=deepseek_ceiling, color='r', linestyle='--', linewidth=2, 
               label=f'DeepSeek ceiling = {deepseek_ceiling:.4f}')
    ax.axhline(y=prf015_ceiling, color='g', linestyle=':', linewidth=2,
               label=f'PRF-015 ceiling = {prf015_ceiling:.4f}')
    
    # Mark optimal K_eff
    max_idx = np.argmax(bf_values)
    ax.plot(K_eff_values[max_idx], bf_values[max_idx], 'ko', markersize=10, 
            label=f'Max = {bf_values[max_idx]:.4f} at K_eff = {K_eff_values[max_idx]:.2f}')
    
    # Mark DeepSeek's predicted optimal
    K_opt_ds = Delta_omega_max / (2 * delta_hi)
    ax.axvline(x=K_opt_ds, color='r', linestyle=':', alpha=0.5, label=f'K_eff* (DS) = {K_opt_ds:.2f}')
    
    ax.set_xlabel('K_eff', fontsize=12)
    ax.set_ylabel('band_frac', fontsize=12)
    ax.set_title(f'Band Fraction vs K_eff (Δω_max = {Delta_omega_max})', fontsize=14)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 0.5)
    
    # Plot 3: Scale invariance test
    ax = axes[2]
    Delta_omega_max_values = [10, 20, 50, 100, 200]
    max_band_fracs = []
    
    for Delta_omega_max in Delta_omega_max_values:
        K_eff_values = np.linspace(0.01, Delta_omega_max / 2, 5000)
        bf_values = np.array([band_frac_numerical(K, Delta_omega_max, R_lo, R_hi) for K in K_eff_values])
        max_band_fracs.append(np.max(bf_values))
    
    ax.plot(Delta_omega_max_values, max_band_fracs, 'bo-', linewidth=2, markersize=8, label='Numerical max')
    ax.axhline(y=deepseek_ceiling, color='r', linestyle='--', linewidth=2,
               label=f'DeepSeek = {deepseek_ceiling:.6f}')
    ax.axhline(y=prf015_ceiling, color='g', linestyle=':', linewidth=2,
               label=f'PRF-015 = {prf015_ceiling:.6f}')
    
    ax.set_xlabel('Δω_max', fontsize=12)
    ax.set_ylabel('Maximum band_frac', fontsize=12)
    ax.set_title('Scale Invariance of Adler Ceiling', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.40, 0.44)
    
    plt.tight_layout()
    output_path = 'shared_agora/artifacts/adler_ceiling_independent_verification.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Figure saved to: {output_path}")
    plt.close()
    
    # Final verdict
    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    
    # Check if numerical results match DeepSeek's formula
    tolerance = 0.001
    if abs(max_band_fracs[-1] - deepseek_ceiling) < tolerance:
        print(f"✓ DeepSeek's ceiling ({deepseek_ceiling:.6f}) CONFIRMED numerically")
        print(f"✗ PRF-015's ceiling ({prf015_ceiling:.6f}) is INCORRECT")
        print()
        print("ROOT CAUSE: PRF-015 incorrectly assumed band_frac + locked_frac ≤ 1")
        print("Since δ_lo > 1, the locked region [0, 2K_eff] and intermediate band")
        print("[2K_eff·δ_lo, 2K_eff·δ_hi] are DISJOINT, so the constraint is invalid.")
        print()
        print("CORRECT CONSTRAINT: Only 2K_eff·δ_hi ≤ Δω_max (band must fit)")
        print(f"This gives: band_frac_max = (δ_hi - δ_lo)/δ_hi = {deepseek_ceiling:.6f}")
    else:
        print("⚠ Discrepancy detected - further analysis needed")
    
    return max_band_fracs, deepseek_ceiling, prf015_ceiling

if __name__ == '__main__':
    main()
