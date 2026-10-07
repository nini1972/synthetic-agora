import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 200
dt = 0.02
T_trans = 100.0
T_per = 300.0
trans = int(T_trans/dt)
per = int(T_per/dt)
sigma_omega = 0.1
rng = np.random.default_rng(123)
omega = rng.normal(0, sigma_omega, N)
alpha = 1.0
K_grid = np.arange(4.0, 0.05, -0.1)

def run(K0, theta0):
    theta = theta0.copy()
    for s in range(trans):
        z = np.exp(1j*theta).mean()
        R = abs(z); psi = np.angle(z)
        K = K0 * (R**alpha)
        theta += dt*(omega + K*np.sin(psi-theta))
    Rs = []
    for s in range(per):
        z = np.exp(1j*theta).mean()
        R = abs(z); psi = np.angle(z)
        K = K0 * (R**alpha)
        theta += dt*(omega + K*np.sin(psi-theta))
        if s % 50 == 0:
            Rs.append(R)
    return np.mean(Rs[-100:]), theta

theta = np.zeros(N)
R_back = []
for K0 in K_grid:
    R, theta = run(K0, theta)
    R_back.append(R)
    print(f'K0={K0:.2f} R={R:.4f}')

plt.figure(figsize=(8,5))
plt.plot(K_grid, R_back, 'o-', label='backward coherent')
plt.xlabel('K0'); plt.ylabel('R')
plt.title(f'Deterministic alpha={alpha}, sigma={sigma_omega}')
plt.ylim(-0.05,1.05); plt.grid(True)
plt.legend()
plt.savefig('debug_alpha1_back.png')
print('saved debug_alpha1_back.png')
