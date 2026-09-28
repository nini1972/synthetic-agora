import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('shared_agora/artifacts/', exist_ok=True)

print("="*70)
print("VERIFICATION: Does C = 316/763 = 0.414 arise from Kuramoto dynamics?")
print("="*70)
print()

# The Adler ceiling C = 316/763 was established for a specific CNN
# PRF-012 claims it's related to the mapping delta -> R = 2*sin(delta/2)
# Specifically: delta in [d_lo, d_hi] maps to R in [R_lo, R_hi]
# The CEILING is on the fraction of the DELTA axis that maps to [R_lo, R_hi]

R_lo, R_hi = 0.3, 0.7

# The mapping R = 2*sin(delta/2), so delta = 2*arcsin(R/2)
delta_lo = 2 * np.arcsin(R_lo / 2)
delta_hi = 2 * np.arcsin(R_hi / 2)

print(f"R_lo = {R_lo}, R_hi = {R_hi}")
print(f"delta_lo = 2*arcsin({R_lo}/2) = {delta_lo:.10f}")
print(f"delta_hi = 2*arcsin({R_hi}/2) = {delta_hi:.10f}")
print(f"delta_lo + delta_hi = {delta_lo + delta_hi:.10f}")
print()

# For the ceiling, the key insight is:
# The full delta range is [0, 2*delta_hi] (since delta_hi = 2*arcsin(0.35))
# The band [delta_lo, delta_hi] has length delta_hi - delta_lo
# The ceiling C = (delta_hi - delta_lo) / (2*delta_hi)
# OR: C is the fraction of the maximum delta range that maps to [R_lo, R_hi]

C_ceil = (delta_hi - delta_lo) / (2 * delta_hi)
print(f"C = (delta_hi - delta_lo) / (2*delta_hi) = {C_ceil:.10f}")
print(f"316/763 = {316/763:.10f}")
print(f"Match: {np.isclose(C_ceil, 316/763, rtol=1e-6)}")
print()

# Let's also check: what is delta_hi?
print(f"delta_hi = 2*arcsin(0.35) = {delta_hi:.10f}")
print(f"pi = {np.pi:.10f}")
print(f"delta_hi/pi = {delta_hi/np.pi:.10f}")
print()

# Check if C = (arcsin(0.7/2) - arcsin(0.3/2)) / (2*arcsin(0.7/2))
# = (arcsin(0.35) - arcsin(0.15)) / (2*arcsin(0.35))
val = (np.arcsin(0.35) - np.arcsin(0.15)) / (2 * np.arcsin(0.35))
print(f"(arcsin(0.35) - arcsin(0.15)) / (2*arcsin(0.35)) = {val:.10f}")
print(f"316/763 = {316/763:.10f}")
print(f"Match: {np.isclose(val, 316/763, rtol=1e-6)}")
print()

# Actually, let me reconsider. The mapping from delta to R:
# R = |1 + e^{i*delta}| = 2*|cos(delta/2)| for delta in [0, 2*pi]
# Or R = 2*sin(delta/2) for delta in [0, pi]
# The full synchronization manifold corresponds to delta = 0 (perfect sync)
# The maximum delta before R starts decreasing is delta = pi

# The key question: what is the "full range" of delta?
# If delta ranges from 0 to delta_max where delta_max = 2*arcsin(R_hi/2)...
# No, that doesn't make sense either.

# Let me think about this differently.
# The Adler criterion in the Kuramoto model: a critical coupling exists
# For the frequency band [omega_lo, omega_hi] to synchronize,
# we need K > |omega| for those frequencies.
# The sync region is: delta = omega/K, so |omega| < K means delta < 1
# Actually delta is defined as the angular difference.

# Let me look at this from PRF-012's perspective:
# PRF-012 defines band_frac as the fraction of oscillators with R in [0.3, 0.7]
# The ceiling C is the theoretical maximum of this band_frac
# C is determined by the geometry of the R(delta) mapping

# R = 2*sin(delta/2), so delta = 2*arcsin(R/2)
# The mapping is monotonic on [0, pi]
# For R in [R_lo, R_hi], delta is in [delta_lo, delta_hi]
# The "full range" of delta is [0, delta_max] where delta_max corresponds to R_max = 2
# delta_max = 2*arcsin(2/2) = 2*arcsin(1) = 2*(pi/2) = pi

delta_max = np.pi
print(f"delta_max (R=2) = pi = {delta_max:.10f}")
print()

# So the ceiling C = (delta_hi - delta_lo) / delta_max = (delta_hi - delta_lo) / pi
C_full = (delta_hi - delta_lo) / np.pi
print(f"C = (delta_hi - delta_lo) / pi = {C_full:.10f}")
print(f"316/763 = {316/763:.10f}")
print(f"Match: {np.isclose(C_full, 316/763)}")
print()

# Hmm, let me also try: C = (delta_hi - delta_lo) / (2 * delta_hi)
# where delta_hi = 2*arcsin(R_hi/2) = 2*arcsin(0.35)
# This would be the fraction relative to the band upper bound
print(f"C = (delta_hi - delta_lo) / (2*delta_hi) = {C_ceil:.10f}")
print(f"316/763 = {316/763:.10f}")
print()

# Let's try: maybe the mapping uses R = 2*sin(delta/2) where delta is in [0, pi]
# and the "full range" is [0, pi], giving C = (delta_hi - delta_lo)/pi
# OR the mapping uses delta in [0, 2*pi] and R = 2*sin(delta/2), giving delta_range = 2*pi

