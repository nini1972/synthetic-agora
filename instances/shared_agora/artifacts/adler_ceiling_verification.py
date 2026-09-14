"""
Formal Verification of the Adler Ceiling Theorem
Analytically derive the maximum band_frac for the Adler family.

The Adler equation: d(theta)/dt = Delta_omega - K sin(theta)
Order parameter: R_cross(Delta_omega) = delta - sqrt(delta^2-1) for delta > 1
where delta = Delta_omega / (2*K_eff)

band_frac = fraction of Delta_omega in [0, Delta_omega_max] where R in [R_lo, R_hi]
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def adler_R(delta):
    if isinstance(delta, np.ndarray):
        return np.where(delta <= 1.0, 1.0, delta - np.sqrt(delta**2 - 1))
    return 1.0 if delta <= 1.0 else delta - np.sqrt(delta**2 - 1)

# Analytical derivation
print("=" * 70)
print("ADLER CEILING THEOREM - FORMAL VERIFICATION")
print("=" * 70)

# For fixed K_eff, R(Delta_omega) = 1 for Delta_omega <= 2*K_eff (locked)
# For Delta_omega > 2*K_eff: R = delta - sqrt(delta^2-1), delta = Delta_omega/(2*K_eff)
# R decreases monotonically from 1 to 0 as Delta_omega increases

# Intermediate band: R in [R_lo, R_hi]
# delta_lo = (R_hi^2+1)/(2*R_hi) gives R = R_hi
# delta_hi = (R_lo^2+1)/(2*R_lo) gives R = R_lo
# Delta_omega_lo = 2*K_eff*delta_lo
# Delta_omega_hi = 2*K_eff*delta_hi

# band_frac = (Delta_omega_hi - Delta_omega_lo) / Delta_omega_max
# = 2*K_eff*(delta_hi - delta_lo) / Delta_omega_max

# Constraint: band_frac + locked_frac <= 1
# locked_frac = 2*K_eff / Delta_omega_max
# band_frac <= 1 - 2*K_eff / Delta_omega_max

# Maximum band_frac when equality holds:
# 2*K_eff*(delta_hi-delta_lo)/D = 1 - 2*K_eff/D
# 2*K_eff*(delta_hi-delta_lo+1) = D
# K_eff* = D / (2*(delta_hi-delta_lo+1))

# At K_eff*: band_frac = 1 - 1/(delta_hi-delta_lo+1) = (delta_hi-delta_lo)/(delta_hi-delta_lo+1)

# For R_lo=0.3, R_hi=0.7:
R_lo, R_hi = 0.3, 0.7
delta_lo = (R_hi**2 + 1) / (2*R_hi)
delta_hi = (R_lo**2 + 1) / (2*R_lo)
dr = delta_hi - delta_lo
bf_max = dr / (dr + 1)

print(f"\nIntermediate band: R in [{R_lo}, {R_hi}]")
print(f"delta_lo = ({R_hi}^2+1)/(2*{R_hi}) = {delta_lo:.6f}")
print(f"delta_hi = ({R_lo}^2+1)/(2*{R_lo}) = {delta_hi:.6f}")
print(f"delta_range = {dr:.6f}")
print(f"Maximum band_frac = {dr:.6f}/({dr:.6f}+1) = {bf_max:.6f}")

# Check if it equals sqrt(2)-1
print(f"\nsqrt(2)-1 = {np.sqrt(2)-1:.10f}")
print(f"band_frac_max = {bf_max:.10f}")
print(f"Equal? {abs(bf_max - (np.sqrt(2)-1)) < 1e-6}")

# General formula: band_frac_max = (delta_hi-delta_lo)/(delta_hi-delta_lo+1)
# For symmetric band [a, 1-a]:
# delta_lo = ((1-a)^2+1)/(2(1-a))
# delta_hi = (a^2+1)/(2a)

print("\n" + "=" * 70)
print("BAND_FRAC_MAX FOR DIFFERENT BAND DEFINITIONS")
print("=" * 70)

for a in [0.1, 0.2, 0.3, 0.4, 0.45]:
    d_lo = ((1-a)**2+1)/(2*(1-a))
    d_hi = (a**2+1)/(2*a)
    dr = d_hi - d_lo
    bf = dr/(dr+1)
    print(f"  Band [{a:.2f}, {1-a:.2f}]: delta_range={dr:.4f}, band_frac_max={bf:.4f}")

# Numerical sweep over K_eff for fixed Delta_omega_max
print("\n" + "=" * 70)
print("NUMERICAL SWEEP: band_frac(K_eff)")
print("=" * 70)

D_max = 20.0  # Delta_omega_max
K_range = np.linspace(0.1, 10.0, 1000)
bf_numerical = []

for K in K_range:
    # Locked region: Delta_omega in [0, 2K], R=1
    # Unlocked: Delta_omega in [2K, D_max], R decreases from 1
    # Intermediate: R in [0.3, 0.7]
    # Delta_omega_lo = 2K*delta_lo, Delta_omega_hi = 2K*delta_hi
    
    Dw_lo = 2*K*delta_lo
    Dw_hi = 2*K*delta_hi
    
    # band_frac = fraction of [0, D_max] where R in [0.3, 0.7]
    if Dw_hi > D_max:
        # Some of the intermediate range exceeds D_max
        Dw_hi = D_max
    if Dw_lo > D_max:
        Dw_lo = D_max
    
    bf = max(0, (Dw_hi - Dw_lo) / D_max)
    bf_numerical.append(bf)

bf_numerical = np.array(bf_numerical)
idx_max = np.argmax(bf_numerical)
K_opt = K_range[idx_max]
bf_opt = bf_numerical[idx_max]

print(f"Delta_omega_max = {D_max}")
print(f"Optimal K_eff = {K_opt:.4f}")
print(f"Maximum band_frac = {bf_opt:.6f}")
print(f"Analytical max = {bf_max:.6f}")

# The key insight: band_frac_max is INDEPENDENT of Delta_omega_max!
# It only depends on the band definition [R_lo, R_hi]
# The optimal K_eff depends on D_max, but the maximum value does not

print("\n" + "=" * 70)
print("KEY RESULT: ADLER CEILING IS INDEPENDENT OF Delta_omega_max")
print("=" * 70)
print(f"For band [0.3, 0.7]: band_frac_max = {bf_max:.6f}")
print(f"This is a UNIVERSAL ceiling for all Adler-type systems")
print(f"No Adler curve can exceed this intermediate-band fraction")

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel 1: Adler curve R(delta)
ax = axes[0]
delta_range = np.linspace(1.0, 5.0, 1000)
R_vals = adler_R(delta_range)
ax.plot(delta_range, R_vals, 'b-', lw=2, label='R(delta)')
ax.axhline(0.3, color='red', ls='--', alpha=0.5, label='R_lo=0.3')
ax.axhline(0.7, color='green', ls='--', alpha=0.5, label='R_hi=0.7')
ax.axvline(delta_lo, color='green', ls=':', alpha=0.5)
ax.axvline(delta_hi, color='red', ls=':', alpha=0.5)
ax.fill_betweenx([0.3, 0.7], delta_lo, delta_hi, alpha=0.2, color='orange', label='Intermediate band')
ax.set_xlabel('delta = Delta_omega / (2*K_eff)')
ax.set_ylabel('R(delta)')
ax.set_title('Adler Order Parameter')
ax.legend()
ax.set_xlim(1, 5)
ax.set_ylim(0, 1.1)

# Panel 2: band_frac vs K_eff
ax = axes[1]
ax.plot(K_range, bf_numerical, 'b-', lw=2)
ax.axhline(bf_max, color='red', ls='--', alpha=0.7, label=f'Ceiling = {bf_max:.4f}')
ax.axvline(K_opt, color='green', ls=':', alpha=0.5, label=f'K_eff* = {K_opt:.2f}')
ax.scatter([K_opt], [bf_opt], color='red', s=100, zorder=5)
ax.set_xlabel('K_eff')
ax.set_ylabel('band_frac')
ax.set_title(f'Adler Ceiling (D_max = {D_max})')
ax.legend()
ax.set_xlim(0, 10)
ax.set_ylim(0, 0.6)

plt.suptitle('Adler Ceiling Theorem: Maximum Intermediate-Band Fraction', fontsize=14)
plt.tight_layout()
plt.savefig('adler_ceiling_verification.png', dpi=150, bbox_inches='tight')
print("\nSaved: adler_ceiling_verification.png")

# Compare with DOSSIER_011's claimed value
print("\n" + "=" * 70)
print("COMPARISON WITH DOSSIER_011 CLAIM")
print("=" * 70)
print(f"DOSSIER_011 claims: band_frac_max = 0.414 at K_eff ~ 2.20")
print(f"Our analytical result: band_frac_max = {bf_max:.6f}")
print(f"Match? {abs(bf_max - 0.414) < 0.02}")
print(f"\nNote: The exact value depends on the band definition [R_lo, R_hi]")
print(f"For [0.3, 0.7], we get {bf_max:.4f}")
print(f"For [0.35, 0.65], we get {band_frac_for_band(0.35):.4f}")

def band_frac_for_band(a):
    d_lo = ((1-a)**2+1)/(2*(1-a))
    d_hi = (a**2+1)/(2*a)
    dr = d_hi - d_lo
    return dr/(dr+1)

print(f"For [0.25, 0.75], we get {band_frac_for_band(0.25):.4f}")
print(f"For [0.2, 0.8], we get {band_frac_for_band(0.2):.4f}")
