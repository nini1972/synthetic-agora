#!/usr/bin/env python3
"""
Fallback Replication of Hénon Q=-2.08 Critical Point (SYN-053).
Local implementation of Hénon map to bypass colony_lib import error.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from numpy import log

# Hénon Map (Local Implementation)
def henon_map(a, b, n, x0, y0):
    x, y = np.zeros(n), np.zeros(n)
    x[0], y[0] = x0, y0
    for i in range(1, n):
        x[i] = 1 - a * x[i-1]**2 + y[i-1]
        y[i] = b * x[i-1]
    return x, y

# Maximal Lyapunov Exponent (Tangent QR)
def lyapunov_max(a, b, x, y, n_tangent=10000):
    n = len(x)
    u, v = np.zeros(n), np.zeros(n)
    u[0], v[0] = 1.0, 0.0
    lyap = 0.0
    for i in range(1, n):
        # Tangent map
        jacobian = np.array([[-2 * a * x[i-1], 1], [b, 0]])
        u_new = jacobian[0, 0] * u[i-1] + jacobian[0, 1] * v[i-1]
        v_new = jacobian[1, 0] * u[i-1] + jacobian[1, 1] * v[i-1]
        # QR decomposition
        norm = np.sqrt(u_new**2 + v_new**2)
        u[i] = u_new / norm
        v[i] = v_new / norm
        lyap += log(norm)
    return lyap / n

# Correlation Dimension (Grassberger-Procaccia)
def correlation_dimension(data, embedding_dim=2, r_min=0.01, r_max=1.0, n_r=10):
    n = len(data)
    distances = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            distances[i, j] = np.linalg.norm(data[i] - data[j])
            distances[j, i] = distances[i, j]
    
    r_values = np.linspace(r_min, r_max, n_r)
    C_r = np.zeros(n_r)
    for k, r in enumerate(r_values):
        C_r[k] = np.sum(distances < r) / (n * (n - 1))
    
    # Fit slope
    mask = (C_r > 0) & (C_r < 1)
    if np.sum(mask) < 2:
        return 0.0
    slope, _ = np.polyfit(log(r_values[mask]), log(C_r[mask]), 1)
    return slope

# Parameters
a = 1.0
b = 0.3
N = 1000
transient = 100
x0, y0 = 0.1, 0.1

# Compute Q
x, y = henon_map(a, b, N + transient, x0, y0)
x, y = x[transient:], y[transient:]

lambda_max = lyapunov_max(a, b, x, y)
D_2 = correlation_dimension(np.column_stack((x, y)))
K = a * np.mean(x**2)
Q = -lambda_max - D_2 - K

# Report
with open('REPORT_henon_q_critical_point_fallback.md', 'w') as f:
    f.write("# Hénon Q=-2.08 Critical Point Replication (SYN-053) - Fallback\n\n")
    f.write("## Parameters\n")
    f.write(f"- a: {a}, b: {b}\n")
    f.write(f"- N: {N}, Transient: {transient}\n\n")
    
    f.write("## Results\n")
    f.write(f"- λ_max: {lambda_max:.6f}\n")
    f.write(f"- D_2: {D_2:.6f}\n")
    f.write(f"- K: {K:.6f}\n")
    f.write(f"- Q: {Q:.6f}\n\n")
    
    f.write("## Interpretation\n")
    if abs(Q + 2.08) < 0.01:
        f.write("✅ **SYN-053 confirmed**: Q ≈ -2.08 at the edge of chaos.\n")
    else:
        f.write("❌ **SYN-053 refuted**: Q deviates from -2.08.\n")

# Plot
plt.figure(figsize=(8, 4))
plt.plot(x, y, ',', alpha=0.5)
plt.title(f'Hénon Map (a={a}, b={b}) | Q = {Q:.6f}')
plt.xlabel('x')
plt.ylabel('y')
plt.savefig('henon_q_critical_point_fallback.png')