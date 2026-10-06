import numpy as np

# System parameters
r = 3.8625
epsilon = 0.132
n = 320
h = 1440

# Initialize lattice
x = np.random.rand(n)

# Time-stepping
for t in range(h):
    x_new = (1-epsilon) * r * x * (1-x) + (epsilon/2) * r * (np.roll(x, -1) * (1-np.roll(x, -1)) + np.roll(x, 1) * (1-np.roll(x, 1)))
    x = x_new

# Binary field and motif width
b = np.where(x >= np.median(x), 1, 0)

# Parity observable
P_w = np.mean(np.correlate(b, b, mode='full')[len(b):]) - np.mean(np.correlate(b, b, mode='full')[:len(b)])

print(P_w)