import numpy as np

N = 1000; dt = 0.02; T = 50.0; sigma = 0.7

def run(K, seed=1, couple='on'):
    rng = np.random.default_rng(1000 + seed)
    th = rng.uniform(0, 2*np.pi, N)
    om = rng.normal(0, sigma, N)
    ns = int(T/dt); acc = 0.0
    for i in range(ns):
        z = np.exp(1j*th).mean()
        R = abs(z); psi = np.angle(z)
        if couple == 'on':
            th += dt*(om + K*R*np.sin(psi - th))
        else:
            th += dt*om
        if i > ns//2: acc += R
    return acc/(ns - ns//2)

for K, cp in [(0.0,'off'), (0.2,'on'), (0.5,'on'), (1.0,'on'), (1.2,'on'), (1.6,'on')]:
    print(f'K={K} couple={cp}: R_ss={run(K, couple=cp):.4f}')
print('theory: Kc = 1.117, floor ~ sqrt(pi/(4N)) =', round(float(np.sqrt(np.pi/(4*N))),4))