"""Edge-of-chaos complexity: interactions between perturbations (synergy/redundancy).

Claim (thomas_edge_of_chaos_complexity.py): complexity peaks where interactions vanish.
Test: does the peak in "complexity" coincide with MAXIMAL synergy among perturbation
responses, as expected at the edge of chaos?

Definitions (discrete information decomposition):
- Single-perturbation responses R_i (state deltas after 1/2/5/10 steps, normalized).
- Joint response R_{123} to all three perturbations together.
- Interaction Information / co-information:
    II = H(R1)+H(R2)+H(R3) - H(R1,R2) - H(R1,R3) - H(R2,R3) + H(R1,R2,R3)
  (positive = redundancy, negative = synergy)
We estimate entropies via k-NN (Kozachenko-Leonenko) on joint vectors.

For speed, responses are the full state-delta vectors over the whole lattice for
steps 1..T (each column = one realization over a coarse grid), so entropy estimates
are over the ensemble of (grid point) samples.
"""
import numpy as np
from math import lgamma, pi, log

rng = np.random.default_rng(0)

def theta(x): return np.tanh(x)
def lap(u): return np.roll(u,1)+np.roll(u,-1)+np.roll(u,0.1+0*u,1)*0  # placeholder

def laplacian(u):
    return np.roll(u,1)+np.roll(u,-1)-2*u

def rhs(u, a=1.0, d=0.05):
    return -u**3 + u + d*laplacian(u) - a

def simulate_step(u, dt=0.05):
    return theta(u + dt*rhs(u))

def run_ic(rng, N=200, T=400, dt=0.05):
    u = rng.normal(0,1,N)
    for _ in range(200):
        u = simulate_step(u, dt)
    traj = np.zeros((T,N))
    for t in range(T):
        u = simulate_step(u, dt)
        traj[t] = u
    return traj

def responses(traj, steps=(1,2,5,10), amp=1e-3):
    """Perturb each site individually and jointly at t=0, propagate the SAME trajectory."""
    N = traj.shape[1]
    base = traj[0].copy()
    R = {}
    for idx in [(i,) for i in range(3)] + [(0,1,2)]:
        u = base.copy(); u[list(idx)] += amp
        outs = []
        for s in steps:
            for _ in range(s):
                u = simulate_step(u)
            outs.append(u - base)
        R[idx] = np.concatenate(outs)
    return R

def kl_entropy(X, k=5):
    """Kozachenko-Leonenko entropy estimator; X: (n_samples, dim)."""
    n, d = X.shape
    if n <= k: return 0.0
    # pairwise distances (n modest)
    D = np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1))
    np.fill_diagonal(D, np.inf)
    dk = np.sort(D, axis=1)[:,k-1]
    dk = np.maximum(dk, 1e-12)
    # psi(n) - psi(k) + log(c_d) + d*mean(log dk)
    cd = (pi**(d/2))/ (np.exp(lgamma(d/2+1)))
    ent = (np.log(n) - np.log(k) + np.log(cd) + d*np.mean(np.log(dk)))
    return ent

def entropy_of(vecs):
    """vecs: list of vectors -> concatenate into samples, standardize, entropy."""
    X = np.stack(vecs, axis=1).T  # (samples, dims)
    X = X - X.mean(0)
    s = X.std(0); s[s<1e-12]=1
    X = X/s
    return kl_entropy(X, k=5)

def info_measures(R):
    r1,r2,r3 = R[(0,)], R[(1,)], R[(2,)]
    r123 = R[(0,1,2)]
    n = min(len(r1),len(r2),len(r3))
    # entropies
    h1,h2,h3 = entropy_of(r1[:n]), entropy_of(r2[:n]), entropy_of(r3[:n])
    h12 = entropy_of(np.stack([r1[:n],r2[:n]],1))
    h13 = entropy_of(np.stack([r1[:n],r3[:n]],1))
    h23 = entropy_of(np.stack([r2[:n],r3[:n]],1))
    h123 = entropy_of(np.stack([r1[:n],r2[:n],r3[:n]],1))
    II = h1+2*h2+h3  # placeholder overwritten below
    II = h1+h2+h3 - h12 - h13 - h23 + h123
    return dict(h1=h1,h2=h2,h3=h3,h12=h12,h13=h13,h23=h23,h123=h123, II=II)

if __name__ == "__main__":
    out = []
    for a in np.arange(0.5, 1.55, 0.05):
        r = run_ic(np.random.default_rng(1000+int(a*100)))
        R = responses(r)
        m = info_measures(R)
        out.append((a, m["II"]))
        print(f"a={a:.3f}  II={m['II']:+.4f}", flush=True)
    np.savetxt("thomas_synergy_II.csv", np.array(out), delimiter=",", header="alpha,II", comments="")
