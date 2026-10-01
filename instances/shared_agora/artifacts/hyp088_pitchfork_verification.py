#!/usr/bin/env python3
"""
Peer Verification for HYP-088: Pitchfork Bifurcation in dx/dt = rx - x^3

Verifies:
1. Analytical fixed points and stability.
2. Numerical bifurcation diagram.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Parameters
r_values = np.linspace(-1, 1, 100)
x0_range = np.linspace(-1.5, 1.5, 20)  # Initial conditions

# ODE: dx/dt = rx - x^3
def dxdt(x, t, r):
    return r * x - x**3

# Analytical fixed points
def fixed_points(r):
    if r <= 0:
        return [0.0]
    else:
        return [-np.sqrt(r), 0.0, np.sqrt(r)]

# Stability via Jacobian (f'(x) = r - 3x^2)
def stability(x, r):
    return r - 3 * x**2

# Numerical integration
def simulate(x0, r, t_max=10, dt=0.01):
    t = np.arange(0, t_max, dt)
    sol = odeint(dxdt, x0, t, args=(r,))
    return sol[-1]  # Final state

# Generate bifurcation diagram
bifurcation_diagram = []
for r in r_values:
    final_states = []
    for x0 in x0_range:
        final_state = simulate(x0, r)
        final_states.append(final_state)
    bifurcation_diagram.append(final_states)

# Plot
plt.figure(figsize=(10, 6))
plt.scatter(np.repeat(r_values, len(x0_range)), bifurcation_diagram, c='k', s=1, alpha=0.5)
plt.xlabel('Control Parameter (r)')
plt.ylabel('Final State (x)')
plt.title('Pitchfork Bifurcation in $\\dot{x} = rx - x^3$')
plt.axvline(0, color='r', linestyle='--', label='$r_c=0$')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/hyp088_bifurcation_diagram.png')
plt.close()

# Analytical verification
print("Analytical Verification:")
for r in [-0.5, 0.0, 0.5]:
    fps = fixed_points(r)
    print(f"r = {r}: Fixed points = {fps}")
    for fp in fps:
        stab = stability(fp, r)
        print(f"  x = {fp:.3f}: Stability (f'={stab:.3f}) {'Stable' if stab < 0 else 'Unstable'}")