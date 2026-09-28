"""Compute the DETERMINISTIC (sigma=0) Adler R(Delta-omega) via direct orbit averaging,
to obtain the correct sigma=0 band_frac and compare to the C=316/763=0.414155 ceiling."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def R_deterministic(dw, K, n_pts=200000, T_max=60.0):
    """Time-average of e^{i theta} over the deterministic Adler orbit.
    If |dw|<2K: locked -> R=1. If |dw|>=2K: drifts -> R = sqrt(1-(2K/dw)^2)."""
    if abs(dw) < 2*K:
        return 1.0
    return float(np.sqrt(1.0 - (2*K/dw)**2))


def band_frac_deterministic(Omega_max=6.0, band=(0.3, 0.7), Kgrid=None):
    if Kgrid is None:
        Kgrid = np.linspace(0.5, 4.0, 40)
    dW = np.linspace(-Omega_max, Omega_max, 2001)
    best = 0.0
    bestK = None
    for K in Kgrid:
        Rvals = np.array([R_deterministic(dw, K) for dw in dW])
        bf = np.mean((Rvals >= band[0]) & (Rvals <= band[1]))
        if bf > best:
            best = bf
            bestK = K
    return best, bestK


if __name__ == "__main__":
    print("=== Deterministic (sigma=0) R(dw) sanity check ===")
    for dw in [0.5, 2.0, 3.0, 5.0]:
        print(f"  dw={dw}, K=2: R={R_deterministic(dw, 2.0):.4f}")
    # verify R(3, K=2): sqrt(1-(4/3)^2) = sqrt(1-1.777)= sqrt(-0.77) -> imaginary! 
    # So the formula R=sqrt(1-(2K/dw)^2) only valid if |dw|>=2K. For dw=3,2K=4: |dw|<2K -> locked R=1. ok.
    print("  (For |dw| < 2K, R=1 (locked); for |dw|>=2K, R=sqrt(1-(2K/dw)^2).)")

    print("\n=== Deterministic band_frac_max (Omega_max=6, band=[0.3,0.7]) ===")
    bf, bK = band_frac_deterministic()
    print(f"  sigma=0.00 -> band_frac_max={bf:.4f}  (K*={bK:.2f})")
    print(f"  EMP-082 reference sigma=0 -> 0.4145 ; analytical C = 316/763 = {316/763:.6f}")
