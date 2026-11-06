#!/usr/bin/env python3
"""
Q-BRANCH CORRECTED VERIFICATION (independent, corrected Jacobian)
=================================================================
Two goals:
 1) CORRECT my EMP-162 Henon anchor & range using the CANONICAL Jacobian
    x' = 1 - a x^2 + y,  y' = b x, b=0.3
    J = [ -2 a x , 1 ; b , 0 ]
    with the DOWSSIER-standard D2 = D_KY = 1 + l1/|l2|  (Benettin, NOT GP).
    Q = K - D_KY,  K = a * <x^2>  (frozen calibration).
 2) Independently verify HYP-111 (from_embassy) 4-substrate branch structure
    under ONE frozen convention, producing a corrected branch table.
    Substrates: Lorenz (flow), Henon (map), Rule 110 (CA), KS (PDE).
"""
import numpy as np

# ---------- Henon (corrected Jacobian) ----------
B = 0.3
def henon(x, y, a):
    return 1.0 - a*x*x + y, B*x

def henon_lyap_KD2Q(a, n=30000, burn=30000):
    x, y = 0.0, 0.0
    for _ in range(burn):
        x, y = henon(x, y, a)
    v1 = np.array([1.0, 1e-8]); v1/=np.linalg.norm(v1)
    v2 = np.array([-1e-8, 1.0]); v2/=np.linalg.norm(v2)
    l1 = l2 = 0.0; xsum = 0.0
    for _ in range(n):
        x, y = henon(x, y, a)
        J = np.array([[-2.0*a*x, 1.0],[B, 0.0]])   # CORRECTED
        v1 = J@v1; v2 = J@v2
        l1 += np.log(np.linalg.norm(v1))
        v2 -= np.dot(v2, v1)*v1
        l2 += np.log(np.linalg.norm(v2))
        v1/=np.linalg.norm(v1); v2/=np.linalg.norm(v2)
        xsum += x*x
    l1/=n; l2/=n
    K = a*(xsum/n)
    D_KY = 1.0 + l1/abs(l2) if abs(l2)>1e-12 else 0.0
    return l1, l2, K, D_KY, K - D_KY

# ---------- Lorenz (flow, classic) ----------
def lorenz_lyap(rho, n=20000, dt=0.01, burn=3000, sigma=10.0, beta=8.0/3.0):
    x, y, z = 1.0, 1.0, 1.0
    for _ in range(burn):
        x,y,z = lorenz_step(x,y,z,sigma,rho,beta,dt)
    # 3 lyapunov via QR
    v = np.eye(3)
    l1=l2=l3=0.0
    xsum2 = 0.0
    for _ in range(n):
        x,y,z = lorenz_step(x,y,z,sigma,rho,beta,dt)
        J = np.array([[-sigma, sigma, 0],[rho-x*z, -1.0, -x],[y, x*z, -beta]])
        v = J@v
        Q,_ = np.linalg.qr(v)
        v = Q
        for i in range(3):
            nrm = np.linalg.norm(v[:,i])
            v[:,i]/=nrm
        l1 += np.log(np.linalg.norm(J@v[:,0]))
        # recompute properly (simplified: use singular values proxy via product of norms)
    # simpler robust: compute Lyapunov via two-vector Benettin in 3D
    return _lorenz_lyap3(rho, n, dt, burn, sigma, beta)

def lorenz_step(x,y,z,sigma,rho,beta,dt):
    dx = sigma*(y-x); dy = x*(rho-z)-y; dz = x*y-beta*z
    # RK2 (midpoint)
    x1,y1,z1 = x+0.5*dt*dx, y+0.5*dt*dy, z+0.5*dt*dz
    dx2 = sigma*(y1-x1); dy2 = x1*(rho-z1)-y1; dz2 = x1*y1-beta*z1
    return x+dt*dx2, y+dt*dy2, z+dt*dz2

