"""Independent replication of SYN-054 spatiotemporal Lyapunov claims.
CML: x_i(t+1) = (1-eps) f(x_i) + (eps/2)[f(x_{i-1}) + f(x_{i+1})], f(x)=r x(1-x), periodic BC.
From scratch, no code reuse. Verify lambda_max at SYN-054's cited points.
"""
import numpy as np

def cml_step(x, r, eps):
    f = r*x*(1-x)
    return (1-eps)*f + 0.5*eps*(np.roll(f,1)+np.roll(f,-1))

def lambda_max(r, eps, L=128, nburn=20000, nsteps=60000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1,0.9,L)
    for _ in range(nburn):
        x = cml_step(x,r,eps)
    # tangent-space: single perturbation vector, Gram-Schmidt (only need largest)
    v = rng.standard_normal(L); v /= np.linalg.norm(v)
    acc = 0.0
    for _ in range(nsteps):
        # Jacobian J_ij = df/dx * coupling; f'(x)=r(1-2x)
        fp = r*(1-2*x)
        Jv = (1-eps)*fp*v + 0.5*eps*(np.roll(fp,1)*np.roll(v,1)+np.roll(fp,-1)*np.roll(v,-1))
        nrm = np.linalg.norm(Jv)
        if nrm < 1e-300: nrm = 1e-300
        acc += np.log(nrm)
        v = Jv/nrm
        x = cml_step(x,r,eps)
    return acc/nsteps

def cone_width(r, eps, L=128, npert=200, thresh=1e-8, seed=1):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1,0.9,L)
    for _ in range(20000): x = cml_step(x,r,eps)
    x0 = x.copy()
    c = L//2
    x0[c] += 1e-6
    n = 0
    for _ in range(npert):
        x = cml_step(x,r,eps); x0 = cml_step(x0,r,eps)
        n = np.sum(np.abs(x-x0) > thresh)
    return n

points = [
    ("resonant A", 3.845, 0.125, -0.047),
    ("resonant B", 3.860, 0.136, -0.081),
    ("chaotic A",  3.900, 0.103, +0.337),
    ("chaotic B",  3.923, 0.136, +0.211),
]
print("point        r      eps    lambda_max(mine)  claimed   cone/128")
for name,r,eps,claim in points:
    lam = lambda_max(r,eps)
    cw = cone_width(r,eps)
    print("%-11s %.3f  %.3f   %+8.4f        %+7.3f   %d"%(name,r,eps,lam,claim,cw))
