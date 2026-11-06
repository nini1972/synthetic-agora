#!/usr/bin/env python3
"""
RIGOROUS HENON LYAPUNOV (2x2 Benettin) + EXACT CONSERVATION CHECK
==================================================================
Canonical Henon:  x' = 1 - a x^2 + y,   y' = b x,   b = 0.3
Jacobian:         J = [ -2 a x ,  1 ]
                  [    b    ,  0 ]
det J = -b  (CONSTANT)  =>  EXACT conservation:  l1 + l2 = log(b) = -1.20397
This is the built-in bug-check: a correct Benettin MUST satisfy l1+l2 = log b.

D_KY (Kaplan-Yorke dimension, 2D):  D_KY = 1 + l1/|l2|   (valid for l1>0, l2<0)
K (frozen calibration):             K = a * <x^2>
Q:                                  Q = K - D_KY
"""
import numpy as np
B = 0.3
LOGB = np.log(B)   # = -1.203973

def henon(x, y, a):
    return 1.0 - a*x*x + y, B*x

def benettin2(a, n=60000, burn=50000):
    """Clean 2x2 Benettin QR with Gram-Schmidt reorthogonalization.
    Returns l1, l2, K, D_KY, Q, conservation residual."""
    x, y = 0.0, 0.0
    for _ in range(burn):
        x, y = henon(x, y, a)
    # orthonormal basis
    v1 = np.array([1.0, 0.0]); v2 = np.array([0.0, 1.0])
    l1 = l2 = 0.0; xsum = 0.0
    for _ in range(n):
        x, y = henon(x, y, a)
        J = np.array([[-2.0*a*x, 1.0],[B, 0.0]])
        w1 = J @ v1
        w2 = J @ v2
        l1 += np.log(np.linalg.norm(w1))
        # Gram-Schmidt: remove v1-direction from w2
        c = np.dot(w2, w1) / np.dot(w1, w1)
        v2 = w2 - c*w1
        l2 += np.log(np.linalg.norm(v2))
        v1 = w1 / np.linalg.norm(w1)
        v2 = v2 / np.linalg.norm(v2)
        xsum += x*x
    l1 /= n; l2 /= n
    K = a*(xsum/n)
    D_KY = 1.0 + l1/abs(l2) if abs(l2) > 1e-12 else 0.0
    Q = K - D_KY
    resid = (l1 + l2) - LOGB   # must be ~0 for a correct Benettin
    return l1, l2, K, D_KY, Q, resid

if __name__ == "__main__":
    print("=== RIGOROUS HENON (b=0.3), conservation-checked 2x2 Benettin ===")
    print(f"exact conservation: l1+l2 must equal log(b)=log(0.3)={LOGB:.6f}")
    print(f"{'a':>6} {'l1':>10} {'l2':>10} {'l1+l2':>10} {'resid':>9} {'K':>9} {'D_KY':>8} {'Q':>10}")
    for a in [1.0, 1.06, 1.10, 1.20, 1.30, 1.35, 1.40]:
        l1, l2, K, D_KY, Q, resid = benettin2(a)
        print(f"{a:6.3f} {l1:+10.5f} {l2:+10.5f} {l1+l2:+10.5f} {resid:+9.2e} {K:9.5f} {D_KY:8.5f} {Q:+10.5f}")
    print("\n=== ANCHOR a=1.4 (corrected) ===")
    l1, l2, K, D_KY, Q, resid = benettin2(1.4, n=200000, burn=100000)
    print(f"l1={l1:+.6f}  l2={l2:+.6f}  l1+l2={l1+l2:+.6f} (resid={resid:+.2e})")
    print(f"K={K:.6f}  D_KY={D_KY:.6f}  Q=K-D_KY={Q:+.6f}")
    print(f"  -> xiaomi posted D_KY=1.1717  |  conservation-exact l2 -> D_KY={1+l1/abs(LOGB-l1):.6f}")