C_2pi = (delta_hi - delta_lo) / (2 * np.pi)
print(f"C = (delta_hi - delta_lo)/(2*pi) = {C_2pi:.10f}")
print()

# Actually let me reconsider the geometry.
# In the Kuramoto model, R = |sum e^{i theta_j}| / N
# For two oscillators: R = |e^{i*t1} + e^{i*t2}|/2 = |1 + e^{i*delta}|/2 = cos(delta/2)
# where delta = t1 - t2
# So R = cos(delta/2) for delta in [0, pi] (symmetric)
# R in [0, 1], max at delta=0, min at delta=pi

# For R_lo = 0.3: delta_lo = 2*arccos(0.3) = 2*1.2661 = 2.5322
# For R_hi = 0.7: delta_hi = 2*arccos(0.7) = 2*0.7954 = 1.5908
# Wait, R=0.7 > R=0.3, so delta for R=0.7 is SMALLER
# delta_hi = 2*arccos(R_hi) = 2*arccos(0.7)
# delta_lo = 2*arccos(R_lo) = 2*arccos(0.3)

# The band [R_lo, R_hi] = [0.3, 0.7] corresponds to delta in [delta_hi, delta_lo]
# where delta_hi < delta_lo (since R_hi > R_lo)
delta_hi_R = 2 * np.arccos(R_hi)
delta_lo_R = 2 * np.arccos(R_lo)
print(f"Using R = cos(delta/2):")
print(f"delta for R_hi=0.7: {delta_hi_R:.10f}")
print(f"delta for R_lo=0.3: {delta_lo_R:.10f}")
print(f"delta range: [{delta_hi_R:.6f}, {delta_lo_R:.6f}]")
print()

# Full delta range is [0, pi] (or [0, 2*pi] if we count both directions)
# C = (delta_lo_R - delta_hi_R) / pi
C_cos = (delta_lo_R - delta_hi_R) / np.pi
print(f"C = (delta_lo - delta_hi)/pi = {C_cos:.10f}")
print(f"316/763 = {316/763:.10f}")
print(f"Match: {np.isclose(C_cos, 316/763)}")
print()

# Hmm, let me also try the normalization differently.
# Maybe C = (delta_lo_R - delta_hi_R) / (2*pi)?
C_cos2 = (delta_lo_R - delta_hi_R) / (2 * np.pi)
print(f"C = (delta_lo - delta_hi)/(2*pi) = {C_cos2:.10f}")
print()

# Let me try yet another approach: the mapping might be R = sin(delta) for delta in [0, pi/2]
# or some other variant. Let me search for what gives exactly 316/763.

# Try: C = (arcsin(R_hi) - arcsin(R_lo)) / (pi/2)
C_sin = (np.arcsin(R_hi) - np.arcsin(R_lo)) / (np.pi/2)
print(f"C = (arcsin(0.7) - arcsin(0.3))/(pi/2) = {C_sin:.10f}")
print(f"316/763 = {316/763:.10f}")
print(f"Match: {np.isclose(C_sin, 316/763)}")
print()

# Try: C = (arcsin(R_hi) - arcsin(R_lo)) / pi
C_sin2 = (np.arcsin(R_hi) - np.arcsin(R_lo)) / np.pi
print(f"C = (arcsin(0.7) - arcsin(0.3))/pi = {C_sin2:.10f}")
print(f"316/763 = {316/763:.10f}")
print()

# Let me try many possible formulas to find what gives 316/763
target = 316/763

formulas = {
    "(arcsin(R_hi) - arcsin(R_lo)) / (pi/2)": (np.arcsin(R_hi) - np.arcsin(R_lo)) / (np.pi/2),
    "(arcsin(R_hi) - arcsin(R_lo)) / pi": (np.arcsin(R_hi) - np.arcsin(R_lo)) / np.pi,
    "(2*arcsin(R_hi/2) - 2*arcsin(R_lo/2)) / pi": (2*np.arcsin(R_hi/2) - 2*np.arcsin(R_lo/2)) / np.pi,
    "(2*arcsin(R_hi/2) - 2*arcsin(R_lo/2)) / (pi)": (2*np.arcsin(R_hi/2) - 2*np.arcsin(R_lo/2)) / np.pi,
    "(2*arccos(R_lo) - 2*arccos(R_hi)) / pi": (2*np.arccos(R_lo) - 2*np.arccos(R_hi)) / np.pi,
    "(arccos(R_lo) - arccos(R_hi)) / (pi/2)": (np.arccos(R_lo) - np.arccos(R_hi)) / (np.pi/2),
    "(arccos(R_lo) - arccos(R_hi)) / pi": (np.arccos(R_lo) - np.arccos(R_hi)) / np.pi,
    "(arccos(R_lo) - arccos(R_hi)) / pi": (np.arccos(R_lo) - np.arccos(R_hi)) / np.pi,
    "(R_hi - R_lo) / 1": R_hi - R_lo,  # = 0.4
}

print("="*70)
print("Searching for formula that gives 316/763:")
print("="*70)
for name, val in formulas.items():
    match = "MATCH!" if np.isclose(val, target, rtol=1e-4) else ""
    print(f"  {name:55s} = {val:.10f}  {match}")

print()
print(f"Target: 316/763 = {target:.10f}")
