#!/usr/bin/env python3
"""
Replicate the Aizawa attractor locally to verify EMP-114.

Equations:
    dx/dt = (z - b)x - dy
    dy/dt = dx + (z - b)y
    dz/dt = c + az - z^3/3 - (x^2 + y^2)(1 + ez) + fzx^3

Parameters: a=0.95, b=0.7, c=0.6, d=3.5, e=0.25, f=0.1
"""

import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

# Parameters
a, b, c, e, f = 0.95, 0.7, 0.6, 0.25, 0.1

# Aizawa system
def aizawa(state, t):
    x, y, z = state
    dxdt = (z - b) * x - y
    dydt = x + (z - b) * y
    dzdt = c + a * z - (z**3) / 3 - (x**2 + y**2) * (1 + e * z) + f * z * x**3
    return [dxdt, dydt, dzdt]

# Initial conditions and time span
state0 = [0.1, 0.0, 0.0]
t = np.linspace(0, 100, 10000)

# Integrate
states = odeint(aizawa, state0, t)

# Plot x-y projection
plt.figure(figsize=(10, 8))
plt.plot(states[:, 0], states[:, 1], lw=0.5, color='blue')
plt.title('Aizawa Attractor (x-y Projection)')
plt.xlabel('x')
plt.ylabel('y')
plt.grid(True)
plt.savefig('aizawa_attractor_replication.png')

# Save trajectory data
np.save('aizawa_attractor_replication.npy', states)

print("Replication complete. Artifacts saved:")
print("- aizawa_attractor_replication.png")
print("- aizawa_attractor_replication.npy")