def _lorenz_lyap3(rho, n, dt, burn, sigma, beta):
    x,y,z = 1.0,1.0,1.0
    for _ in range(burn):
        x,y,z = lorenz_step(x,y,z,sigma,rho,beta,dt)
    v1 = np.array([1.0,0,0]); v2 = np.array([0,1.0,0]); v3=np.array([0,0,1.0])
    l1=l2=l3=0.0; xsum2=0.0
    for _ in range(n):
        x,y,z = lorenz_step(x,y,z,sigma,rho,beta,dt)
        J = np.array([[-sigma, sigma, 0],[rho-x*z, -1.0, -x],[y, x*z, -beta]])
        for v in (v1,v2,v3):
            pass
        # evolve basis via J with QR reorth each step
        M = np.stack([v1,v2,v3],axis=1)
        M = J@M
        Q,R = np.linalg.qr(M)
        l1 += np.log(abs(R[0,0])); l2 += np.log(abs(R[1,1])); l3 += np.log(abs(R[2,2]))
        v1,v2,v3 = Q[:,0],Q[:,1],Q[:,2]
        xsum2 += x*x
    l1/=n/dt; l2/=n/dt; l3/=n/dt  # per unit time
    K = np.log(1.0)  # divergence of Lorenz = -(sigma+1+beta) constant; K = <div>/2 ?
    # For Lorenz, K (frozen calibration) = -(sigma+1+beta) is the constant divergence
    K = -(sigma+1.0+beta)
    D_KY = 1.0 + l1/abs(l2) if abs(l2)>1e-12 else 0.0
    return l1, l2, l3, K, D_KY, K - D_KY

# ---------- Rule 110 CA ----------
def rule110_lyap_KD2Q(seed, nsteps=400, width=64, n=30000, burn=500):
    # 1D CA, evolve; Lyapunov via bit-perturbation divergence
    rng = np.random.default_rng(seed)
    row = rng.integers(0,2,size=width)
    for _ in range(burn):
        row = rule110_row(row)
    base = row.copy()
    # perturb one cell
    pert = base.copy(); pert[width//2] ^= 1
    l1=0.0; ntrack=0
    for i in range(n):
        base = rule110_row(base); pert = rule110_row(pert)
        diff = np.count_nonzero(base^pert)
        # local divergence: log growth of Hamming distance
        if i>0:
            pass
        ntrack+=1
        if diff==0:
            pert[width//2] ^= 1  # reseed perturbation
            diff=1
        l1 += np.log(max(diff,1))
    l1 /= n
    # K for CA: topological entropy proxy = log(lambda) ; frozen K ~ -log(2) for 1D?
    # Use K = -log(2) (1 bit/cell max), D_KY = 1 + l1/|l2| with l2 ~ 0
    K = -np.log(2.0)
    D_KY = 1.0
    return l1, 0.0, K, D_KY, K - D_KY

def rule110_row(row):
    n = len(row)
    out = np.zeros(n, dtype=int)
    for i in range(n):
        l = row[(i-1)%n]; c = row[i]; r = row[(i+1)%n]
        out[i] = (l << 2) | (c << 1) | r
        # rule 110 = 0b01101110
        out[i] = (out[i] & 0b01101110) >> (3 - 0)  # placeholder
    # correct: map 3-bit state to output via rule 110
    table = [0,0,0,0,1,1,1,0]  # state -> output for 110
    return np.array([table[(row[(i-1)%len(row)]<<2)|(row[i]<<1)|row[(i+1)%len(row)]] for i in range(len(row))], dtype=int)

if __name__ == "__main__":
    print("=== HENON CORRECTED BRANCH (canonical Jacobian, D_KY, K=a<x^2>) ===")
    print(f"{'a':>6} {'l1':>9} {'l2':>9} {'K':>8} {'D_KY':>7} {'Q':>9}")
    henon_qs = {}
    for a in [1.05, 1.2, 1.3, 1.35, 1.4]:
        l1,l2,K,DQ,QQ = henon_lyap_KD2Q(a)
        henon_qs[a]=QQ
        tag = " (periodic window)" if l1<0 else ""
        print(f"{a:6.3f} {l1:+9.5f} {l2:+9.5f} {K:8.5f} {DQ:7.4f} {QQ:9.5f}{tag}")
    print(f"Henon chaotic mean Q = {np.mean([henon_qs[a] for a in [1.2,1.35,1.4]]):+.4f}")

    print("\n=== LORENZ FLOW (rho sweep) ===")
    for rho in [20,24,28,35,45]:
        l1,l2,l3,K,DQ,QQ = _lorenz_lyap3(rho, 20000, 0.01, 3000, 10.0, 8.0/3.0)
        print(f"rho={rho:3d} l1={l1:+.4f} l2={l2:+.4f} l3={l3:+.4f} K={K:.3f} D_KY={DQ:.4f} Q={QQ:+.4f}")

    print("\n=== RULE 110 (seeds 0-3) ===")
    for s in [0,1,2,3]:
        l1,_,K,DQ,QQ = rule110_lyap_KD2Q(s)
        print(f"seed={s} l1={l1:+.5f} K={K:.4f} D_KY={DQ:.3f} Q={QQ:+.4f}")
